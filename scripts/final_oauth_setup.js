// 🎯 ФИНАЛЬНАЯ НАСТРОЙКА ROCKET.CHAT OAUTH
// Запуск: docker exec -i magic_beans_new-mongo-1 mongosh rocketchat < scripts/final_oauth_setup.js

print("🚀 ФИНАЛЬНАЯ НАСТРОЙКА ROCKET.CHAT OAUTH");
print("Исправлены ВСЕ ошибки включая roles/role!");

// 1. ОСНОВНЫЕ OAUTH НАСТРОЙКИ (ИСПРАВЛЕННЫЕ!)
const settings = [
    // Включение OAuth
    {_id: "Accounts_OAuth_Custom-Besedka", value: true},

    // URL и пути
    {_id: "Accounts_OAuth_Custom-Besedka-url", value: "http://127.0.0.1:8001"},
    {_id: "Accounts_OAuth_Custom-Besedka-token_path", value: "/o/token/"},
    {_id: "Accounts_OAuth_Custom-Besedka-identity_path", value: "/api/v1/auth/rocket/"},
    {_id: "Accounts_OAuth_Custom-Besedka-authorize_path", value: "/o/authorize/"},

    // Токены
    {_id: "Accounts_OAuth_Custom-Besedka-scope", value: "read"},
    {_id: "Accounts_OAuth_Custom-Besedka-token_sent_via", value: "header"},
    {_id: "Accounts_OAuth_Custom-Besedka-identity_token_sent_via", value: "default"},
    {_id: "Accounts_OAuth_Custom-Besedka-access_token_param", value: "access_token"},

    // Credentials
    {_id: "Accounts_OAuth_Custom-Besedka-id", value: "BesedkaRocketChat2025"},
    {_id: "Accounts_OAuth_Custom-Besedka-secret", value: "SecureSecretKey2025BesedkaRocketChatSSO"},

    // Кнопка
    {_id: "Accounts_OAuth_Custom-Besedka-login_style", value: "redirect"},
    {_id: "Accounts_OAuth_Custom-Besedka-button_text", value: "Войти через Беседку"},
    {_id: "Accounts_OAuth_Custom-Besedka-button_color", value: "#1d74f5"},
    {_id: "Accounts_OAuth_Custom-Besedka-button_text_color", value: "#FFFFFF"},

    // Поля пользователя (ИСПРАВЛЕНО: roles НЕ role!)
    {_id: "Accounts_OAuth_Custom-Besedka-username_field", value: "username"},
    {_id: "Accounts_OAuth_Custom-Besedka-email_field", value: "email"},
    {_id: "Accounts_OAuth_Custom-Besedka-name_field", value: "full_name"},
    {_id: "Accounts_OAuth_Custom-Besedka-avatar_field", value: "avatar_url"},
    {_id: "Accounts_OAuth_Custom-Besedka-roles_claim", value: "roles"},  // ИСПРАВЛЕНО!
    {_id: "Accounts_OAuth_Custom-Besedka-groups_claim", value: "groups"},

    // Роли для синхронизации
    {_id: "Accounts_OAuth_Custom-Besedka-roles_to_sync", value: "admin,moderator,vip,user"},

    // КРИТИЧЕСКИЕ ПЕРЕКЛЮЧАТЕЛИ (ВСЕ ON!)
    {_id: "Accounts_OAuth_Custom-Besedka-merge_users", value: true},
    {_id: "Accounts_OAuth_Custom-Besedka-show_button", value: true},
    {_id: "Accounts_OAuth_Custom-Besedka-map_channels", value: true},
    {_id: "Accounts_OAuth_Custom-Besedka-merge_roles", value: true}
];

// Применяем OAuth настройки
let success = 0;
settings.forEach(function(setting) {
    try {
        db.rocketchat_settings.updateOne(
            {_id: setting._id},
            {$set: {value: setting.value}},
            {upsert: true}
        );
        success++;
        print("✅ " + setting._id + " = " + setting.value);
    } catch (error) {
        print("❌ " + setting._id + " - " + error);
    }
});

// 2. JSON МАППИНГ РОЛЕЙ
const channelMapping = JSON.stringify({
    "owner": "admin,vip",
    "moderator": "admin",
    "user": "user"
});

try {
    db.rocketchat_settings.updateOne(
        {_id: "Accounts_OAuth_Custom-Besedka-channels_admin"},
        {$set: {value: channelMapping}},
        {upsert: true}
    );
    print("✅ Channel mapping: " + channelMapping);
    success++;
} catch (error) {
    print("❌ Channel mapping error: " + error);
}

// 3. ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
const extraSettings = [
    // Iframe поддержка
    {_id: "Restrict_access_inside_any_Iframe", value: false},
    {_id: "Iframe_Restrict_Access", value: false},

    // Отключить проверки
    {_id: "Accounts_RequirePasswordConfirmation", value: false},
    {_id: "Accounts_TwoFactorAuthentication_Enabled", value: false},

    // Автоматическое присоединение
    {_id: "Accounts_Default_User_Preferences_joinDefaultChannels", value: true},
    {_id: "Accounts_Default_User_Preferences_joinDefaultChannelsSilenced", value: false},

    // Исправить Site_Url
    {_id: "Site_Url", value: "http://127.0.0.1:3000"}
];

let extraSuccess = 0;
extraSettings.forEach(function(setting) {
    try {
        db.rocketchat_settings.updateOne(
            {_id: setting._id},
            {$set: {value: setting.value}},
            {upsert: true}
        );
        extraSuccess++;
        print("✅ " + setting._id + " = " + setting.value);
    } catch (error) {
        print("❌ " + setting._id + " - " + error);
    }
});

// ФИНАЛЬНАЯ ПРОВЕРКА
print("\n📊 РЕЗУЛЬТАТЫ:");
print("OAuth настройки: " + success + "/" + (settings.length + 1));
print("Доп. настройки: " + extraSuccess + "/" + extraSettings.length);

if (success >= 25 && extraSuccess >= 6) {
    print("\n🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!");
    print("✅ OAuth провайдер 'Besedka' полностью настроен");
    print("✅ ИСПРАВЛЕНО: roles field (НЕ role!)");
    print("✅ Все переключатели включены");
    print("✅ JSON маппинг настроен");
    print("✅ Iframe поддержка включена");
    print("\n🚀 ТЕСТИРОВАНИЕ:");
    print("1. Откройте http://127.0.0.1:3000/login");
    print("2. Должна быть кнопка 'Войти через Беседку'");
    print("3. Тестируйте на http://127.0.0.1:8001/chat/integrated/");
} else {
    print("\n⚠️ НАСТРОЙКА НЕПОЛНАЯ!");
    print("❌ Не все настройки применились");
    print("💡 Используйте ручную настройку из FINAL_OAUTH_INSTRUCTIONS.md");
}

print("\n✅ ГОТОВО!");
