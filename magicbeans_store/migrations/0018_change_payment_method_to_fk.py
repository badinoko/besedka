# Generated by Django 4.2.21 on 2025-05-26 22:27

from django.db import migrations, models
import django.db.models.deletion


def convert_payment_method_to_fk(apps, schema_editor):
    """Преобразует строковые значения payment_method в ForeignKey"""
    Order = apps.get_model('magicbeans_store', 'Order')
    PaymentMethod = apps.get_model('magicbeans_store', 'PaymentMethod')

    for order in Order.objects.all():
        if order.payment_method_old:  # Используем временное поле
            try:
                # Ищем PaymentMethod по имени
                payment_method = PaymentMethod.objects.filter(
                    name__icontains=order.payment_method_old
                ).first()
                if payment_method:
                    order.payment_method_new = payment_method
                    order.save(update_fields=['payment_method_new'])
            except Exception:
                # Если не найден, оставляем NULL
                pass


def reverse_payment_method_conversion(apps, schema_editor):
    """Обратное преобразование ForeignKey в строку"""
    Order = apps.get_model('magicbeans_store', 'Order')

    for order in Order.objects.all():
        if order.payment_method_new:
            order.payment_method_old = order.payment_method_new.name
            order.save(update_fields=['payment_method_old'])


class Migration(migrations.Migration):

    dependencies = [
        ("magicbeans_store", "0017_alter_order_shipping_method"),
    ]

    operations = [
        # Шаг 1: Переименовываем старое поле
        migrations.RenameField(
            model_name='order',
            old_name='payment_method',
            new_name='payment_method_old',
        ),

        # Шаг 2: Добавляем новое поле ForeignKey
        migrations.AddField(
            model_name='order',
            name='payment_method_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='orders',
                to='magicbeans_store.paymentmethod',
                verbose_name='Способ оплаты',
            ),
        ),

        # Шаг 3: Преобразуем данные
        migrations.RunPython(
            convert_payment_method_to_fk,
            reverse_payment_method_conversion
        ),

        # Шаг 4: Удаляем старое поле
        migrations.RemoveField(
            model_name='order',
            name='payment_method_old',
        ),

        # Шаг 5: Переименовываем новое поле
        migrations.RenameField(
            model_name='order',
            old_name='payment_method_new',
            new_name='payment_method',
        ),
    ]
