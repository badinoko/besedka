from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from magicbeans_store.models import (
    SeedBank, Strain, StockItem, OrderStatus,
    ShippingMethod, PaymentMethod, Promotion, Coupon, OrderItem, Order, CartItem, Cart
)
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Создает тестовые данные для магазина'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед созданием новых',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Создание тестовых данных для магазина...'))

        try:
            with transaction.atomic():
                if options['clear']:
                    self.clear_data()

                self.create_seedbanks()
                self.create_strains()
                self.create_stock_items()
                self.create_order_statuses()
                self.create_shipping_methods()
                self.create_payment_methods()
                self.create_promotions()
                self.create_coupons()

            self.stdout.write(self.style.SUCCESS('✅ Тестовые данные успешно созданы!'))
            self.print_summary()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка при создании данных: {e}'))
            raise CommandError(f'Не удалось создать тестовые данные: {e}')

    def clear_data(self):
        self.stdout.write('🗑️  Очистка существующих данных...')
        # Сначала удаляем зависимые объекты
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        # Затем основные
        StockItem.objects.all().delete()
        Strain.objects.all().delete()
        SeedBank.objects.all().delete()
        OrderStatus.objects.all().delete()
        ShippingMethod.objects.all().delete()
        PaymentMethod.objects.all().delete()
        Promotion.objects.all().delete()
        Coupon.objects.all().delete()

    def create_seedbanks(self):
        self.stdout.write('🌱 Создание сидбанков...')

        seedbanks_data = [
            {
                'name': 'Dutch Passion',
                'description': 'Голландская компания с 35-летним опытом селекции премиальных автоцветов и фотопериодных сортов',
                'website': 'https://dutch-passion.com',
                'is_active': True
            },
            {
                'name': 'Royal Queen Seeds',
                'description': 'Европейский лидер в производстве каннабиса семян с акцентом на качество и стабильность',
                'website': 'https://royalqueenseeds.com',
                'is_active': True
            },
            {
                'name': 'FastBuds',
                'description': 'Специалисты по автоцветущим сортам с невероятно быстрым циклом роста',
                'website': 'https://fastbuds.com',
                'is_active': True
            },
            {
                'name': "Barney's Farm",
                'description': 'Амстердамская сидбанка с уникальными сортами и множеством наград',
                'website': 'https://barneysfarm.com',
                'is_active': True
            }
        ]

        for data in seedbanks_data:
            seedbank, created = SeedBank.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if seedbank is not None:
                if created:
                    self.stdout.write(f'  ✅ Создан сидбанк: {seedbank.name}')
                else:
                    self.stdout.write(f'  ℹ️ Сидбанк уже существует: {seedbank.name}')
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️ Не удалось создать или получить сидбанк: {data["name"]}'))

    def create_strains(self):
        self.stdout.write('🌿 Создание сортов...')

        seedbanks = {sb.name: sb for sb in SeedBank.objects.all()}

        barneys_farm_name = "Barney's Farm"
        barneys_farm_sb = seedbanks.get(barneys_farm_name)
        if not barneys_farm_sb:
            raise CommandError(f"Seedbank '{barneys_farm_name}' not found. Please ensure it is defined in the create_seedbanks method.")

        strains_data = [
            # Dutch Passion
            {
                'name': 'Auto Ultimate',
                'seedbank': seedbanks['Dutch Passion'],
                'strain_type': 'autoflowering',
                'description': 'Мощный автоцвет с огромными урожаями и сильным расслабляющим эффектом',
                'genetics': 'Big Bud x Chronic x Skunk',
                'thc_content': '20-25',
                'cbd_content': '1-1.5',
                'flowering_time': '10-12 недель',
                'height': '100-150 см',
                'yield_indoor': '400-500 г/м²',
                'yield_outdoor': '200-300 г/растение',
                'effect': 'Расслабляющий, эйфорический',
                'flavor': 'Сладкий, фруктовый',
                'is_active': True
            },
            {
                'name': 'Frisian Dew',
                'seedbank': seedbanks['Dutch Passion'],
                'strain_type': 'feminized',
                'description': 'Красивый фиолетовый сорт для открытого грунта, устойчивый к плесени.',
                'genetics': 'Super Skunk x Purple Star',
                'thc_content': '15-20',
                'cbd_content': '0.5-1',
                'flowering_time': '8-10 недель',
                'height': '200-300 см',
                'yield_indoor': '400-500 г/м²',
                'yield_outdoor': '700-800 г/растение',
                'effect': 'Сбалансированный, эйфорический и расслабляющий',
                'flavor': 'Фруктовый, пряный',
                'is_active': True
            },
            # Royal Queen Seeds
            {
                'name': 'Northern Light',
                'seedbank': seedbanks['Royal Queen Seeds'],
                'strain_type': 'feminized',
                'description': 'Легендарная индика с мощным stone-эффектом и простотой выращивания',
                'genetics': 'Afghani x Thai',
                'thc_content': '15-20',
                'cbd_content': '0.5-1',
                'flowering_time': '6-8 недель',
                'height': '100-120 см',
                'yield_indoor': '500-550 г/м²',
                'yield_outdoor': '575-625 г/растение',
                'effect': 'Глубокое расслабление, сонливость',
                'flavor': 'Сладкий, землистый',
                'is_active': True
            },
            {
                'name': 'Royal Dwarf',
                'seedbank': seedbanks['Royal Queen Seeds'],
                'strain_type': 'autoflowering',
                'description': 'Компактный и быстрый автоцвет, идеален для незаметного выращивания.',
                'genetics': 'Skunk x Ruderalis',
                'thc_content': '10-15',
                'cbd_content': '0-0.5',
                'flowering_time': '8-10 недель',
                'height': '40-70 см',
                'yield_indoor': '150-200 г/м²',
                'yield_outdoor': '30-80 г/растение',
                'effect': 'Легкий, расслабляющий',
                'flavor': 'Сканковый, сладкий',
                'is_active': True
            },
            # FastBuds
            {
                'name': 'Gorilla Glue Auto',
                'seedbank': seedbanks['FastBuds'],
                'strain_type': 'autoflowering',
                'description': 'Автоцветущая версия знаменитого сорта с липкими смолистыми шишками',
                'genetics': 'Gorilla Glue #4 x Ruderalis',
                'thc_content': '20-25',
                'cbd_content': '0-0.5',
                'flowering_time': '8-10 недель',
                'height': '80-120 см',
                'yield_indoor': '450-500 г/м²',
                'yield_outdoor': '150-200 г/растение',
                'effect': 'Мощная эйфория, креативность',
                'flavor': 'Сосновый, землистый, дизельный',
                'is_active': True
            },
            {
                'name': 'LSD-25 Auto',
                'seedbank': seedbanks['FastBuds'],
                'strain_type': 'autoflowering',
                'description': 'Невероятно фиолетовый автоцвет с психоделическим эффектом.',
                'genetics': 'L.S.D. x Ruderalis',
                'thc_content': '20-25',
                'cbd_content': '0.5-1',
                'flowering_time': '8-10 недель',
                'height': '70-120 см',
                'yield_indoor': '400-500 г/м²',
                'yield_outdoor': '50-250 г/растение',
                'effect': 'Психоделический, эйфорический, творческий',
                'flavor': 'Дизельный, кисло-сладкий',
                'is_active': True
            },
            # Barney's Farm
            {
                'name': 'Mimosa EVO',
                'seedbank': barneys_farm_sb,
                'strain_type': 'feminized',
                'description': 'Энергичная сатива с цитрусовым ароматом и бодрящим эффектом',
                'genetics': 'Orange Punch x Purple Punch',
                'thc_content': '25-30',
                'cbd_content': '0-0.5',
                'flowering_time': '8-10 недель',
                'height': '120-160 см',
                'yield_indoor': '550-600 г/м²',
                'yield_outdoor': '800-1000 г/растение',
                'effect': 'Энергия, фокус, эйфория',
                'flavor': 'Цитрусовый, тропический',
                'is_active': True
            },
            {
                'name': 'Wedding Cake Auto',
                'seedbank': barneys_farm_sb,
                'strain_type': 'autoflowering',
                'description': 'Сладкий и мощный автоцвет с высоким содержанием THC.',
                'genetics': 'Wedding Cake x BF Super Auto #1',
                'thc_content': '20-25',
                'cbd_content': '1-1.5',
                'flowering_time': '10-12 недель',
                'height': '90-110 см',
                'yield_indoor': '500 г/м²',
                'yield_outdoor': 'до 750 г/растение',
                'effect': 'Расслабляющий, счастливый, эйфорический',
                'flavor': 'Сладкий, ванильный, землистый',
                'is_active': True
            },
            {
                'name': 'Regular Skunk #1',
                'seedbank': seedbanks['Dutch Passion'],
                'strain_type': 'regular',
                'description': 'Классический Skunk #1 в регулярной версии для селекции.',
                'genetics': 'Skunk #1 (Afghani x Colombian Gold x Acapulco Gold)',
                'thc_content': '10-15',
                'cbd_content': '0-0.5',
                'flowering_time': '8-10 недель',
                'height': '100-150 см',
                'yield_indoor': '400-500 г/м²',
                'yield_outdoor': 'до 600 г/растение',
                'effect': 'Сбалансированный, эйфория и расслабление',
                'flavor': 'Сканковый, сладкий, землистый',
                'is_active': True
            }
        ]

        for data in strains_data:
            strain, created = Strain.objects.get_or_create(
                name=data['name'],
                seedbank=data['seedbank'],
                defaults=data
            )

            if strain is not None:
                seedbank_name_for_log = "N/A"
                if strain.seedbank is not None:
                    seedbank_name_for_log = strain.seedbank.name
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠️ У сорта {strain.name} отсутствует сидбанк в объекте!'))

                if created:
                    self.stdout.write(f'  ✅ Создан сорт: {strain.name} ({seedbank_name_for_log}) - Тип: {strain.get_strain_type_display()}')
                else:
                    update_fields = []
                    for key, value in data.items():
                        if key == 'seedbank':
                            current_seedbank_obj = getattr(strain, key)
                            if isinstance(current_seedbank_obj, SeedBank) and isinstance(value, SeedBank):
                                if current_seedbank_obj.pk != value.pk:
                                    setattr(strain, key, value)
                                    update_fields.append(key)
                            # Если value не объект SeedBank или current_seedbank_obj None, пропускаем
                            continue # Переходим к следующему ключу в data.items()

                        # Для всех остальных ключей
                        if getattr(strain, key) != value:
                            setattr(strain, key, value)
                            update_fields.append(key)

                    if update_fields:
                        strain.save(update_fields=update_fields)
                        self.stdout.write(f'  🔄 Обновлен сорт: {strain.name} ({seedbank_name_for_log}) - Поля: {", ".join(update_fields)}')
                    else:
                        self.stdout.write(f'  ℹ️ Сорт уже существует и актуален: {strain.name} ({seedbank_name_for_log})')
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️ Не удалось создать или получить сорт: {data["name"]}'))

    def create_stock_items(self):
        self.stdout.write('📋 Создание товаров на складе...')

        strains_qs = Strain.objects.filter(is_active=True) # Берем только активные сорта
        self.stdout.write(f'  🔍 Найдено активных сортов для создания упаковок: {strains_qs.count()}')

        for strain_obj in strains_qs: # Переименовал переменную, чтобы не конфликтовать с именем модуля
            self.stdout.write(f'     обрабатывается сорт: {strain_obj.name}')
            # Создаем разные упаковки для каждого сорта
            # Цены теперь фиксированные, но немного варьируются для разнообразия
            base_price = 10
            if 'Auto' in strain_obj.name or strain_obj.strain_type == 'autoflowering':
                base_price = 12
            if 'EVO' in strain_obj.name or 'LSD' in strain_obj.name:
                base_price = 15
            if strain_obj.thc_content == '25-30' or strain_obj.thc_content == '30+':
                base_price += 5

            packages = [
                {'seeds': 1,  'price': 15,  'qty': 50}, # Упрощенные цены для примера
                {'seeds': 3,  'price': 40,  'qty': 30},
                {'seeds': 5,  'price': 65, 'qty': 20},
                {'seeds': 10, 'price': 120, 'qty': 10}
            ]

            for pkg in packages:
                current_price = Decimal(str(pkg['price'])) if pkg['price'] > 0 else Decimal('5.00')
                stock_item, created = StockItem.objects.get_or_create(
                    strain=strain_obj,
                    seeds_count=pkg['seeds'],
                    defaults={
                        'price': current_price,
                        'quantity': pkg['qty'],
                        'sku': f'{strain_obj.name.upper().replace(" ", "")[:10]}-{pkg["seeds"]}PCS',
                        'is_active': True
                    }
                )
                if stock_item is not None: # Явная проверка на None
                    if created:
                        self.stdout.write(f'      ✅ СОЗДАН товар: {stock_item.strain.name} x{stock_item.seeds_count} - {stock_item.price} руб. - Количество: {stock_item.quantity}')
                    else:
                        # Обновляем существующие, если нужно (например, количество или цену)
                        updated_stock_fields = []
                        if stock_item.quantity != pkg['qty']:
                            stock_item.quantity = pkg['qty']
                            updated_stock_fields.append('quantity')
                        if stock_item.price != current_price:
                            stock_item.price = current_price
                            updated_stock_fields.append('price')
                        if not stock_item.is_active:
                            stock_item.is_active = True
                            updated_stock_fields.append('is_active')

                        if updated_stock_fields:
                            stock_item.save(update_fields=updated_stock_fields)
                            self.stdout.write(f'      🔄 ОБНОВЛЕН товар: {stock_item.strain.name} x{stock_item.seeds_count} - Поля: {", ".join(updated_stock_fields)}')
                        else:
                            self.stdout.write(f'      ℹ️  Товар УЖЕ СУЩЕСТВУЕТ и актуален: {stock_item.strain.name} x{stock_item.seeds_count}')
                else:
                    self.stdout.write(self.style.WARNING(f'      ⚠️ Не удалось создать или получить товар для: {strain_obj.name} x{pkg["seeds"]}'))

    def create_order_statuses(self):
        self.stdout.write('📦 Создание статусов заказов...')

        statuses_data = [
            {'name': 'Новый', 'description': 'Заказ только что создан'},
            {'name': 'Обработка', 'description': 'Заказ обрабатывается менеджером'},
            {'name': 'Оплачен', 'description': 'Платеж получен и подтвержден'},
            {'name': 'Упакован', 'description': 'Заказ упакован и готов к отправке'},
            {'name': 'Отправлен', 'description': 'Заказ передан в службу доставки'},
            {'name': 'Доставлен', 'description': 'Заказ успешно доставлен клиенту'},
            {'name': 'Отменен', 'description': 'Заказ отменен по просьбе клиента'},
            {'name': 'Возврат', 'description': 'Оформлен возврат товара'}
        ]

        for data in statuses_data:
            status, created = OrderStatus.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if status is not None:
                if created:
                    self.stdout.write(f'  ✅ Создан статус: {status.name}')
                else:
                    self.stdout.write(f'  ℹ️ Статус уже существует: {status.name}')
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️ Не удалось создать или получить статус: {data["name"]}'))

    def create_shipping_methods(self):
        self.stdout.write('🚚 Создание способов доставки...')

        methods_data = [
            {
                'name': 'Почта России',
                'description': 'Стандартная доставка Почтой России (7-21 день)',
                'price': Decimal('350.00'),
                'estimated_days': 14,
                'is_active': True
            },
            {
                'name': 'СДЭК (до пункта выдачи)',
                'description': 'Доставка до пункта выдачи СДЭК (3-7 дней)',
                'price': Decimal('450.00'),
                'estimated_days': 5,
                'is_active': True
            },
            {
                'name': 'СДЭК (курьером до двери)',
                'description': 'Курьерская доставка СДЭК до двери (3-7 дней)',
                'price': Decimal('650.00'),
                'estimated_days': 5,
                'is_active': True
            }
        ]

        for data in methods_data:
            method, created = ShippingMethod.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if method is not None:
                if created:
                    self.stdout.write(f'  ✅ Создан способ доставки: {method.name}')
                else:
                    self.stdout.write(f'  ℹ️ Способ доставки уже существует: {method.name}')
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️ Не удалось создать или получить способ доставки: {data["name"]}'))

    def create_payment_methods(self):
        self.stdout.write('💳 Создание способов оплаты...')

        methods_data = [
            {
                'name': 'Банковский перевод',
                'description': 'Оплата через банковский перевод (SEPA)',
                'is_active': True
            },
            {
                'name': 'Биткойн (BTC)',
                'description': 'Криптовалютная оплата Bitcoin',
                'is_active': True
            },
            {
                'name': 'Ethereum (ETH)',
                'description': 'Криптовалютная оплата Ethereum',
                'is_active': True
            },
            {
                'name': 'Наличные при получении',
                'description': 'Оплата наличными курьеру (только для некоторых регионов)',
                'is_active': False
            }
        ]

        for data in methods_data:
            method, created = PaymentMethod.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if method is not None:
                if created:
                    self.stdout.write(f'  ✅ Создан способ оплаты: {method.name}')
                else:
                    self.stdout.write(f'  ℹ️ Способ оплаты уже существует: {method.name}')
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️ Не удалось создать или получить способ оплаты: {data["name"]}'))

    def create_promotions(self):
        self.stdout.write('🎯 Создание промоакций...')

        promotions_data = [
            {
                'name': 'Весенняя распродажа',
                'description': 'Скидка 20% на все автоцветы в честь начала сезона!',
                'discount_type': 'percentage',
                'discount_value': Decimal('20.0'),
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=30),
                'is_active': True
            },
            {
                'name': 'Новинки FastBuds',
                'description': 'Специальные цены на новые сорта от FastBuds',
                'discount_type': 'percentage',
                'discount_value': Decimal('15.0'),
                'start_date': timezone.now() - timedelta(days=5),
                'end_date': timezone.now() + timedelta(days=45),
                'is_active': True
            },
            {
                'name': 'Летний буст',
                'description': 'Грандиозная летняя акция - скидки до 30%',
                'discount_type': 'percentage',
                'discount_value': Decimal('30.0'),
                'start_date': timezone.now() + timedelta(days=60),
                'end_date': timezone.now() + timedelta(days=150),
                'is_active': False
            }
        ]

        for data in promotions_data:
            promotion, created = Promotion.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if promotion is not None:
                if created:
                    self.stdout.write(f'  ✅ Создана промоакция: {promotion.name} ({promotion.discount_value}%)')
                else:
                    self.stdout.write(f'  ℹ️ Промоакция уже существует: {promotion.name}')
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️ Не удалось создать или получить промоакцию: {data["name"]}'))

    def create_coupons(self):
        self.stdout.write('🎫 Создание купонов...')

        coupons_data = [
            {
                'code': 'WELCOME10',
                'description': 'Скидка 10% для новых клиентов',
                'discount_percentage': Decimal('10.0'),
                'start_date': timezone.now() - timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=365),
                'is_active': True
            },
            {
                'code': 'SPRING20',
                'description': 'Весенняя скидка 20% на весь ассортимент',
                'discount_percentage': Decimal('20.0'),
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=30),
                'is_active': True
            },
            {
                'code': 'BULK50',
                'description': 'Скидка при покупке от 5 упаковок',
                'discount_percentage': Decimal('50.0'),
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=90),
                'is_active': True
            },
            {
                'code': 'EXPIRED',
                'description': 'Тестовый истекший купон',
                'discount_percentage': Decimal('25.0'),
                'start_date': timezone.now() - timedelta(days=60),
                'end_date': timezone.now() - timedelta(days=1),
                'is_active': False
            }
        ]

        for data in coupons_data:
            coupon, created = Coupon.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            if coupon is not None:
                if created:
                    self.stdout.write(f'  ✅ Создан купон: {coupon.code} ({coupon.discount_percentage}%)')
                else:
                    self.stdout.write(f'  ℹ️ Купон уже существует: {coupon.code}')
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️ Не удалось создать или получить купон: {data["code"]}'))

    def print_summary(self):
        self.stdout.write('\n📊 СВОДКА СОЗДАННЫХ ДАННЫХ:')
        self.stdout.write(f'  🌱 Сидбанки: {SeedBank.objects.count()}')
        self.stdout.write(f'  🌿 Сорта: {Strain.objects.count()}')
        self.stdout.write(f'  📋 Товары: {StockItem.objects.count()}')
        self.stdout.write(f'  📦 Статусы заказов: {OrderStatus.objects.count()}')
        self.stdout.write(f'  🚚 Способы доставки: {ShippingMethod.objects.count()}')
        self.stdout.write(f'  💳 Способы оплаты: {PaymentMethod.objects.count()}')
        self.stdout.write(f'  🎯 Промоакции: {Promotion.objects.count()}')
        self.stdout.write(f'  🎫 Купоны: {Coupon.objects.count()}')
        self.stdout.write('\n🎉 Теперь администратор магазина может полноценно работать!')
