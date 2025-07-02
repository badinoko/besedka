/**
 * 🕒 Универсальная система умных временных меток для проекта "Беседка"
 * Версия: 1.0 - Полная реализация согласно дорожной карте
 *
 * Функции:
 * - formatSmartTimestamp(dateString) - основная функция форматирования
 * - initSmartTimestamps() - инициализация на странице
 * - updateAllTimestamps() - обновление всех меток (автоматическое)
 */

class SmartTimestamps {
    constructor() {
        this.updateInterval = null;
        this.init();
    }

    /**
     * 🎯 ОСНОВНАЯ ФУНКЦИЯ ФОРМАТИРОВАНИЯ (из чата)
     * Преобразует дату в человекочитаемый формат
     */
    formatSmartTimestamp(dateString) {
        if (!dateString) return '';

        const targetDate = new Date(dateString);
        const now = new Date();
        const diffInMs = now - targetDate;
        const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
        const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
        const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

        // Менее 1 минуты назад
        if (diffInMinutes < 1) {
            return 'только что';
        }

        // Менее часа назад (1-59 минут)
        if (diffInMinutes < 60) {
            const minuteWord = diffInMinutes === 1 ? 'минуту' :
                              (diffInMinutes >= 2 && diffInMinutes <= 4) ? 'минуты' : 'минут';
            return `${diffInMinutes} ${minuteWord} назад`;
        }

        // Менее 24 часов назад (1-23 часа)
        if (diffInHours < 24) {
            const hourWord = diffInHours === 1 ? 'час' :
                           (diffInHours >= 2 && diffInHours <= 4) ? 'часа' : 'часов';
            return `${diffInHours} ${hourWord} назад`;
        }

        // 1 день назад
        if (diffInDays === 1) {
            return `вчера в ${targetDate.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`;
        }

        // 2 дня назад
        if (diffInDays === 2) {
            return `позавчера в ${targetDate.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`;
        }

        // До недели назад (3-7 дней)
        if (diffInDays <= 7) {
            const dayWord = diffInDays === 1 ? 'день' :
                           (diffInDays >= 2 && diffInDays <= 4) ? 'дня' : 'дней';
            return `${diffInDays} ${dayWord} назад`;
        }

        // До месяца назад (1-4 недели)
        if (diffInDays <= 30) {
            const weekCount = Math.floor(diffInDays / 7);
            const weekWord = weekCount === 1 ? 'неделю' :
                           (weekCount >= 2 && weekCount <= 4) ? 'недели' : 'недель';
            return `${weekCount} ${weekWord} назад`;
        }

        // Больше месяца - показываем точную дату
        return targetDate.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * 🔄 ПОЛУЧЕНИЕ ПОЛНОЙ ДАТЫ ДЛЯ TOOLTIP
     */
    getFullDateTime(dateString) {
        if (!dateString) return '';

        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            weekday: 'long',
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    /**
     * 🚀 ИНИЦИАЛИЗАЦИЯ УМНЫХ ВРЕМЕННЫХ МЕТОК НА СТРАНИЦЕ
     */
    init() {
        // Ждем загрузки DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.processAllTimestamps());
        } else {
            this.processAllTimestamps();
        }

        // Автоматическое обновление каждую минуту
        this.startAutoUpdate();
    }

    /**
     * 🔍 ОБРАБОТКА ВСЕХ ВРЕМЕННЫХ МЕТОК НА СТРАНИЦЕ
     */
    processAllTimestamps() {
        // 1. Карточки унифицированных списков (галерея, новости, гроулоги)
        const cardMetas = document.querySelectorAll('.card-meta small');
        cardMetas.forEach(meta => this.processCardMeta(meta));

        // 2. Сообщения чата
        const chatTimestamps = document.querySelectorAll('.message-timestamp');
        chatTimestamps.forEach(timestamp => this.processChatTimestamp(timestamp));

        // 3. Индикаторы редактирования в чате
        const editIndicators = document.querySelectorAll('.edit-indicator');
        editIndicators.forEach(indicator => this.processEditIndicator(indicator));

        // 4. Пользовательские элементы с data-атрибутами
        const customElements = document.querySelectorAll('[data-smart-timestamp]');
        customElements.forEach(element => this.processCustomElement(element));

        console.log('✅ Smart timestamps initialized for', {
            cardMetas: cardMetas.length,
            chatTimestamps: chatTimestamps.length,
            editIndicators: editIndicators.length,
            customElements: customElements.length
        });
    }

    /**
     * 📋 ОБРАБОТКА ВРЕМЕНИ В КАРТОЧКАХ (галерея, новости, гроулоги)
     */
    processCardMeta(metaElement) {
        const text = metaElement.textContent;

        // Ищем дату в формате "автор • дата"
        const dateMatch = text.match(/(.+?)\s*•\s*(.+)/);
        if (!dateMatch) return;

        const author = dateMatch[1].trim();
        const dateStr = dateMatch[2].trim();

        // Пытаемся распарсить дату
        const date = this.parseDateString(dateStr);
        if (!date) return;

        // Сохраняем оригинальную дату в data-атрибуте
        metaElement.setAttribute('data-original-date', date.toISOString());

        // Обновляем отображение
        const smartTime = this.formatSmartTimestamp(date.toISOString());
        const fullDateTime = this.getFullDateTime(date.toISOString());

        metaElement.innerHTML = `${author} • <span class="smart-timestamp" title="${fullDateTime}">${smartTime}</span>`;
    }

    /**
     * 💬 ОБРАБОТКА ВРЕМЕНИ В ЧАТЕ
     */
    processChatTimestamp(timestampElement) {
        // Если уже обработан, пропускаем
        if (timestampElement.hasAttribute('data-smart-processed')) return;

        // Ищем дату в ближайшем сообщении
        const messageElement = timestampElement.closest('[data-message-id]');
        if (!messageElement) return;

        // Пытаемся получить дату из атрибута или текущего содержимого
        let dateStr = timestampElement.getAttribute('data-created') ||
                      timestampElement.textContent;

        const date = this.parseDateString(dateStr);
        if (!date) return;

        // Сохраняем и обновляем
        timestampElement.setAttribute('data-original-date', date.toISOString());
        timestampElement.setAttribute('data-smart-processed', 'true');

        const smartTime = this.formatSmartTimestamp(date.toISOString());
        const fullDateTime = this.getFullDateTime(date.toISOString());

        timestampElement.textContent = smartTime;
        timestampElement.setAttribute('title', fullDateTime);
    }

    /**
     * ✏️ ОБРАБОТКА ИНДИКАТОРОВ РЕДАКТИРОВАНИЯ В ЧАТЕ
     */
    processEditIndicator(indicatorElement) {
        // Индикаторы редактирования уже используют formatSmartTimestamp в чате
        // Добавляем только tooltip с полной датой
        const timeMatch = indicatorElement.textContent.match(/(\d+\s+\w+\s+назад|вчера|позавчера|только что)/);
        if (timeMatch) {
            const dateStr = indicatorElement.getAttribute('data-edited-at');
            if (dateStr) {
                const fullDateTime = this.getFullDateTime(dateStr);
                indicatorElement.setAttribute('title', fullDateTime);
            }
        }
    }

    /**
     * 🎯 ОБРАБОТКА ПОЛЬЗОВАТЕЛЬСКИХ ЭЛЕМЕНТОВ
     */
    processCustomElement(element) {
        const dateStr = element.getAttribute('data-smart-timestamp');
        if (!dateStr) return;

        const smartTime = this.formatSmartTimestamp(dateStr);
        const fullDateTime = this.getFullDateTime(dateStr);

        element.textContent = smartTime;
        element.setAttribute('title', fullDateTime);
    }

    /**
     * 📅 УНИВЕРСАЛЬНЫЙ ПАРСЕР ДАТ
     */
    parseDateString(dateStr) {
        if (!dateStr || typeof dateStr !== 'string') return null;

        // Стандартный ISO формат
        let date = new Date(dateStr);
        if (!isNaN(date.getTime())) return date;

        // Русский формат "дд месяц гггг"
        const ruMonths = {
            'янв': 0, 'января': 0, 'февр': 1, 'февраля': 1, 'мар': 2, 'марта': 2,
            'апр': 3, 'апреля': 3, 'май': 4, 'мая': 4, 'июн': 5, 'июня': 5,
            'июл': 6, 'июля': 6, 'авг': 7, 'августа': 7, 'сент': 8, 'сентября': 8,
            'окт': 9, 'октября': 9, 'нояб': 10, 'ноября': 10, 'дек': 11, 'декабря': 11
        };

        const ruMatch = dateStr.match(/(\d{1,2})\s+(\w+)\s+(\d{4})/);
        if (ruMatch) {
            const day = parseInt(ruMatch[1]);
            const month = ruMonths[ruMatch[2].toLowerCase()];
            const year = parseInt(ruMatch[3]);

            if (month !== undefined) {
                return new Date(year, month, day);
            }
        }

        return null;
    }

    /**
     * ⚡ АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ ВРЕМЕННЫХ МЕТОК
     */
    startAutoUpdate() {
        // Обновляем каждую минуту
        this.updateInterval = setInterval(() => {
            this.updateAllTimestamps();
        }, 60000); // 60 секунд
    }

    /**
     * 🔄 ОБНОВЛЕНИЕ ВСЕХ ВРЕМЕННЫХ МЕТОК
     */
    updateAllTimestamps() {
        // Обновляем элементы с сохраненными датами
        const elementsToUpdate = document.querySelectorAll('[data-original-date]');

        elementsToUpdate.forEach(element => {
            const originalDate = element.getAttribute('data-original-date');
            if (!originalDate) return;

            const smartTime = this.formatSmartTimestamp(originalDate);
            const fullDateTime = this.getFullDateTime(originalDate);

            // Обновляем в зависимости от типа элемента
            if (element.classList.contains('smart-timestamp')) {
                element.textContent = smartTime;
                element.setAttribute('title', fullDateTime);
            } else if (element.classList.contains('message-timestamp')) {
                element.textContent = smartTime;
                element.setAttribute('title', fullDateTime);
            } else {
                // Для сложных элементов обновляем весь текст
                const currentText = element.textContent;
                const newText = currentText.replace(/\d+\s+\w+\s+назад|вчера|позавчера|только что|\d{2}\.\d{2}\.\d{4}/g, smartTime);
                element.textContent = newText;
                element.setAttribute('title', fullDateTime);
            }
        });

        console.log('🔄 Updated', elementsToUpdate.length, 'smart timestamps');
    }

    /**
     * 🧹 ОЧИСТКА РЕСУРСОВ
     */
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}

// Глобальная инициализация
window.SmartTimestamps = SmartTimestamps;

// Автоматический запуск
let globalSmartTimestamps = null;

document.addEventListener('DOMContentLoaded', function() {
    globalSmartTimestamps = new SmartTimestamps();
});

// Экспорт функций для использования в других скриптах
window.formatSmartTimestamp = function(dateString) {
    if (!globalSmartTimestamps) {
        globalSmartTimestamps = new SmartTimestamps();
    }
    return globalSmartTimestamps.formatSmartTimestamp(dateString);
};

window.initSmartTimestamps = function() {
    if (globalSmartTimestamps) {
        globalSmartTimestamps.processAllTimestamps();
    }
};

window.updateAllTimestamps = function() {
    if (globalSmartTimestamps) {
        globalSmartTimestamps.updateAllTimestamps();
    }
};
