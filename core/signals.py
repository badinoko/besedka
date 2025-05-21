from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from .utils import log_login, log_logout, log_add, log_edit, log_delete

# Import models to monitor
from magicbeans_store.models import SeedBank, Strain, StockItem
from growlogs.models import GrowLog, GrowLogEntry
from gallery.models import Photo, PhotoComment
from chat.models import ChatMessage

# List of models to monitor for changes
MONITORED_MODELS = [SeedBank, Strain, StockItem, GrowLog, GrowLogEntry, Photo, PhotoComment]

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Signal handler to log user login events.
    """
    log_login(user)

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    Signal handler to log user logout events.
    """
    if user:  # User might be None if session is corrupted
        log_logout(user)

# Register post_save signal for each monitored model
for model in MONITORED_MODELS:
    @receiver(post_save, sender=model)
    def model_saved(sender, instance, created, **kwargs):
        """
        Signal handler for model save events.
        Logs creation or update of monitored models.
        """
        # Skip logging if we don't have a request user context
        if not hasattr(instance, '_change_user'):
            return
            
        if created:
            log_add(instance._change_user, instance)
        else:
            log_edit(instance._change_user, instance)

# Register post_delete signal for each monitored model
for model in MONITORED_MODELS:
    @receiver(post_delete, sender=model)
    def model_deleted(sender, instance, **kwargs):
        """
        Signal handler for model delete events.
        Logs deletion of monitored models.
        """
        # Skip logging if we don't have a request user context
        if not hasattr(instance, '_change_user'):
            return
            
        log_delete(
            instance._change_user,
            instance.__class__,
            instance.pk,
            str(instance)
        ) 