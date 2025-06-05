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
            this.showNotification('Подключено к чату', 'success');

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
                this.showNotification('Соединение потеряно', 'error');
            }
        };

        this.socket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.updateConnectionStatus('disconnected');
            this.showNotification('Ошибка подключения', 'error');
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
        messageDiv.className = `message ${message.is_own ? 'own-message' : 'other-message'}`;

        const timeString = new Date(message.created).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });

        if (message.is_own) {
            messageDiv.innerHTML = `
                <div class="message-bubble">
                    <div class="message-content">${this.escapeHtml(message.content)}</div>
                    <div class="message-time">${timeString}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-header">
                    <strong>${this.escapeHtml(message.author_name)}</strong>
                    <span class="text-muted">${timeString}</span>
                </div>
                <div class="message-bubble">
                    <div class="message-content">${this.escapeHtml(message.content)}</div>
                </div>
            `;
        }

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
                <span class="user-name">${this.escapeHtml(user.display_name || user.username)}</span>
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
            this.socket.send(JSON.stringify({
                type: 'message',
                message: message
            }));

            input.value = '';
            this.stopTyping();
        } else if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            this.showNotification('Нет соединения с сервером', 'error');
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

    showNotification(message, type = 'info') {
        // Простая система уведомлений
        console.log(`${type.toUpperCase()}: ${message}`);

        // Можно добавить визуальные уведомления
        if (type === 'error') {
            // Показать красное уведомление
        } else if (type === 'success') {
            // Показать зеленое уведомление
        }
    }

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
}

// Глобальная функция для инициализации чата
function initChat(chatType = 'general', roomId = null) {
    return new ChatClient(chatType, roomId);
}

// Экспорт для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChatClient, initChat };
}
