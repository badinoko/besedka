from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from PIL import Image
import os

from .models import Photo, PhotoComment
from growlogs.models import GrowLog

class PhotoUploadForm(forms.ModelForm):
    """Форма загрузки фотографии"""

    class Meta:
        model = Photo
        fields = ['title', 'description', 'image', 'growlog', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название фотографии...',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о фото...'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True
            }),
            'growlog': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'checked': True
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Фильтруем гроу-логи только для текущего пользователя
        if self.user:
            self.fields['growlog'].queryset = GrowLog.objects.filter(
                grower=self.user,
                is_active=True
            ).order_by('-start_date')
        else:
            self.fields['growlog'].queryset = GrowLog.objects.none()

        # Делаем поле опциональным
        self.fields['growlog'].empty_label = "Не связано с grow log"
        self.fields['growlog'].required = False

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if not image:
            # Это поле обязательно, так что эта проверка может быть излишней, если required=True на уровне поля
            raise ValidationError(_("Image file is required."))

        # Проверяем размер файла (максимум 10MB)
        if image.size > 10 * 1024 * 1024:
            raise ValidationError(_("Image file too large (maximum 10MB)."))

        # Временно убираем сложную валидацию формата и размеров через Pillow для теста
        # allowed_formats = ['JPEG', 'JPG', 'PNG', 'WEBP']
        # try:
        #     image.seek(0)
        #     img = Image.open(image)
        #     if img.format not in allowed_formats:
        #         raise ValidationError(
        #             _("Unsupported image format. Please use JPEG, PNG or WEBP.")
        #         )
        #     # if img.width < 300 or img.height < 300: # Временно комментируем для теста
        #     #     raise ValidationError(_("Image too small (minimum 300x300 pixels)."))
        #     if img.width > 8000 or img.height > 8000:
        #         raise ValidationError(_("Image too large (maximum 8000x8000 pixels)."))
        # except Exception as e:
        #     print(f"DEBUG Pillow error: {e}") # Добавим вывод ошибки Pillow
        #     raise ValidationError(_("Invalid image file."))
        # image.seek(0)

        return image

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 3:
            raise ValidationError(_("Title must be at least 3 characters long."))
        return title

class PhotoCommentForm(forms.ModelForm):
    """Форма комментария к фотографии"""

    class Meta:
        model = PhotoComment
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
        if text and len(text) > 1000:
            raise ValidationError(_("Comment too long (maximum 1000 characters)."))
        return text

class PhotoSearchForm(forms.Form):
    """Форма поиска фотографий"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию, описанию или автору...'
        })
    )

    author = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Автор...'
        })
    )

    growlog = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_("Only photos from grow logs")
    )

    sort = forms.ChoiceField(
        choices=[
            ('-created_at', 'Новые сначала'),
            ('created_at', 'Старые сначала'),
            ('popular', 'Популярные'),
            ('commented', 'Комментируемые'),
            ('title', 'По названию А-Я'),
            ('-title', 'По названию Я-А'),
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

class PhotoBulkUploadForm(forms.Form):
    """Форма массовой загрузки фотографий"""

    images = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text=_("Select an image to upload")
    )

    default_title_prefix = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Префикс для названий (например: "Day 25")'
        }),
        help_text=_("This will be added to the beginning of each photo title")
    )

    default_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Описание для всех фото...'
        })
    )

    growlog = forms.ModelChoiceField(
        queryset=GrowLog.objects.none(),
        required=False,
        empty_label="Не связано с grow log",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    is_public = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Фильтруем гроу-логи для текущего пользователя
        if self.user:
            self.fields['growlog'].queryset = GrowLog.objects.filter(
                grower=self.user,
                is_active=True
            ).order_by('-start_date')
