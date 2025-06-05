from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div, HTML
from crispy_forms.bootstrap import FormActions
from .models import Message, DiscussionRoom, Tag


class MessageForm(forms.ModelForm):
    """Форма для отправки сообщений"""

    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Введите ваше сообщение...'),
                'rows': 3,
                'maxlength': 500,
            })
        }
        labels = {
            'content': _('Сообщение'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = True


class DiscussionRoomForm(forms.ModelForm):
    """Форма для создания группового обсуждения"""

    class Meta:
        model = DiscussionRoom
        fields = ['headline', 'description', 'tags']
        widgets = {
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Введите заголовок обсуждения'),
                'maxlength': 220,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Опишите тему обсуждения (необязательно)'),
                'rows': 4,
            }),
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'headline': _('Заголовок'),
            'description': _('Описание'),
            'tags': _('Теги'),
        }
        help_texts = {
            'headline': _('Краткое и понятное название темы обсуждения'),
            'description': _('Подробное описание того, о чем будет обсуждение'),
            'tags': _('Выберите подходящие теги для категоризации'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['headline'].required = True
        self.fields['description'].required = False
        self.fields['tags'].required = False

        # Получаем все доступные теги
        self.fields['tags'].queryset = Tag.objects.all()

    def clean_headline(self):
        headline = self.cleaned_data.get('headline')
        if headline:
            # Проверяем уникальность заголовка
            if DiscussionRoom.objects.filter(headline__iexact=headline).exists():
                raise forms.ValidationError(_('Обсуждение с таким заголовком уже существует'))
        return headline


class TagForm(forms.ModelForm):
    """Форма для создания тегов"""

    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Введите название тега'),
                'maxlength': 124,
            }),
        }
        labels = {
            'name': _('Название тега'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # Проверяем уникальность названия
            if Tag.objects.filter(name__iexact=name).exists():
                raise forms.ValidationError(_('Тег с таким названием уже существует'))
        return name


class SearchForm(forms.Form):
    """Форма поиска по чатам и обсуждениям"""

    query = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Поиск по сообщениям, обсуждениям...'),
            'class': 'form-control',
        }),
        label=''
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'search-form d-flex'
        self.helper.layout = Layout(
            Div(
                Field('query', css_class='flex-grow-1'),
                Submit('submit', _('Поиск'), css_class='btn btn-outline-primary ms-2'),
                css_class='d-flex'
            )
        )
