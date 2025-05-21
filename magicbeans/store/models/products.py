from django.db import models
from django.utils.translation import gettext_lazy as _


class SeedBank(models.Model):
    """Модель сидбанка (производителя семян)."""
    name = models.CharField(_("Название"), max_length=255)
    logo = models.ImageField(
        _("Логотип"), upload_to="seedbanks/", blank=True, null=True,
    )
    description = models.TextField(_("Описание"), blank=True)
    is_visible = models.BooleanField(_("Отображается"), default=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)

    class Meta:
        verbose_name = _("Сидбанк")
        verbose_name_plural = _("Сидбанки")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Strain(models.Model):
    """Модель сорта семян."""
    TYPE_AUTO = "auto"
    TYPE_PHOTO = "photo"
    TYPE_REGULAR = "regular"

    TYPE_CHOICES = [
        (TYPE_AUTO, _("Автоцветущий")),
        (TYPE_PHOTO, _("Фотопериодный")),
        (TYPE_REGULAR, _("Регулярный")),
    ]

    name = models.CharField(_("Название"), max_length=255)
    description = models.TextField(_("Описание"), blank=True)
    strain_type = models.CharField(
        _("Тип сорта"),
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_PHOTO,
    )
    seed_bank = models.ForeignKey(
        SeedBank,
        on_delete=models.CASCADE,
        related_name="strains",
        verbose_name=_("Сидбанк"),
    )
    is_visible = models.BooleanField(_("Отображается"), default=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)

    class Meta:
        verbose_name = _("Сорт")
        verbose_name_plural = _("Сорта")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.seed_bank.name})"


class StrainImage(models.Model):
    """Изображение сорта."""
    image = models.ImageField(_("Изображение"), upload_to="strains/")
    strain = models.ForeignKey(
        Strain,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Сорт"),
    )
    order = models.PositiveSmallIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Изображение сорта")
        verbose_name_plural = _("Изображения сортов")
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["strain", "order"],
                name="unique_strain_image_order",
            ),
        ]

    def __str__(self):
        return f"{self.strain.name} - {self.order}"
