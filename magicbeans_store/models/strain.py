from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .managers import StrainManager

class Strain(models.Model):
    STRAIN_TYPES = [
        ('regular', _("Регулярный")),
        ('feminized', _("Феминизированный")),
        ('autoflowering', _("Автоцветущий")),
    ]

    THC_CONTENT_CHOICES = [
        ('0-5', '0-5%'),
        ('5-10', '5-10%'),
        ('10-15', '10-15%'),
        ('15-20', '15-20%'),
        ('20-25', '20-25%'),
        ('25-30', '25-30%'),
        ('30+', '30%+'),
        ('unknown', 'Неизвестно'),
    ]

    CBD_CONTENT_CHOICES = [
        ('0-0.5', '0-0.5%'),
        ('0.5-1', '0.5-1%'),
        ('1-1.5', '1-1.5%'),
        ('1.5-2', '1.5-2%'),
        ('2-2.5', '2-2.5%'),
        ('2.5-3', '2.5-3%'),
        ('3+', '3%+'),
        ('unknown', 'Неизвестно'),
    ]

    FLOWERING_TIME_CHOICES = [
        ('6-8', '6-8 недель'),
        ('8-10', '8-10 недель'),
        ('10-12', '10-12 недель'),
        ('12+', '12+ недель'),
        ('auto', 'Автоцвет'),
        ('unknown', 'Неизвестно'),
    ]

    name = models.CharField(_("Название"), max_length=255)
    seedbank = models.ForeignKey(
        'magicbeans_store.SeedBank',
        on_delete=models.CASCADE,
        verbose_name=_("Сидбанк"),
        related_name='strains',
        null=True,
        blank=True
    )
    strain_type = models.CharField(
        _("Тип"),
        max_length=20,
        choices=STRAIN_TYPES,
        default='regular'
    )
    description = models.TextField(_("Описание"), blank=True)
    genetics = models.CharField(_("Генетика"), max_length=255, blank=True)
    thc_content = models.CharField(
        _("Содержание THC"),
        max_length=20,
        choices=THC_CONTENT_CHOICES,
        blank=True,
        default='unknown'
    )
    cbd_content = models.CharField(
        _("Содержание CBD"),
        max_length=20,
        choices=CBD_CONTENT_CHOICES,
        blank=True,
        default='unknown'
    )
    flowering_time = models.CharField(
        _("Время цветения"),
        max_length=20,
        choices=FLOWERING_TIME_CHOICES,
        blank=True,
        default='unknown'
    )
    height = models.CharField(_("Высота"), max_length=50, blank=True)
    yield_indoor = models.CharField(_("Урожайность (indoor)"), max_length=50, blank=True)
    yield_outdoor = models.CharField(_("Урожайность (outdoor)"), max_length=50, blank=True)
    effect = models.TextField(_("Эффект"), blank=True)
    flavor = models.TextField(_("Вкус и аромат"), blank=True)
    is_active = models.BooleanField(_("Виден"), default=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    # Менеджеры
    objects = StrainManager()

    class Meta:
        verbose_name = _("Сорт")
        verbose_name_plural = _("Сорта")
        ordering = ['seedbank', 'name']
        unique_together = ['seedbank', 'name']

    def __str__(self):
        return f"{self.seedbank.name} - {self.name}"

    @property
    def has_stock(self):
        """Проверяет наличие товара на складе"""
        return self.stock_items.filter(is_active=True, quantity__gt=0).exists()

    def get_min_price(self):
        """Получает минимальную цену среди доступных товаров"""
        stock_items = self.stock_items.filter(is_active=True, quantity__gt=0)
        if stock_items.exists():
            return stock_items.order_by('price').first().price
        return None

    def get_primary_image(self):
        """Получает основное изображение сорта"""
        primary_image = self.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image
        # Если нет основного, возвращаем первое по порядку
        return self.images.first()

    def get_image_url(self):
        """Получает URL основного изображения или дефолтного"""
        primary_image = self.get_primary_image()
        if primary_image and primary_image.image:
            return primary_image.image.url
        # Возвращаем дефолтное изображение
        return '/static/images/default_strain.jpg'

    def has_images(self):
        """Проверяет наличие изображений"""
        return self.images.exists()

    def get_absolute_url(self):
        """Получает абсолютный URL для модели Strain"""
        return reverse('store:strain_detail', args=[self.id])
