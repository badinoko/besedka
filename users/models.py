from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom user model with Telegram integration.
    """
    ROLE_CHOICES = (
        ('owner', _('Owner')),
        ('admin', _('Admin')),
        ('store_owner', _('Store Owner')),
        ('user', _('User')),
        ('guest', _('Guest')),
    )
    
    telegram_id = models.CharField(_("Telegram ID"), max_length=100, unique=True, null=True)
    role = models.CharField(_("Role"), max_length=20, choices=ROLE_CHOICES, default='user')
    avatar = models.ImageField(_("Avatar"), upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(_("Bio"), blank=True)
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        
    def __str__(self):
        return self.username or self.telegram_id
