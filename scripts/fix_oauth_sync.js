// ИСПРАВЛЕНИЕ КРИТИЧЕСКОЙ ПРОБЛЕМЫ: синхронизация OAuth настроек
// Django Client ID: BesedkaRocketChat2025
// Rocket.Chat Client ID был: OhyXGbFxYqzOIFgSvdZqgfbFqoXqRHOqKdxArWwp

print("🔧 ИСПРАВЛЕНИЕ OAUTH СИНХРОНИЗАЦИИ");

// 1. Удаляем все старые OAuth настройки
db.rocketchat_settings.deleteMany({_id: /^Accounts_OAuth_Custom-Besedka/});

// 2. Создаем правильные настройки с Client ID из Django
const oauthSettings = [
    {_id: 'Accounts_OAuth_Custom-Besedka', value: true, type: 'boolean'},
    {_id: 'Accounts_OAuth_Custom-Besedka-url', value: 'http://127.0.0.1:8001', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-token_path', value: '/o/token/', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-identity_path', value: '/api/v1/auth/rocket/user/', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-authorize_path', value: '/o/authorize/', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-scope', value: 'read', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-id', value: 'BesedkaRocketChat2025', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-secret', value: 'SecureSecretKey2025BesedkaRocketChatSSO', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-button_label_text', value: 'Войти через Беседку', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-button_color', value: '#1d74f5', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-button_label_color', value: '#FFFFFF', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-login_style', value: 'redirect', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-username_field', value: 'username', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-email_field', value: 'email', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-name_field', value: 'name', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-avatar_field', value: 'avatar', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-roles_claim', value: 'roles', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-groups_claim', value: 'groups', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-channels_admin', value: 'admin,vip', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-show_button', value: true, type: 'boolean'},
    {_id: 'Accounts_OAuth_Custom-Besedka-merge_users', value: true, type: 'boolean'},
    {_id: 'Accounts_OAuth_Custom-Besedka-token_sent_via', value: 'header', type: 'string'},
    {_id: 'Accounts_OAuth_Custom-Besedka-identity_token_sent_via', value: 'default', type: 'string'}
];

// Добавляем все настройки
oauthSettings.forEach(setting => {
    setting.valueSource = 'customValue';
    setting.packageValue = false;
    setting._updatedAt = new Date();
    setting.hidden = false;
    setting.blocked = false;
    setting.sorter = 1;
    setting.i18nLabel = setting._id.replace('Accounts_OAuth_Custom-Besedka-', '');
    setting.autocomplete = true;
    setting.processEnvValue = undefined;
    setting.meteorSettingsValue = undefined;

    db.rocketchat_settings.insertOne(setting);
    print(`✅ Добавлена настройка: ${setting._id} = ${setting.value}`);
});

print("🎯 OAuth настройки синхронизированы!");
print("📋 Client ID теперь: BesedkaRocketChat2025");
print("🔗 Identity endpoint: /api/v1/auth/rocket/user/");
print("🌍 Authorization URL: http://127.0.0.1:8001/o/authorize/");
