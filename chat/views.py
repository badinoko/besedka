from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView, CreateView, TemplateView
from django.http import JsonResponse
from django.views import View
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Room, Message, Thread, DiscussionRoom, Tag, GlobalChatRoom, VIPChatRoom
from .forms import MessageForm, DiscussionRoomForm
from django.db.models import Count
from core.base_views import UnifiedListView

User = get_user_model()


class ChatHomeView(LoginRequiredMixin, TemplateView):
    """Главная страница чата - перенаправляет на общий чат"""
    # Используем единый шаблон общего чата как безопасный fallback (старый chat_home удалён)
    template_name = 'chat/general_chat.html'

    def dispatch(self, request, *args, **kwargs):
        # Перенаправляем сразу на общий чат, убирая промежуточную страницу
        return redirect('chat:general')

    def get_context_data(self, **kwargs):
        # Этот метод больше не используется, так как мы перенаправляем
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Последние приватные чаты
        private_threads = Thread.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).select_related('room', 'user1', 'user2')[:5]

        # Активные обсуждения
        active_discussions = DiscussionRoom.objects.filter(
            members=user
        ).select_related('room', 'owner')[:5]

        # Трендовые обсуждения
        trending_discussions = DiscussionRoom.objects.get_trendings()[:5]

        context.update({
            'private_threads': private_threads,
            'active_discussions': active_discussions,
            'trending_discussions': trending_discussions,
        })
        return context


class PrivateChatsView(LoginRequiredMixin, UnifiedListView):
    """Унифицированный список приватных чатов пользователя"""

    model = Thread
    paginate_by = 20

    # Настройки единой hero-секции
    section_title = "Личные чаты"
    section_subtitle = "Ваши приватные разговоры с другими участниками"
    section_hero_class = "chat-hero"
    card_type = "chat"

    def get_queryset(self):
        """Получить все приватные чаты текущего пользователя, отсортированные по дате изменения."""
        user = self.request.user
        return (
            Thread.objects.filter(Q(user1=user) | Q(user2=user))
            .select_related('room', 'user1', 'user2')
            .order_by('-room__modified')
        )

    # --- HERO ---
    def get_hero_stats(self):
        user = self.request.user
        qs = self.get_queryset()
        unread_total = 0
        for thread in qs:
            unread_total += thread.room.unread_count(user)
        return [
            {'value': qs.count(), 'label': 'Всего чатов'},
            {'value': unread_total, 'label': 'Непрочитанных'},
        ]

    def get_filter_list(self):
        # Пока фильтров нет – возвращаем пустой список
        return []

    def get_unified_cards(self, page_obj):
        """Преобразовать объекты Thread в формат унифицированных карточек."""
        cards = []
        current_user = self.request.user
        for thread in page_obj:
            partner = thread.get_partner(current_user)

            # Аватар партнёра или плейсхолдер
            if partner and getattr(partner, 'avatar', None):
                avatar_url = partner.avatar.url
            else:
                avatar_url = '/static/images/default_avatar.svg'

            # Последнее сообщение
            last_msg = thread.room.latest_message()
            last_msg_text = last_msg.content if last_msg else 'Еще нет сообщений'

            unread_count = thread.room.unread_count(current_user)

            cards.append({
                'id': str(thread.id),
                'type': 'chat',
                'title': partner.username if partner else 'Неизвестный',
                'description': last_msg_text[:120],
                'image_url': avatar_url,
                'detail_url': reverse_lazy('chat:private_thread', kwargs={'thread_id': thread.id}),
                'author': {
                    'name': partner.username if partner else 'Неизвестный',
                    'avatar': avatar_url,
                },
                'stats': (
                    [{'icon': 'fa-envelope', 'count': unread_count, 'css': 'unread'}]
                    if unread_count else []
                ),
                'created_at': thread.room.modified,
            })
        return cards


class PrivateThreadView(LoginRequiredMixin, DetailView):
    """Детальный вид приватного чата"""
    model = Thread
    # Удалённый шаблон private_thread.html заменён на общий шаблон чата для предотвращения 500 ошибок
    template_name = 'chat/general_chat.html'
    context_object_name = 'thread'
    pk_url_kwarg = 'thread_id'

    def get_object(self):
        thread = get_object_or_404(Thread, id=self.kwargs['thread_id'])
        user = self.request.user

        # Проверяем, что пользователь участвует в этом чате
        if user not in [thread.user1, thread.user2]:
            raise PermissionError(_('У вас нет доступа к этому чату'))

        return thread

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.object
        user = self.request.user

        # Получаем сообщения
        chat_messages = thread.room.get_messages().select_related('author')[:50]

        # Отмечаем сообщения как прочитанные
        thread.room.unread_messages(user).update(unread=False)

        # Партнер по чату
        partner = thread.get_partner(user)

        context.update({
            'chat_messages': chat_messages,
            'partner': partner,
            'room': thread.room,
            'message_form': MessageForm(),
        })
        return context


class StartPrivateChatView(LoginRequiredMixin, View):
    """Начать приватный чат с пользователем"""

    def get(self, request, user_id):
        partner = get_object_or_404(User, id=user_id)

        if partner == request.user:
            messages.error(request, _('Нельзя начать чат с самим собой'))
            return redirect('chat:private_chats')

        # Создаем или получаем существующий чат
        thread, created = Thread.objects.new_or_get(request.user, partner)

        if created:
            messages.success(request, _('Приватный чат создан'))

        return redirect('chat:private_thread', thread_id=thread.id)


class DiscussionsView(LoginRequiredMixin, UnifiedListView):
    """Унифицированный список групповых обсуждений"""

    model = DiscussionRoom
    paginate_by = 20

    section_title = "Групповые обсуждения"
    section_subtitle = "Обсуждайте темы сообщества в открытых комнатах"
    section_hero_class = "chat-hero"
    card_type = "discussion"

    def dispatch(self, request, *args, **kwargs):
        # Функционал обсуждений временно закрыт – используем общий чат
        messages.warning(request, _('Функционал групповых обсуждений временно недоступен. Используйте общий чат "Беседка".'))
        return redirect('chat:general')

    def get_queryset(self):
        queryset = DiscussionRoom.objects.select_related('room', 'owner').prefetch_related('tags', 'members')

        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.search(search)

        # Фильтр по тегам
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        return queryset.order_by('-modified')

    def get_filter_list(self):
        return []

    def get_hero_stats(self):
        qs = self.get_queryset()
        return [
            {'value': qs.count(), 'label': 'Всего обсуждений'},
            {'value': qs.aggregate(total_members=Count('members'))['total_members'] or 0, 'label': 'Участников'},
        ]

    def get_unified_cards(self, page_obj):
        cards = []
        for discussion in page_obj:
            owner = discussion.owner
            avatar_url = owner.avatar.url if getattr(owner, 'avatar', None) else '/static/images/default_avatar.svg'
            last_msg = discussion.room.latest_message()
            last_msg_text = last_msg.content if last_msg else discussion.description[:120] if discussion.description else 'Нет сообщений'
            cards.append({
                'id': discussion.id,
                'type': 'discussion',
                'title': discussion.headline,
                'description': last_msg_text[:120],
                'image_url': avatar_url,
                'detail_url': reverse_lazy('chat:discussion_detail', kwargs={'pk': discussion.pk}),
                'author': {'name': owner.username, 'avatar': avatar_url},
                'stats': [
                    {'icon': 'fa-users', 'count': discussion.members.count(), 'css': 'members'},
                    {'icon': 'fa-comment', 'count': discussion.room.room_messages.count(), 'css': 'messages'},
                ],
                'created_at': discussion.modified,
            })
        return cards


class CreateDiscussionView(LoginRequiredMixin, CreateView):
    """Создание нового группового обсуждения"""
    model = DiscussionRoom
    form_class = DiscussionRoomForm
    # Fallback на единый шаблон чата; специализированный шаблон будет создан позднее при рефакторинге обсуждений
    template_name = 'chat/general_chat.html'
    success_url = reverse_lazy('chat:discussions')

    def dispatch(self, request, *args, **kwargs):
        # ВРЕМЕННО ЗАБЛОКИРОВАНО: Функционал обсуждений в разработке
        messages.warning(request, _('Функционал групповых обсуждений временно недоступен. Используйте общий чат "Беседка".'))
        return redirect('chat:general')

    def form_valid(self, form):
        # Создаем комнату для обсуждения
        room = Room.objects.create(is_discussion=True)

        # Устанавливаем владельца и комнату
        form.instance.owner = self.request.user
        form.instance.room = room

        response = super().form_valid(form)

        messages.success(self.request, _('Обсуждение успешно создано'))
        return response


class DiscussionDetailView(LoginRequiredMixin, DetailView):
    """Детальный вид группового обсуждения"""
    model = DiscussionRoom
    # Временный fallback до полной переработки обсуждений
    template_name = 'chat/general_chat.html'
    context_object_name = 'discussion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        discussion = self.object
        user = self.request.user

        # Получаем сообщения
        chat_messages = discussion.room.get_messages().select_related('author')[:50]

        # Отмечаем сообщения как прочитанные
        discussion.room.unread_messages(user).update(unread=False)

        # Добавляем пользователя в участники, если его там нет
        if user not in discussion.members.all():
            discussion.members.add(user)

        context.update({
            'chat_messages': chat_messages,
            'room': discussion.room,
            'message_form': MessageForm(),
            'is_member': user in discussion.members.all(),
        })
        return context


class RoomView(LoginRequiredMixin, DetailView):
    """Общий вид комнаты (для WebSocket подключений)"""
    model = Room
    # Унифицированный шаблон комнаты заменён на общий шаблон чата
    template_name = 'chat/general_chat.html'
    context_object_name = 'room'
    pk_url_kwarg = 'room_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = self.object
        user = self.request.user

        # Проверяем доступ к комнате
        has_access = False

        if room.is_private and hasattr(room, 'room_thread'):
            thread = room.room_thread
            has_access = user in [thread.user1, thread.user2]
        elif room.is_discussion and hasattr(room, 'discussion_room'):
            discussion = room.discussion_room
            has_access = user in discussion.members.all()

        if not has_access:
            raise PermissionError(_('У вас нет доступа к этой комнате'))

        # Получаем сообщения
        chat_messages = room.get_messages().select_related('author')[:50]

        context.update({
            'chat_messages': chat_messages,
            'message_form': MessageForm(),
        })
        return context


# AJAX Views

class SendMessageAjaxView(LoginRequiredMixin, View):
    """AJAX отправка сообщения"""

    def post(self, request):
        room_id = request.POST.get('room_id')
        content = request.POST.get('content', '').strip()
        reply_to_id = request.POST.get('reply_to')

        if not content:
            return JsonResponse({'error': _('Сообщение не может быть пустым')}, status=400)

        try:
            room = Room.objects.get(id=room_id)

            # Проверяем доступ
            user = request.user
            has_access = False

            if room.is_private and hasattr(room, 'room_thread'):
                thread = room.room_thread
                has_access = user in [thread.user1, thread.user2]
            elif room.is_discussion and hasattr(room, 'discussion_room'):
                discussion = room.discussion_room
                has_access = user in discussion.members.all()

            if not has_access:
                return JsonResponse({'error': _('Нет доступа к комнате')}, status=403)

            # Создаем сообщение
            reply_to = None
            if reply_to_id:
                try:
                    reply_to = Message.objects.get(id=reply_to_id, room=room)
                except Message.DoesNotExist:
                    pass

            message = Message.objects.create(
                author=user,
                room=room,
                content=content,
                reply_to=reply_to
            )

            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'author': message.author.username,
                    'created': message.created.isoformat(),
                    'reply_to': reply_to.id if reply_to else None,
                }
            })

        except Room.DoesNotExist:
            return JsonResponse({'error': _('Комната не найдена')}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class MarkMessagesReadAjaxView(LoginRequiredMixin, View):
    """AJAX отметка сообщений как прочитанных"""

    def post(self, request):
        room_id = request.POST.get('room_id')

        try:
            room = Room.objects.get(id=room_id)
            unread_count = room.unread_messages(request.user).update(unread=False)

            return JsonResponse({
                'success': True,
                'marked_count': unread_count
            })

        except Room.DoesNotExist:
            return JsonResponse({'error': _('Комната не найдена')}, status=404)


class LoadMessagesAjaxView(LoginRequiredMixin, View):
    """AJAX загрузка сообщений"""

    def get(self, request):
        room_id = request.GET.get('room_id')
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))

        try:
            room = Room.objects.get(id=room_id)

            # Проверяем доступ
            user = request.user
            has_access = False

            if room.is_private and hasattr(room, 'room_thread'):
                thread = room.room_thread
                has_access = user in [thread.user1, thread.user2]
            elif room.is_discussion and hasattr(room, 'discussion_room'):
                discussion = room.discussion_room
                has_access = user in discussion.members.all()

            if not has_access:
                return JsonResponse({'error': _('Нет доступа к комнате')}, status=403)

            # Получаем сообщения
            messages = room.get_messages().select_related('author')[offset:offset+limit]

            messages_data = []
            for msg in messages:
                messages_data.append({
                    'id': msg.id,
                    'content': msg.content,
                    'author': msg.author.username,
                    'created': msg.created.isoformat(),
                    'reply_to': msg.reply_to.id if msg.reply_to else None,
                })

            return JsonResponse({
                'success': True,
                'messages': messages_data,
                'has_more': len(messages) == limit
            })

        except Room.DoesNotExist:
            return JsonResponse({'error': _('Комната не найдена')}, status=404)


class GeneralChatView(LoginRequiredMixin, TemplateView):
    """Общий чат для всех пользователей"""
    template_name = 'chat/general_chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем или создаем общий чат
        global_chat = GlobalChatRoom.get_or_create_default()

        # Получаем последние сообщения
        chat_messages = Message.objects.filter(
            room=global_chat.room
        ).select_related('author').order_by('-created')[:50]

        # Получаем количество онлайн пользователей (приблизительно)
        online_count = global_chat.room.connected_clients.count()

        # Получаем список онлайн пользователей
        online_users = global_chat.room.connected_clients.all()[:20]

        # Получаем общее количество сообщений и пользователей для статистики
        total_general_messages = Message.objects.filter(room=global_chat.room).count()
        total_general_users = User.objects.filter(is_active=True).count()

        # ДАННЫЕ ДЛЯ УНИФИЦИРОВАННОГО ЗАГОЛОВКА
        user = self.request.user

        # Метаданные для заголовка
        header_meta = [
            {
                'icon': 'fa-users',
                'text': f'Онлайн: {online_count}'
            },
            {
                'icon': 'fa-globe',
                'text': 'Открытый чат'
            },
            {
                'icon': 'fa-shield-alt',
                'text': 'Модерируется'
            }
        ]

        context.update({
            'global_chat': global_chat,
            'chat_messages': chat_messages,
            'online_count': online_count,
            'online_users': online_users,
            'total_general_messages': total_general_messages,
            'total_general_users': total_general_users,
            # Данные для унифицированного заголовка
            'header_theme': 'chat',
            'header_title': 'Чат Беседка',
            'header_icon': 'fa-comments',
            'header_meta': header_meta,
        })
        return context


class VIPChatView(LoginRequiredMixin, TemplateView):
    """VIP-чат только по приглашениям"""
    template_name = 'chat/vip_chat.html'

    def dispatch(self, request, *args, **kwargs):
        """Проверяем доступ к VIP-чату"""
        user = request.user

        try:
            self.vip_chat = VIPChatRoom.objects.get(is_active=True)
        except VIPChatRoom.DoesNotExist:
            messages.error(request, _('VIP-чат не найден'))
            return redirect('chat:home')

        # Проверяем права доступа
        if not self.vip_chat.can_access(user):
            messages.error(request, _('У вас нет доступа к VIP-чату'))
            return redirect('chat:home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        room = self.vip_chat.room

        # Получаем последние сообщения
        chat_messages = room.get_messages().select_related('author')[:50]

        # Отмечаем сообщения как прочитанные
        room.unread_messages(user).update(unread=False)

        # Подключаем пользователя к комнате
        room.connect(user)

        # Получаем участников VIP-чата
        vip_members = self.vip_chat.members.filter(
            vipchatmembership__is_active=True
        )

        # Получаем пользователей онлайн
        online_users = room.connected_clients.all()

        # СТАТИСТИКА ДЛЯ VIP ЧАТА
        total_vip_messages = Message.objects.filter(room=room).count()
        total_vip_users = vip_members.count()

        # ДАННЫЕ ДЛЯ УНИФИЦИРОВАННОГО ЗАГОЛОВКА
        # Метаданные для заголовка
        header_meta = [
            {
                'icon': 'fa-users',
                'text': f'Онлайн: {online_users.count()}'
            },
            {
                'icon': 'fa-lock',
                'text': 'Приватный чат'
            }
        ]

        context.update({
            'vip_chat': self.vip_chat,
            'room': room,
            'chat_messages': chat_messages,
            'message_form': MessageForm(),
            'vip_members': vip_members,
            'online_users': online_users,
            'online_count': online_users.count(),
            'total_vip_messages': total_vip_messages,
            'total_vip_users': total_vip_users,
            # Данные для унифицированного заголовка
            'header_theme': 'vip',
            'header_title': 'VIP Беседка',
            'header_icon': 'fa-crown',
            'header_meta': header_meta,
        })
        return context


# 🚀 ROCKET.CHAT МИГРАЦИЯ - ИЗОЛИРОВАННАЯ ТЕСТОВАЯ СТРАНИЦА

class RocketChatTestView(TemplateView):
    """Изолированный view для тестирования Rocket.Chat"""
    template_name = 'chat/rocketchat_test.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rocketchat_url'] = 'http://127.0.0.1:3000'
        return context


from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class RocketChatOAuthView(View):
    """
    Кастомный OAuth view для Rocket.Chat.
    Автоматически одобряет OAuth запросы для залогиненных пользователей.
    """

    def get(self, request, *args, **kwargs):
        """Автоматически создаем authorization code и редиректим"""
        client_id = request.GET.get('client_id')
        redirect_uri = request.GET.get('redirect_uri')
        response_type = request.GET.get('response_type')
        scope = request.GET.get('scope', 'read')
        state = request.GET.get('state', '')

        # Проверяем что это запрос от Rocket.Chat
        if client_id != 'BesedkaRocketChat2025':
            # Для других клиентов используем стандартный OAuth view
            from oauth2_provider.views import AuthorizationView
            return AuthorizationView.as_view()(request, *args, **kwargs)

        logger.info(f"RocketChat OAuth request from {request.user.username}")

        # Импортируем необходимые модели
        from oauth2_provider.models import Application, Grant
        from django.utils import timezone
        from datetime import timedelta
        import secrets

        try:
            # Получаем приложение
            application = Application.objects.get(client_id=client_id)

            # Создаем authorization grant (код авторизации)
            code = secrets.token_urlsafe(30)

            grant = Grant.objects.create(
                user=request.user,
                application=application,
                code=code,
                expires=timezone.now() + timedelta(seconds=60),
                redirect_uri=redirect_uri,
                scope=scope
            )

            logger.info(f"Created authorization code for {request.user.username}: {code[:10]}...")

            # Формируем URL для редиректа с кодом
            params = {
                'code': code,
                'state': state
            }

            # Парсим redirect_uri и добавляем параметры
            if '?' in redirect_uri:
                full_redirect_url = f"{redirect_uri}&{urlencode(params)}"
            else:
                full_redirect_url = f"{redirect_uri}?{urlencode(params)}"

            logger.info(f"Redirecting to: {full_redirect_url}")

            return HttpResponseRedirect(full_redirect_url)

        except Application.DoesNotExist:
            logger.error(f"OAuth application not found: {client_id}")
            # Если приложение не найдено, используем стандартный view
            from oauth2_provider.views import AuthorizationView
            return AuthorizationView.as_view()(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"OAuth auto-auth error: {str(e)}")
            # При ошибке используем стандартный view
            from oauth2_provider.views import AuthorizationView
            return AuthorizationView.as_view()(request, *args, **kwargs)

# В конец файла chat/views.py добавьте:

class RocketChatIntegratedView(LoginRequiredMixin, TemplateView):
    """Интегрированный view для Rocket.Chat с кнопками переключения каналов"""
    template_name = 'chat/rocketchat_integrated.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rocketchat_url'] = 'http://127.0.0.1:3000'

        # Проверяем VIP доступ
        user = self.request.user
        context['user_has_vip_access'] = (
            user.is_staff or
            user.role == 'owner' or
            hasattr(user, 'vip_memberships') and
            user.vip_memberships.filter(is_active=True).exists()
        )

        return context
