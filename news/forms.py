from django import forms
from django.core.validators import MinLengthValidator
from .models import Comment, Post, Poll, PollChoice


class CommentForm(forms.ModelForm):
    """Форма для добавления комментариев"""

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Напишите ваш комментарий...',
                'required': True
            })
        }
        labels = {
            'content': 'Комментарий'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].validators.append(MinLengthValidator(3))


class PostForm(forms.ModelForm):
    """Форма для создания/редактирования постов"""

    class Meta:
        model = Post
        fields = [
            'title', 'category', 'tags', 'post_type', 'content',
            'excerpt', 'image', 'video_url', 'status', 'is_pinned'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок поста'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'post_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Содержание поста...'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание (необязательно)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=...'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем некоторые поля необязательными в зависимости от типа поста
        self.fields['video_url'].required = False
        self.fields['image'].required = False
        self.fields['excerpt'].required = False

    def clean(self):
        cleaned_data = super().clean()
        post_type = cleaned_data.get('post_type')
        video_url = cleaned_data.get('video_url')

        # Для видео-постов требуем URL
        if post_type == 'video_link' and not video_url:
            raise forms.ValidationError('Для видео-поста необходимо указать ссылку на видео')

        return cleaned_data


class PollForm(forms.ModelForm):
    """Форма для создания опросов"""

    class Meta:
        model = Poll
        fields = ['question_text', 'multiple_choice']
        widgets = {
            'question_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите вопрос опроса'
            }),
            'multiple_choice': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class PollChoiceFormSet(forms.BaseInlineFormSet):
    """Формсет для вариантов ответов в опросе"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = PollChoice.objects.none()

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        choices = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                choice_text = form.cleaned_data.get('choice_text')
                if choice_text:
                    choices.append(choice_text)

        if len(choices) < 2:
            raise forms.ValidationError('Опрос должен содержать минимум 2 варианта ответа')

        if len(set(choices)) != len(choices):
            raise forms.ValidationError('Варианты ответов не должны повторяться')


PollChoiceInlineFormSet = forms.inlineformset_factory(
    Poll,
    PollChoice,
    fields=['choice_text'],
    extra=3,
    min_num=2,
    max_num=10,
    formset=PollChoiceFormSet,
    widgets={
        'choice_text': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Вариант ответа'
        })
    }
)
