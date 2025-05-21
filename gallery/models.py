from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import PublicModel, TimeStampedModel
from django.conf import settings
from growlogs.models import GrowLog, GrowLogEntry

class Photo(PublicModel):
    """
    Represents a photo in the gallery.
    """
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    image = models.ImageField(_("Image"), upload_to='gallery/')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='photos')
    growlog = models.ForeignKey(GrowLog, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    growlog_entry = models.ForeignKey(GrowLogEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_photos', blank=True)
    
    class Meta:
        verbose_name = _("Photo")
        verbose_name_plural = _("Photos")
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title

class PhotoComment(TimeStampedModel):
    """
    Represents a comment on a photo.
    """
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='photo_comments')
    text = models.TextField(_("Comment"))
    
    class Meta:
        verbose_name = _("Photo Comment")
        verbose_name_plural = _("Photo Comments")
        ordering = ['created_at']
        
    def __str__(self):
        return f"Comment by {self.author.username} on {self.photo.title}"
