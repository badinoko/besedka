// 🪄 АВТОМАТИЧЕСКАЯ НАСТРОЙКА ROCKET.CHAT OAUTH

print('🚀 Автоматическая настройка Rocket.Chat OAuth...');

// 1. Отключаем Setup Wizard навсегда
db.rocketchat_settings.updateOne(
    {_id: 'Show_Setup_Wizard'},
    {$set: {value: 'completed', valueSource: 'customValue', _updatedAt: new Date()}},
    {upsert: true}
);

// 2. Удаляем старые OAuth настройки
db.rocketchat_settings.deleteMany({_id: /^Accounts_OAuth_Custom/});

// 3. Создаем правильный OAuth провайдер "besedka"
const oauthSettings = [
    {_id: 'Accounts_OAuth_Custom-besedka', value: true, type: 'boolean', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-url', value: 'http://127.0.0.1:8001', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-token_path', value: '/o/token/', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-identity_path', value: '/api/v1/auth/rocket/', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-authorize_path', value: '/o/authorize/', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-scope', value: 'read', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-id', value: 'BesedkaRocketChat2025', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-secret', value: 'SecureSecretKey2025BesedkaRocketChatSSO', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-button_label_text', value: 'Войти через Беседку', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-button_color', value: '#1976d2', type: 'color', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-login_style', value: 'redirect', type: 'select', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-merge_users', value: true, type: 'boolean', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-show_button', value: true, type: 'boolean', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-username_field', value: 'username', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-email_field', value: 'email', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-name_field', value: 'name', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-roles_claim', value: 'role', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-merge_roles', value: true, type: 'boolean', valueSource: 'customValue'}
];

// Применяем все настройки
oauthSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {...setting, _updatedAt: new Date()}},
        {upsert: true}
    );
});

// 4. Отключаем iframe ограничения
db.rocketchat_settings.updateOne(
    {_id: 'Iframe_Restrict_Access'},
    {$set: {value: false, valueSource: 'customValue', _updatedAt: new Date()}},
    {upsert: true}
);

// 5. Убираем кнопку "Join the Channel"
db.rocketchat_settings.updateOne(
    {_id: 'Accounts_OAuth_Custom-besedka-show_button'},
    {$set: {value: true, valueSource: 'customValue', _updatedAt: new Date()}},
    {upsert: true}
);

// 6. Создаем каналы если их нет
const channels = [
    {_id: 'general', name: 'general', fname: 'Общий чат', t: 'c', default: true},
    {_id: 'vip', name: 'vip', fname: 'VIP чат', t: 'p', default: false},
    {_id: 'moderators', name: 'moderators', fname: 'Модераторы', t: 'p', default: false}
];

channels.forEach(channel => {
    const existing = db.rocketchat_room.findOne({_id: channel._id});
    if (!existing) {
        db.rocketchat_room.insertOne({
            ...channel,
            ts: new Date(),
            _updatedAt: new Date(),
            msgs: 0,
            usersCount: 0,
            lm: new Date()
        });
        print(`✅ Создан канал: ${channel.name}`);
    } else {
        print(`ℹ️ Канал уже существует: ${channel.name}`);
    }
});

print('✅ Автоматическая настройка завершена!');
print('🎯 OAuth провайдер "besedka" настроен');
print('📱 Каналы созданы: general, vip, moderators');
print('🔧 Setup Wizard отключен');
print('🚀 Готово к тестированию!');
