"""Uploads and attachments shared by both question storage formats."""
import io
import json
import uuid
import warnings

from PIL import Image, ImageOps
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .decorators import role_required
from .models import QuestionImage

MAX_IMAGES = 8
MAX_BYTES = 5 * 1024 * 1024


def image_data(question):
    return [{'id': image.pk, 'url': image.image.url, 'caption': image.caption}
            for image in question.images.all().order_by('pk')]


def read_image_data(request, test=None):
    if 'question_images' in request.POST:
        data = json.loads(request.POST['question_images'])
        if not isinstance(data, list) or any(not isinstance(row, list) or len(row) > MAX_IMAGES for row in data):
            raise ValueError('Некорректный список изображений.')
        return data
    if test is None:
        return None
    # Compatibility with an already open editor using the previous JS version.
    rows = [variant for group in test.task_groups.order_by('number', 'pk')
            for variant in group.variants.order_by('pk')]
    rows += list(test.expressions.order_by('block_expression_num', 'number', 'pk'))
    return [image_data(row) for row in rows]


def attach_images(question, rows, index, user):
    if rows is None or index >= len(rows):
        return
    selected = []
    for entry in rows[index]:
        if not isinstance(entry, dict) or type(entry.get('id')) is not int:
            raise ValueError('Некорректное изображение задания.')
        images = QuestionImage.objects.select_for_update().filter(pk=entry['id'])
        if not user.is_superuser and user.role != 'admin':
            images = images.filter(uploader=user)
        image = images.first()
        if image is None:
            raise ValueError('Изображение не найдено или принадлежит другому преподавателю.')
        caption = entry.get('caption', '')
        if not isinstance(caption, str) or len(caption) > 500:
            raise ValueError('Подпись изображения должна содержать не более 500 символов.')
        image.caption = caption.strip()
        image.save(update_fields=['caption'])
        selected.append(image)
    question.images.set(selected)


@login_required
@role_required(['teacher', 'admin'])
@require_POST
def upload_question_image(request):
    uploaded = request.FILES.get('image')
    if uploaded is None or uploaded.size > MAX_BYTES:
        return JsonResponse({'error': 'Выберите изображение размером до 5 МБ.'}, status=400)
    try:
        field = forms.ImageField()
        uploaded = field.clean(uploaded)
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(uploaded) as original:
                if original.format not in ('JPEG', 'PNG', 'WEBP'):
                    raise ValueError('Поддерживаются PNG, JPEG и WebP.')
                if original.width * original.height > 20_000_000:
                    raise ValueError('Изображение слишком большое: максимум 20 мегапикселей.')
                image = ImageOps.exif_transpose(original)
                image.load()
                # Re-encode pixels instead of storing arbitrary uploaded bytes.
                output = io.BytesIO()
                if original.format == 'JPEG':
                    image.convert('RGB').save(output, format='JPEG', quality=90)
                    suffix = '.jpg'
                else:
                    image.save(output, format='PNG')
                    suffix = '.png'
        if output.tell() > MAX_BYTES:
            raise ValueError('После обработки размер изображения превышает 5 МБ.')
        record = QuestionImage(uploader=request.user)
        record.image.save(uuid.uuid4().hex + suffix, ContentFile(output.getvalue()), save=True)
        return JsonResponse({'id': record.pk, 'url': record.image.url, 'caption': ''}, status=201)
    except (ValueError, forms.ValidationError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        return JsonResponse({'error': str(error) if isinstance(error, ValueError) else 'Не удалось прочитать изображение. Используйте PNG, JPEG или WebP.'}, status=400)
