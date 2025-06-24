/**
 * Auto Join Fix для Rocket.Chat
 * Автоматически "нажимает" кнопку Join the Channel
 * Дата: 23 июня 2025
 */

(function() {
    'use strict';

    console.log('🚀 Auto Join Fix загружен');

    let autoJoinAttempts = 0;
    const maxAutoJoinAttempts = 15;
    const autoJoinInterval = 1000; // ускорено

    /**
     * Функция поиска и автоматического нажатия кнопки Join
     */
    function autoJoinChannel() {
        if (autoJoinAttempts >= maxAutoJoinAttempts) {
            console.log('⏹️ Прекращаем попытки автоматического присоединения');
            return;
        }

        autoJoinAttempts++;
        console.log(`🔍 Попытка автоматического присоединения #${autoJoinAttempts}`);

        // Получаем iframe с Rocket.Chat
        const iframe = document.getElementById('rocketChatFrame');
        if (!iframe) {
            console.log('❌ Iframe не найден');
            return;
        }

        try {
            // Пытаемся получить доступ к содержимому iframe
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

            if (iframeDoc) {
                // Ищем кнопку Join the Channel
                const joinButton = iframeDoc.querySelector('[data-qa="join-channel"]') ||
                                 iframeDoc.querySelector('button[title*="Join"]') ||
                                 iframeDoc.querySelector('button:contains("Join")') ||
                                 iframeDoc.querySelector('.join-channel') ||
                                 iframeDoc.querySelector('[class*="join"]');

                if (joinButton) {
                    console.log('✅ Найдена кнопка Join the Channel, автоматически нажимаем');
                    joinButton.click();

                    // Даем время на обработку
                    setTimeout(() => {
                        console.log('🎉 Автоматическое присоединение выполнено!');
                    }, 1000);
                    return;
                }

                // Ищем текст "Channel not joined" или "Join general to view history"
                const notJoinedText = iframeDoc.querySelector('[data-qa="not-joined"]') ||
                                    iframeDoc.querySelector(':contains("Channel not joined")') ||
                                    iframeDoc.querySelector(':contains("Join") + :contains("to view history")');

                if (notJoinedText) {
                    console.log('📝 Найден текст о необходимости присоединения, ищем кнопку...');

                    // Ищем любую кнопку рядом с этим текстом
                    const nearbyButton = notJoinedText.closest('div').querySelector('button') ||
                                       notJoinedText.parentElement.querySelector('button');

                    if (nearbyButton) {
                        console.log('✅ Найдена кнопка рядом с текстом присоединения, нажимаем');
                        nearbyButton.click();
                        return;
                    }
                }

                console.log('ℹ️ Кнопка Join не найдена, возможно уже присоединен');
            }
        } catch (e) {
            // Если нет прямого доступа к iframe (CORS), используем postMessage
            console.log('🔄 Прямой доступ к iframe заблокирован, используем postMessage');

            // Отправляем сообщение в iframe для автоматического присоединения
            iframe.contentWindow.postMessage({
                type: 'AUTO_JOIN_CHANNEL',
                channelId: getCurrentChannelId()
            }, '*');
        }

        // Повторяем попытку через интервал
        setTimeout(autoJoinChannel, autoJoinInterval);
    }

    /**
     * Получение текущего ID канала из URL iframe
     */
    function getCurrentChannelId() {
        const iframe = document.getElementById('rocketChatFrame');
        if (iframe && iframe.src) {
            let match = iframe.src.match(/\/channel\/([^?]+)/);
            if (!match) {
                match = iframe.src.match(/embed\?channel=([^&]+)/);
            }
            return match ? match[1] : 'general';
        }
        return 'general';
    }

    /**
     * Обработчик сообщений от iframe
     */
    window.addEventListener('message', function(event) {
        // Проверяем происхождение сообщения
        if (event.origin !== 'http://127.0.0.1:3000' && event.origin !== 'http://localhost:3000') {
            return;
        }

        const data = event.data;

        if (data.type === 'CHANNEL_JOINED') {
            console.log('🎉 Канал успешно присоединен через postMessage:', data.channelId);
            autoJoinAttempts = maxAutoJoinAttempts; // Останавливаем попытки
        } else if (data.type === 'JOIN_BUTTON_FOUND') {
            console.log('✅ Кнопка Join найдена и нажата через postMessage');
        }
    });

    /**
     * Запуск автоматического присоединения при переключении каналов
     */
    function setupAutoJoinOnChannelSwitch() {
        // Переопределяем функцию switchChannel для запуска автоматического присоединения
        const originalSwitchChannel = window.switchChannel;

        if (originalSwitchChannel) {
            window.switchChannel = function(channelName) {
                console.log('🔄 Переключение канала, сбрасываем счетчик автоматического присоединения');
                autoJoinAttempts = 0;

                // Вызываем оригинальную функцию
                originalSwitchChannel(channelName);

                // Запускаем автоматическое присоединение через 3 секунды после переключения
                setTimeout(() => {
                    autoJoinChannel();
                }, 3000);
            };
        }
    }

    /**
     * Скрипт для вставки в iframe Rocket.Chat
     * Этот код будет выполняться внутри iframe
     */
    function injectAutoJoinScript() {
        const iframe = document.getElementById('rocketChatFrame');
        if (!iframe) return;

        // Отказались от прямого внедрения из-за CORS – используем только postMessage
    }

    /**
     * Инициализация
     */
    function init() {
        console.log('🔧 Инициализация Auto Join Fix');

        // Ждем загрузки iframe
        setTimeout(() => {
            injectAutoJoinScript();
            setupAutoJoinOnChannelSwitch();

            // Запускаем первую попытку автоматического присоединения
            setTimeout(autoJoinChannel, 5000);
        }, 2000);
    }

    // Запускаем инициализацию при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
