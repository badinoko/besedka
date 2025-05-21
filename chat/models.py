from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel
from django.conf import settings

class ChatMessage(TimeStampedModel):
    """
    Represents a chat message.
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    text = models.TextField(_("Message"))
    is_system = models.BooleanField(_("System Message"), default=False)
    
    class Meta:
        verbose_name = _("Chat Message")
        verbose_name_plural = _("Chat Messages")
        ordering = ['created_at']
        
    def __str__(self):
        return f"Message by {self.author.username} at {self.created_at}"
