from django import forms
from django.utils.translation import gettext_lazy as _


class CsvImportForm(forms.Form):
    """Форма для загрузки CSV-файла для импорта данных."""
    csv_file = forms.FileField(
        label=_('CSV-файл'),
        help_text=_('Выберите CSV-файл для импорта фасовок. '
                  'Формат: сидбанк,сорт,количество_семян,цена,количество_на_складе,видимость')
    )
    update_existing = forms.BooleanField(
        label=_('Обновить существующие'),
        required=False,
        help_text=_('Если отмечено, существующие фасовки будут обновлены. '
                  'В противном случае будут созданы новые фасовки.')
    )
