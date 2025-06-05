from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.http import JsonResponse
from django.views import View
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Room, Message, Thread, DiscussionRoom, Tag, GlobalChatRoom, VIPChatRoom
from .forms import MessageForm, DiscussionRoomForm

User = get_user_model()


class ChatHomeView(LoginRequiredMixin, TemplateView):
    """Главная страница чата - перенаправляет на общий чат"""
    template_name = 'chat/chat_home.html'

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


class PrivateChatsView(LoginRequiredMixin, ListView):
    """Список приватных чатов пользователя"""
    template_name = 'chat/private_chats.html'
    context_object_name = 'threads'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        return Thread.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).select_related('room', 'user1', 'user2').order_by('-room__modified')


class PrivateThreadView(LoginRequiredMixin, DetailView):
    """Детальный вид приватного чата"""
    model = Thread
    template_name = 'chat/private_thread.html'
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


class DiscussionsView(LoginRequiredMixin, ListView):
    """Список групповых обсуждений"""
    model = DiscussionRoom
    template_name = 'chat/discussions.html'
    context_object_name = 'discussions'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # ВРЕМЕННО ЗАБЛОКИРОВАНО: Функционал обсуждений в разработке
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tags'] = Tag.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_tag'] = self.request.GET.get('tag', '')
        return context


class CreateDiscussionView(LoginRequiredMixin, CreateView):
    """Создание нового группового обсуждения"""
    model = DiscussionRoom
    form_class = DiscussionRoomForm
    template_name = 'chat/create_discussion.html'
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
    template_name = 'chat/discussion_detail.html'
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
    template_name = 'chat/room.html'
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
        total_messages = Message.objects.filter(room=global_chat.room).count()
        total_users = User.objects.filter(is_active=True).count()

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
            'total_messages': total_messages,
            'total_users': total_users,
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
            # Данные для унифицированного заголовка
            'header_theme': 'vip',
            'header_title': 'VIP Беседка',
            'header_icon': 'fa-crown',
            'header_meta': header_meta,
        })
        return context
