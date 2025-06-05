/* Основной JavaScript файл проекта "Беседка" */

/**
 * Глобальная функция для отображения toast уведомлений
 * @param {string} message - Текст сообщения
 * @param {string} type - Тип: success, error, warning, info
 * @param {number} duration - Длительность в миллисекундах (по умолчанию 4000)
 */
function showToast(message, type = 'success', duration = 4000) {
    const container = document.getElementById('global-toast-container');
    if (!container) {
        console.error('Toast container not found');
        return;
    }

    // Создаем уникальный ID для toast
    const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);

    // Определяем иконку и цвет для разных типов
    const typeConfig = {
        success: { icon: 'fas fa-check-circle', bgClass: 'bg-success' },
        error: { icon: 'fas fa-exclamation-circle', bgClass: 'bg-danger' },
        warning: { icon: 'fas fa-exclamation-triangle', bgClass: 'bg-warning' },
        info: { icon: 'fas fa-info-circle', bgClass: 'bg-info' }
    };

    const config = typeConfig[type] || typeConfig.info;

    // HTML для toast
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${config.bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="${config.icon} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    // Добавляем toast в контейнер
    container.insertAdjacentHTML('beforeend', toastHTML);

    // Показываем toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        delay: duration
    });

    toast.show();

    // Удаляем toast из DOM после скрытия
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🌱 Беседка загружена!');

    // Инициализация всех компонентов
    initializeTooltips();
    initializeAlerts();
    initializeFormValidation();
    initializeLoadingButtons();
    // initializeNotifications(); // Временно отключено для проверки бага в чате

    // Утилиты
    setupCSRFProtection();

    console.log('✅ Все компоненты инициализированы');
});

/**
 * Инициализация всплывающих подсказок Bootstrap
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Автоматическое скрытие алертов
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        // Автоматически скрывать алерты через 5 секунд
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
}

/**
 * Улучшенная валидация форм
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');

    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();

                // Найти первое невалидное поле и сфокусироваться на нем
                const firstInvalidField = form.querySelector(':invalid');
                if (firstInvalidField) {
                    firstInvalidField.focus();
                    firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }

            form.classList.add('was-validated');
        });

        // Валидация в реальном времени
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                if (form.classList.contains('was-validated')) {
                    input.classList.toggle('is-valid', input.checkValidity());
                    input.classList.toggle('is-invalid', !input.checkValidity());
                }
            });
        });
    });
}

/**
 * Кнопки с индикатором загрузки
 */
function initializeLoadingButtons() {
    const loadingButtons = document.querySelectorAll('.btn-loading');

    loadingButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            if (button.type === 'submit') {
                const form = button.closest('form');
                if (form && form.checkValidity()) {
                    showButtonLoading(button);
                }
            } else {
                showButtonLoading(button);
            }
        });
    });
}

/**
 * Показать состояние загрузки кнопки
 * @param {HTMLElement} button
 */
function showButtonLoading(button) {
    const originalText = button.innerHTML;
    const loadingText = button.getAttribute('data-loading-text') || 'Загрузка...';

    button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        ${loadingText}
    `;
    button.disabled = true;

    // Восстановить кнопку через 30 секунд (защита от зависания)
    setTimeout(function() {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 30000);
}

/**
 * Система уведомлений
 */
function initializeNotifications() {
    // Обновление счетчиков уведомлений
    updateNotificationBadges();

    // Периодическое обновление (каждые 30 секунд)
    setInterval(updateNotificationBadges, 30000);

    // Обработка кликов по уведомлениям
    const notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(function(item) {
        item.addEventListener('click', function() {
            markNotificationAsRead(item);
        });
    });
}

/**
 * Обновление счетчиков уведомлений
 */
function updateNotificationBadges() {
    // Простая реализация - можно расширить AJAX-запросами
    const unreadNotifications = document.querySelectorAll('.notification-item.unread');
    const badges = document.querySelectorAll('.notification-badge');

    const count = unreadNotifications.length;
    badges.forEach(function(badge) {
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    });
}

/**
 * Отметить уведомление как прочитанное
 * @param {HTMLElement} notificationItem
 */
function markNotificationAsRead(notificationItem) {
    if (notificationItem.classList.contains('unread')) {
        notificationItem.classList.remove('unread');
        notificationItem.classList.add('read');
        updateNotificationBadges();

        // Здесь можно добавить AJAX-запрос для обновления на сервере
        const notificationId = notificationItem.getAttribute('data-notification-id');
        if (notificationId) {
            markNotificationReadOnServer(notificationId);
        }
    }
}

/**
 * Отправка запроса на сервер для отметки уведомления как прочитанное
 * @param {string} notificationId
 */
function markNotificationReadOnServer(notificationId) {
    fetch(`/api/notifications/${notificationId}/mark-read/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    }).catch(function(error) {
        console.error('Ошибка при отметке уведомления как прочитанное:', error);
    });
}

/**
 * Настройка CSRF-защиты для AJAX-запросов
 */
function setupCSRFProtection() {
    // Получаем CSRF токен
    const csrfToken = getCSRFToken();

    // Настраиваем для всех AJAX-запросов
    if (window.jQuery) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                }
            }
        });
    }
}

/**
 * Получение CSRF токена
 * @returns {string}
 */
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1]; // Добавлена безопасная навигация

    return cookieValue || ''; // Возвращаем пустую строку, если токен не найден
}

/**
 * Проверка безопасных HTTP методов для CSRF
 * @param {string} method
 * @returns {boolean}
 */
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

/**
 * Утилиты для работы с формами
 */
const FormUtils = {
    /**
     * Очистка формы
     * @param {HTMLFormElement} form
     */
    clearForm: function(form) {
        form.reset();
        form.classList.remove('was-validated');

        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.classList.remove('is-valid', 'is-invalid');
        });
    },

    /**
     * Сериализация данных формы в объект
     * @param {HTMLFormElement} form
     * @returns {object}
     */
    serializeForm: function(form) {
        const formData = new FormData(form);
        const object = {};
        formData.forEach((value, key) => {
            if (object[key]) {
                if (!Array.isArray(object[key])) {
                    object[key] = [object[key]];
                }
                object[key].push(value);
            } else {
                object[key] = value;
            }
        });
        return object;
    }
};

/**
 * Утилиты для работы с таблицами
 */
const TableUtils = {
    /**
     * Инициализация динамических таблиц (например, с DataTables)
     * @param {string} tableSelector
     * @param {object} options
     */
    initializeDynamicTable: function(tableSelector, options = {}) {
        // Пример с jQuery DataTables (если используется)
        if (window.jQuery && $.fn.DataTable) {
            $(tableSelector).DataTable(options);
        }
    }
};

// Экспорт утилит (если нужно)
window.AppUtils = {
    FormUtils,
    TableUtils,
    showButtonLoading,
    markNotificationAsRead, // Экспортируем, если используется извне
    getCSRFToken
};
