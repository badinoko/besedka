// ===================================================================
// ПРОВЕРКА НАСТРОЕК КАНАЛОВ - ПОИСК ПРИЧИНЫ КНОПКИ "JOIN THE CHANNEL"
// ===================================================================
// Создан: 23 июня 2025, 20:15 MSK
// Цель: Проверить настройки каналов и URL endpoint
// ===================================================================

print('🔍 ПРОВЕРКА НАСТРОЕК КАНАЛОВ И URL ENDPOINT...');
print('🎯 Поиск причины кнопки "Join the Channel"');
print('');

// ===================================================================
// 1. ДЕТАЛЬНАЯ ПРОВЕРКА КАНАЛОВ
// ===================================================================

const channels = ['general', 'vip', 'moderators'];
print('💬 ДЕТАЛЬНАЯ ПРОВЕРКА КАНАЛОВ:');

channels.forEach(channelId => {
    const channel = db.rocketchat_room.findOne({ _id: channelId });

    print(`   🔍 Канал ${channelId}:`);

    if (!channel) {
        print(`      ❌ Канал не найден!`);
        return;
    }

    print(`      📋 ID: ${channel._id}`);
    print(`      📋 Name: ${channel.name}`);
    print(`      📋 Display Name: ${channel.fname}`);
    print(`      📋 Type: ${channel.t}`);
    print(`      📋 Default: ${channel.default}`);
    print(`      📋 Read Only: ${channel.ro}`);
    print(`      📋 System Messages: ${channel.sysMes}`);
    print(`      📋 Users Count: ${channel.usersCount || 0}`);
    print(`      📋 Messages: ${channel.msgs || 0}`);

    // Проверяем специальные настройки
    if (channel.joinCodeRequired) {
        print(`      ⚠️ Требуется код для входа: ${channel.joinCodeRequired}`);
    }

    if (channel.broadcast) {
        print(`      ⚠️ Broadcast канал: ${channel.broadcast}`);
    }

    if (channel.encrypted) {
        print(`      ⚠️ Зашифрованный канал: ${channel.encrypted}`);
    }

    // Проверяем владельца канала
    if (channel.u) {
        print(`      👤 Владелец: ${channel.u.username} (${channel.u._id})`);
    }

    print('');
});

// ===================================================================
// 2. ПРОВЕРКА URL ENDPOINT И EMBED НАСТРОЕК
// ===================================================================

print('🌐 ПРОВЕРКА URL ENDPOINT И EMBED НАСТРОЕК:');

const embedSettings = [
    'Iframe_Integration_send_enable',
    'Iframe_Integration_receive_enable',
    'Iframe_Restrict_Access',
    'Iframe_X_Frame_Options',
    'API_Enable_CORS',
    'API_CORS_Origin'
];

embedSettings.forEach(settingId => {
    const setting = db.rocketchat_settings.findOne({ _id: settingId });
    if (setting) {
        print(`   📋 ${settingId}: ${setting.value}`);
    } else {
        print(`   ❓ ${settingId}: НЕ НАЙДЕНО`);
    }
});

print('');

// ===================================================================
// 3. ПРОВЕРКА НАСТРОЕК АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ К КАНАЛАМ
// ===================================================================

print('🔐 НАСТРОЙКИ АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ К КАНАЛАМ:');

const channelJoinSettings = [
    'Accounts_AllowAnonymousRead',
    'Accounts_AllowAnonymousWrite',
    'Accounts_AllowUserProfileChange',
    'Accounts_AllowUserAvatarChange',
    'Message_AllowEditing',
    'Message_AllowDeleting',
    'Channel_Allow_Anonymous_Read',
    'Channel_Allow_Anonymous_Write'
];

channelJoinSettings.forEach(settingId => {
    const setting = db.rocketchat_settings.findOne({ _id: settingId });
    if (setting) {
        print(`   📋 ${settingId}: ${setting.value}`);
    } else {
        print(`   ❓ ${settingId}: НЕ НАЙДЕНО`);
    }
});

print('');

// ===================================================================
// 4. ПРОВЕРКА OAUTH И SSO НАСТРОЕК
// ===================================================================

print('🔑 OAUTH И SSO НАСТРОЙКИ:');

const oauthSettings = [
    'Accounts_OAuth_Custom-besedka',
    'Accounts_OAuth_Custom-besedka-url',
    'Accounts_OAuth_Custom-besedka-token_path',
    'Accounts_OAuth_Custom-besedka-identity_path',
    'Accounts_OAuth_Custom-besedka-authorize_path',
    'Accounts_OAuth_Custom-besedka-scope',
    'Accounts_OAuth_Custom-besedka-id',
    'Accounts_OAuth_Custom-besedka-secret',
    'Accounts_OAuth_Custom-besedka-login_style',
    'Accounts_OAuth_Custom-besedka-button_label_text',
    'Accounts_OAuth_Custom-besedka-button_label_color',
    'Accounts_OAuth_Custom-besedka-button_color',
    'Accounts_OAuth_Custom-besedka-username_field',
    'Accounts_OAuth_Custom-besedka-email_field',
    'Accounts_OAuth_Custom-besedka-name_field',
    'Accounts_OAuth_Custom-besedka-roles_claim',
    'Accounts_OAuth_Custom-besedka-merge_users',
    'Accounts_OAuth_Custom-besedka-show_button',
    'Accounts_OAuth_Custom-besedka-map_channels',
    'Accounts_OAuth_Custom-besedka-merge_roles'
];

let oauthConfigured = false;
oauthSettings.forEach(settingId => {
    const setting = db.rocketchat_settings.findOne({ _id: settingId });
    if (setting && setting.value) {
        print(`   ✅ ${settingId}: ${setting.value}`);
        oauthConfigured = true;
    }
});

if (!oauthConfigured) {
    print('   ❌ OAuth настройки не найдены или не настроены!');
    print('   🔧 Это может быть причиной проблем с авторизацией');
}

print('');

// ===================================================================
// 5. ПРОВЕРКА EMBED MODE НАСТРОЕК
// ===================================================================

print('📺 EMBED MODE НАСТРОЙКИ:');

// Проверяем можно ли использовать каналы в embed режиме
channels.forEach(channelId => {
    const channel = db.rocketchat_room.findOne({ _id: channelId });

    print(`   🔍 Embed доступ для ${channelId}:`);

    // Проверяем настройки которые могут блокировать embed
    if (channel.ro) {
        print(`      ⚠️ Канал только для чтения - может блокировать ввод`);
    }

    if (!channel.sysMes) {
        print(`      ⚠️ Системные сообщения отключены`);
    }

    // Проверяем есть ли ограничения на embed
    const embedSetting = db.rocketchat_settings.findOne({
        _id: `Channel_${channelId}_AllowEmbedding`
    });

    if (embedSetting) {
        print(`      📋 Embedding разрешен: ${embedSetting.value}`);
    } else {
        print(`      📋 Embedding: настройка не найдена (вероятно разрешено)`);
    }

    print('');
});

// ===================================================================
// 6. ПРОВЕРКА РЕЖИМА /embed VS /channel
// ===================================================================

print('🔄 АНАЛИЗ URL ENDPOINT:');
print('   📋 Текущий URL формат: /channel/{channelId}?layout=embedded');
print('   📋 Альтернатива: /embed?channel={channelId}');
print('');
print('   🤔 Возможные причины кнопки Join Channel:');
print('      1. URL /channel/{id}?layout=embedded может не полностью скрывать UI');
print('      2. Нужно использовать /embed?channel={id} для полного embed режима');
print('      3. Настройки канала требуют дополнительного подтверждения входа');
print('      4. OAuth интеграция работает не полностью');

// ===================================================================
// 7. РЕКОМЕНДАЦИИ
// ===================================================================

print('');
print('💡 РЕКОМЕНДАЦИИ ДЛЯ УСТРАНЕНИЯ КНОПКИ JOIN CHANNEL:');
print('');
print('   🔧 ВАРИАНТ 1: Изменить URL endpoint');
print('      - Заменить /channel/{id}?layout=embedded');
print('      - На /embed?channel={id}');
print('      - Это может дать более чистый embed режим');
print('');
print('   🔧 ВАРИАНТ 2: Настроить автоматическое присоединение');
print('      - Проверить настройки Accounts_RequireNameForSignUp');
print('      - Убедиться что OAuth полностью настроен');
print('      - Добавить автоматическое присоединение к каналам');
print('');
print('   🔧 ВАРИАНТ 3: Использовать postMessage API');
print('      - Отправлять команды присоединения через iframe.postMessage');
print('      - Автоматически присоединять к каналу при переключении');
print('');
print('   ⚠️ ВАЖНО: Делать изменения постепенно с бэкапами!');

print('');
print('🎉 ПРОВЕРКА НАСТРОЕК ЗАВЕРШЕНА!');
