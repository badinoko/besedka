/**
 * Telegram-подобные hover кнопки поверх Rocket.Chat iframe
 * Версия: 1.0
 * Согласно дорожной карте §2.5 ЭТАП 1: Базовые hover эффекты
 */

class TelegramLikeChat {
    constructor(iframeId) {
        this.iframe = document.getElementById(iframeId);
        this.iframeDoc = null;
        this.hoveredMessage = null;
        this.replyMode = null;
        this.overlayContainer = null;

        this.init();
    }

    init() {
        // Ждем загрузки iframe
        this.iframe.addEventListener('load', () => {
            this.setupIframeAccess();
            this.createOverlayContainer();
            this.initMessageHoverSystem();
        });
    }

    setupIframeAccess() {
        try {
            this.iframeDoc = this.iframe.contentDocument || this.iframe.contentWindow.document;
            console.log('✅ Telegram overlay: iframe доступен');
        } catch (e) {
            console.warn('⚠️ Telegram overlay: iframe недоступен (CORS), используем postMessage');
            this.setupPostMessageBridge();
        }
    }

    createOverlayContainer() {
        // Создаем overlay контейнер поверх iframe
        this.overlayContainer = document.createElement('div');
        this.overlayContainer.id = 'telegram-chat-overlay';
        this.overlayContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1000;
        `;

        // Размещаем overlay поверх iframe
        const iframeContainer = this.iframe.parentElement;
        iframeContainer.style.position = 'relative';
        iframeContainer.appendChild(this.overlayContainer);
    }

    initMessageHoverSystem() {
        if (!this.iframeDoc) return;

        // Отслеживаем добавление новых сообщений
        const messagesContainer = this.iframeDoc.querySelector('.rcx-message-list');
        if (messagesContainer) {
            this.observeMessages(messagesContainer);
        }

        // Обновляем overlay при скролле
        messagesContainer?.addEventListener('scroll', () => {
            this.updateOverlayPositions();
        });
    }

    observeMessages(container) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        this.processNewMessage(node);
                    }
                });
            });
        });

        observer.observe(container, { childList: true, subtree: true });

        // Обрабатываем существующие сообщения
        const existingMessages = container.querySelectorAll('[data-qa="message"]');
        existingMessages.forEach(msg => this.processNewMessage(msg));
    }

    processNewMessage(messageElement) {
        // Добавляем data-message-id для идентификации
        const messageId = this.generateMessageId(messageElement);
        messageElement.setAttribute('data-telegram-message-id', messageId);

        // Создаем hover кнопки для сообщения
        this.createHoverButtons(messageElement, messageId);

        // Добавляем обработчики hover
        messageElement.addEventListener('mouseenter', (e) => {
            this.showHoverButtons(messageId);
        });

        messageElement.addEventListener('mouseleave', (e) => {
            // Задержка для плавного исчезновения
            setTimeout(() => {
                if (!this.isHoveringButtons(messageId)) {
                    this.hideHoverButtons(messageId);
                }
            }, 200);
        });
    }

    createHoverButtons(messageElement, messageId) {
        // Получаем позицию сообщения относительно iframe
        const rect = this.getMessageRect(messageElement);

        // Создаем контейнер для кнопок
        const buttonsContainer = document.createElement('div');
        buttonsContainer.id = `hover-buttons-${messageId}`;
        buttonsContainer.className = 'telegram-hover-buttons';
        buttonsContainer.style.cssText = `
            position: absolute;
            top: ${rect.top}px;
            right: 10px;
            display: flex;
            gap: 8px;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: auto;
            z-index: 1001;
        `;

        // Кнопка "Ответить"
        const replyBtn = this.createButton('reply', '↩️', () => {
            this.activateReplyMode(messageId, messageElement);
        });

        // Кнопка реакций
        const reactionsBtn = this.createButton('reactions', '😊', () => {
            this.showReactionMenu(messageId, messageElement);
        });

        buttonsContainer.appendChild(replyBtn);
        buttonsContainer.appendChild(reactionsBtn);
        this.overlayContainer.appendChild(buttonsContainer);

        // Обработчики для кнопок
        buttonsContainer.addEventListener('mouseenter', () => {
            this.hoveredMessage = messageId;
        });

        buttonsContainer.addEventListener('mouseleave', () => {
            this.hoveredMessage = null;
            this.hideHoverButtons(messageId);
        });
    }

    createButton(type, icon, onClick) {
        const button = document.createElement('button');
        button.className = `telegram-hover-btn telegram-${type}-btn`;
        button.innerHTML = icon;
        button.style.cssText = `
            width: 32px;
            height: 32px;
            border: none;
            border-radius: 50%;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            transition: all 0.2s ease;
        `;

        button.addEventListener('mouseenter', () => {
            button.style.background = 'rgba(0, 0, 0, 0.9)';
            button.style.transform = 'scale(1.1)';
        });

        button.addEventListener('mouseleave', () => {
            button.style.background = 'rgba(0, 0, 0, 0.7)';
            button.style.transform = 'scale(1)';
        });

        button.addEventListener('click', onClick);

        return button;
    }

    showHoverButtons(messageId) {
        const buttons = document.getElementById(`hover-buttons-${messageId}`);
        if (buttons) {
            buttons.style.opacity = '1';
        }
    }

    hideHoverButtons(messageId) {
        const buttons = document.getElementById(`hover-buttons-${messageId}`);
        if (buttons) {
            buttons.style.opacity = '0';
        }
    }

    isHoveringButtons(messageId) {
        return this.hoveredMessage === messageId;
    }

    activateReplyMode(messageId, messageElement) {
        // Режим ответа согласно дорожной карте §2.5 ЭТАП 2
        console.log('🔄 Активация режима ответа для сообщения:', messageId);

        // Показываем индикатор режима ответа
        this.showReplyIndicator(messageElement);

        // Уведомляем родительское окно о режиме ответа
        window.parent.postMessage({
            type: 'telegram-reply-mode',
            messageId: messageId,
            messageText: this.getMessageText(messageElement),
            messageAuthor: this.getMessageAuthor(messageElement)
        }, '*');
    }

    showReactionMenu(messageId, messageElement) {
        // Система реакций согласно дорожной карте §2.5 ЭТАП 3
        console.log('😊 Показать меню реакций для сообщения:', messageId);

        // Создаем быстрое меню реакций
        const reactionsMenu = this.createReactionsMenu(messageId);
        this.overlayContainer.appendChild(reactionsMenu);

        // Позиционируем относительно кнопки
        const rect = this.getMessageRect(messageElement);
        reactionsMenu.style.top = `${rect.top - 50}px`;
        reactionsMenu.style.right = '10px';
    }

    createReactionsMenu(messageId) {
        const menu = document.createElement('div');
        menu.className = 'telegram-reactions-menu';
        menu.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            border-radius: 25px;
            padding: 8px;
            display: flex;
            gap: 8px;
            opacity: 0;
            animation: fadeIn 0.3s ease forwards;
            pointer-events: auto;
            z-index: 1002;
        `;

        // Быстрые реакции как в Telegram
        const quickReactions = ['❤️', '👍', '👎', '😂', '😮', '😢'];

        quickReactions.forEach(emoji => {
            const reactionBtn = document.createElement('button');
            reactionBtn.textContent = emoji;
            reactionBtn.style.cssText = `
                width: 32px;
                height: 32px;
                border: none;
                border-radius: 50%;
                background: transparent;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s ease;
            `;

            reactionBtn.addEventListener('mouseenter', () => {
                reactionBtn.style.transform = 'scale(1.3)';
            });

            reactionBtn.addEventListener('mouseleave', () => {
                reactionBtn.style.transform = 'scale(1)';
            });

            reactionBtn.addEventListener('click', () => {
                this.addReaction(messageId, emoji);
                menu.remove();
            });

            menu.appendChild(reactionBtn);
        });

        // Автоудаление через 3 секунды
        setTimeout(() => {
            if (menu.parentElement) {
                menu.remove();
            }
        }, 3000);

        return menu;
    }

    addReaction(messageId, emoji) {
        console.log('👍 Добавление реакции:', emoji, 'к сообщению:', messageId);

        // Отправляем реакцию через postMessage
        window.parent.postMessage({
            type: 'telegram-add-reaction',
            messageId: messageId,
            emoji: emoji
        }, '*');
    }

    showReplyIndicator(messageElement) {
        // Подсветка сообщения для ответа
        messageElement.style.cssText += `
            background-color: rgba(0, 123, 255, 0.1) !important;
            border-left: 3px solid #007bff !important;
            transition: all 0.3s ease;
        `;

        // Убираем подсветку через 3 секунды
        setTimeout(() => {
            messageElement.style.background = '';
            messageElement.style.borderLeft = '';
        }, 3000);
    }

    getMessageRect(messageElement) {
        const iframeRect = this.iframe.getBoundingClientRect();
        const messageRect = messageElement.getBoundingClientRect();

        return {
            top: messageRect.top - iframeRect.top,
            left: messageRect.left - iframeRect.left,
            width: messageRect.width,
            height: messageRect.height
        };
    }

    getMessageText(messageElement) {
        return messageElement.querySelector('.rcx-message-body')?.textContent || '';
    }

    getMessageAuthor(messageElement) {
        return messageElement.querySelector('.rcx-message-header')?.textContent || '';
    }

    generateMessageId(messageElement) {
        // Генерируем уникальный ID для сообщения
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    updateOverlayPositions() {
        // Обновляем позиции overlay элементов при скролле
        const hoverButtons = this.overlayContainer.querySelectorAll('.telegram-hover-buttons');
        hoverButtons.forEach(buttons => {
            const messageId = buttons.id.replace('hover-buttons-', '');
            const messageElement = this.iframeDoc?.querySelector(`[data-telegram-message-id="${messageId}"]`);

            if (messageElement) {
                const rect = this.getMessageRect(messageElement);
                buttons.style.top = `${rect.top}px`;
            }
        });
    }

    setupPostMessageBridge() {
        // Fallback для случаев когда iframe недоступен из-за CORS
        window.addEventListener('message', (event) => {
            if (event.data.type === 'rocketchat-message-hover') {
                this.handleExternalHover(event.data);
            }
        });
    }

    handleExternalHover(data) {
        // Обработка hover сообщений через postMessage
        console.log('📨 Внешний hover сообщения:', data);
    }
}

// CSS анимации для плавного появления
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .telegram-hover-buttons {
        pointer-events: auto;
    }

    .telegram-reactions-menu {
        pointer-events: auto;
    }
`;
document.head.appendChild(style);

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Ждем появления iframe
    const checkIframe = setInterval(() => {
        const iframe = document.getElementById('rocketchat-iframe');
        if (iframe) {
            clearInterval(checkIframe);
            console.log('🚀 Инициализация Telegram-подобного чата');
            new TelegramLikeChat('rocketchat-iframe');
        }
    }, 500);
});
