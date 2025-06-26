from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import Room, Message
from users.models import User

class Command(BaseCommand):
    help = 'Создает тестовые сообщения в чатах для разработки (НЕ удаляет существующие)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие сообщения перед созданием новых (только по явному флагу)',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Количество сообщений для каждого пользователя (по умолчанию 15)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🧪 СОЗДАНИЕ ТЕСТОВЫХ СООБЩЕНИЙ ЧАТА"))

        # Очистка только по явному флагу
        if options['clear']:
            Message.objects.all().delete()
            self.stdout.write(self.style.WARNING("🗑️ Очищены все существующие сообщения"))
        else:
            existing_count = Message.objects.count()
            self.stdout.write(self.style.SUCCESS(f"📝 Существующих сообщений: {existing_count} (сохраняем)"))

        # Правильные логины из BESEDKA_USER_SYSTEM.md
        test_users_data = [
            ('owner', '👑 Добро пожаловать в нашу Беседку! Здесь мы обсуждаем все что связано с растениеводством.'),
            ('admin', '🛡️ Кстати, у нас есть стартовые наборы для новичков в магазине. Очень удобно!'),
            ('store_owner', '🏪 Скоро поступление новых сортов семян. Следите за обновлениями!'),
            ('store_admin', '📦 Обработка заказов идет в обычном режиме. Доставка 2-3 дня.'),
            ('test_user', '🌱 Поделитесь опытом выращивания томатов в теплице!')
        ]

        # Получаем комнаты
        try:
            general_room = Room.objects.get(name='general')
            vip_room = Room.objects.get(name='vip')
            self.stdout.write(self.style.SUCCESS("✅ Комнаты чатов найдены"))
        except Room.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Комнаты чатов не найдены"))
            return

        count_per_user = options['count']
        messages_created = 0

        # Дополнительные варианты сообщений
        message_templates = {
            'owner': [
                '👑 Добро пожаловать в нашу Беседку! Здесь мы обсуждаем все что связано с растениеводством.',
                '🌟 Рады видеть новых участников в нашем сообществе!',
                '🏆 Скоро запустим конкурс лучших гроу-репортов с призами!',
                '💡 Предлагайте идеи для улучшения платформы - мы всегда открыты к предложениям.',
                '🎯 Наша цель - создать лучшее сообщество растениеводов в рунете!'
            ],
            'admin': [
                '🛡️ Кстати, у нас есть стартовые наборы для новичков в магазине. Очень удобно!',
                '⚠️ Напоминаю о правилах чата - будьте уважительны к другим участникам.',
                '🔍 Проверяю галерею на новые фотографии - много интересного контента!',
                '📋 Если заметили нарушения - сообщайте в личные сообщения.',
                '🎭 Модерация работает 24/7 для комфорта всех участников.'
            ],
            'store_owner': [
                '🏪 Скоро поступление новых сортов семян. Следите за обновлениями!',
                '💰 Действует скидка 15% на все удобрения до конца месяца!',
                '📦 Новая партия LED-светильников поступила на склад.',
                '🎁 Для постоянных клиентов подготовили специальные бонусы.',
                '🚚 Расширили зону бесплатной доставки - теперь включает пригороды!'
            ],
            'store_admin': [
                '📦 Обработка заказов идет в обычном режиме. Доставка 2-3 дня.',
                '⏰ Все заказы, сделанные до 15:00, отправляются в тот же день.',
                '📋 Проверил остатки на складе - все популярные позиции в наличии.',
                '🔄 Обновил статусы заказов - можете проверить в личном кабинете.',
                '📞 Служба поддержки работает с 9:00 до 21:00 без выходных.'
            ],
            'test_user': [
                '🌱 Поделитесь опытом выращивания томатов в теплице!',
                '🤔 Подскажите, какие удобрения лучше для рассады перца?',
                '📸 Загрузил новые фото своего гроу-репорта в галерею.',
                '🌿 Кто-нибудь пробовал выращивать микрозелень дома?',
                '💧 Вопрос по поливу: как часто поливать молодые растения?',
                '🌡️ Какая оптимальная температура для проращивания семян?',
                '🪴 Показываю результаты после месяца выращивания!',
                '🔬 Интересно почитать про новые методы гидропоники.',
                '🐛 Столкнулся с вредителями - как бороться экологично?',
                '🏆 Участвую в конкурсе - желайте удачи!'
            ]
        }

        # Создаем сообщения для каждого пользователя
        base_time = timezone.now() - timedelta(hours=24)  # Начинаем с суток назад
        time_offset = 0

        for username, default_message in test_users_data:
            try:
                user = User.objects.get(username=username)
                templates = message_templates.get(username, [default_message])

                # Создаем сообщения в общем чате
                for i in range(count_per_user):
                    message_text = templates[i % len(templates)]
                    message_time = base_time + timedelta(minutes=time_offset)

                    Message.objects.create(
                        room=general_room,
                        author=user,
                        content=message_text,
                        created_at=message_time
                    )
                    time_offset += 3  # 3 минуты между сообщениями
                    messages_created += 1

                # Создаем несколько сообщений в VIP чате для владельца
                if username == 'owner':
                    vip_messages = [
                        '💎 Добро пожаловать в VIP-зону нашей Беседки!',
                        '🏆 Здесь мы обсуждаем эксклюзивные сорта и премиум технологии.',
                        '🤝 VIP-участники получают приоритетную поддержку и специальные предложения.',
                        '🔒 Контент этого чата доступен только проверенным участникам.',
                        '💫 Скоро будут анонсы новых VIP-возможностей!'
                    ]

                    for vip_msg in vip_messages:
                        message_time = base_time + timedelta(minutes=time_offset)
                        Message.objects.create(
                            room=vip_room,
                            author=user,
                            content=vip_msg,
                            created_at=message_time
                        )
                        time_offset += 5  # 5 минут между VIP сообщениями
                        messages_created += 1

                self.stdout.write(self.style.SUCCESS(f"✅ {user.get_role_icon} {username}: создано {count_per_user} сообщений"))

            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Пользователь {username} не найден"))

        self.stdout.write(self.style.SUCCESS(f"🎉 СОЗДАНИЕ ЗАВЕРШЕНО! Всего создано: {messages_created} сообщений"))
        self.stdout.write(self.style.WARNING("💡 Для скроллинга в чате теперь достаточно контента!"))
        self.stdout.write(self.style.WARNING("🧪 Перейдите в чат для тестирования: http://127.0.0.1:8001/chat/general/"))
