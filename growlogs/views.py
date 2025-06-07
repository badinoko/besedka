from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.db.models import Q, F
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
import json
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import GrowLog, GrowLogEntry, GrowLogComment, GrowLogEntryLike, GrowLogEntryComment
from .forms import GrowLogCreateForm, GrowLogEntryForm, GrowLogCommentForm, GrowLogEntryCommentForm
from core.models import ActionLog
from users.models import Notification
from magicbeans_store.models import Strain, SeedBank

class GrowLogListView(ListView):
    """Список всех публичных гроу-логов"""
    model = GrowLog
    template_name = 'growlogs/list.html'
    context_object_name = 'growlogs'
    paginate_by = 12

    def get_queryset(self):
        queryset = GrowLog.objects.filter(
            is_active=True,
            is_public=True
        ).select_related('grower', 'strain').prefetch_related('likes', 'comments')

        # Поиск
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(grower__username__icontains=search_query) |
                Q(strain__name__icontains=search_query)
            )

        # Фильтр по стадии
        stage = self.request.GET.get('stage')
        if stage:
            queryset = queryset.filter(current_stage=stage)

        # Фильтр по среде
        environment = self.request.GET.get('environment')
        if environment:
            queryset = queryset.filter(environment=environment)

        # Сортировка
        sort_by = self.request.GET.get('sort_by', '-start_date')

        if sort_by == '-start_date':
            # Новые сначала по дате начала, потом по id для стабильности
            queryset = queryset.order_by('-start_date', '-id')
        elif sort_by == 'start_date':
            # Старые сначала
            queryset = queryset.order_by('start_date', 'id')
        elif sort_by == '-views_count':
            # Популярные
            queryset = queryset.order_by('-views_count', '-start_date')
        elif sort_by == 'title':
            # По названию А-Я
            queryset = queryset.order_by('title', '-start_date')
        elif sort_by == '-title':
            # По названию Я-А
            queryset = queryset.order_by('-title', '-start_date')
        elif sort_by == '-created_at':
            # По дате создания (новые сначала)
            queryset = queryset.order_by('-created_at', '-id')
        elif sort_by == 'created_at':
            # По дате создания (старые сначала)
            queryset = queryset.order_by('created_at', 'id')
        else:
            # По умолчанию - новые по дате начала
            queryset = queryset.order_by('-start_date', '-id')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Добавляем статистику для hero-секции
        all_growlogs = GrowLog.objects.filter(is_active=True, is_public=True)
        total_reports = all_growlogs.count()
        total_growers = all_growlogs.values('grower').distinct().count()

        # Считаем общее количество дней опыта
        total_days = sum([growlog.current_day for growlog in all_growlogs])

        context.update({
            'stages': GrowLog.STAGE_CHOICES,
            'environments': GrowLog.ENVIRONMENT_CHOICES,
            'search_query': self.request.GET.get('search', ''),
            'current_stage': self.request.GET.get('stage', ''),
            'current_environment': self.request.GET.get('environment', ''),
            'current_sort': self.request.GET.get('sort_by', '-start_date'),
            # Статистика для hero-секции
            'total_reports': total_reports,
            'total_growers': total_growers,
            'total_days': total_days,
        })
        return context

class MyGrowLogsView(LoginRequiredMixin, ListView):
    """Мои гроу-логи"""
    model = GrowLog
    template_name = 'growlogs/my_logs.html'
    context_object_name = 'growlogs'
    paginate_by = 10

    def get_queryset(self):
        return GrowLog.objects.filter(grower=self.request.user).select_related('strain')

class GrowLogCreateView(LoginRequiredMixin, FormView):
    """Создание гроу-репорта с пошаговым мастером"""
    template_name = 'growlogs/create_wizard.html'
    form_class = GrowLogCreateForm

    # Определяем поля для каждого шага
    STEP_FIELDS = {
        1: ['title', 'strain_name', 'seedbank_name', 'start_date', 'logo', 'short_description'],
        2: ['environment', 'medium', 'nutrients', 'lighting', 'container_size', 'setup_description'],
        3: ['goals', 'notes', 'yield_expected', 'is_public']
    }

    def get_form_class(self):
        """Возвращаем класс формы в зависимости от шага"""
        current_step = self.get_current_step()
        step_fields = self.get_step_fields(current_step)

        # Создаем динамическую форму только с полями текущего шага
        class StepForm(GrowLogCreateForm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Оставляем только поля текущего шага (используем step_fields из замыкания)
                for field_name in list(self.fields.keys()):
                    if field_name not in step_fields:
                        del self.fields[field_name]

        return StepForm

    def get_step_fields(self, step):
        """Получаем поля для конкретного шага"""
        return self.STEP_FIELDS.get(step, [])

    def get_current_step(self):
        """Получаем текущий шаг"""
        return int(self.request.GET.get('step', 1))

    def get_form_kwargs(self):
        """Передаем сохраненные данные в форму"""
        kwargs = super().get_form_kwargs()

        # Если есть сохраненные данные, используем их как начальные
        if 'growlog_wizard_data' in self.request.session:
            saved_data = self.request.session['growlog_wizard_data']
            kwargs['initial'] = kwargs.get('initial', {})
            kwargs['initial'].update(saved_data)

        return kwargs

    def get(self, request, *args, **kwargs):
        current_step = self.get_current_step()

        # Проверяем валидность шага
        if current_step < 1 or current_step > 3:
            return redirect('growlogs:create')

        # Инициализируем мастер создания
        wizard_data = {
            'current_step': current_step,
            'steps': [
                {'num': 1, 'title': 'Основная информация', 'icon': 'fa-info-circle', 'description': 'Название, сорт, даты и краткое описание'},
                {'num': 2, 'title': 'Настройка grow', 'icon': 'fa-cogs', 'description': 'Среда, освещение, питание'},
                {'num': 3, 'title': 'Цели и приватность', 'icon': 'fa-target', 'description': 'Планы, ожидания и настройки доступа'}
            ],
            'form': self.get_form()
        }

        # Если есть данные в сессии (для многошагового процесса)
        if 'growlog_wizard_data' in request.session:
            wizard_data['saved_data'] = request.session['growlog_wizard_data']

        return render(request, self.template_name, wizard_data)

    def post(self, request, *args, **kwargs):
        current_step = self.get_current_step()
        form = self.get_form()

        if form.is_valid():
            # Сохраняем данные в сессии
            if 'growlog_wizard_data' not in request.session:
                request.session['growlog_wizard_data'] = {}

            # Обновляем данные текущего шага
            for field, value in form.cleaned_data.items():
                if field == 'logo':
                    # Пропускаем логотип - обработаем отдельно
                    continue
                elif hasattr(value, 'strftime'):  # Даты
                    request.session['growlog_wizard_data'][field] = value.isoformat()
                elif isinstance(value, models.Model): # Сохраняем PK для объектов моделей
                    request.session['growlog_wizard_data'][field] = value.pk
                elif hasattr(value, 'quantize'):  # Decimal поля
                    request.session['growlog_wizard_data'][field] = str(value)
                else:
                    request.session['growlog_wizard_data'][field] = value

            # Обрабатываем файлы (логотип) - сохраняем временно
            if 'logo' in request.FILES:
                import tempfile
                import os
                import shutil

                uploaded_file = request.FILES['logo']

                # Создаем временную директорию если её нет
                temp_dir = os.path.join(tempfile.gettempdir(), 'growlog_wizard')
                os.makedirs(temp_dir, exist_ok=True)

                # Создаем уникальное имя файла
                import uuid
                temp_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
                temp_path = os.path.join(temp_dir, temp_filename)

                # Сохраняем файл временно
                with open(temp_path, 'wb') as temp_file:
                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)

                # Сохраняем путь к временному файлу в сессии
                request.session['growlog_wizard_logo_path'] = temp_path
                request.session['growlog_wizard_logo_name'] = uploaded_file.name

            request.session.modified = True

            if current_step < 3:
                # Переходим к следующему шагу
                return redirect(f"{reverse('growlogs:create')}?step={current_step + 1}")
            else:
                # Финальный шаг - создаем grow log
                return self.create_growlog(request)
        else:
            # Если форма не валидна, показываем ошибки
            wizard_data = {
                'current_step': current_step,
                'steps': [
                    {'num': 1, 'title': 'Основная информация', 'icon': 'fa-info-circle', 'description': 'Название, сорт, даты и краткое описание'},
                    {'num': 2, 'title': 'Настройка grow', 'icon': 'fa-cogs', 'description': 'Среда, освещение, питание'},
                    {'num': 3, 'title': 'Цели и приватность', 'icon': 'fa-target', 'description': 'Планы, ожидания и настройки доступа'}
                ],
                'form': form
            }

            if 'growlog_wizard_data' in request.session:
                wizard_data['saved_data'] = request.session['growlog_wizard_data']

            return render(request, self.template_name, wizard_data)

    def create_growlog(self, request):
        """Создание гроу-лога из данных мастера"""
        try:
            data = request.session.get('growlog_wizard_data', {})

            # Преобразуем строковые значения обратно в нужные типы
            if 'start_date' in data and isinstance(data['start_date'], str):
                from datetime import datetime
                data['start_date'] = datetime.fromisoformat(data['start_date']).date()

            # Преобразуем Decimal поля
            if 'yield_expected' in data and isinstance(data['yield_expected'], str):
                from decimal import Decimal
                try:
                    data['yield_expected'] = Decimal(data['yield_expected'])
                except:
                    data['yield_expected'] = None

            # Создаем объект
            growlog = GrowLog.objects.create(
                grower=request.user,
                title=data.get('title', ''),
                start_date=data.get('start_date'),
                environment=data.get('environment', 'indoor'),
                medium=data.get('medium', ''),
                nutrients=data.get('nutrients', ''),
                lighting=data.get('lighting', ''),
                container_size=data.get('container_size', ''),
                setup_description=data.get('setup_description', ''),
                short_description=data.get('short_description', ''),
                goals=data.get('goals', ''),
                notes=data.get('notes', ''),
                yield_expected=data.get('yield_expected'),
                is_public=data.get('is_public', True)
            )

            # Обрабатываем сорт
            strain_name = data.get('strain_name')
            seedbank_name = data.get('seedbank_name')

            if strain_name:
                # Используем улучшенную логику поиска из формы
                strain_name = strain_name.strip()
                seedbank_name = seedbank_name.strip() if seedbank_name else None

                # Ищем точное совпадение в магазине
                strain = self._find_strain_in_store(strain_name, seedbank_name)

                if strain:
                    growlog.strain = strain
                    growlog.strain_custom = ""
                else:
                    # Если не найден в магазине - сохраняем как произвольный сорт
                    growlog.strain = None
                    # Сохраняем нормализованное название (возможно с сидбанком)
                    if seedbank_name:
                        growlog.strain_custom = f"{strain_name} ({seedbank_name})"
                    else:
                        growlog.strain_custom = strain_name

                growlog.save()

            # Обрабатываем логотип, если он был загружен
            if 'growlog_wizard_logo_path' in request.session:
                import os
                from django.core.files import File

                temp_path = request.session['growlog_wizard_logo_path']
                original_name = request.session.get('growlog_wizard_logo_name', 'logo.jpg')

                if os.path.exists(temp_path):
                    with open(temp_path, 'rb') as temp_file:
                        growlog.logo.save(original_name, File(temp_file), save=True)

                    # Удаляем временный файл
                    try:
                        os.remove(temp_path)
                    except:
                        pass  # Игнорируем ошибки удаления

            # Создаем первую запись
            GrowLogEntry.objects.create(
                growlog=growlog,
                day=1,
                stage='germination',
                activities='Grow log started! 🌱'
            )

            # Логируем действие
            ActionLog.objects.create(
                user=request.user,
                action_type='growlog_created',
                model_name='GrowLog',
                object_id=growlog.pk,
                object_repr=str(growlog),
                details=f'Created grow log: {growlog.title}'
            )

            # Очищаем сессию
            if 'growlog_wizard_data' in request.session:
                del request.session['growlog_wizard_data']
            if 'growlog_wizard_logo_path' in request.session:
                # Удаляем временный файл если еще не удален
                temp_path = request.session['growlog_wizard_logo_path']
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
                del request.session['growlog_wizard_logo_path']
            if 'growlog_wizard_logo_name' in request.session:
                del request.session['growlog_wizard_logo_name']

            messages.success(request, f'Grow log "{growlog.title}" успешно создан!')
            return redirect('growlogs:detail', pk=growlog.pk)

        except Exception as e:
            messages.error(request, f'Ошибка при создании grow log: {str(e)}')
            # Также очищаем сессию при ошибке
            if 'growlog_wizard_data' in request.session:
                del request.session['growlog_wizard_data']
            if 'growlog_wizard_logo_path' in request.session:
                temp_path = request.session['growlog_wizard_logo_path']
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
                del request.session['growlog_wizard_logo_path']
            if 'growlog_wizard_logo_name' in request.session:
                del request.session['growlog_wizard_logo_name']
            return redirect('growlogs:create')

    def _find_strain_in_store(self, strain_name, seedbank_name):
        """
        Ищем сорт в магазине с улучшенной логикой сопоставления:
        1. Если указан сидбанк - ищем точное совпадение по сорту И сидбанку
        2. Если сидбанк не указан - НЕ автоматически связываем, чтобы избежать ошибок
        3. Автокоррекция регистра для нормализации данных
        """
        if not strain_name:
            return None

        # Если указан сидбанк - ищем строгое совпадение
        if seedbank_name:
            # Сначала ищем сидбанк
            seedbank = SeedBank.objects.filter(
                name__iexact=seedbank_name
            ).first()

            if seedbank:
                # Ищем сорт у конкретного сидбанка
                strain = Strain.objects.filter(
                    name__iexact=strain_name,
                    seedbank=seedbank,
                    is_active=True
                ).first()
                return strain
            else:
                # Сидбанк не найден - не связываем
                return None
        else:
            # Сидбанк не указан - проверяем, есть ли уникальный сорт
            strains = Strain.objects.filter(
                name__iexact=strain_name,
                is_active=True
            )

            # Если есть ровно ОДИН сорт с таким названием - связываем
            if strains.count() == 1:
                return strains.first()
            elif strains.count() > 1:
                # Есть несколько сортов с одинаковым названием - НЕ связываем автоматически
                # Требуем указания сидбанка для точности
                return None
            else:
                # Сорт не найден
                return None

class GrowLogDetailView(DetailView):
    """Детальный просмотр с таймлайном"""
    model = GrowLog
    template_name = 'growlogs/detail_new.html'
    context_object_name = 'growlog'

    def dispatch(self, request, *args, **kwargs):
        """Проверяем доступ для гостей"""
        # Получаем объект чтобы проверить его публичность
        try:
            growlog = self.get_object()
        except:
            raise Http404("Гроурепорт не найден")

        # Если гроурепорт приватный и пользователь не авторизован - показываем приглашение
        if not growlog.is_public and not request.user.is_authenticated:
            from django.shortcuts import render

            return render(request, 'growlogs/guest_access_denied.html', {
                'growlog': growlog,
                'section_name': 'приватный гроурепорт',
                'action_description': 'просматривать приватные гроурепорты'
            })

        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        obj = super().get_object()

        # Проверяем доступ для авторизованных пользователей
        if not obj.is_public and obj.grower != self.request.user:
            raise Http404("Гроурепорт не найден")

        # Увеличиваем счетчик просмотров (но не для автора и гостей)
        if self.request.user.is_authenticated and self.request.user != obj.grower:
            GrowLog.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Формируем таймлайн
        entries = self.object.entries.all().order_by('day').prefetch_related('entry_photos', 'comments', 'likes')
        timeline = []

        for entry in entries:
            timeline.append({
                'id': entry.id,
                'day': entry.day,
                'date': entry.created_at,
                'stage': entry.stage,
                'stage_display': entry.get_stage_display(),
                'photos': entry.entry_photos.all(),
                'activities': entry.activities,
                'environmental_data': {
                    'temperature': entry.temperature,
                    'humidity': entry.humidity,
                    'ph': entry.ph,
                    'ec': entry.ec
                },
                'plant_data': {
                    'height': entry.height,
                    'width': entry.width,
                    'water_amount': entry.water_amount,
                    'nutrients_used': entry.nutrients_used
                },
                'likes_count': entry.likes.count(),
                'comments_count': entry.comments.count(),
                'comments': entry.comments.all()[:5],  # Показываем первые 5 комментариев
            })

        context['timeline'] = timeline

        # Получаем последние параметры среды для боковой панели
        latest_entry = self.object.entries.filter(
            models.Q(temperature__isnull=False) |
            models.Q(humidity__isnull=False) |
            models.Q(ph__isnull=False) |
            models.Q(ec__isnull=False)
        ).order_by('-day').first()

        if latest_entry:
            context['latest_environment'] = {
                'temperature': latest_entry.temperature,
                'humidity': latest_entry.humidity,
                'ph': latest_entry.ph,
                'ec': latest_entry.ec,
                'day': latest_entry.day,
                'date': latest_entry.created_at
            }
        else:
            context['latest_environment'] = None

        # Статистика
        context['stats'] = {
            'total_days': self.object.current_day,
            'total_entries': self.object.entries.count(),
            'current_stage': self.object.get_current_stage_display(),
            'environment': self.object.get_environment_display(),
        }

        # Лайки
        context['likes_count'] = self.object.likes.count()
        context['user_liked'] = self.object.likes.filter(id=self.request.user.id).exists() if self.request.user.is_authenticated else False

        # Комментарии
        context['comments'] = self.object.comments.all().order_by('created_at')
        context['comment_form'] = GrowLogCommentForm()

        # Права доступа
        context['can_edit'] = (
            self.request.user.is_authenticated and
            self.request.user == self.object.grower
        )

        return context

class GrowLogEntryCreateView(LoginRequiredMixin, CreateView):
    """Добавление новой записи в гроу-лог"""
    model = GrowLogEntry
    form_class = GrowLogEntryForm
    template_name = 'growlogs/add_entry.html'

    def dispatch(self, request, *args, **kwargs):
        self.growlog = get_object_or_404(GrowLog, pk=kwargs['growlog_pk'])

        # Проверяем права
        if self.growlog.grower != request.user:
            return HttpResponseForbidden("You can only add entries to your own grow logs")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['growlog'] = self.growlog
        return kwargs

    def form_valid(self, form):
        form.instance.growlog = self.growlog

        # Автоматически определяем день
        last_entry = self.growlog.entries.order_by('-day').first()
        if last_entry:
            form.instance.day = last_entry.day + 1
        else:
            form.instance.day = 1

        response = super().form_valid(form)

        # Обновляем текущую стадию grow log
        self.growlog.current_stage = form.instance.stage
        self.growlog.save(update_fields=['current_stage'])

        messages.success(self.request, f'Запись для дня {form.instance.day} добавлена!')
        return response

    def get_success_url(self):
        return reverse('growlogs:detail', kwargs={'pk': self.growlog.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['growlog'] = self.growlog
        return context

@login_required
def toggle_like_growlog(request, pk):
    """НЕОБРАТИМЫЙ лайк гроу-лога (для системы кармы и рейтинга)"""
    growlog = get_object_or_404(GrowLog, pk=pk)
    user = request.user

    # Проверяем, уже лайкнул ли пользователь
    if user in growlog.likes.all():
        return JsonResponse({
            'success': False,
            'liked': True,
            'action': 'already_liked',
            'likes_count': growlog.likes.count(),
            'message': 'Вы уже поставили лайк этому репорту'
        })

    # Добавляем лайк (необратимо)
    growlog.likes.add(user)
    action_taken = "liked"

    ActionLog.objects.create(
        user=user,
        action_type='growlog_liked',
        model_name='GrowLog',
        object_id=growlog.pk,
        object_repr=str(growlog),
        details=f'User liked growlog: {growlog.title}'
    )

    # Уведомление автору (если не сам себе лайк)
    if growlog.grower != user:
        Notification.objects.create(
            recipient=growlog.grower,
            sender=user,
            notification_type='like',
            title='Новый лайк!',
            message=f'{user.username} лайкнул ваш гроу-лог "{growlog.title}"',
            content_object=growlog
        )

    return JsonResponse({
        'success': True,
        'liked': True,
        'action': action_taken,
        'likes_count': growlog.likes.count(),
        'message': 'Лайк засчитан! Спасибо за поддержку'
    })

class GrowLogCommentCreateView(LoginRequiredMixin, CreateView):
    """Добавление комментария к гроу-логу"""
    model = GrowLogComment
    form_class = GrowLogCommentForm
    # template_name = 'growlogs/detail.html' # Комментарий добавляется на странице детализации

    def dispatch(self, request, *args, **kwargs):
        self.growlog = get_object_or_404(GrowLog, pk=self.kwargs.get('growlog_pk'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.growlog = self.growlog
        comment.save()

        ActionLog.objects.create(
            user=self.request.user,
            action_type='comment_added_growlog',
            model_name='GrowLogComment',
            object_id=comment.pk,
            object_repr=str(comment),
            details=f'Comment added to growlog: {self.growlog.title}'
        )

        # Уведомление автору гроу-лога
        if self.growlog.grower != self.request.user:
            Notification.objects.create(
                recipient=self.growlog.grower,
                sender=self.request.user,
                notification_type='comment',
                title='Новый комментарий к вашему гроу-логу!',
                message=f'{self.request.user.username} прокомментировал ваш гроу-лог "{self.growlog.title}"',
                content_object=self.growlog
            )

        messages.success(self.request, 'Комментарий успешно добавлен.')
        return redirect('growlogs:detail', pk=self.growlog.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['growlog'] = self.growlog
        return context

    def get_success_url(self):
        return reverse('growlogs:detail', kwargs={'pk': self.growlog.pk})

# TODO: GrowLogUpdateView, GrowLogDeleteView, GrowLogEntryUpdateView, GrowLogEntryDeleteView
# TODO: GrowLogCommentUpdateView, GrowLogCommentDeleteView

@login_required
@require_POST
def toggle_entry_like(request, entry_id):
    """НЕОБРАТИМЫЙ лайк записи гроу-лога (для системы кармы и рейтинга)"""
    try:
        entry = get_object_or_404(GrowLogEntry, id=entry_id)

        # Проверяем права доступа
        if not entry.growlog.is_public and entry.growlog.grower != request.user:
            return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

        like, created = GrowLogEntryLike.objects.get_or_create(
            entry=entry,
            user=request.user
        )

        if not created:
            # Лайк уже существует - нельзя отозвать
            return JsonResponse({
                'status': 'error',
                'action': 'already_liked',
                'likes_count': entry.likes.count(),
                'message': 'Вы уже поставили лайк этой записи'
            })

        # Лайк успешно добавлен
        likes_count = entry.likes.count()

        return JsonResponse({
            'status': 'ok',
            'action': 'liked',
            'likes_count': likes_count,
            'message': 'Лайк засчитан! Спасибо за поддержку'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def add_entry_comment(request, entry_id):
    """AJAX добавление комментария к записи"""
    try:
        entry = get_object_or_404(GrowLogEntry, id=entry_id)

        # Проверяем, что growlog публичный или пользователь - автор
        if not entry.growlog.is_public and entry.growlog.grower != request.user:
            return JsonResponse({'success': False, 'error': 'No access'}, status=403)

        # Обрабатываем JSON данные
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            text = data.get('text', '').strip()
        else:
            text = request.POST.get('text', '').strip()

        if not text:
            return JsonResponse({'success': False, 'error': 'Comment text is required'})

        comment = GrowLogEntryComment.objects.create(
            entry=entry,
            author=request.user,
            text=text
        )

        # Создаем уведомление для автора grow log (если это не он сам)
        if entry.growlog.grower != request.user:
            try:
                Notification.objects.create(
                    recipient=entry.growlog.grower,
                    sender=request.user,
                    title="Новый комментарий к записи",
                    message=f"{request.user.username} прокомментировал день {entry.day} в вашем grow log '{entry.growlog.title}'",
                    notification_type='comment',
                    content_object=entry.growlog
                )
            except:
                # Если модель Notification не импортирована или не существует, пропускаем уведомление
                pass

        return JsonResponse({
            'success': True,
            'comment': {
                'author': comment.author.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
            },
            'comments_count': entry.comments.count()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

class GrowLogUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование гроу-репорта"""
    model = GrowLog
    form_class = GrowLogCreateForm
    template_name = 'growlogs/edit_growlog.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Проверяем права
        if self.object.grower != request.user:
            return HttpResponseForbidden("Вы можете редактировать только свои гроу-репорты")

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        """Заполняем форму текущими данными"""
        initial = super().get_initial()

        # Заполняем поля сорта и сидбанка
        if self.object.strain:
            initial['strain_name'] = self.object.strain.name
            if self.object.strain.seedbank:
                initial['seedbank_name'] = self.object.strain.seedbank.name
        elif self.object.strain_custom:
            # Парсим произвольный сорт
            if '(' in self.object.strain_custom and ')' in self.object.strain_custom:
                parts = self.object.strain_custom.rsplit('(', 1)
                initial['strain_name'] = parts[0].strip()
                initial['seedbank_name'] = parts[1].replace(')', '').strip()
            else:
                initial['strain_name'] = self.object.strain_custom

        return initial

    def form_valid(self, form):
        response = super().form_valid(form)

        # Обрабатываем изменение сорта
        strain_name = form.cleaned_data.get('strain_name')
        seedbank_name = form.cleaned_data.get('seedbank_name')

        if strain_name:
            strain = form._find_strain_in_store(strain_name.strip(), seedbank_name.strip() if seedbank_name else None)

            if strain:
                self.object.strain = strain
                self.object.strain_custom = ""
            else:
                self.object.strain = None
                if seedbank_name:
                    self.object.strain_custom = f"{strain_name.strip()} ({seedbank_name.strip()})"
                else:
                    self.object.strain_custom = strain_name.strip()

            self.object.save()

        # Логируем изменение
        ActionLog.objects.create(
            user=self.request.user,
            action_type='growlog_updated',
            model_name='GrowLog',
            object_id=self.object.pk,
            object_repr=str(self.object),
            details=f'Updated grow log: {self.object.title}'
        )

        messages.success(self.request, 'Гроу-репорт успешно обновлен!')
        return response

    def get_success_url(self):
        return reverse('growlogs:detail', kwargs={'pk': self.object.pk})

class GrowLogEntryUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование записи гроу-репорта"""
    model = GrowLogEntry
    form_class = GrowLogEntryForm
    template_name = 'growlogs/edit_entry.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Проверяем права
        if self.object.growlog.grower != request.user:
            return HttpResponseForbidden("Вы можете редактировать только записи своих гроу-репортов")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['growlog'] = self.object.growlog
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        # Обновляем текущую стадию гроу-репорта на основе записи
        growlog = self.object.growlog
        growlog.current_stage = self.object.stage
        growlog.save()

        # Логируем изменение
        ActionLog.objects.create(
            user=self.request.user,
            action_type='growlog_entry_updated',
            model_name='GrowLogEntry',
            object_id=self.object.pk,
            object_repr=str(self.object),
            details=f'Updated entry for day {self.object.day} in grow log: {growlog.title}'
        )

        messages.success(self.request, f'Запись "День {self.object.day}" успешно обновлена!')
        return response

    def get_success_url(self):
        return reverse('growlogs:detail', kwargs={'pk': self.object.growlog.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['growlog'] = self.object.growlog
        return context
