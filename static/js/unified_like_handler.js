/**
 * Унифицированный обработчик лайков для всех разделов проекта
 * Поддерживает: галерею, гроурепорты, новости
 * SSOT: Single Source of Truth для всех лайков
 * ИСПРАВЛЕНО: кнопки ВСЕГДА кликабельные и красивые, показывают уведомления при повторных нажатиях
 */

class UnifiedLikeHandler {
    constructor() {
        this.apiUrl = '/internal/core/ajax/like/';
        this.notifications = window.unifiedNotifications || null;
        this.init();
    }

    init() {
        // Привязываем обработчики к кнопкам лайков
        document.addEventListener('click', (e) => {
            const likeBtn = e.target.closest('[data-like-object-type]');
            if (likeBtn) {
                e.preventDefault();
                this.handleLike(likeBtn);
            }
        });

        // ✅ НОВОЕ: Инициализируем красивые кнопки при загрузке (БЕЗ отключения)
        this.initializeButtonStates();
    }

    initializeButtonStates() {
        // Находим все кнопки лайков и ВСЕГДА оставляем их красивыми и кликабельными
        const likeButtons = document.querySelectorAll('[data-like-object-type]');
        likeButtons.forEach(button => {
            // ✅ НОВОЕ: Даже лайкнутые кнопки остаются кликабельными
            // Просто помечаем их как лайкнутые для визуальной индикации
            if (button.classList.contains('liked')) {
                button.title = 'Лайк уже поставлен (нажмите для повтора)';
            } else {
                button.title = 'Лайкнуть';
            }
            // НЕ отключаем кнопки - они остаются всегда активными
        });
    }

    async handleLike(button) {
        // Предотвращаем повторные клики только во время обработки
        if (button.classList.contains('processing')) {
            return;
        }

        const objectType = button.dataset.likeObjectType;
        const objectId = button.dataset.likeObjectId;
        const action = button.dataset.likeAction || 'toggle';
        const reactionType = button.dataset.reactionType || 'like';

        if (!objectType || !objectId) {
            console.error('Отсутствуют обязательные данные для лайка');
            return;
        }

        // Показываем состояние загрузки
        this.setLoadingState(button, true);

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    object_type: objectType,
                    object_id: parseInt(objectId),
                    action: action,
                    reaction_type: reactionType
                })
            });

            const data = await response.json();

            if (data.success) {
                this.updateButton(button, data);
                this.updateCounter(button, data.likes_count);
                this.showFeedback(button, data);
            } else {
                throw new Error(data.error || 'Ошибка при обработке лайка');
            }

        } catch (error) {
            console.error('Ошибка лайка:', error);
            this.showNotification('Ошибка при добавлении лайка', 'error');
        } finally {
            this.setLoadingState(button, false);
        }
    }

    updateButton(button, data) {
        // ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Кнопка ВСЕГДА остается красивой!
        // НЕ МЕНЯЕМ стили кнопки - она должна всегда выглядеть одинаково

        // Только обновляем title для информативности
        if (data.action === 'liked') {
            button.classList.add('liked');
            button.title = 'Лайк добавлен! (можете нажать еще раз)';
        } else if (data.action === 'already_liked') {
            button.classList.add('liked');
            button.title = 'Лайк уже поставлен (нажмите еще раз если хотите)';
        } else if (data.action === 'cannot_like_own') {
            button.title = 'Нельзя лайкнуть собственный контент';
        }

        // ✅ ПРИНУДИТЕЛЬНО СОХРАНЯЕМ КРАСИВЫЙ ДИЗАЙН
        // Убираем любые лишние классы, которые могут сломать дизайн
        button.classList.remove('btn-outline-danger', 'btn-secondary', 'disabled');

        // ✅ ПРИНУДИТЕЛЬНО ВОЗВРАЩАЕМ КРАСИВУЮ ИКОНКУ ПАЛЬЦА ВВЕРХ
        const iconElement = button.querySelector('.like-icon');
        if (iconElement) {
            iconElement.innerHTML = '<i class="fas fa-thumbs-up"></i>';
            // Принудительно белый цвет иконки
            iconElement.style.color = '#ffffff';
        }

        // ✅ ПРИНУДИТЕЛЬНО СОХРАНЯЕМ КРАСИВЫЕ СТИЛИ КНОПКИ
        button.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 50%, #bd2130 100%)';
        button.style.border = '3px solid #dc3545';
        button.style.color = '#ffffff';
        button.style.boxShadow = '0 15px 35px rgba(220, 53, 69, 0.45), 0 8px 20px rgba(220, 53, 69, 0.35), 0 4px 8px rgba(0, 0, 0, 0.25), inset 0 2px 0 rgba(255, 255, 255, 0.3), inset 0 -2px 0 rgba(0, 0, 0, 0.2)';

        // ✅ КНОПКА ВСЕГДА ОСТАЕТСЯ КЛИКАБЕЛЬНОЙ
        button.disabled = false;
        button.style.pointerEvents = 'auto';
        button.style.cursor = 'pointer';
    }

    updateCounter(button, count) {
        // Ищем счетчик лайков рядом с кнопкой или по data-атрибуту
        const counterId = button.dataset.likeCounterId;
        let counter = null;

        if (counterId) {
            counter = document.getElementById(counterId);
        } else {
            // Ищем счетчик в родительском элементе
            const container = button.closest('.like-container, .stats-container, .hero-stat, .card');
            if (container) {
                counter = container.querySelector('.likes-count, .like-count, [data-stat="likes"]');
            }
        }

        if (counter) {
            counter.textContent = count;

            // Анимация изменения счетчика
            counter.classList.add('count-updated');
            setTimeout(() => counter.classList.remove('count-updated'), 300);
        }
    }

    showFeedback(button, data) {
        // Легкая анимация кнопки
        button.classList.add('like-animation');
        setTimeout(() => button.classList.remove('like-animation'), 300);

        // ✅ ИСПРАВЛЕНО: Показываем уведомления для всех случаев
        switch (data.action) {
            case 'liked':
                // Эффект частиц при успешном лайке
                this.createLikeParticles(button);
                this.showNotification('Лайк добавлен!', 'success');
                break;
            case 'already_liked':
                // ✅ НОВОЕ: Показываем уведомление при повторном клике
                this.showNotification('Вы уже поставили лайк этому контенту', 'info');
                break;
            case 'cannot_like_own':
                // ✅ НОВОЕ: Показываем уведомление при попытке лайкнуть свой контент
                this.showNotification('Нельзя лайкнуть собственный контент', 'warning');
                break;
        }
    }

    createLikeParticles(button) {
        // Простая анимация частиц при лайке
        const rect = button.getBoundingClientRect();
        const particle = document.createElement('div');
        particle.className = 'like-particle';
        particle.innerHTML = '❤️';
        particle.style.cssText = `
            position: fixed;
            left: ${rect.left + rect.width / 2}px;
            top: ${rect.top}px;
            z-index: 9999;
            pointer-events: none;
            font-size: 20px;
            animation: likeParticle 1s ease-out forwards;
        `;

        document.body.appendChild(particle);
        setTimeout(() => particle.remove(), 1000);
    }

    setLoadingState(button, loading) {
        if (loading) {
            button.classList.add('processing');
            // ✅ НЕ МЕНЯЕМ ИКОНКУ - оставляем палец вверх всегда
            // Только добавляем легкую анимацию пульсации
        } else {
            button.classList.remove('processing');
            // ✅ ПРИНУДИТЕЛЬНО ВОЗВРАЩАЕМ КРАСИВУЮ ИКОНКУ И СТИЛИ
            const iconElement = button.querySelector('.like-icon');
            if (iconElement) {
                iconElement.innerHTML = '<i class="fas fa-thumbs-up"></i>';
                iconElement.style.color = '#ffffff';
            }

            // ✅ ПРИНУДИТЕЛЬНО СОХРАНЯЕМ КРАСИВЫЕ СТИЛИ
            button.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 50%, #bd2130 100%)';
            button.style.border = '3px solid #dc3545';
            button.style.color = '#ffffff';
            button.style.cursor = 'pointer';
        }
    }

    showNotification(message, type = 'info') {
        // ✅ ИСПРАВЛЕНО: Используем центральную систему уведомлений
        if (this.notifications && typeof this.notifications.show === 'function') {
            this.notifications.show(message, type);
        } else {
            // Fallback на случай недоступности системы уведомлений
            this.showFallbackNotification(message, type);
        }
    }

    showFallbackNotification(message, type) {
        // Простая fallback реализация, если основная система недоступна
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'warning' ? 'warning' : type === 'success' ? 'success' : 'info'}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            padding: 15px 20px;
            border-radius: 8px;
            max-width: 350px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideInRight 0.3s ease-out;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Автоматическое удаление
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    getCSRFToken() {
        return this.getCookie('csrftoken');
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// CSS для анимаций частиц и уведомлений
const style = document.createElement('style');
style.textContent = `
@keyframes likeParticle {
    0% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
    100% {
        opacity: 0;
        transform: translateY(-50px) scale(1.5);
    }
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

.like-animation {
    animation: likePress 0.3s ease-out;
}

@keyframes likePress {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

.count-updated {
    animation: countBounce 0.3s ease-out;
}

@keyframes countBounce {
    0% { transform: scale(1); }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); }
}
`;
document.head.appendChild(style);

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new UnifiedLikeHandler();
});

// Экспорт для использования в других скриптах
window.UnifiedLikeHandler = UnifiedLikeHandler;
