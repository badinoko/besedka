from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

class SeedBank(models.Model):
    name = models.CharField(_("Название"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, blank=True)
    description = models.TextField(_("Описание"), blank=True)
    website = models.URLField(_("Веб-сайт"), blank=True)
    logo = models.ImageField(_("Логотип"), upload_to='seedbanks/logos/', blank=True)
    is_active = models.BooleanField(_("Виден"), default=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    class Meta:
        verbose_name = _("Сидбанк")
        verbose_name_plural = _("Сидбанки")
        ordering = ['name']
        app_label = 'magicbeans_store'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
