(function() {
    'use strict';

    // Простой скрипт для диагностики.
    // Если он работает, фон внутри iframe станет красным.
    console.log('🚀 [Telegram UI - DIAGNOSTIC MODE] Script loaded. Attempting to change background color...');

    // Ждем полной загрузки DOM внутри iframe
    window.addEventListener('load', () => {
        try {
            document.body.style.backgroundColor = 'red';
            console.log('✅ [Telegram UI - DIAGNOSTIC MODE] Background color changed to red!');
        } catch (e) {
            console.error('❌ [Telegram UI - DIAGNOSTIC MODE] Failed to change background color:', e);
        }
    });

    // Ждем, пока Rocket Chat полностью загрузится
    window.addEventListener('load', () => {
        // Небольшая задержка, чтобы убедиться, что DOM сообщений уже построен
        setTimeout(initTelegramUI, 1500);
    });

    function initTelegramUI() {
        console.log('🚀 [Telegram UI v3] Initializing...');

        const messageList = document.querySelector('.messages-box .wrapper');
        if (!messageList) {
            console.error('🚀 [Telegram UI v3] Message list not found. Aborting.');
            return;
        }

        // --- 1. Добавляем кнопки к уже существующим сообщениям ---
        const existingMessages = messageList.querySelectorAll('.message');
        existingMessages.forEach(addTelegramButtons);
        console.log(`🚀 [Telegram UI v3] Added buttons to ${existingMessages.length} existing messages.`);

        // --- 2. Отслеживаем появление новых сообщений ---
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && node.classList.contains('message')) {
                        addTelegramButtons(node);
                    }
                });
            });
        });

        observer.observe(messageList, { childList: true, subtree: true });
        console.log('🚀 [Telegram UI v3] MutationObserver is now watching for new messages.');
    }

    function addTelegramButtons(messageElement) {
        // Проверяем, не добавлены ли уже кнопки
        if (messageElement.querySelector('.telegram-buttons')) {
            return;
        }

        const messageId = messageElement.dataset.id;
        if (!messageId) return;

        // Создаем контейнер для наших кнопок
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'telegram-buttons';

        // --- Кнопка "Ответить" ---
        const replyButton = document.createElement('button');
        replyButton.className = 'telegram-btn reply-btn';
        replyButton.innerHTML = '↩️';
        replyButton.title = 'Ответить';
        replyButton.onclick = () => {
            console.log(`[Telegram UI] Reply to message: ${messageId}`);
        };

        // --- Кнопка "Реакции" ---
        const reactionButton = document.createElement('button');
        reactionButton.className = 'telegram-btn reaction-btn';
        reactionButton.innerHTML = '😊';
        reactionButton.title = 'Добавить реакцию';
        reactionButton.onclick = () => {
            console.log(`[Telegram UI] React to message: ${messageId}`);
        };


        buttonContainer.appendChild(replyButton);
        buttonContainer.appendChild(reactionButton);

        const messageBody = messageElement.querySelector('.body');
        if (messageBody) {
            messageBody.appendChild(buttonContainer);
        }
    }

})();
