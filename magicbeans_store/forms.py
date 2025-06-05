from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ShippingMethod, PaymentMethod, Strain, SeedBank, ShippingAddress # Order, OrderItem, StockItem, Coupon removed as not directly used by this form after changes
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from django.utils.html import format_html
from django.urls import reverse_lazy
# from django.contrib.auth.models import AnonymousUser # No longer needed here

User = get_user_model()

class StrainFilterForm(forms.Form):
    """Форма фильтрации сортов в каталоге"""
    name = forms.CharField(label=_("Поиск по названию"), required=False, widget=forms.TextInput(attrs={'placeholder': _('Название или описание')}))
    genetics = forms.MultipleChoiceField(label=_("Тип генетики"), choices=Strain.STRAIN_TYPES, required=False, widget=forms.CheckboxSelectMultiple)
    # Добавьте поле для тегов, если модель Strain имеет связь с тегами
    # tags = forms.ModelMultipleChoiceField(label=_("Теги"), queryset=Tag.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)
    min_price = forms.DecimalField(label=_("Цена от"), required=False, min_value=0)
    max_price = forms.DecimalField(label=_("Цена до"), required=False, min_value=0)

    SORT_CHOICES = [
        ('', _('По умолчанию')),
        ('name_asc', _('Название (А-Я)')),
        ('name_desc', _('Название (Я-А)')),
        ('price_asc', _('Цена (сначала дешевые)')),
        ('price_desc', _('Цена (сначала дорогие)')),
        # ('rating_desc', _('Рейтинг (сначала высокие)')), # Если есть рейтинг
        # ('popularity_desc', _('Популярность')), # Если есть метрика популярности
    ]
    sort_by = forms.ChoiceField(label=_("Сортировать по"), choices=SORT_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('sort_by', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Field('genetics', template='forms/custom_checkbox_select_multiple.html'), # Пример кастомного шаблона для чекбоксов
            # Field('tags', template='forms/custom_checkbox_select_multiple.html'),
            Row(
                Column('min_price', css_class='form-group col-md-6 mb-0'),
                Column('max_price', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', _('Применить фильтры'), css_class='btn btn-primary w-100'),
            HTML(format_html('<a href="{}" class="btn btn-secondary w-100 mt-2">{}</a>', reverse_lazy('store:catalog'), _("Сбросить фильтры")))
        )

class CheckoutForm(forms.Form):
    """Форма оформления заказа для всех пользователей."""

    # Поля адреса (теперь общие для всех, но для зарегистрированных могут быть предзаполнены)
    full_name = forms.CharField(label=_("Полное имя получателя"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(label=_("Номер телефона"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label=_("Email для связи"), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    address_line_1 = forms.CharField(label=_("Адрес (улица, дом, квартира)"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    address_line_2 = forms.CharField(label=_("Адрес (дополнительно)"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(label=_("Город"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    state_province_region = forms.CharField(label=_("Область/Край/Республика"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    postal_code = forms.CharField(label=_("Почтовый индекс"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(label=_("Страна"), initial="Россия", widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Возвращаем shipping_method
    shipping_method = forms.ModelChoiceField(
        queryset=ShippingMethod.objects.filter(is_active=True),
        label=_("Способ доставки"),
        widget=forms.RadioSelect,
        empty_label=None,
        required=True
    )

    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        label=_("Способ оплаты"),
        widget=forms.RadioSelect,
        empty_label=None,
        required=True
    )

    agree_to_terms = forms.BooleanField(
        label=_("Я согласен с условиями обслуживания и политикой конфиденциальности."),
        required=True
    )
    comment = forms.CharField(
        label=_("Комментарий к заказу"),
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': _('Ваши пожелания, детали доставки и т.д.')}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_authenticated:
            # Предзаполнение для зарегистрированного пользователя
            self.fields['email'].initial = self.user.email
            # Пытаемся предзаполнить адрес из ShippingAddress, если есть
            shipping_address = ShippingAddress.objects.filter(user=self.user).order_by('-is_default', '-updated_at').first()
            if shipping_address:
                self.fields['full_name'].initial = shipping_address.full_name
                self.fields['phone_number'].initial = shipping_address.phone_number
                self.fields['address_line_1'].initial = shipping_address.address_line_1
                self.fields['address_line_2'].initial = shipping_address.address_line_2
                self.fields['city'].initial = shipping_address.city
                self.fields['state_province_region'].initial = shipping_address.state_province_region
                self.fields['postal_code'].initial = shipping_address.postal_code
                self.fields['country'].initial = shipping_address.country
        else:
            # Для гостя email остается обязательным, но без initial value от user
            pass

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            HTML(f"<h4>{_('Контактная информация и адрес доставки')}</h4>"),
            Row(
                Column(Field('full_name', placeholder=_("Иванов Иван Иванович")), css_class='col-md-6'),
                Column(Field('phone_number', placeholder=_("+7 (XXX) XXX-XX-XX")), css_class='col-md-6'),
            ),
            Field('email', placeholder=_("Ваш email для связи")),
            Field('address_line_1', placeholder=_('ул. Ленина, д. 1, кв. 10')),
            Field('address_line_2', placeholder=_('Подъезд 1, этаж 5')),
            Row(
                Column(Field('city', placeholder=_("Москва")), css_class='col-md-6'),
                Column(Field('postal_code', placeholder=_("123456")), css_class='col-md-6'),
            ),
            Row(
                Column(Field('state_province_region', placeholder=_('Московская область')), css_class='col-md-6'),
                Column(Field('country', placeholder=_('Россия')), css_class='col-md-6'),
            ),
            HTML(f"<hr><h4>{_('Способ доставки')}</h4>"),
            Field('shipping_method', template='forms/custom_radio_select.html'),
            HTML(f"<hr><h4>{_('Способ оплаты')}</h4>"),
            Field('payment_method', template='forms/custom_radio_select.html'),
            HTML("<hr>"),
            Field('agree_to_terms'),
            HTML(f"<hr><h4>{_('Комментарий к заказу')}</h4>"),
            Field('comment'),
        )

class AddToCartForm(forms.Form):
    """Форма добавления товара в корзину"""
    stock_item_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 80px;'
        })
    )

class ApplyCouponForm(forms.Form):
    """Форма для применения купона к корзине."""
    code = forms.CharField(
        label=_("Промокод"),
        widget=forms.TextInput(attrs={
            'placeholder': _("Введите промокод"),
            'class': 'form-control'
        }),
        max_length=50,
        required=True
    )
