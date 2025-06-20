// Полная настройка Rocket.Chat для проекта Беседка

// 1. Пропускаем Setup Wizard
db.rocketchat_settings.updateOne(
    { _id: 'Show_Setup_Wizard' },
    { $set: { value: 'completed' } }
);

// 2. Создаем пользователя owner (если его еще нет)
const existingUser = db.users.findOne({ username: 'owner' });
if (!existingUser) {
    // Генерируем необходимые данные
    const userId = 'owner_user_id';
    const now = new Date();

    // Создаем пользователя
    db.users.insertOne({
        _id: userId,
        username: 'owner',
        emails: [{
            address: 'owner@besedka.local',
            verified: true
        }],
        status: 'online',
        active: true,
        type: 'user',
        roles: ['admin', 'user'],
        name: 'Owner',
        lastLogin: now,
        statusConnection: 'online',
        createdAt: now,
        _updatedAt: now,
        services: {
            password: {
                // Хэш для пароля "owner123" (нужно будет поменять)
                bcrypt: '$2b$10$CJJxqr4BQX7HZGfMnqcxH.Y.m7lGzB0OjKxH9VH3I0rY7AYkEq6qW'
            }
        }
    });

    print('Создан пользователь owner');
} else {
    print('Пользователь owner уже существует');
}

// 3. Основные настройки сайта
const siteSettings = [
    { _id: 'Site_Name', value: 'Беседка Chat' },
    { _id: 'Language', value: 'ru' },
    { _id: 'Site_Url', value: 'http://127.0.0.1:3000' },
    { _id: 'From_Email', value: 'noreply@besedka.local' },
    { _id: 'SMTP_Host', value: '' },
    { _id: 'Accounts_RegistrationForm', value: 'Disabled' }
];

siteSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        { _id: setting._id },
        { $set: { value: setting.value } },
        { upsert: true }
    );
});

// 4. OAuth настройки для Беседки
const oauthSettings = [
    { _id: 'Accounts_OAuth_Custom-Besedka', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-url', value: 'http://127.0.0.1:8001' },
    { _id: 'Accounts_OAuth_Custom-Besedka-token_path', value: '/o/token/' },
    { _id: 'Accounts_OAuth_Custom-Besedka-identity_path', value: '/api/v1/auth/rocket/' },
    { _id: 'Accounts_OAuth_Custom-Besedka-authorize_path', value: '/o/authorize/' },
    { _id: 'Accounts_OAuth_Custom-Besedka-scope', value: 'read' },
    { _id: 'Accounts_OAuth_Custom-Besedka-id', value: 'OhyXGbFxYqzOIFgSvdZqgfbFqoXqRHOqKdxArWwp' },
    { _id: 'Accounts_OAuth_Custom-Besedka-secret', value: 'z0nI7QezCmekBMtoKXDdxzxVz6FxNvQfkv4kESZGP1XWYXGHFvEcVbIZU1TorncflOQEBfpXgYLJh4yffVQ8ha7RVjo0VE4h6DPlYhMYrb85WRt3GMdp4LWSsR5jiV0y' },
    { _id: 'Accounts_OAuth_Custom-Besedka-login_style', value: 'redirect' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_label_text', value: 'Войти через Беседку' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_label_color', value: '#FFFFFF' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_color', value: '#1d74f5' },
    { _id: 'Accounts_OAuth_Custom-Besedka-username_field', value: 'username' },
    { _id: 'Accounts_OAuth_Custom-Besedka-merge_users', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-show_button', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-avatar_field', value: 'avatar_url' },
    { _id: 'Accounts_OAuth_Custom-Besedka-email_field', value: 'email' },
    { _id: 'Accounts_OAuth_Custom-Besedka-name_field', value: 'full_name' },
    { _id: 'Accounts_OAuth_Custom-Besedka-roles_claim', value: 'roles' },
    { _id: 'Accounts_OAuth_Custom-Besedka-groups_claim', value: 'groups' },
    { _id: 'Accounts_OAuth_Custom-Besedka-map_channels', value: false },
    { _id: 'Accounts_OAuth_Custom-Besedka-merge_roles', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-roles_to_sync', value: 'admin,moderator,vip' },
    { _id: 'Accounts_OAuth_Custom-Besedka-groups_channel_map', value: '{"vip": "vip-chat"}' }
];

oauthSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        { _id: setting._id },
        { $set: { value: setting.value } },
        { upsert: true }
    );
});

// 5. Отключаем iframe ограничения
db.rocketchat_settings.updateOne(
    { _id: 'Restrict_access_inside_any_Iframe' },
    { $set: { value: false } }
);

// 6. Создаем каналы
const channels = [
    { name: 'general', displayName: 'Общий чат' },
    { name: 'vip-chat', displayName: 'VIP чат' }
];

channels.forEach(channel => {
    const existingChannel = db.rocketchat_room.findOne({ name: channel.name });
    if (!existingChannel) {
        db.rocketchat_room.insertOne({
            _id: channel.name,
            name: channel.name,
            fname: channel.displayName,
            t: 'c',
            msgs: 0,
            u: {
                _id: 'owner_user_id',
                username: 'owner'
            },
            ts: new Date(),
            ro: false,
            sysMes: true,
            _updatedAt: new Date()
        });
        print('Создан канал: ' + channel.name);
    } else {
        print('Канал уже существует: ' + channel.name);
    }
});

// 7. Проверяем результаты
print('\n=== РЕЗУЛЬТАТЫ НАСТРОЙКИ ===');
print('Setup Wizard: ' + db.rocketchat_settings.findOne({ _id: 'Show_Setup_Wizard' }).value);
print('OAuth включен: ' + db.rocketchat_settings.findOne({ _id: 'Accounts_OAuth_Custom-Besedka' }).value);
print('Пользователей: ' + db.users.countDocuments());
print('Каналов: ' + db.rocketchat_room.countDocuments());
print('Настроек: ' + db.rocketchat_settings.countDocuments());
