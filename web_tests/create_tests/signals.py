import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


def get_pusher_client():
    try:
        import pusher
        return pusher.Pusher(
            app_id=settings.PUSHER_APP_ID,
            key=settings.PUSHER_KEY,
            secret=settings.PUSHER_SECRET,
            cluster=settings.PUSHER_CLUSTER,
            ssl=True,
        )
    except Exception as e:
        logger.warning(f"Pusher init failed: {e}")
        return None


@receiver(pre_save, sender='create_tests.AboutTest')
def track_is_published(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_is_published = sender.objects.get(pk=instance.pk).is_published
        except sender.DoesNotExist:
            instance._old_is_published = None
    else:
        instance._old_is_published = None


@receiver(post_save, sender='create_tests.AboutTest')
def notify_test_availability(sender, instance, **kwargs):
    old = getattr(instance, '_old_is_published', None)
    if old is None or old == instance.is_published:
        return

    client = get_pusher_client()
    if not client:
        return

    try:
        client.trigger(
            f'test-{instance.name_slug_tests}',
            'availability-changed',
            {'is_published': instance.is_published},
        )
        logger.info(f"Pusher event sent for test '{instance.name_slug_tests}': is_published={instance.is_published}")
    except Exception as e:
        logger.error(f"Pusher trigger failed for test '{instance.name_slug_tests}': {e}")
