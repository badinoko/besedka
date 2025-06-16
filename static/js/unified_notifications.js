/**
 * Глобальная унифицированная система уведомлений v2.2
 * Центральные уведомления с наложением друг на друга
 * v2.2 - позиционирование изменено на top: 40% для лучшего центрирования
 */

class UnifiedNotifications {
    constructor() {
        this.container = null;
        this.activeNotifications = [];
        this.createContainer();
    }

    createContainer() {
        // Создаем контейнер для уведомлений, если его нет
        this.container = document.getElementById('central-notification-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'central-notification-container';
            this.container.style.cssText = `
                position: fixed;
                top: 40%;
                left: 50%;
                transform: translateX(-50%);
                z-index: 99999;
                pointer-events: none;
                width: 100%;
                max-width: 500px;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 0px;
            `;
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = 3000) {
        const notification = this.createNotification(message, type);

        // ✅ НОВОЕ: Накладываем уведомления друг на друга
        // Убираем все предыдущие уведомления с плавным исчезновением
        this.clearPreviousNotifications();

        // Добавляем новое уведомление
        this.container.appendChild(notification);
        this.activeNotifications.push(notification);

        // Триггерим появление
        requestAnimationFrame(() => {
            notification.style.transform = 'translateY(0) scale(1)';
            notification.style.opacity = '1';
        });

        // Автоматическое удаление
        setTimeout(() => {
            this.removeNotification(notification);
        }, duration);

        return notification;
    }

    clearPreviousNotifications() {
        // ✅ НОВОЕ: Быстро убираем предыдущие уведомления
        this.activeNotifications.forEach(notification => {
            if (notification && notification.parentNode) {
                this.removeNotification(notification, true); // Быстрое удаление
            }
        });
        this.activeNotifications = [];
    }

    createNotification(message, type) {
        const notification = document.createElement('div');

        // Определяем цветовую схему и иконку
        const typeConfig = {
            success: { color: '#28a745', icon: '✓' },
            error: { color: '#dc3545', icon: '✕' },
            warning: { color: '#fd7e14', icon: '⚠' },
            info: { color: '#007bff', icon: 'ℹ' }
        };

        const config = typeConfig[type] || typeConfig.info;

        notification.style.cssText = `
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border: 2px solid ${config.color};
            border-radius: 12px;
            padding: 16px 24px;
            margin: 0;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            color: #333;
            font-weight: 500;
            min-width: 300px;
            max-width: 450px;
            text-align: center;
            font-size: 14px;
            line-height: 1.4;
            pointer-events: auto;
            cursor: pointer;
            position: relative;

            /* ✅ НОВОЕ: Начальное состояние для анимации */
            transform: translateY(-100px) scale(0.8);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);

            /* ✅ НОВОЕ: Позиционирование - все в одном месте */
            position: relative;
            top: 0;
            transform: translateY(-100px) scale(0.8);
        `;

        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px; justify-content: center;">
                <span style="
                    font-size: 18px;
                    color: ${config.color};
                    font-weight: bold;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.1);
                ">${config.icon}</span>
                <span style="flex: 1;">${message}</span>
            </div>
        `;

        // Клик для закрытия
        notification.addEventListener('click', () => {
            this.removeNotification(notification);
        });

        return notification;
    }

    removeNotification(notification, fast = false) {
        if (!notification || !notification.parentNode) return;

        const animationDuration = fast ? 150 : 300;

        // Анимация исчезновения
        notification.style.transition = `all ${animationDuration}ms ease-in`;
        notification.style.transform = notification.style.transform.replace('scale(1)', 'scale(0.8)');
        notification.style.opacity = '0';

        // Удаление из DOM
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }

            // Удаляем из массива активных
            const index = this.activeNotifications.indexOf(notification);
            if (index > -1) {
                this.activeNotifications.splice(index, 1);
            }
        }, animationDuration);
    }

    // Метод для совместимости с другими системами
    showNotification(message, type = 'info', duration = 3000) {
        return this.show(message, type, duration);
    }
}

// Создаем глобальный экземпляр
window.unifiedNotifications = new UnifiedNotifications();

// Глобальная функция для быстрого доступа
window.showNotification = function(message, type = 'info', duration = 3000) {
    return window.unifiedNotifications.show(message, type, duration);
};

// Экспорт для модульных систем
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedNotifications;
}
