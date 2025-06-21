from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.db import models

from .models import GrowLog, GrowLogEntry, GrowLogComment, GrowLogEntryPhoto, GrowLogEntryComment
from magicbeans_store.models import Strain

class GrowLogCreateForm(forms.ModelForm):
    """Форма создания гроу-лога с пошаговым мастером"""

    # Добавляем поле для свободного ввода сорта
    strain_name = forms.CharField(
        label=_("Название сорта"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Gorilla Glue Auto',
            'required': True
        }),
        help_text=_("Можете указать любой сорт, не обязательно из нашего магазина")
    )

    # Добавляем поле для сидбанка
    seedbank_name = forms.CharField(
        label=_("Сидбанк (производитель)"),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: FastBuds, Barney\'s Farm'
        }),
        help_text=_("Укажите производителя семян для более точного поиска в магазине")
    )

    class Meta:
        model = GrowLog
        fields = [
            'title', 'logo', 'strain_name', 'seedbank_name', 'start_date', 'environment', 'medium',
            'nutrients', 'lighting', 'container_size', 'setup_description',
            'short_description', 'goals', 'yield_expected', 'is_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Мой первый автоцвет',
                'required': True
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'environment': forms.Select(attrs={
                'class': 'form-control'
            }),
            'medium': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Кокос + перлит, земля, гидропоника...'
            }),
            'nutrients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Какие удобрения планируете использовать?'
            }),
            'lighting': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'LED 600W, ДНаТ 400W...'
            }),
            'container_size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '20L, 15L...'
            }),
            'setup_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите подробно о вашем гроу-боксе, оборудовании и планах...',
                'required': True
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Краткое описание, которое будет видно на карточке в списке репортов',
                'maxlength': 500
            }),
            'goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Какие цели вы ставите перед собой в этом grow?'
            }),
            'yield_expected': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ожидаемый урожай в граммах',
                'min': '0',
                'step': '0.1'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'short_description': _('Описание для карточки репорта'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Убираем поле strain из формы, так как используем strain_name
        if 'strain' in self.fields:
            del self.fields['strain']

        # Устанавливаем дефолтную дату
        if not self.initial.get('start_date'):
            self.initial['start_date'] = date.today()

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Пытаемся найти сорт в магазине по названию И сидбанку
        strain_name = self.cleaned_data.get('strain_name')
        seedbank_name = self.cleaned_data.get('seedbank_name')

        if strain_name:
            # Нормализуем названия (приводим к единому регистру)
            strain_name = strain_name.strip()
            seedbank_name = seedbank_name.strip() if seedbank_name else None

            # Ищем точное совпадение
            strain = self._find_strain_in_store(strain_name, seedbank_name)

            if strain:
                instance.strain = strain
                instance.strain_custom = ""  # Очищаем кастомное поле
            else:
                # Если не найден в магазине - сохраняем как произвольный сорт
                instance.strain = None
                # Сохраняем нормализованное название (возможно с сидбанком)
                if seedbank_name:
                    instance.strain_custom = f"{strain_name} ({seedbank_name})"
                else:
                    instance.strain_custom = strain_name

        if commit:
            instance.save()
        return instance

    def _find_strain_in_store(self, strain_name, seedbank_name=None):
        """
        Улучшенный поиск сорта в магазине с поддержкой частичного совпадения
        и автоматическим подхватом сидбанка
        """
        from magicbeans_store.models import Strain, SeedBank

        # Сначала ищем точные совпадения
        exact_matches = []

        if seedbank_name:
            # Ищем сидбанк (точное или частичное совпадение)
            seedbanks = SeedBank.objects.filter(
                models.Q(name__iexact=seedbank_name) |
                models.Q(name__icontains=seedbank_name)
            )

            if seedbanks.exists():
                # Ищем сорт в найденных сидбанках
                for seedbank in seedbanks:
                    strains = Strain.objects.filter(
                        seedbank=seedbank,
                        is_active=True
                    ).filter(
                        models.Q(name__iexact=strain_name) |
                        models.Q(name__icontains=strain_name)
                    )
                    exact_matches.extend(list(strains))

        # Если с сидбанком ничего не нашли или сидбанк не указан,
        # ищем сорт по всей базе
        if not exact_matches:
            # Точное совпадение по названию сорта
            exact_strains = Strain.objects.filter(
                name__iexact=strain_name,
                is_active=True
            )
            exact_matches.extend(list(exact_strains))

        # Если есть точное совпадение
        if exact_matches:
            if len(exact_matches) == 1:
                return exact_matches[0]
            elif len(exact_matches) > 1:
                # Если несколько точных совпадений, приоритет сорту с указанным сидбанком
                if seedbank_name:
                    for strain in exact_matches:
                        if strain.seedbank and strain.seedbank.name.lower() in seedbank_name.lower():
                            return strain
                # Иначе возвращаем первый найденный
                return exact_matches[0]

        # Если точных совпадений нет, ищем частичные
        partial_matches = []

        if seedbank_name:
            # Ищем частичные совпадения с учетом сидбанка
            seedbanks = SeedBank.objects.filter(
                name__icontains=seedbank_name
            )

            for seedbank in seedbanks:
                strains = Strain.objects.filter(
                    seedbank=seedbank,
                    is_active=True,
                    name__icontains=strain_name
                )
                partial_matches.extend(list(strains))

        # Частичные совпадения по всей базе
        if not partial_matches:
            partial_strains = Strain.objects.filter(
                name__icontains=strain_name,
                is_active=True
            )
            partial_matches.extend(list(partial_strains))

        # Возвращаем лучшее частичное совпадение
        if partial_matches:
            # Сортируем по релевантности (чем ближе к началу названия, тем лучше)
            def relevance_score(strain):
                strain_lower = strain.name.lower()
                search_lower = strain_name.lower()

                # Точное совпадение в начале - высший приоритет
                if strain_lower.startswith(search_lower):
                    return 0
                # Содержит в начале слова
                elif ' ' + search_lower in ' ' + strain_lower:
                    return 1
                # Просто содержит
                else:
                    return 2

            partial_matches.sort(key=relevance_score)
            return partial_matches[0]

        # Ничего не найдено
        return None

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')

        if start_date:
            # Не позволяем устанавливать дату в будущем
            if start_date > date.today():
                raise ValidationError(_("Start date cannot be in the future."))

            # Не позволяем устанавливать дату более года назад
            if start_date < date.today() - timedelta(days=365):
                raise ValidationError(_("Start date cannot be more than a year ago."))

        return start_date

    def clean_yield_expected(self):
        yield_expected = self.cleaned_data.get('yield_expected')

        if yield_expected and yield_expected < 0:
            raise ValidationError(_("Expected yield cannot be negative."))

        if yield_expected and yield_expected > 10000:  # 10kg max
            raise ValidationError(_("Expected yield seems unrealistic."))

        return yield_expected

class GrowLogEntryForm(forms.ModelForm):
    """Форма добавления записи в гроу-лог"""

    class Meta:
        model = GrowLogEntry
        fields = [
            'stage', 'activities', 'temperature', 'humidity',
            'ph', 'ec', 'height', 'width', 'water_amount', 'nutrients_used'
        ]
        widgets = {
            'stage': forms.Select(attrs={
                'class': 'form-control'
            }),
            'activities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Полив, подкормка, тренировка, наблюдения...',
                'required': True
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Температура °C',
                'min': '0',
                'max': '50',
                'step': '0.1'
            }),
            'humidity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Влажность %',
                'min': '0',
                'max': '100',
                'step': '0.1'
            }),
            'ph': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '7,2',
                'min': '0',
                'max': '14',
                'step': '0.1'
            }),
            'ec': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'EC мС/см',
                'min': '0',
                'max': '10',
                'step': '0.01'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Высота см',
                'min': '0',
                'step': '0.1'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ширина см',
                'min': '0',
                'step': '0.1'
            }),
            'water_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '3,70',
                'min': '0',
                'step': '0.1'
            }),
            'nutrients_used': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Какие удобрения использовали...'
            })
        }

    def __init__(self, *args, **kwargs):
        self.growlog = kwargs.pop('growlog', None)
        super().__init__(*args, **kwargs)

        # Если это первая запись, устанавливаем дефолтную стадию
        if self.growlog:
            entries_count = self.growlog.entries.count()
            if entries_count == 0:
                self.initial['stage'] = 'germination'
            else:
                # Предлагаем текущую стадию как дефолт
                self.initial['stage'] = self.growlog.current_stage

    def clean_temperature(self):
        temperature = self.cleaned_data.get('temperature')
        if temperature and (temperature < 0 or temperature > 50):
            raise ValidationError(_("Temperature must be between 0 and 50°C."))
        return temperature

    def clean_humidity(self):
        humidity = self.cleaned_data.get('humidity')
        if humidity and (humidity < 0 or humidity > 100):
            raise ValidationError(_("Humidity must be between 0 and 100%."))
        return humidity

    def clean_ph(self):
        ph = self.cleaned_data.get('ph')
        if ph and (ph < 0 or ph > 14):
            raise ValidationError(_("pH must be between 0 and 14."))
        return ph

class GrowLogCommentForm(forms.ModelForm):
    """Форма комментария к гроу-логу"""

    class Meta:
        model = GrowLogComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Напишите ваш комментарий...',
                'required': True
            })
        }

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if text and len(text.strip()) < 3:
            raise ValidationError(_("Comment must be at least 3 characters long."))
        return text

class GrowLogSearchForm(forms.Form):
    """Форма поиска гроу-логов"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию, автору или сорту...'
        })
    )

    stage = forms.ChoiceField(
        choices=[('', 'Все стадии')] + GrowLog.STAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    environment = forms.ChoiceField(
        choices=[('', 'Все среды')] + GrowLog.ENVIRONMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    sort_by = forms.ChoiceField(
        choices=[
            ('-start_date', 'Новые сначала'),
            ('start_date', 'Старые сначала'),
            ('-views_count', 'Популярные'),
            ('title', 'По названию А-Я'),
            ('-title', 'По названию Я-А'),
        ],
        required=False,
        initial='-start_date',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

class GrowLogWizardForm(forms.ModelForm):
    """Пошаговая форма создания гроу-лога (для мастера)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['strain'].queryset = Strain.objects.filter(
            is_active=True
        ).select_related('seedbank')
        if not self.initial.get('start_date'):
            self.initial['start_date'] = date.today()

    class Meta:
        model = GrowLog
        fields = [
            'title', 'strain', 'start_date', 'environment', 'medium',
            'nutrients', 'lighting', 'container_size', 'setup_description',
            'goals', 'yield_expected', 'is_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: "White Widow Grow #1"',
                'required': True
            }),
            'strain': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'environment': forms.Select(attrs={
                'class': 'form-control'
            }),
            'medium': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: "Coco + Perlite"'
            }),
            'nutrients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Какие удобрения планируете использовать?'
            }),
            'lighting': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: "LED 300W"'
            }),
            'container_size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: "20L"'
            }),
            'setup_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите ваш setup...',
                'required': True
            }),
            'goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Какие цели вы ставите перед собой в этом grow?'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные заметки...'
            }),
            'yield_expected': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ожидаемый урожай в граммах',
                'min': '0',
                'step': '0.1'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')

        if start_date:
            # Не позволяем устанавливать дату в будущем
            if start_date > date.today():
                raise ValidationError(_("Start date cannot be in the future."))

            # Не позволяем устанавливать дату более года назад
            if start_date < date.today() - timedelta(days=365):
                raise ValidationError(_("Start date cannot be more than a year ago."))

        return start_date

    def clean_yield_expected(self):
        yield_expected = self.cleaned_data.get('yield_expected')

        if yield_expected and yield_expected < 0:
            raise ValidationError(_("Expected yield cannot be negative."))

        if yield_expected and yield_expected > 10000:  # 10kg max
            raise ValidationError(_("Expected yield seems unrealistic."))

        return yield_expected

class GrowLogEntryPhotoForm(forms.ModelForm):
    """Форма загрузки фотографий к записи гроу-лога"""

    class Meta:
        model = GrowLogEntryPhoto
        fields = ['image', 'title', 'description']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название фото...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Описание фото...'
            })
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            raise ValidationError(_("Image file is required."))

        # Проверяем размер файла (максимум 10MB)
        if image.size > 10 * 1024 * 1024:
            raise ValidationError(_("Image file too large (maximum 10MB)."))

        return image

class GrowLogEntryPhotoFormSet(forms.BaseInlineFormSet):
    """Формсет для множественной загрузки фотографий"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_num = 10  # Максимум 10 фотографий на запись
        self.extra = 3     # Показываем 3 пустые формы по умолчанию
        self.can_delete = True

# Создаем формсет
GrowLogEntryPhotoInlineFormSet = forms.inlineformset_factory(
    GrowLogEntry,
    GrowLogEntryPhoto,
    form=GrowLogEntryPhotoForm,
    formset=GrowLogEntryPhotoFormSet,
    extra=3,
    max_num=10,
    can_delete=True
)

class GrowLogEntryCommentForm(forms.ModelForm):
    """Форма комментария к записи гроу-лога"""

    class Meta:
        model = GrowLogEntryComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Оставьте комментарий к этому дню...',
                'required': True
            })
        }

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if not text or len(text.strip()) < 3:
            raise ValidationError(_("Comment must be at least 3 characters long."))
        return text.strip()
