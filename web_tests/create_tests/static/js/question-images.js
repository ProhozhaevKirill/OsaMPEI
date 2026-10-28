(() => {
    const uploadUrl = document.currentScript.dataset.questionImageUpload;
    let uploading = 0;
    const notice = (panel, message) => panel.querySelector('.question-images-status').textContent = message;
    const changed = panel => panel.querySelector('input[type="file"]').dispatchEvent(new Event('input', {bubbles: true}));
    const add = (panel, image) => {
        const row = document.createElement('div');
        row.className = 'question-image-row';
        row.dataset.imageId = image.id;
        const preview = document.createElement('img');
        preview.src = image.url;
        preview.alt = 'Предпросмотр иллюстрации';
        const label = document.createElement('label');
        label.textContent = 'Подпись к изображению';
        const caption = document.createElement('input');
        caption.type = 'text';
        caption.className = 'question-image-caption';
        caption.maxLength = 500;
        caption.placeholder = 'Например: Рисунок 1. Схема цепи';
        caption.value = image.caption || '';
        label.append(caption);
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'question-image-remove';
        remove.textContent = 'Удалить';
        // Delegated listeners also work when a variant is cloned by jQuery.
        row.append(preview, label, remove);
        panel.querySelector('.question-images-list').append(row);
    };
    const initialize = variant => {
        let panel = variant.querySelector('.question-images-editor');
        if (panel) return panel;
        panel = document.createElement('section');
        panel.className = 'question-images-editor';
        panel.innerHTML = '<div class="question-images-heading">Иллюстрации к заданию</div>' +
            '<div class="question-images-list"></div>' +
            '<label class="question-image-upload">Добавить изображения' +
            '<input type="file" accept="image/png,image/jpeg,image/webp" multiple></label>' +
            '<p class="question-images-hint">PNG, JPEG или WebP · до 5 МБ · не больше 8 изображений</p>' +
            '<p class="question-images-status" role="status"></p>';
        const seed = variant.querySelector('.question-images-seed');
        let images = [];
        try { images = JSON.parse(seed?.querySelector('script').textContent || '[]'); } catch (_) {}
        variant.querySelector('.expression').after(panel);
        (images || []).forEach(image => add(panel, image));
        seed?.remove();
        return panel;
    };
    window.QuestionImages = {
        get(variant) {
            const panel = initialize(variant);
            return [...panel.querySelectorAll('.question-image-row')].map(row => ({
                id: Number(row.dataset.imageId), url: row.querySelector('img').getAttribute('src'),
                caption: row.querySelector('.question-image-caption').value,
            }));
        },
        set(variant, images) {
            const panel = initialize(variant);
            panel.querySelector('.question-images-list').replaceChildren();
            images.forEach(image => add(panel, image));
        },
    };
    document.addEventListener('DOMContentLoaded', () => {
        const container = document.getElementById('taskGroupsContainer');
        if (!container) return;
        const initializeAll = () => container.querySelectorAll('.task-variant').forEach(initialize);
        initializeAll();
        new MutationObserver(initializeAll).observe(container, {childList: true, subtree: true});
        document.addEventListener('click', event => {
            if (uploading && event.target.closest('#save-draft-btn')) {
                event.preventDefault();
                event.stopImmediatePropagation();
                alert('Дождитесь загрузки изображений перед сохранением.');
            }
        }, true);
        container.addEventListener('click', event => {
            if (!event.target.matches('.question-image-remove')) return;
            const panel = event.target.closest('.question-images-editor');
            event.target.closest('.question-image-row').remove();
            notice(panel, '');
            changed(panel);
        });
        container.addEventListener('change', async event => {
            if (!event.target.matches('.question-image-upload input')) return;
            const input = event.target;
            const panel = input.closest('.question-images-editor');
            const files = [...input.files];
            if (panel.querySelectorAll('.question-image-row').length + files.length > 8) {
                notice(panel, 'Можно добавить не больше 8 изображений к варианту.');
                input.value = '';
                return;
            }
            uploading++;
            input.disabled = true;
            try {
                for (const file of files) {
                    if (file.size > 5 * 1024 * 1024) throw Error('Размер каждого изображения — до 5 МБ.');
                    notice(panel, 'Загружаем изображение…');
                    const data = new FormData();
                    data.append('image', file);
                    const response = await fetch(uploadUrl, {
                        method: 'POST', credentials: 'same-origin', body: data,
                        headers: {'X-CSRFToken': document.querySelector('#testForm [name=csrfmiddlewaretoken]').value},
                    });
                    if (!response.headers.get('content-type')?.includes('application/json')) throw Error('Не удалось загрузить изображение. Проверьте подключение и вход в аккаунт.');
                    const image = await response.json();
                    if (!response.ok) throw Error(image.error || 'Не удалось загрузить изображение.');
                    add(panel, image);
                    changed(panel);
                }
                notice(panel, '');
            } catch (error) {
                notice(panel, error.message);
            } finally {
                uploading--;
                input.value = '';
                input.disabled = false;
            }
        });
        document.addEventListener('submit', event => {
            if (event.target.id !== 'testForm') return;
            if (uploading) {
                event.preventDefault();
                event.stopImmediatePropagation();
                alert('Дождитесь загрузки изображений перед сохранением.');
                return;
            }
            let field = event.target.querySelector('[name="question_images"]');
            if (!field) {
                field = document.createElement('input');
                field.type = 'hidden';
                field.name = 'question_images';
                event.target.append(field);
            }
            field.value = JSON.stringify([...container.querySelectorAll('.task-variant')].map(window.QuestionImages.get));
        }, true);
    });
})();
