# 🎯 План завершения проекта "Беседка"

## 📋 Оглавление

1. [Обзор текущего состояния](#обзор-текущего-состояния)
2. [Критические исправления](#этап-1-критические-исправления)
3. [Завершение магазина](#этап-2-завершение-магазина)
4. [Социальные функции](#этап-3-социальные-функции)
5. [Оптимизация и продакшн](#этап-4-оптимизация-и-продакшн)
6. [Инструкции по выполнению](#инструкции-по-выполнению)

---

## 🔍 Обзор текущего состояния

### ✅ Что уже готово:
- Архитектура проекта и структура
- Модели данных для всех модулей
- Система авторизации и ролей
- Административные панели для разных ролей
- Docker-контейнеризация
- Базовая инфраструктура

### ❌ Что требует доработки:
- Критическая ошибка в логике доступа владельца
- Отсутствие UI для социальных функций
- WebSocket для чата не настроен
- Нет публичного каталога магазина
- Отсутствуют тесты

### 📊 Оценка времени:
- **Общее время**: 15-20 рабочих дней
- **При интенсивной работе**: 10-12 дней

---

## 🚨 Этап 1: Критические исправления

**Время**: 1-2 дня  
**Приоритет**: КРИТИЧЕСКИЙ

### 1.1 Исправление логики ролей

#### Проблема:
Владелец платформы не может зайти в админки магазина из-за ошибки в `AdminRedirectMiddleware`.

#### Решение:

```python
# core/middleware.py - исправить логику для владельца
if getattr(user, 'role', None) == 'owner':
    # Владелец имеет доступ ко всем админкам без ограничений
    if path.startswith('/store_owner/') or path.startswith('/store_admin/'):
        print(f"   ✅ ВЛАДЕЛЕЦ ПЛАТФОРМЫ → ДОСТУП К АДМИНКЕ МАГАЗИНА")
        return None  # Разрешаем доступ
    
    # Остальная логика остается прежней
    elif path.startswith('/moderator_admin/'):
        target_admin = '/moderator_admin/'
        print(f"   👑 ВЛАДЕЛЕЦ ПЛАТФОРМЫ → АДМИНКА МОДЕРАТОРА")
    else:
        target_admin = '/owner_admin/'
        print(f"   👑 ВЛАДЕЛЕЦ ПЛАТФОРМЫ → АДМИНКА ПЛАТФОРМЫ")
```

### 1.2 Создание системы тестирования

#### Структура тестов:

```
tests/
├── test_roles/
│   ├── test_owner_access.py
│   ├── test_admin_access.py
│   ├── test_store_roles.py
│   └── test_user_permissions.py
├── test_models/
│   ├── test_user_model.py
│   ├── test_store_models.py
│   └── test_social_models.py
└── test_integration/
    ├── test_auth_flow.py
    ├── test_admin_redirect.py
    └── test_store_workflow.py
```

#### Пример теста для ролей:

```python
# tests/test_roles/test_owner_access.py
from django.test import TestCase, Client
from django.urls import reverse
from users.models import User

class OwnerAccessTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123',
            role='owner',
            is_staff=True
        )
        self.client = Client()
        self.client.login(username='owner', password='testpass123')
    
    def test_owner_can_access_all_admins(self):
        """Владелец должен иметь доступ ко всем админкам"""
        admin_urls = [
            '/owner_admin/',
            '/moderator_admin/',
            '/store_owner/',
            '/store_admin/',
        ]
        
        for url in admin_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [200, 302])
            if response.status_code == 302:
                # Проверяем, что не перенаправляет на логин
                self.assertNotIn('/login/', response.url)
```

### 1.3 Настройка системы уведомлений

#### Активация модели Notification:

```python
# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User, UserFollow, Notification

@receiver(post_save, sender=UserFollow)
def create_follow_notification(sender, instance, created, **kwargs):
    """Создает уведомление о новом подписчике"""
    if created:
        Notification.objects.create(
            recipient=instance.followed,
            sender=instance.follower,
            notification_type='follow',
            title='Новый подписчик',
            message=f'{instance.follower.username} подписался на вас'
        )

# Аналогично для лайков, комментариев и т.д.
```

### 1.4 Создание базового UI для уведомлений

```html
<!-- templates/includes/notifications.html -->
<div class="notifications-dropdown">
    <button class="btn btn-icon" data-bs-toggle="dropdown">
        <i class="fas fa-bell"></i>
        {% if user.unread_notifications_count %}
            <span class="badge">{{ user.unread_notifications_count }}</span>
        {% endif %}
    </button>
    <div class="dropdown-menu">
        {% for notification in user.recent_notifications %}
            <a class="dropdown-item {% if not notification.is_read %}unread{% endif %}"
               href="{{ notification.get_absolute_url }}">
                <i class="{{ notification.type_icon }}"></i>
                <div>
                    <strong>{{ notification.title }}</strong>
                    <p>{{ notification.message }}</p>
                    <small>{{ notification.created_at|timesince }}</small>
                </div>
            </a>
        {% empty %}
            <p class="text-center p-3">Нет новых уведомлений</p>
        {% endfor %}
    </div>
</div>
```

---

## 🛒 Этап 2: Завершение магазина

**Время**: 3-4 дня  
**Приоритет**: ВЫСОКИЙ

### 2.1 Публичный каталог

#### Структура URL:

```python
# magicbeans_store/urls.py
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Каталог
    path('', views.CatalogView.as_view(), name='catalog'),
    path('seedbank/<slug:slug>/', views.SeedBankDetailView.as_view(), name='seedbank_detail'),
    path('strain/<slug:slug>/', views.StrainDetailView.as_view(), name='strain_detail'),
    
    # Корзина
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:item_id>/', views.AddToCartView.as_view(), name='cart_add'),
    path('cart/remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='cart_remove'),
    
    # Оформление заказа
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('checkout/confirm/', views.OrderConfirmView.as_view(), name='order_confirm'),
    
    # Личный кабинет
    path('account/', views.AccountView.as_view(), name='account'),
    path('account/orders/', views.OrderListView.as_view(), name='order_list'),
    path('account/order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]
```

#### Views для каталога:

```python
# magicbeans_store/views.py
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Strain, SeedBank, StockItem

class CatalogView(ListView):
    model = Strain
    template_name = 'store/catalog.html'
    context_object_name = 'strains'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Strain.objects.filter(is_active=True)
        
        # Фильтр по сидбанку
        seedbank = self.request.GET.get('seedbank')
        if seedbank:
            queryset = queryset.filter(seedbank__slug=seedbank)
        
        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Сортировка
        sort = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seedbanks'] = SeedBank.objects.filter(is_active=True)
        context['current_seedbank'] = self.request.GET.get('seedbank')
        return context
```

### 2.2 Корзина покупок

#### Модель корзины:

```python
# magicbeans_store/models/cart.py
from django.db import models
from django.conf import settings

class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['user', 'session_key']]
    
    def get_total(self):
        return sum(item.get_total() for item in self.items.all())
    
    def get_items_count(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    stock_item = models.ForeignKey('StockItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = [['cart', 'stock_item']]
    
    def get_total(self):
        return self.stock_item.price * self.quantity
```

### 2.3 Процесс оформления заказа

#### Checkout View:

```python
# magicbeans_store/views/checkout.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView
from django.shortcuts import redirect
from ..forms import CheckoutForm
from ..models import Order, OrderItem

class CheckoutView(LoginRequiredMixin, FormView):
    template_name = 'store/checkout.html'
    form_class = CheckoutForm
    
    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        initial.update({
            'email': user.email,
            'phone': getattr(user.profile_extra, 'phone', ''),
            'delivery_address': getattr(user.profile_extra, 'address', ''),
        })
        return initial
    
    def form_valid(self, form):
        # Создаем заказ
        cart = self.get_cart()
        order = Order.objects.create(
            user=self.request.user,
            status=OrderStatus.objects.get(code='pending'),
            total_amount=cart.get_total(),
            delivery_address=form.cleaned_data['delivery_address'],
            phone=form.cleaned_data['phone'],
            email=form.cleaned_data['email'],
            shipping_method=form.cleaned_data['shipping_method'],
            payment_method=form.cleaned_data['payment_method'],
        )
        
        # Создаем позиции заказа
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                stock_item=cart_item.stock_item,
                quantity=cart_item.quantity,
                price=cart_item.stock_item.price
            )
        
        # Очищаем корзину
        cart.items.all().delete()
        
        # Отправляем уведомления
        self.send_order_notifications(order)
        
        return redirect('store:order_confirm', pk=order.pk)
```

### 2.4 Шаблоны для магазина

#### Каталог (store/catalog.html):

```html
{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="container">
    <div class="row">
        <!-- Фильтры -->
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5>Фильтры</h5>
                    
                    <!-- Сидбанки -->
                    <div class="mb-3">
                        <h6>Сидбанки</h6>
                        <div class="list-group">
                            <a href="{% url 'store:catalog' %}" 
                               class="list-group-item {% if not current_seedbank %}active{% endif %}">
                                Все сидбанки
                            </a>
                            {% for seedbank in seedbanks %}
                                <a href="?seedbank={{ seedbank.slug }}" 
                                   class="list-group-item {% if current_seedbank == seedbank.slug %}active{% endif %}">
                                    {{ seedbank.name }}
                                </a>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <!-- Сортировка -->
                    <div class="mb-3">
                        <h6>Сортировка</h6>
                        <select class="form-select" onchange="location = this.value;">
                            <option value="?sort=-created_at">Новинки</option>
                            <option value="?sort=price">Цена: по возрастанию</option>
                            <option value="?sort=-price">Цена: по убыванию</option>
                            <option value="?sort=name">По названию</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Товары -->
        <div class="col-md-9">
            <div class="row">
                {% for strain in strains %}
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            {% if strain.main_photo %}
                                <img src="{{ strain.main_photo.url }}" class="card-img-top" alt="{{ strain.name }}">
                            {% else %}
                                <img src="{% static 'images/no-image.jpg' %}" class="card-img-top" alt="No image">
                            {% endif %}
                            
                            <div class="card-body">
                                <h5 class="card-title">{{ strain.name }}</h5>
                                <p class="text-muted">{{ strain.seedbank.name }}</p>
                                <p class="card-text">{{ strain.description|truncatewords:20 }}</p>
                                
                                <div class="d-flex justify-content-between align-items-center">
                                    <div class="price">
                                        {% with stock=strain.stock_items.first %}
                                            {% if stock %}
                                                <strong>{{ stock.price }} ₽</strong>
                                            {% else %}
                                                <span class="text-muted">Нет в наличии</span>
                                            {% endif %}
                                        {% endwith %}
                                    </div>
                                    
                                    <div class="btn-group">
                                        <a href="{% url 'store:strain_detail' strain.slug %}" 
                                           class="btn btn-sm btn-outline-primary">
                                            Подробнее
                                        </a>
                                        {% if strain.stock_items.exists %}
                                            <button class="btn btn-sm btn-primary add-to-cart"
                                                    data-item-id="{{ strain.stock_items.first.id }}">
                                                В корзину
                                            </button>
                                        {% endif %}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                {% empty %}
                    <div class="col-12">
                        <p class="text-center">Товары не найдены</p>
                    </div>
                {% endfor %}
            </div>
            
            <!-- Пагинация -->
            {% if is_paginated %}
                <nav>
                    <ul class="pagination justify-content-center">
                        {% if page_obj.has_previous %}
                            <li class="page-item">
                                <a class="page-link" href="?page={{ page_obj.previous_page_number }}">
                                    Предыдущая
                                </a>
                            </li>
                        {% endif %}
                        
                        {% for num in page_obj.paginator.page_range %}
                            <li class="page-item {% if page_obj.number == num %}active{% endif %}">
                                <a class="page-link" href="?page={{ num }}">{{ num }}</a>
                            </li>
                        {% endfor %}
                        
                        {% if page_obj.has_next %}
                            <li class="page-item">
                                <a class="page-link" href="?page={{ page_obj.next_page_number }}">
                                    Следующая
                                </a>
                            </li>
                        {% endif %}
                    </ul>
                </nav>
            {% endif %}
        </div>
    </div>
</div>

<script>
// Добавление в корзину через AJAX
document.querySelectorAll('.add-to-cart').forEach(button => {
    button.addEventListener('click', function() {
        const itemId = this.dataset.itemId;
        fetch(`/store/cart/add/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Обновляем счетчик корзины
                updateCartCounter(data.cart_count);
                // Показываем уведомление
                showNotification('Товар добавлен в корзину');
            }
        });
    });
});
</script>
{% endblock %}
```

---

## 🌱 Этап 3: Социальные функции

**Время**: 5-7 дней  
**Приоритет**: СРЕДНИЙ

### 3.1 Grow Logs (Гроу-репорты)

#### Установка django-blog для адаптации:

```bash
pip install django-blog-it
# Или создаем свою реализацию на основе существующих моделей
```

#### Views для гроу-логов:

```python
# growlogs/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import GrowLog, GrowLogEntry
from .forms import GrowLogForm, GrowLogEntryForm

class GrowLogListView(ListView):
    model = GrowLog
    template_name = 'growlogs/list.html'
    context_object_name = 'growlogs'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Для гостей показываем только публичные
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        # Для авторизованных показываем публичные + свои приватные
        elif not self.request.user.has_admin_access:
            queryset = queryset.filter(
                Q(is_public=True) | Q(grower=self.request.user)
            )
        return queryset.select_related('grower', 'strain')

class GrowLogCreateView(LoginRequiredMixin, CreateView):
    model = GrowLog
    form_class = GrowLogForm
    template_name = 'growlogs/create.html'
    
    def form_valid(self, form):
        form.instance.grower = self.request.user
        return super().form_valid(form)

class GrowLogDetailView(DetailView):
    model = GrowLog
    template_name = 'growlogs/detail.html'
    context_object_name = 'growlog'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Проверяем доступ к приватным логам
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = self.object.entries.all().order_by('day')
        context['photos'] = self.object.photos.all()
        return context
```

#### Шаблон для списка гроу-логов:

```html
<!-- templates/growlogs/list.html -->
{% extends 'base.html' %}

{% block content %}
<div class="container">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Гроу-репорты</h1>
        {% if user.is_authenticated %}
            <a href="{% url 'growlogs:create' %}" class="btn btn-primary">
                <i class="fas fa-plus"></i> Создать репорт
            </a>
        {% endif %}
    </div>
    
    <div class="row">
        {% for growlog in growlogs %}
            <div class="col-md-4 mb-4">
                <div class="card h-100">
                    {% if growlog.photos.first %}
                        <img src="{{ growlog.photos.first.image.url }}" 
                             class="card-img-top" 
                             alt="{{ growlog.title }}">
                    {% endif %}
                    
                    <div class="card-body">
                        <h5 class="card-title">
                            {{ growlog.title }}
                            {% if not growlog.is_public %}
                                <i class="fas fa-lock text-muted" title="Приватный"></i>
                            {% endif %}
                        </h5>
                        
                        <p class="card-text">
                            <small class="text-muted">
                                <i class="fas fa-user"></i> {{ growlog.grower.username }}<br>
                                <i class="fas fa-seedling"></i> {{ growlog.strain.name }}<br>
                                <i class="fas fa-calendar"></i> {{ growlog.start_date|date:"d.m.Y" }}
                            </small>
                        </p>
                        
                        <p class="card-text">{{ growlog.setup_description|truncatewords:20 }}</p>
                        
                        <a href="{% url 'growlogs:detail' growlog.pk %}" 
                           class="btn btn-primary btn-sm">
                            Читать дальше
                        </a>
                    </div>
                </div>
            </div>
        {% empty %}
            <div class="col-12">
                <p class="text-center">Пока нет гроу-репортов</p>
            </div>
        {% endfor %}
    </div>
    
    <!-- Пагинация -->
    {% include 'includes/pagination.html' %}
</div>
{% endblock %}
```

### 3.2 Галерея

#### Использование django-photologue:

```bash
pip install django-photologue
```

#### Или своя реализация:

```python
# gallery/views.py
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .models import Photo, PhotoComment

class GalleryView(ListView):
    model = Photo
    template_name = 'gallery/gallery.html'
    context_object_name = 'photos'
    paginate_by = 24
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        return queryset.select_related('author').prefetch_related('likes')

class PhotoUploadView(LoginRequiredMixin, CreateView):
    model = Photo
    fields = ['title', 'description', 'image', 'growlog', 'is_public']
    template_name = 'gallery/upload.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        # Добавляем карму за загрузку фото
        self.request.user.add_karma(5, "Загрузка фото")
        
        return response

class PhotoLikeView(LoginRequiredMixin, View):
    def post(self, request, pk):
        photo = get_object_or_404(Photo, pk=pk)
        
        if request.user in photo.likes.all():
            photo.likes.remove(request.user)
            liked = False
        else:
            photo.likes.add(request.user)
            liked = True
            
            # Уведомление автору
            if photo.author != request.user:
                Notification.objects.create(
                    recipient=photo.author,
                    sender=request.user,
                    notification_type='like',
                    title='Новый лайк',
                    message=f'{request.user.username} оценил ваше фото',
                    content_object=photo
                )
        
        return JsonResponse({
            'liked': liked,
            'likes_count': photo.likes.count()
        })
```

### 3.3 Чат с WebSocket

#### Настройка Django Channels:

```python
# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'main_chat'
        self.room_group_name = f'chat_{self.room_name}'
        
        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Покидаем группу
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Сохраняем сообщение в БД
        chat_message = await self.save_message(message)
        
        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.scope['user'].username,
                'timestamp': chat_message.created_at.isoformat()
            }
        )
    
    async def chat_message(self, event):
        # Отправляем сообщение в WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def save_message(self, message):
        return ChatMessage.objects.create(
            author=self.scope['user'],
            text=message
        )
```

#### Routing для WebSocket:

```python
# chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
]
```

#### Настройка ASGI:

```python
# config/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

#### Фронтенд для чата:

```html
<!-- templates/chat/room.html -->
{% extends 'base.html' %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-8 offset-md-2">
            <div class="card">
                <div class="card-header">
                    <h4>Чат сообщества</h4>
                </div>
                
                <div class="card-body" id="chat-messages" style="height: 400px; overflow-y: auto;">
                    <!-- Загружаем историю сообщений -->
                    {% for message in messages %}
                        <div class="message mb-2">
                            <strong>{{ message.author.username }}:</strong>
                            <span>{{ message.text }}</span>
                            <small class="text-muted">{{ message.created_at|date:"H:i" }}</small>
                        </div>
                    {% endfor %}
                </div>
                
                <div class="card-footer">
                    <form id="chat-form">
                        <div class="input-group">
                            <input type="text" 
                                   id="chat-message-input" 
                                   class="form-control" 
                                   placeholder="Введите сообщение...">
                            <button type="submit" class="btn btn-primary">
                                Отправить
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    const chatSocket = new WebSocket(
        'ws://' + window.location.host + '/ws/chat/'
    );
    
    const messagesContainer = document.getElementById('chat-messages');
    const messageInput = document.getElementById('chat-message-input');
    const chatForm = document.getElementById('chat-form');
    
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message mb-2';
        messageDiv.innerHTML = `
            <strong>${data.username}:</strong>
            <span>${data.message}</span>
            <small class="text-muted">${new Date(data.timestamp).toLocaleTimeString()}</small>
        `;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };
    
    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
    };
    
    chatForm.onsubmit = function(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (message) {
            chatSocket.send(JSON.stringify({
                'message': message
            }));
            messageInput.value = '';
        }
    };
</script>
{% endblock %}
```

---

## 🚀 Этап 4: Оптимизация и продакшн

**Время**: 3-5 дней  
**Приоритет**: ВАЖНЫЙ

### 4.1 Настройка кеширования

```python
# config/settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

# Кеширование сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Кеширование шаблонов
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]
```

### 4.2 Оптимизация запросов

```python
# Пример оптимизации в views
class OptimizedStrainListView(ListView):
    model = Strain
    
    def get_queryset(self):
        return (
            super().get_queryset()
            .select_related('seedbank')
            .prefetch_related('stock_items', 'photos')
            .annotate(
                min_price=Min('stock_items__price'),
                in_stock=Count('stock_items', filter=Q(stock_items__quantity__gt=0))
            )
        )
```

### 4.3 Настройка мониторинга

```python
# requirements/production.txt
sentry-sdk==1.45.0
django-prometheus==2.3.1

# config/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True
)

# Prometheus метрики
INSTALLED_APPS += ['django_prometheus']
MIDDLEWARE = ['django_prometheus.middleware.PrometheusBeforeMiddleware'] + MIDDLEWARE
MIDDLEWARE += ['django_prometheus.middleware.PrometheusAfterMiddleware']
```

### 4.4 Безопасность

```python
# config/settings/production.py
# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_VIEW = 'ratelimit.views.ratelimited'
```

### 4.5 Настройка CI/CD

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/local.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/besedka_test
      run: |
        python manage.py migrate
        python manage.py test
    
    - name: Run linting
      run: |
        flake8 .
        black --check .
        isort --check-only .
```

---

## 📝 Инструкции по выполнению

### Для внедрения этого плана в проект:

1. **Сохраните файл в корне проекта:**
   ```bash
   # Файл уже создан как BESEDKA_COMPLETION_PLAN.md
   ```

2. **Добавьте в Git:**
   ```bash
   git add BESEDKA_COMPLETION_PLAN.md
   git commit -m "Add detailed completion plan for Besedka project"
   ```

3. **Используйте как чек-лист:**
   - Отмечайте выполненные пункты
   - Добавляйте заметки о проблемах
   - Обновляйте временные оценки

### Структура для отслеживания прогресса:

```markdown
## Прогресс выполнения

### Этап 1: Критические исправления
- [x] Исправление логики ролей - ✅ Выполнено 15.01.2025
- [ ] Создание системы тестирования - 🚧 В процессе
- [ ] Настройка системы уведомлений - ⏳ Ожидает
- [ ] Создание базового UI для уведомлений - ⏳ Ожидает

### Этап 2: Завершение магазина
...
```

### Команды для быстрого старта:

```bash
# Проверка текущего состояния
python manage.py check_modules_status

# Запуск тестов
python manage.py test

# Создание миграций
python manage.py makemigrations
python manage.py migrate

# Запуск сервера разработки
python manage.py runserver

# Запуск с WebSocket (для чата)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

---

## 🎯 Ключевые метрики успеха

1. **Все тесты проходят** (coverage > 80%)
2. **Нет критических ошибок** в Sentry
3. **Время загрузки страниц** < 2 секунд
4. **Все роли работают корректно**
5. **WebSocket чат стабилен**
6. **Каталог магазина функционален**
7. **Социальные функции доступны**

---

## 📞 Контрольные точки

После каждого этапа проверяйте:

1. ✅ Работает ли авторизация?
2. ✅ Корректно ли работают роли?
3. ✅ Доступны ли все админки?
4. ✅ Функционирует ли магазин?
5. ✅ Работают ли социальные функции?
6. ✅ Стабилен ли чат?
7. ✅ Нет ли ошибок в консоли?

---

Этот план представляет собой пошаговое руководство для завершения проекта "Беседка" с учетом всех обнаруженных проблем и необходимых улучшений. 
