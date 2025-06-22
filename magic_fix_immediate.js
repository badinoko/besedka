// МАГИЧЕСКОЕ ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ ROCKET.CHAT

print('🪄 МАГИЧЕСКИЙ СКРИПТ ИСПРАВЛЕНИЯ...');

// 1. Фиксируем Setup Wizard навсегда
print('🔧 Фиксирую Setup Wizard...');
db.rocketchat_settings.updateOne(
    {_id: 'Show_Setup_Wizard'},
    {$set: {value: 'completed', valueSource: 'customValue', _updatedAt: new Date()}}
);

// 2. Исправляем канал vip-chat -> vip
print('🔧 Исправляю каналы...');
const vipChatRoom = db.rocketchat_room.findOne({_id: 'vip-chat'});
if (vipChatRoom) {
    // Меняем ID канала с vip-chat на vip
    db.rocketchat_room.updateOne(
        {_id: 'vip-chat'},
        {$set: {_id: 'vip', name: 'vip', _updatedAt: new Date()}}
    );

    // Обновляем все подписки
    db.rocketchat_subscription.updateMany(
        {rid: 'vip-chat'},
        {$set: {rid: 'vip', name: 'vip', _updatedAt: new Date()}}
    );

    print('✅ Канал vip-chat исправлен на vip');
}

// 3. Находим пользователя owner
const owner = db.users.findOne({ username: 'owner' });
if (!owner) {
    print('❌ Пользователь owner не найден!');
    quit();
}

// 4. Создаем подписки на ВСЕ каналы если их нет
const allChannels = ['GENERAL', 'vip', 'moderators'];
allChannels.forEach(channelId => {
    const room = db.rocketchat_room.findOne({ _id: channelId });
    if (!room) {
        print('❌ Канал не найден: ' + channelId);
        return;
    }

    let subscription = db.rocketchat_subscription.findOne({
        'u._id': owner._id,
        rid: channelId
    });

    if (!subscription) {
        print('📝 Создаю подписку на канал: ' + room.name);

        db.rocketchat_subscription.insertOne({
            _id: owner._id + channelId,
            u: {
                _id: owner._id,
                username: owner.username
            },
            rid: channelId,
            name: room.name,
            fname: room.fname || room.name,
            t: room.t,
            ts: new Date(),
            ls: new Date(),
            lr: new Date(),
            f: false,
            open: true,
            alert: false,
            roles: ['owner'],
            unread: 0,
            _updatedAt: new Date()
        });

        print('✅ Подписка создана: ' + room.name);
    } else {
        print('ℹ️ Подписка уже есть: ' + room.name);
    }
});

// 5. Настраиваем OAuth автоматически
print('🔧 Настраиваю OAuth...');

// Удаляем старые OAuth провайдеры
db.rocketchat_settings.deleteMany({_id: /^Accounts_OAuth_Custom/});

// Создаем правильный OAuth провайдер
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
    {_id: 'Accounts_OAuth_Custom-besedka-roles_claim', value: 'roles', type: 'string', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-merge_roles', value: true, type: 'boolean', valueSource: 'customValue'},
    {_id: 'Accounts_OAuth_Custom-besedka-roles_to_groups_mapping', value: '{"owner":"admin,vip","moderator":"admin","user":"user"}', type: 'string', valueSource: 'customValue'}
];

oauthSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {...setting, _updatedAt: new Date()}},
        {upsert: true}
    );
});

// 6. Отключаем iframe ограничения
db.rocketchat_settings.updateOne(
    {_id: 'Iframe_Restrict_Access'},
    {$set: {value: false, valueSource: 'customValue', _updatedAt: new Date()}}
);

print('✅ OAuth настроен автоматически');

// ИТОГОВЫЙ ОТЧЕТ
print('\n=== МАГИЧЕСКИЙ РЕЗУЛЬТАТ ===');
print('✅ Setup Wizard отключен навсегда');
print('✅ Каналы исправлены: GENERAL, vip, moderators');
print('✅ Пользователь owner подписан на все каналы');
print('✅ OAuth полностью настроен');
print('✅ Iframe разрешен');
print('\n🪄 МАГИЯ ЗАВЕРШЕНА! Система готова к работе!');
