from django.db import models
from django.utils.translation import gettext_lazy as _


class StrainImage(models.Model):
    """Изображение сорта."""
    image = models.ImageField(
        _("Изображение"),
        upload_to="strains/",
        help_text=_("Изображение товара")
    )
    strain = models.ForeignKey(
        'magicbeans_store.Strain',
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Сорт"),
    )
    order = models.PositiveSmallIntegerField(_("Порядок"), default=0)
    is_primary = models.BooleanField(_("Основное изображение"), default=False)
    alt_text = models.CharField(
        _("Альтернативный текст"),
        max_length=255,
        blank=True,
        help_text=_("Описание изображения для доступности")
    )
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Изображение сорта")
        verbose_name_plural = _("Изображения сортов")
        ordering = ["order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["strain", "order"],
                name="unique_strain_image_order",
            ),
        ]

    def __str__(self):
        return f"{self.strain.name} - {self.order}"

    def save(self, *args, **kwargs):
        # Если это первое изображение для сорта, делаем его основным
        if not self.strain.images.exists():
            self.is_primary = True
            self.order = 0

        # Если установлено как основное, убираем флаг у других
        if self.is_primary:
            self.strain.images.exclude(id=self.id).update(is_primary=False)

        super().save(*args, **kwargs)
