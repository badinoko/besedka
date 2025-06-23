// OAuth интеграция Django ↔ Rocket.Chat
print('🔐 НАСТРОЙКА OAUTH ИНТЕГРАЦИИ DJANGO ↔ ROCKET.CHAT...');

// Функция для безопасного обновления настроек
function updateSetting(id, value, type = 'string') {
    try {
        const result = db.rocketchat_settings.updateOne(
            {_id: id},
            {$set: {value: value, type: type}},
            {upsert: true}
        );
        print(`  ✅ ${id}: ${value}`);
        return result;
    } catch (error) {
        print(`  ❌ Ошибка настройки ${id}: ${error}`);
        return null;
    }
}

// ОСНОВНЫЕ OAuth НАСТРОЙКИ
print('\n🔧 Основные OAuth настройки...');
updateSetting('Accounts_OAuth_Custom-Besedka', true, 'boolean');
updateSetting('Accounts_OAuth_Custom-Besedka-enable', true, 'boolean');
updateSetting('Accounts_OAuth_Custom-Besedka-url', 'http://127.0.0.1:8001');
updateSetting('Accounts_OAuth_Custom-Besedka-token_path', '/api/v1/auth/rocket/');
updateSetting('Accounts_OAuth_Custom-Besedka-identity_path', '/api/v1/auth/rocket/user/');
updateSetting('Accounts_OAuth_Custom-Besedka-authorize_path', '/accounts/login/');
updateSetting('Accounts_OAuth_Custom-Besedka-scope', 'read');
updateSetting('Accounts_OAuth_Custom-Besedka-id', 'BesedkaRocketChat2025');
updateSetting('Accounts_OAuth_Custom-Besedka-secret', 'SecureSecretKey2025BesedkaRocketChatSSO');
updateSetting('Accounts_OAuth_Custom-Besedka-button_label_text', 'Войти через Беседку');
updateSetting('Accounts_OAuth_Custom-Besedka-button_label_color', '#FFFFFF');
updateSetting('Accounts_OAuth_Custom-Besedka-button_color', '#28a745');

// ПРОДВИНУТЫЕ НАСТРОЙКИ
print('\n⚙️ Продвинутые OAuth настройки...');
updateSetting('Accounts_OAuth_Custom-Besedka-login_style', 'popup');
updateSetting('Accounts_OAuth_Custom-Besedka-key_field', 'username');
updateSetting('Accounts_OAuth_Custom-Besedka-username_field', 'username');
updateSetting('Accounts_OAuth_Custom-Besedka-email_field', 'email');
updateSetting('Accounts_OAuth_Custom-Besedka-name_field', 'name');
updateSetting('Accounts_OAuth_Custom-Besedka-avatar_field', 'avatar');

// КРИТИЧЕСКИЕ НАСТРОЙКИ ДЛЯ ИНТЕГРАЦИИ
print('\n🎯 Критические настройки интеграции...');
updateSetting('Accounts_OAuth_Custom-Besedka-merge_users', true, 'boolean');
updateSetting('Accounts_OAuth_Custom-Besedka-show_button', true, 'boolean');
updateSetting('Accounts_OAuth_Custom-Besedka-map_channels', true, 'boolean');
updateSetting('Accounts_OAuth_Custom-Besedka-merge_roles', true, 'boolean');

// МАППИНГ РОЛЕЙ (JSON строка)
const roleMapping = {
    "owner": "admin,vip,user",
    "moderator": "admin,user",
    "store_owner": "user",
    "store_admin": "user",
    "user": "user"
};
updateSetting('Accounts_OAuth_Custom-Besedka-roles_claim', 'role');
updateSetting('Accounts_OAuth_Custom-Besedka-group_claim', 'role');
updateSetting('Accounts_OAuth_Custom-Besedka-channels_claim', 'channels');

// API НАСТРОЙКИ
print('\n📡 API настройки...');
updateSetting('API_Enable_CORS', true, 'boolean');
updateSetting('API_CORS_Origin', '*');
updateSetting('API_Embed', true, 'boolean');
updateSetting('API_Enabled', true, 'boolean');

// IFRAME И EMBEDDED НАСТРОЙКИ
print('\n🖼️ Iframe и embedded настройки...');
updateSetting('Iframe_Integration_send_enable', true, 'boolean');
updateSetting('Iframe_Integration_receive_enable', true, 'boolean');
updateSetting('Iframe_Restrict_Access', false, 'boolean');

// АВТОМАТИЧЕСКАЯ ПОДПИСКА НА КАНАЛЫ
print('\n🔄 Настройки автоматической подписки...');
updateSetting('Accounts_Default_User_Preferences_joinDefaultChannels', true, 'boolean');
updateSetting('Accounts_Registration_AuthenticationServices_Enabled', true, 'boolean');

// ОТКЛЮЧЕНИЕ ПРОБЛЕМНЫХ НАСТРОЕК
print('\n❌ Отключение проблемных настроек...');
updateSetting('First_Channel_After_Login', ''); // Убираем принудительный канал
updateSetting('Show_Setup_Wizard', 'completed'); // Навсегда отключаем Setup Wizard

// FINALIZE
print('\n🎉 OAuth интеграция настроена!');
print('📋 Django endpoint: http://127.0.0.1:8001/api/v1/auth/rocket/');
print('🔐 Client ID: BesedkaRocketChat2025');
print('🔑 Client Secret: SecureSecretKey2025BesedkaRocketChatSSO');
print('🔗 Кнопка "Войти через Беседку" должна появиться на /login');

// ПРОВЕРКА
print('\n🔍 Проверка настроек...');
const oauthEnabled = db.rocketchat_settings.findOne({_id: 'Accounts_OAuth_Custom-Besedka'});
const apiEnabled = db.rocketchat_settings.findOne({_id: 'API_Enabled'});
print(`OAuth включен: ${oauthEnabled ? oauthEnabled.value : 'НЕ НАЙДЕН'}`);
print(`API включен: ${apiEnabled ? apiEnabled.value : 'НЕ НАЙДЕН'}`);

print('\n✅ OAuth интеграция полностью настроена!');
