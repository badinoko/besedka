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
    const autoJoinInterval = 1500; // 1.5 секунды

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
            const match = iframe.src.match(/\/channel\/([^?]+)/);
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

        // Создаем скрипт для вставки в iframe
        const scriptContent = `
            (function() {
                console.log('📦 Auto Join скрипт загружен внутри Rocket.Chat iframe');

                function findAndClickJoinButton() {
                                         const joinSelectors = [
                         '[data-qa="join-channel"]',
                         'button[title*="Join"]',
                         'button[aria-label*="Join"]',
                         '.join-channel-button',
                         '.join-channel',
                         '[class*="join"]',
                         'button:contains("Join")',
                         '.rc-button--primary:contains("Join")',
                         '.rc-button:contains("Join")',
                         'button[type="button"]:contains("Join")',
                         '[role="button"]:contains("Join")',
                         '.button:contains("Join")',
                         'a:contains("Join")'
                     ];

                                         for (const selector of joinSelectors) {
                         const button = document.querySelector(selector);
                         if (button) {
                             console.log('✅ Найдена кнопка Join:', selector);
                             button.click();

                             // Уведомляем родительское окно
                             window.parent.postMessage({
                                 type: 'JOIN_BUTTON_FOUND',
                                 selector: selector
                             }, '*');

                             return true;
                         }
                     }

                     // Дополнительный поиск по текстовому содержимому
                     const allButtons = document.querySelectorAll('button, [role="button"], .button, a');
                     for (const button of allButtons) {
                         const text = button.textContent || button.innerText || '';
                         if (text.toLowerCase().includes('join') &&
                             (text.toLowerCase().includes('channel') ||
                              text.toLowerCase().includes('general') ||
                              text.toLowerCase().includes('присоединить'))) {
                             console.log('✅ Найдена кнопка Join по тексту:', text);
                             button.click();

                             window.parent.postMessage({
                                 type: 'JOIN_BUTTON_FOUND',
                                 selector: 'text-based',
                                 text: text
                             }, '*');

                             return true;
                         }
                     }

                     return false;
                }

                // Слушаем сообщения от родительского окна
                window.addEventListener('message', function(event) {
                    if (event.data.type === 'AUTO_JOIN_CHANNEL') {
                        console.log('🔄 Получен запрос на автоматическое присоединение');
                        if (findAndClickJoinButton()) {
                            window.parent.postMessage({
                                type: 'CHANNEL_JOINED',
                                channelId: event.data.channelId
                            }, '*');
                        }
                    }
                });

                                 // Автоматический поиск кнопки при загрузке
                 setTimeout(findAndClickJoinButton, 1000);
                 setTimeout(findAndClickJoinButton, 3000);
                 setTimeout(findAndClickJoinButton, 5000);

                // Наблюдатель за изменениями DOM
                const observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.addedNodes.length > 0) {
                            // Ищем кнопку Join среди новых элементов
                            const hasJoinButton = Array.from(mutation.addedNodes).some(node => {
                                if (node.nodeType === 1) { // Element node
                                    return node.querySelector && (
                                        node.querySelector('[data-qa="join-channel"]') ||
                                        node.textContent.includes('Join')
                                    );
                                }
                                return false;
                            });

                            if (hasJoinButton) {
                                setTimeout(findAndClickJoinButton, 500);
                            }
                        }
                    });
                });

                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            })();
        `;

        // Пытаемся выполнить скрипт в iframe
        try {
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            if (iframeDoc) {
                const script = iframeDoc.createElement('script');
                script.textContent = scriptContent;
                iframeDoc.head.appendChild(script);
                console.log('✅ Auto Join скрипт внедрен в iframe');
            }
        } catch (e) {
            console.log('❌ Не удалось внедрить скрипт в iframe (CORS):', e.message);
        }
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
