from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from core.models import PublicModel, TimeStampedModel, BaseComment
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
    is_public = models.BooleanField(default=True, verbose_name="Публичное")
    is_active = models.BooleanField(default=True, verbose_name="Активное")
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_photos', blank=True)

    # Счётчик просмотров для системы кармы / аналитики
    views_count = models.PositiveIntegerField("Просмотры", default=0)

    # Обратная совместимость: некоторые части проекта обращаются к `views` напрямую.
    @property
    def views(self):
        return self.views_count

    class Meta:
        verbose_name = _("Photo")
        verbose_name_plural = _("Photos")
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('gallery:photo_detail', args=[self.id])

class PhotoComment(BaseComment):
    """
    Represents a comment on a photo with support for nested comments.
    """
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')

    class Meta:
        verbose_name = _("Photo Comment")
        verbose_name_plural = _("Photo Comments")
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.photo.title}"
