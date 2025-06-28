/**
 * Клиент для WebSocket чата "Беседка" v5.0
 * ПОЛНОСТЬЮ КАСТОМНАЯ РЕАЛИЗАЦИЯ
 */
class ChatClient {
    constructor(roomName, currentUser) {
        this.roomName = roomName;
        this.currentUser = currentUser;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isTyping = false;
        this.typingTimer = null;
        this.userReactedMessages = new Set();
        this.replyToId = null;
        this.replyToSnippet = null;
    }

    init() {
        this.connect();
        this.setupEventListeners();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.roomName}/`;

        console.log('Connecting to:', wsUrl);
        this.updateConnectionStatus('connecting');

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = (event) => {
            console.log('✅ WebSocket connected');
            this.updateConnectionStatus('connected');
            this.reconnectAttempts = 0;

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
            }
        };

        this.socket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.updateConnectionStatus('disconnected');
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'new_message':
                this.displayMessage(data.message);
                this.updateMessageCount();
                break;
            case 'messages_history':
                this.displayMessages(data.messages);
                this.updateMessageCount(data.messages.length);
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
            case 'message_deleted':
                this.handleMessageDeleted(data);
                break;
            case 'message_edited':
                this.handleMessageEdited(data);
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

        // Прокручиваем к последнему сообщению с задержкой
        setTimeout(() => {
            this.scrollToBottom();
        }, 100);
    }

    displayMessages(messages) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        if (messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-comments fa-3x mb-3 opacity-50"></i>
                    <p>Пока нет сообщений. Начните общение!</p>
                </div>
            `;
            return;
        }

        // ИСПРАВЛЕНО: Всегда очищаем контейнер перед загрузкой истории сообщений
        // Это устраняет проблему с остающимися placeholder'ами и дублированием
        messagesContainer.innerHTML = '';

        // Добавляем сообщения в правильном порядке (backend уже отправляет в правильном порядке)
        messages.forEach(message => {
            const messageElement = this.createMessageElement(message);
            messagesContainer.appendChild(messageElement);
        });

        // Прокручиваем к последнему сообщению с задержкой для истории
        setTimeout(() => {
            this.scrollToBottom();
        }, 200);
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

        // Время в формате HH:MM
        const timeString = new Date(message.created).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });

        // Защита от отсутствующих полей
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

        // Кнопки реакций и ответов
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

        // Основная разметка сообщения
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
        // Обновляем счетчик в панели
        const onlineCountElement = document.getElementById('online-count');
        if (onlineCountElement) {
            onlineCountElement.textContent = count || users.length;
        }

        // Обновляем список пользователей
        const usersList = document.getElementById('users-list');
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

    updateMessageCount(count = null) {
        const messagesCountElement = document.getElementById('messages-count');
        if (messagesCountElement) {
            if (count !== null) {
                messagesCountElement.textContent = count;
            } else {
                // Увеличиваем счетчик на 1 для нового сообщения
                const currentCount = parseInt(messagesCountElement.textContent) || 0;
                messagesCountElement.textContent = currentCount + 1;
            }
        }
    }

    handleUserJoined(user) {
        console.log(`👋 ${user.username} присоединился к чату`);
        this.fetchOnlineUsers();
    }

    handleUserLeft(user) {
        console.log(`👋 ${user.username} покинул чат`);
        this.fetchOnlineUsers();
    }

    sendMessage() {
        const input = document.getElementById('chat-message-input');
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
            console.error('Нет соединения с сервером');
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
        const sendButton = document.getElementById('chat-message-submit');
        if (sendButton) {
            sendButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        // Обработчик для поля ввода (Enter для отправки)
        const messageInput = document.getElementById('chat-message-input');
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

        // Обработчик для кнопки отмены ответа
        const cancelReplyBtn = document.getElementById('cancel-reply-btn');
        if (cancelReplyBtn) {
            cancelReplyBtn.addEventListener('click', () => {
                this.replyToId = null;
                this.hideReplyIndicator();
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

                    if (this.userReactedMessages.has(messageId)) return;

                    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                        this.socket.send(JSON.stringify({
                            type: 'reaction',
                            reaction: action,
                            message_id: messageId
                        }));
                        this.userReactedMessages.add(messageId);
                        btn.classList.add('active');
                        btn.classList.add('disabled');

                        const otherBtnSelector = action === 'like' ? '.dislike-btn' : '.like-btn';
                        const otherBtn = btn.closest('.message-reactions').querySelector(otherBtnSelector);
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
                    this.showReplyIndicator(author);
                    const input = document.getElementById('chat-message-input');
                    if (input) input.focus();
                }
            });

            // Снятие подсветки при клике на сообщение
            messagesContainer.addEventListener('click', (e) => {
                const msgEl = e.target.closest('.message.has-reply-to-me');
                if (msgEl) {
                    msgEl.classList.remove('has-reply-to-me');
                }
            });
        }

        // Обновление данных при возврате на страницу
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.fetchOnlineUsers();
            }
        });
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;

        statusElement.className = 'connection-status-nav';
        const icon = statusElement.querySelector('i');
        if (!icon) return;

        switch(status) {
            case 'connected':
                statusElement.classList.add('status-connected');
                icon.className = 'fas fa-unlock';
                break;
            case 'connecting':
                statusElement.classList.add('status-connecting');
                icon.className = 'fas fa-lock';
                break;
            case 'disconnected':
                statusElement.classList.add('status-disconnected');
                icon.className = 'fas fa-lock';
                break;
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            // Используем requestAnimationFrame для надежной прокрутки
            requestAnimationFrame(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            });
        }
    }

    showReplyIndicator(author) {
        const replyIndicator = document.getElementById('reply-indicator-area');
        const replyToText = document.getElementById('reply-to-text');

        if (replyIndicator && replyToText) {
            replyToText.innerHTML = `<i class="fas fa-reply me-2"></i>В ответ на: <strong>${this.escapeHtml(author)}</strong>`;
            replyIndicator.style.display = 'block';
        }
    }

    hideReplyIndicator() {
        const replyIndicator = document.getElementById('reply-indicator-area');
        if (replyIndicator) {
            replyIndicator.style.display = 'none';
        }
    }

    applyReactionUpdate({ message_id, likes, dislikes }) {
        const messageElement = document.querySelector(`.message[data-message-id="${message_id}"]`);
        if (messageElement) {
            const likeCount = messageElement.querySelector('.like-btn .reaction-count');
            const dislikeCount = messageElement.querySelector('.dislike-btn .reaction-count');

            if (likeCount) likeCount.textContent = likes;
            if (dislikeCount) dislikeCount.textContent = dislikes;
        }
    }

    handleMessageDeleted(data) {
        const messageElement = document.querySelector(`.message[data-message-id="${data.message_id}"]`);
        if (messageElement) {
            // Обновляем содержимое сообщения на [Сообщение удалено]
            const contentArea = messageElement.querySelector('.message-content');
            if (contentArea) {
                contentArea.textContent = '[Сообщение удалено]';
                contentArea.style.fontStyle = 'italic';
                contentArea.style.opacity = '0.6';
            }

            // Добавляем класс для визуального отображения удаленного сообщения
            messageElement.classList.add('deleted-message');
        }
    }

    handleMessageEdited(data) {
        const messageElement = document.querySelector(`.message[data-message-id="${data.message_id}"]`);
        if (messageElement) {
            // Обновляем содержимое сообщения
            const contentArea = messageElement.querySelector('.message-content');
            if (contentArea) {
                contentArea.textContent = data.new_content;
            }

            // Добавляем индикатор редактирования
            const messageHeader = messageElement.querySelector('.message-header');
            if (messageHeader) {
                // Убираем старый индикатор если есть
                const oldIndicator = messageHeader.querySelector('.edit-indicator');
                if (oldIndicator) {
                    oldIndicator.remove();
                }

                // Добавляем новый индикатор
                const editIndicator = document.createElement('span');
                editIndicator.className = 'edit-indicator';
                editIndicator.innerHTML = '<i class="fas fa-edit" title="Отредактировано"></i>';
                editIndicator.style.color = '#6c757d';
                editIndicator.style.fontSize = '0.8rem';
                editIndicator.style.marginLeft = '0.5rem';

                const metaSection = messageHeader.querySelector('.message-meta');
                if (metaSection) {
                    metaSection.appendChild(editIndicator);
                }
            }

            // Добавляем класс для визуального отображения редактированного сообщения
            messageElement.classList.add('edited-message');
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'Disconnect requested');
            this.socket = null;
        }
        this.updateConnectionStatus('disconnected');
    }
}

// Функция для инициализации чата (обратная совместимость)
function initChat(roomName, currentUser) {
    return new ChatClient(roomName, currentUser);
}
