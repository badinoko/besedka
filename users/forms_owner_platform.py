from django import forms

class AssignStoreOwnerForm(forms.Form):
    username = forms.CharField(
        label="Имя пользователя (логин)",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    first_name = forms.CharField(
        label="Имя",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        label="Фамилия",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    # Можно добавить дополнительные валидаторы, если необходимо
    # Например, проверку, что username не занят, или email уникален.

class DeactivateStoreOwnerForm(forms.Form):
    confirm_deactivation = forms.BooleanField(
        label="Подтверждаю деактивацию текущего Владельца Магазина",
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
