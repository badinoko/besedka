from import_export import resources
from import_export.fields import Field
from .models import StockItem


class StockItemResource(resources.ModelResource):
    strain_name = Field(attribute='strain__name', column_name='Сорт')
    seed_bank = Field(attribute='strain__seed_bank__name', column_name='Сидбанк')
    seeds_count = Field(attribute='seeds_count', column_name='Количество семян')
    price = Field(attribute='price', column_name='Цена')
    quantity = Field(attribute='quantity', column_name='Остаток')
    sku = Field(attribute='sku', column_name='Артикул')

    class Meta:
        model = StockItem
        fields = ('strain_name', 'seed_bank', 'seeds_count', 'price', 'quantity', 'sku')
        export_order = fields
