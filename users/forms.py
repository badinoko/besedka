from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User, BanRecord

class CustomUserCreationForm(UserCreationForm):
    """
    Форма для регистрации пользователя.
    """
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя.
    """

    # Добавляем поле для выбора базовых аватарок
    default_avatar = forms.ChoiceField(
        choices=[],
        required=False,
        label="Выберите аватарку",
        help_text="Или загрузите свою собственную ниже"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'name', 'default_avatar', 'avatar', 'bio')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Импортируем здесь, чтобы избежать циклических импортов
        from .choices import get_avatar_choices
        self.fields['default_avatar'].choices = get_avatar_choices()

        # Делаем поле avatar необязательным
        self.fields['avatar'].required = False

class UnbanRequestForm(forms.Form):
    """
    Форма для запроса на разбан.
    """
    email = forms.EmailField(
        label=_("Email для связи"),
        help_text=_("Укажите актуальный email для связи с вами")
    )
    reason = forms.CharField(
        label=_("Причина запроса на разбан"),
        widget=forms.Textarea,
        help_text=_("Объясните, почему мы должны снять с вас бан")
    )

class BanUserForm(forms.ModelForm):
    """
    Форма для бана пользователя.
    """
    class Meta:
        model = BanRecord
        fields = ('user', 'ban_type', 'reason', 'expires_at')

    def __init__(self, *args, **kwargs):
        banned_by = kwargs.pop('banned_by', None)
        super().__init__(*args, **kwargs)
        self.banned_by = banned_by

    def save(self, commit=True):
        ban_record = super().save(commit=False)
        ban_record.banned_by = self.banned_by

        # Если это глобальный бан, обновляем статус пользователя
        if ban_record.ban_type == BanRecord.BAN_TYPE_GLOBAL:
            ban_record.user.is_banned = True
            if commit:
                ban_record.user.save()

        if commit:
            ban_record.save()
        return ban_record

class StoreOwnerForm(forms.Form):
    """Форма для управления владельцами магазина."""
    ACTION_CHOICES = [
        ('create_new', _('Создать нового владельца магазина')),
        ('revoke_access', _('Отозвать доступ у существующего владельца')),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, label=_("Действие"))

    # Поля для создания нового владельца
    username = forms.CharField(max_length=150, required=False, label=_("Имя пользователя (для нового)"))
    email = forms.EmailField(required=False, label=_("Email (для нового)"))

    # Поле для отзыва доступа
    # Предполагается, что user_id будет передаваться в initial_data или как-то иначе
    # Либо это будет поле для выбора существующего Store Owner
    user_to_revoke = forms.ModelChoiceField(
        queryset=User.objects.filter(role='store_owner', is_active=True),
        required=False,
        label=_("Владелец магазина для отзыва доступа")
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')

        if action == 'create_new':
            if not cleaned_data.get('username'):
                self.add_error('username', _("Имя пользователя обязательно для создания нового владельца."))
            if not cleaned_data.get('email'):
                self.add_error('email', _("Email обязателен для создания нового владельца."))
        elif action == 'revoke_access':
            if not cleaned_data.get('user_to_revoke'):
                self.add_error('user_to_revoke', _("Необходимо выбрать владельца для отзыва доступа."))
        return cleaned_data
