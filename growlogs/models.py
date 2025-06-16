from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import PublicModel, TimeStampedModel, BaseComment
from django.conf import settings
from magicbeans_store.models import Strain
from django.urls import reverse

class GrowLog(PublicModel):
    """
    Represents a grow diary/log.
    """
    STAGE_CHOICES = [
        ('germination', 'Проращивание'),
        ('seedling', 'Рассада'),
        ('vegetative', 'Вегетация'),
        ('flowering', 'Цветение'),
        ('harvest', 'Харвест'),
        ('curing', 'Пролечка'),
        ('completed', 'Завершено'),
    ]

    ENVIRONMENT_CHOICES = [
        ('indoor', 'Индор'),
        ('outdoor', 'Аутдор'),
        ('greenhouse', 'Теплица'),
    ]

    title = models.CharField("Название", max_length=255)
    logo = models.ImageField("Логотип", upload_to='growlogs/logos/', blank=True, null=True,
                           help_text="Логотип или главное фото гроу-репорта")
    grower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='growlogs')
    strain = models.ForeignKey(Strain, on_delete=models.SET_NULL, null=True, blank=True, related_name='growlogs')
    strain_custom = models.CharField("Название сорта", max_length=255, blank=True,
                                   help_text="Название сорта если его нет в магазине")
    start_date = models.DateField("Дата начала")
    end_date = models.DateField("Дата окончания", null=True, blank=True)

    # Настройка grow
    environment = models.CharField("Среда выращивания", max_length=20, choices=ENVIRONMENT_CHOICES, default='indoor')
    medium = models.CharField("Субстрат", max_length=255, blank=True)
    nutrients = models.TextField("Удобрения", blank=True)
    lighting = models.CharField("Освещение", max_length=255, blank=True)
    container_size = models.CharField("Размер контейнера", max_length=100, blank=True)

    # Описания
    setup_description = models.TextField("Описание установки")
    short_description = models.CharField("Краткое описание", max_length=500, blank=True,
                                       help_text="Краткое описание для карточки")
    goals = models.TextField("Цели", blank=True)

    # Статистика
    current_stage = models.CharField("Текущая стадия", max_length=20, choices=STAGE_CHOICES, default='germination')
    yield_actual = models.DecimalField("Фактический урожай (г)", max_digits=8, decimal_places=2, null=True, blank=True)
    yield_expected = models.DecimalField("Ожидаемый урожай (г)", max_digits=8, decimal_places=2, null=True, blank=True)

    # Социальные поля
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_growlogs', blank=True)
    views_count = models.PositiveIntegerField("Просмотры", default=0)

    is_public = models.BooleanField(default=True, verbose_name="Публичный")
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Гроу-репорт"
        verbose_name_plural = "Гроу-репорты"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.grower.username}"

    def get_absolute_url(self):
        return reverse('growlogs:detail', kwargs={'pk': self.pk})

    @property
    def current_day(self):
        """Текущий день гроу-репорта"""
        if not self.start_date:
            return 1
        from django.utils import timezone
        today = timezone.now().date()
        if self.end_date and today > self.end_date:
            # Если репорт завершен, возвращаем длительность
            return (self.end_date - self.start_date).days + 1
        return (today - self.start_date).days + 1

    @property
    def duration(self):
        """Возвращает длительность grow"""
        if self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None

    @property
    def display_description(self):
        """Возвращает краткое описание или обрезанное полное"""
        if self.short_description:
            return self.short_description
        return self.setup_description[:200] + "..." if len(self.setup_description) > 200 else self.setup_description

    @property
    def main_photo(self):
        """Возвращает главное фото (логотип или первое фото из записей)"""
        if self.logo:
            return self.logo
        # Ищем первое фото из записей
        first_photo = self.photos.first()
        if first_photo:
            return first_photo.image
        return None

    @property
    def last_ph(self):
        """Последнее значение pH"""
        last_entry = self.entries.filter(ph__isnull=False).order_by('-day').first()
        return last_entry.ph if last_entry else None

    @property
    def last_ec(self):
        """Последнее значение EC"""
        last_entry = self.entries.filter(ec__isnull=False).order_by('-day').first()
        return last_entry.ec if last_entry else None

    @property
    def last_temperature(self):
        """Последняя температура"""
        last_entry = self.entries.filter(temperature__isnull=False).order_by('-day').first()
        return last_entry.temperature if last_entry else None

    @property
    def last_humidity(self):
        """Последняя влажность"""
        last_entry = self.entries.filter(humidity__isnull=False).order_by('-day').first()
        return last_entry.humidity if last_entry else None

    def get_strain_name(self):
        """Возвращает название сорта из магазина или произвольное"""
        if self.strain:
            return self.strain.name
        return self.strain_custom or "N/A"

    def get_strain_display(self):
        """Получить информацию о сорте для отображения"""
        if self.strain:
            return {
                'name': self.strain.name,
                'seedbank': self.strain.seedbank.name if self.strain.seedbank else None,
                'from_store': True,
                'url': self.strain.get_absolute_url() if hasattr(self.strain, 'get_absolute_url') else None
            }
        elif self.strain_custom:
            # Пытаемся распарсить пользовательский ввод
            if '(' in self.strain_custom and ')' in self.strain_custom:
                parts = self.strain_custom.rsplit('(', 1)
                strain_name = parts[0].strip()
                seedbank_name = parts[1].replace(')', '').strip()
                return {
                    'name': strain_name,
                    'seedbank': seedbank_name,
                    'from_store': False,
                    'url': None
                }
            else:
                return {
                    'name': self.strain_custom,
                    'seedbank': None,
                    'from_store': False,
                    'url': None
                }
        else:
            return {
                'name': 'N/A',
                'seedbank': None,
                'from_store': False,
                'url': None
            }

class GrowLogEntry(TimeStampedModel):
    """
    Represents a single entry in a grow log.
    """
    STAGE_CHOICES = GrowLog.STAGE_CHOICES

    growlog = models.ForeignKey(GrowLog, on_delete=models.CASCADE, related_name='entries')
    day = models.PositiveIntegerField("День")
    stage = models.CharField("Стадия", max_length=20, choices=STAGE_CHOICES, default='germination')

    # Объединенное поле для описания и активностей
    activities = models.TextField("Что сделано", blank=True,
                                help_text="Полив, подкормка, тренировка, наблюдения...")

    # Параметры среды
    temperature = models.DecimalField("Температура (°C)", max_digits=4, decimal_places=1, null=True, blank=True)
    humidity = models.DecimalField("Влажность (%)", max_digits=4, decimal_places=1, null=True, blank=True)
    ph = models.DecimalField("pH", max_digits=3, decimal_places=1, null=True, blank=True)
    ec = models.DecimalField("EC (мС/см)", max_digits=4, decimal_places=2, null=True, blank=True)

    # Параметры растения
    height = models.DecimalField("Высота (см)", max_digits=5, decimal_places=1, null=True, blank=True)
    width = models.DecimalField("Ширина (см)", max_digits=5, decimal_places=1, null=True, blank=True)

    # Потребление
    water_amount = models.DecimalField("Полив (л)", max_digits=5, decimal_places=2, null=True, blank=True)
    nutrients_used = models.TextField("Использованные удобрения", blank=True)

    class Meta:
        verbose_name = "Запись гроу-репорта"
        verbose_name_plural = "Записи гроу-репортов"
        ordering = ['day']
        unique_together = ['growlog', 'day']

    def __str__(self):
        return f"{self.growlog.title} - День {self.day}"

class GrowLogEntryPhoto(TimeStampedModel):
    """
    Фотографии к записи гроу-лога (до 10 фото на запись)
    """
    entry = models.ForeignKey(GrowLogEntry, on_delete=models.CASCADE, related_name='entry_photos')
    image = models.ImageField(_("Photo"), upload_to='growlogs/entries/')
    title = models.CharField(_("Title"), max_length=255, blank=True)
    description = models.TextField(_("Description"), blank=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Entry Photo")
        verbose_name_plural = _("Entry Photos")
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Photo for {self.entry} - {self.title or 'Untitled'}"

class GrowLogComment(BaseComment):
    """
    Комментарии к гроу-логу с поддержкой вложенных комментариев
    """
    growlog = models.ForeignKey(GrowLog, on_delete=models.CASCADE, related_name='comments')

    class Meta:
        verbose_name = _("Grow Log Comment")
        verbose_name_plural = _("Grow Log Comments")
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.growlog.title}"

class GrowLogEntryComment(BaseComment):
    """
    Комментарии к записям гроу-лога с поддержкой вложенных комментариев
    """
    entry = models.ForeignKey(GrowLogEntry, on_delete=models.CASCADE, related_name='comments')

    class Meta:
        verbose_name = _("Entry Comment")
        verbose_name_plural = _("Entry Comments")
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.entry}"

class GrowLogEntryLike(TimeStampedModel):
    """
    Лайки к записям гроу-лога
    """
    entry = models.ForeignKey(GrowLogEntry, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='growlog_entry_likes')

    class Meta:
        verbose_name = _("Entry Like")
        verbose_name_plural = _("Entry Likes")
        unique_together = ['entry', 'user']

    def __str__(self):
        return f"Like by {self.user.username} on {self.entry}"
