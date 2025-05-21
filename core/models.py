from django.db import models
from django.utils.translation import gettext_lazy as _

class TimeStampedModel(models.Model):
    """
    Abstract base class model that provides self-updating
    created and modified fields.
    """
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        abstract = True

class PublicModel(TimeStampedModel):
    """
    Abstract base class model that provides public/private visibility.
    """
    is_public = models.BooleanField(_("Public"), default=True)
    
    class Meta:
        abstract = True
