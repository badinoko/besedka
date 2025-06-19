print("👻 Захватываем контроль над призрачным провайдером...");

// Мы не удаляем. Мы ЦЕЛЕНАПРАВЛЕННО настраиваем 'custom_besedka'.
var settings = [
    {_id: "Accounts_OAuth_Custom_custom_besedka", value: true},
    {_id: "Accounts_OAuth_Custom_custom_besedka_login_style", value: "redirect"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_url", value: "http://127.0.0.1:8001"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_token_path", value: "/o/token/"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_identity_path", value: "/api/v1/auth/rocket/identity/"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_authorize_path", value: "/o/authorize/"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_client_id", value: "BesedkaRocketChat2025"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_client_secret", value: "BesedkaRocketChatSecret2025VeryLongAndSecure"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_button_label_text", value: "Войти через Беседку"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_button_color", value: "#007bff"}, // Синий цвет
    {_id: "Accounts_OAuth_Custom_custom_besedka_button_label_color", value: "#FFFFFF"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_username_field", value: "username"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_email_field", value: "email"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_name_field", value: "username"},
    {_id: "Accounts_OAuth_Custom_custom_besedka_merge_users", value: true},
    {_id: "Accounts_OAuth_Custom_custom_besedka_show_button", value: true}
];

settings.forEach(function(setting) {
    db.getCollection('rocketchat_settings').updateOne(
        {_id: setting._id},
        {$set: { value: setting.value }},
        {upsert: true}
    );
});

print("✅ Настройки для 'custom_besedka' применены.");
print("‼️ Теперь необходимо перезапустить Rocket.Chat.");
