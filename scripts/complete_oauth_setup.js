print("🚀 Прямая запись полной конфигурации OAuth в MongoDB...");

const settings = [
    {_id: "Accounts_OAuth_Custom-besedka", value: true},
    {_id: "Accounts_OAuth_Custom-besedka-url", value: "http://127.0.0.1:8001"},
    {_id: "Accounts_OAuth_Custom-besedka-token_path", value: "/o/token/"},
    {_id: "Accounts_OAuth_Custom-besedka-token_sent_via", value: "header"},
    {_id: "Accounts_OAuth_Custom-besedka-identity_token_sent_via", value: "header"},
    {_id: "Accounts_OAuth_Custom-besedka-identity_path", value: "/api/v1/auth/rocket/"},
    {_id: "Accounts_OAuth_Custom-besedka-authorize_path", value: "/o/authorize/"},
    {_id: "Accounts_OAuth_Custom-besedka-scope", value: "read"},
    {_id: "Accounts_OAuth_Custom-besedka-access_token_param", value: "access_token"},
    {_id: "Accounts_OAuth_Custom-besedka-id", value: "BesedkaRocketChat2025"},
    {_id: "Accounts_OAuth_Custom-besedka-secret", value: "SecureSecretKey2025BesedkaRocketChatSSO"},
    {_id: "Accounts_OAuth_Custom-besedka-login_style", value: "redirect"},
    {_id: "Accounts_OAuth_Custom-besedka-button_text", value: "Войти через Беседку"},
    {_id: "Accounts_OAuth_Custom-besedka-button_text_color", value: "#FFFFFF"},
    {_id: "Accounts_OAuth_Custom-besedka-button_color", value: "#28a745"},
    {_id: "Accounts_OAuth_Custom-besedka-username_field", value: "username"},
    {_id: "Accounts_OAuth_Custom-besedka-email_field", value: "email"},
    {_id: "Accounts_OAuth_Custom-besedka-name_field", value: "display_name"},
    {_id: "Accounts_OAuth_Custom-besedka-avatar_field", value: "avatar_url"},
    {_id: "Accounts_OAuth_Custom-besedka-roles_claim", value: "role"},
    {_id: "Accounts_OAuth_Custom-besedka-groups_claim", value: "groups"},
    {_id: "Accounts_OAuth_Custom-besedka-merge_users", value: true},
    {_id: "Accounts_OAuth_Custom-besedka-show_button", value: true},
    {_id: "Accounts_OAuth_Custom-besedka-map_channels", value: "groups"},
    {_id: "Accounts_OAuth_Custom-besedka-channel_map", value: '{"owner":["admin","vip"],"moderator":["admin"],"user":["user"]}'},
    {_id: "Accounts_OAuth_Custom-besedka-merge_roles", value: true},
    {_id: "Restrict_access_inside_any_Iframe", value: false}
];

let successCount = 0;
let errorCount = 0;

settings.forEach(setting => {
    try {
        const result = db.getCollection('rocketchat_settings').replaceOne(
            { _id: setting._id },
            {
                value: setting.value,
                type: typeof setting.value === 'boolean' ? 'boolean' : (typeof setting.value === 'number' ? 'int' : 'string'),
                _id: setting._id
            },
            { upsert: true }
        );
        if (result.acknowledged) {
            print(`✅ Настройка "${setting._id}" успешно создана/заменена.`);
            successCount++;
        } else {
            print(`❌ Ошибка записи настройки "${setting._id}".`);
            errorCount++;
        }
    } catch (e) {
        print(`❌ Исключение при записи "${setting._id}": ${e}`);
        errorCount++;
    }
});

print(`\n🎉 Конфигурация завершена! Успешно записано: ${successCount}. Ошибок: ${errorCount}.`);
print("‼️ Перезапустите Rocket.Chat для применения всех изменений.");
