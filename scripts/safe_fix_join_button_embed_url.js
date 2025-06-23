// ===================================================================
// БЕЗОПАСНОЕ ИСПРАВЛЕНИЕ КНОПКИ "JOIN THE CHANNEL" - ИЗМЕНЕНИЕ URL
// ===================================================================
// Создан: 23 июня 2025, 20:25 MSK
// Цель: БЕЗОПАСНО протестировать /embed?channel= вместо /channel/?layout=embedded
// Подход: Минимальные изменения, сохранение работающей системы
// ===================================================================

print('🔧 БЕЗОПАСНОЕ ИСПРАВЛЕНИЕ КНОПКИ "JOIN THE CHANNEL"...');
print('🎯 Тестируем /embed?channel= вместо /channel/?layout=embedded');
print('');

// ===================================================================
// 1. ПРОВЕРКА ТЕКУЩЕГО СОСТОЯНИЯ
// ===================================================================

print('📊 ПРОВЕРКА ТЕКУЩЕГО СОСТОЯНИЯ:');

// Проверяем пользователя owner
const ownerUser = db.users.findOne({ username: 'owner' });
if (!ownerUser) {
    print('❌ КРИТИЧЕСКАЯ ОШИБКА: Пользователь owner не найден!');
    exit(1);
}

print(`   ✅ Пользователь owner найден: ${ownerUser.username}`);

// Проверяем каналы
const channels = ['general', 'vip', 'moderators'];
let allChannelsExist = true;

channels.forEach(channelId => {
    const channel = db.rocketchat_room.findOne({ _id: channelId });
    if (channel) {
        print(`   ✅ Канал ${channelId}: "${channel.fname}"`);
    } else {
        print(`   ❌ Канал ${channelId}: НЕ НАЙДЕН!`);
        allChannelsExist = false;
    }
});

// Проверяем подписки
const ownerSubscriptions = db.rocketchat_subscription.find({ 'u.username': 'owner' }).toArray();
print(`   ✅ Подписки owner: ${ownerSubscriptions.length} из ${channels.length}`);

if (!allChannelsExist || ownerSubscriptions.length !== channels.length) {
    print('');
    print('❌ СИСТЕМА НЕ ГОТОВА К ИЗМЕНЕНИЯМ!');
    print('🔧 Сначала выполните FINAL_ROCKETCHAT_FIX.js для восстановления');
    exit(1);
}

print('');
print('✅ СИСТЕМА СТАБИЛЬНА - МОЖНО ПРОДОЛЖАТЬ');

// ===================================================================
// 2. АНАЛИЗ ПРОБЛЕМЫ
// ===================================================================

print('');
print('🔍 АНАЛИЗ ПРОБЛЕМЫ "JOIN THE CHANNEL":');
print('');
print('   📋 ТЕКУЩИЙ URL ФОРМАТ:');
print('      /channel/{channelId}?layout=embedded');
print('');
print('   🤔 ВОЗМОЖНАЯ ПРИЧИНА:');
print('      layout=embedded НЕ полностью скрывает UI элементы Rocket.Chat');
print('      Кнопка Join Channel остается видимой при переключении каналов');
print('');
print('   💡 ПРЕДЛАГАЕМОЕ РЕШЕНИЕ:');
print('      Использовать /embed?channel={channelId}');
print('      Это специальный endpoint для полного embed режима');

// ===================================================================
// 3. ПРОВЕРКА EMBED ENDPOINT
// ===================================================================

print('');
print('🌐 ПРОВЕРКА EMBED ENDPOINT:');

// Проверяем настройки iframe
const iframeSettings = [
    'Iframe_Integration_send_enable',
    'Iframe_Integration_receive_enable',
    'Iframe_Restrict_Access'
];

let embedSupported = true;
iframeSettings.forEach(settingId => {
    const setting = db.rocketchat_settings.findOne({ _id: settingId });
    if (setting) {
        print(`   📋 ${settingId}: ${setting.value}`);
        if (setting.value === false && settingId.includes('enable')) {
            embedSupported = false;
        }
    } else {
        print(`   ❓ ${settingId}: НЕ НАЙДЕНО (вероятно по умолчанию true)`);
    }
});

if (!embedSupported) {
    print('');
    print('⚠️ ПРЕДУПРЕЖДЕНИЕ: Embed интеграция может быть отключена');
    print('🔧 Рекомендуется включить Iframe_Integration_*_enable настройки');
}

// ===================================================================
// 4. БЕЗОПАСНЫЙ ПЛАН ИЗМЕНЕНИЙ
// ===================================================================

print('');
print('🛡️ БЕЗОПАСНЫЙ ПЛАН ИЗМЕНЕНИЙ:');
print('');
print('   📝 ШАГ 1: Создать бэкап шаблона');
print('      Файл: templates/chat/rocketchat_integrated.html');
print('');
print('   📝 ШАГ 2: Изменить URL endpoint');
print('      ОТ:  /channel/{channelId}?layout=embedded');
print('      НА:  /embed?channel={channelId}');
print('');
print('   📝 ШАГ 3: Протестировать изменения');
print('      - Проверить загрузку каналов');
print('      - Проверить переключение между каналами');
print('      - Проверить появление кнопки Join Channel');
print('');
print('   📝 ШАГ 4: Откат при проблемах');
print('      - Восстановить из бэкапа');
print('      - Проверить работоспособность');

// ===================================================================
// 5. РЕКОМЕНДАЦИИ ПО РЕАЛИЗАЦИИ
// ===================================================================

print('');
print('💡 РЕКОМЕНДАЦИИ ПО РЕАЛИЗАЦИИ:');
print('');
print('   🔧 ИЗМЕНЕНИЯ В ШАБЛОНЕ:');
print('      1. Строка 339: src="{{ rocketchat_url }}/embed?channel=general"');
print('      2. Строка 376: const newUrl = `{{ rocketchat_url }}/embed?channel=${actualChannelId}`;');
print('      3. Обновить все console.log сообщения');
print('');
print('   ⚠️ ВАЖНЫЕ МОМЕНТЫ:');
print('      - НЕ трогать настройки MongoDB');
print('      - НЕ изменять подписки пользователей');
print('      - НЕ перезапускать контейнеры');
print('      - Только изменение URL в шаблоне');
print('');
print('   🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:');
print('      - Кнопка Join Channel исчезнет');
print('      - Переключение каналов станет мгновенным');
print('      - Интерфейс станет чище (только чат)');

// ===================================================================
// 6. ПЛАН ОТКАТА
// ===================================================================

print('');
print('🔄 ПЛАН ОТКАТА (если что-то пойдет не так):');
print('');
print('   📋 ПРИЗНАКИ ПРОБЛЕМ:');
print('      - Iframe не загружается');
print('      - Каналы не переключаются');
print('      - Ошибки в консоли браузера');
print('      - Поле ввода не работает');
print('');
print('   🚨 ДЕЙСТВИЯ ПРИ ПРОБЛЕМАХ:');
print('      1. Восстановить шаблон из бэкапа');
print('      2. Перезапустить Django сервер');
print('      3. Проверить работоспособность');
print('      4. Если не помогает - выполнить полное восстановление');

print('');
print('🎉 ПЛАН ГОТОВ К ВЫПОЛНЕНИЮ!');
print('📋 Следуйте рекомендациям для безопасного исправления');
print('⚠️ ПОМНИТЕ: Лучше работающая система с кнопкой, чем сломанная без неё!');
