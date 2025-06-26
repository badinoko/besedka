/**
 * Клиент для WebSocket чата "Беседка"
 */
class ChatClient {
    constructor(chatType = 'general', roomId = null) {
        this.chatType = chatType;
        this.roomId = roomId;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isTyping = false;
        this.typingTimer = null;
        this.userReactedMessages = new Set(); // track messages reacted by current user to block double reaction
        this.replyToId = null; // <-- ID сообщения, на которое отвечаем
        this.replyToSnippet = null;

        this.init();
    }

    init() {
        this.connect();
        this.setupEventListeners();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        let wsUrl;

        // Определяем URL в зависимости от типа чата
        switch (this.chatType) {
            case 'general':
                wsUrl = `${protocol}//${window.location.host}/ws/chat/general/`;
                break;
            case 'private':
                wsUrl = `${protocol}//${window.location.host}/ws/chat/private/${this.roomId}/`;
                break;
            case 'discussion':
                wsUrl = `${protocol}//${window.location.host}/ws/chat/discussion/${this.roomId}/`;
                break;
            case 'vip':
                wsUrl = `${protocol}//${window.location.host}/ws/chat/vip/`;
                break;
            default:
                console.error('Unknown chat type:', this.chatType);
                return;
        }

        console.log('Connecting to:', wsUrl);
        this.updateConnectionStatus('connecting');

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = (event) => {
            console.log('✅ WebSocket connected');
            this.updateConnectionStatus('connected');
            this.reconnectAttempts = 0;
            window.showNotification('Подключено к чату', 'success');

            // Загружаем историю сообщений и онлайн пользователей
            this.fetchMessages();
            this.fetchOnlineUsers();
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.socket.onclose = (event) => {
            console.log('❌ WebSocket disconnected:', event.code, event.reason);
            this.updateConnectionStatus('disconnected');

            if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts++;
                    console.log(`🔄 Reconnection attempt ${this.reconnectAttempts}`);
                    this.connect();
                }, this.reconnectDelay * this.reconnectAttempts);
            } else {
                window.showNotification('Соединение потеряно', 'error');
            }
        };

        this.socket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.updateConnectionStatus('disconnected');
            window.showNotification('Ошибка подключения', 'error');
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'new_message':
                this.displayMessage(data.message);
                break;
            case 'messages_history':
                this.displayMessages(data.messages);
                break;
            case 'typing':
                this.handleTypingIndicator(data);
                break;
            case 'online_users':
                this.updateOnlineUsers(data.users, data.count);
                break;
            case 'user_joined':
                this.handleUserJoined(data.user);
                break;
            case 'user_left':
                this.handleUserLeft(data.user);
                break;
            case 'reaction_update':
                this.applyReactionUpdate(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    displayMessage(message) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        // Если это первое сообщение, очистим placeholder
        const placeholder = messagesContainer.querySelector('.text-center');
        if (placeholder) {
            messagesContainer.innerHTML = '';
        }

        const messageElement = this.createMessageElement(message);
        messagesContainer.appendChild(messageElement);

        // Прокручиваем к последнему сообщению
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    displayMessages(messages) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        // Очищаем контейнер
        messagesContainer.innerHTML = '';

        if (messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-comments fa-3x mb-3 opacity-50"></i>
                    <p>Пока нет сообщений. Начните общение!</p>
                </div>
            `;
            return;
        }

        // Добавляем сообщения (они приходят в обратном порядке)
        messages.reverse().forEach(message => {
            const messageElement = this.createMessageElement(message);
            messagesContainer.appendChild(messageElement);
        });

        // Прокручиваем к последнему сообщению
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        if (message.is_own) {
            messageDiv.classList.add('own-message');
        } else {
            messageDiv.classList.add('other-message');
        }

        // Базовые data-атрибуты для систем ответов и реакций
        messageDiv.setAttribute('data-message-id', message.id);
        messageDiv.setAttribute('data-author', message.author_name);
        if (message.author_role) {
            messageDiv.setAttribute('data-author-role', message.author_role);
        }

        // Время в формате HH:MM, локализовано под RU
        const timeString = new Date(message.created).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });

        // Защита от отсутствующих полей в полезной нагрузке
        const roleIcon = message.author_role_icon || '👤';
        const likes = typeof message.likes_count !== 'undefined' ? message.likes_count : 0;
        const dislikes = typeof message.dislikes_count !== 'undefined' ? message.dislikes_count : 0;

        // Если сообщение является ответом – готовим цитату
        let quoteSection = '';
        let quoteNavButton = '';
        if (message.reply_to) {
            const replyAuthor = this.escapeHtml(message.reply_to.author_name || '');
            const replySnippet = this.escapeHtml(message.reply_to.content_snippet || '');
            quoteSection = `
                <div class="quoted-message">
                    <div class="quote-author">@${replyAuthor}</div>
                    <div class="quote-text">${replySnippet}</div>
                </div>`;
            quoteNavButton = `
                <button class="quote-nav-btn" data-target-message="${message.reply_to.id}" title="Перейти к исходному сообщению">
                    <i class="fas fa-arrow-up"></i>
                </button>`;
            messageDiv.classList.add('reply-message');
        }

        if (message.is_reply_to_me) {
            messageDiv.classList.add('has-reply-to-me');
        }

        // Build reaction HTML snippet for header (inline)
        const replyControl = `
            <button class="reply-set-btn" data-message-id="${message.id}" data-author="${this.escapeHtml(message.author_name)}" title="Ответить">
                <i class="fas fa-reply"></i>
            </button>`;

        const reactionsInHeader = `
            <div class="message-reactions">
                ${replyControl}
                <button class="reaction-btn like-btn" data-message-id="${message.id}" data-action="like" title="Нравится">
                    <i class="fas fa-thumbs-up"></i>
                    <div class="reaction-count">${likes}</div>
                </button>
                <button class="reaction-btn dislike-btn" data-message-id="${message.id}" data-action="dislike" title="Не нравится">
                    <i class="fas fa-thumbs-down"></i>
                    <div class="reaction-count">${dislikes}</div>
                </button>
            </div>`;

        // Основная разметка единого шаблона сообщения
        messageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-header">
                    <div class="message-meta">
                        <span class="message-author"><span class="role-icon">${roleIcon}</span>${this.escapeHtml(message.author_name)}</span>
                        <span class="message-time">${timeString}</span>
                    </div>
                    ${reactionsInHeader}
                </div>
                <div class="message-content-area">
                    ${quoteSection}
                    <div class="message-content">${this.escapeHtml(message.content)}</div>
                </div>
                ${quoteNavButton}
            </div>`;

        return messageDiv;
    }

    updateOnlineUsers(users, count) {
        // Обновляем счетчик в шапке
        const onlineCountElement = document.getElementById('online-count');
        if (onlineCountElement) {
            onlineCountElement.textContent = count || users.length;
        }

        // Обновляем badge счетчик в боковой панели
        const onlineCountBadge = document.getElementById('online-count-badge');
        if (onlineCountBadge) {
            onlineCountBadge.textContent = count || users.length;
        }

        // Обновляем список пользователей
        const usersList = document.getElementById('online-users-list');
        if (!usersList) return;

        if (users.length === 0) {
            usersList.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="fas fa-user-slash mb-2"></i>
                    <p class="small mb-0">Нет пользователей онлайн</p>
                </div>
            `;
            return;
        }

        usersList.innerHTML = '';
        users.forEach(user => {
            const userElement = document.createElement('div');
            userElement.className = 'online-user';
            userElement.innerHTML = `
                <div class="status-dot"></div>
                <span class="user-name">
                    <span class="role-icon">${user.role_icon || '👤'}</span>
                    ${this.escapeHtml(user.display_name || user.username)}
                </span>
            `;
            usersList.appendChild(userElement);
        });
    }

    handleUserJoined(user) {
        console.log(`👋 ${user.username} присоединился к чату`);
        // Запрашиваем обновленный список пользователей
        this.fetchOnlineUsers();
    }

    handleUserLeft(user) {
        console.log(`👋 ${user.username} покинул чат`);
        // Запрашиваем обновленный список пользователей
        this.fetchOnlineUsers();
    }

    sendMessage() {
        const input = document.getElementById('message-input');
        if (!input) return;

        const message = input.value.trim();

        if (message && this.socket && this.socket.readyState === WebSocket.OPEN) {
            const payload = {
                type: 'message',
                message: message
            };
            if (this.replyToId) {
                payload.reply_to_id = this.replyToId;
            }
            this.socket.send(JSON.stringify(payload));

            input.value = '';
            this.stopTyping();

            // Сбрасываем режим ответа
            this.replyToId = null;
            this.hideReplyIndicator();
        } else if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            window.showNotification('Нет соединения с сервером', 'error');
        }
    }

    fetchMessages(page = 1) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'fetch_messages',
                page: page
            }));
        }
    }

    fetchOnlineUsers() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'fetch_online_users'
            }));
        }
    }

    startTyping() {
        if (!this.isTyping && this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.isTyping = true;
            this.socket.send(JSON.stringify({
                type: 'typing',
                is_typing: true
            }));
        }

        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(() => {
            this.stopTyping();
        }, 3000);
    }

    stopTyping() {
        if (this.isTyping && this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.isTyping = false;
            this.socket.send(JSON.stringify({
                type: 'typing',
                is_typing: false
            }));
        }
        clearTimeout(this.typingTimer);
    }

    handleTypingIndicator(data) {
        const typingIndicator = document.getElementById('typing-indicator');
        if (!typingIndicator) return;

        if (data.is_typing) {
            typingIndicator.innerHTML = `
                <i class="fas fa-ellipsis-h text-primary me-2"></i>
                <span>${this.escapeHtml(data.user)} печатает...</span>
            `;
        } else {
            typingIndicator.innerHTML = '';
        }
    }

    setupEventListeners() {
        // Обработчик для кнопки отправки
        const sendButton = document.getElementById('send-button');
        if (sendButton) {
            sendButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        // Обработчик для поля ввода (Enter для отправки)
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Индикатор печати
            messageInput.addEventListener('input', () => {
                if (messageInput.value.trim()) {
                    this.startTyping();
                } else {
                    this.stopTyping();
                }
            });
        }

        // Делегирование кликов на кнопки реакций и ответов
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.addEventListener('click', (e) => {
                const btn = e.target.closest('.reaction-btn');
                if (btn && !btn.classList.contains('disabled')) {
                    const messageId = btn.getAttribute('data-message-id');
                    const action = btn.getAttribute('data-action');
                    // Предотвращаем повторную реакцию
                    if (this.userReactedMessages.has(messageId)) return;

                    // Отправляем на сервер
                    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                        this.socket.send(JSON.stringify({
                            type: 'reaction',
                            reaction: action,
                            message_id: messageId
                        }));
                        this.userReactedMessages.add(messageId);
                        // Помечаем нажатую кнопку активной (цвет) и блокируем повторный клик
                        btn.classList.add('active');
                        btn.classList.add('disabled');

                        // Делаем противоположную кнопку некликабельной (disabled), но не active
                        const otherBtnSelector = action === 'like' ? '.dislike-btn' : '.like-btn';
                        const otherBtn = btn.parentElement.parentElement.querySelector(otherBtnSelector);
                        if (otherBtn) {
                            otherBtn.classList.add('disabled');
                        }
                    }
                }

                // Обработка клика по кнопке перехода к цитате
                const quoteBtn = e.target.closest('.quote-nav-btn');
                if (quoteBtn) {
                    const targetId = quoteBtn.getAttribute('data-target-message');
                    const targetEl = document.querySelector(`.message[data-message-id="${targetId}"]`);
                    if (targetEl) {
                        targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        targetEl.classList.add('reply-highlighted');
                        setTimeout(() => targetEl.classList.remove('reply-highlighted'), 2000);
                    }
                }

                // Обработка кнопки "Ответить"
                const replyBtn = e.target.closest('.reply-set-btn');
                if (replyBtn) {
                    const targetId = replyBtn.getAttribute('data-message-id');
                    const author = replyBtn.getAttribute('data-author');
                    this.replyToId = targetId;
                    this.replyToSnippet = author;
                    this.showReplyIndicator(author); // Отображаем индикатор
                    const input = document.getElementById('message-input');
                    if (input) input.focus();
                }
            });
        }

        // Снятие красной рамки при клике на сообщение, адресованное мне
        const messagesArea = document.getElementById('chat-messages');
        if (messagesArea) {
            messagesArea.addEventListener('click', (e) => {
                const msgEl = e.target.closest('.message.has-reply-to-me');
                if (msgEl) {
                    msgEl.classList.remove('has-reply-to-me');
                }
            });
        }

        // Дополнительные обработчики событий могут быть добавлены здесь
        // Например, для обработки видимости страницы
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.socket && this.socket.readyState === WebSocket.OPEN) {
                // Обновляем данные при возврате на страницу
                this.fetchOnlineUsers();
            }
        });
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;

        // Убираем все классы статуса
        statusElement.classList.remove('connected', 'connecting', 'disconnected');

        // Добавляем нужный класс и обновляем текст
        switch (status) {
            case 'connected':
                statusElement.classList.add('connected');
                statusElement.innerHTML = '<i class="fas fa-circle me-1"></i> Подключено';
                break;
            case 'connecting':
                statusElement.classList.add('connecting');
                statusElement.innerHTML = '<i class="fas fa-circle me-1"></i> Подключение...';
                break;
            case 'disconnected':
                statusElement.classList.add('disconnected');
                statusElement.innerHTML = '<i class="fas fa-circle me-1"></i> Отключено';
                break;
        }
    }

    // Удалено: используется глобальная система уведомлений window.showNotification

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'User disconnect');
            this.socket = null;
        }
    }

    /**
     * Применить обновление счетчиков реакций, пришедшее с сервера
     */
    applyReactionUpdate({ message_id, likes, dislikes }) {
        const messageEl = document.querySelector(`.message[data-message-id="${message_id}"]`);
        if (!messageEl) return;
        const likeCountEl = messageEl.querySelector('.like-btn .reaction-count');
        const dislikeCountEl = messageEl.querySelector('.dislike-btn .reaction-count');
        if (likeCountEl) likeCountEl.textContent = likes;
        if (dislikeCountEl) dislikeCountEl.textContent = dislikes;
    }

    showReplyIndicator(author) {
        const indicator = document.getElementById('reply-indicator-area');
        if (!indicator) return;
        indicator.innerHTML = `Ответ @${this.escapeHtml(author)}  <button id="cancel-reply-btn" class="btn btn-sm btn-link text-light">Отмена</button>`;
        indicator.style.display = 'block';
        const cancelBtn = document.getElementById('cancel-reply-btn');
        if (cancelBtn) {
            cancelBtn.onclick = () => {
                this.replyToId = null;
                this.hideReplyIndicator();
            };
        }
    }

    hideReplyIndicator() {
        const indicator = document.getElementById('reply-indicator-area');
        if (indicator) {
            indicator.style.display = 'none';
            indicator.innerHTML = '';
        }
    }
}

// Глобальная функция для инициализации чата
function initChat(chatType = 'general', roomId = null) {
    return new ChatClient(chatType, roomId);
}

// Экспорт для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChatClient, initChat };
}
