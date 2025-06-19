// ЯДЕРНЫЙ СБРОС OAUTH - удаляем ВСЁ и настраиваем заново
print("🔥 ЯДЕРНЫЙ СБРОС OAUTH НАСТРОЕК...");

// 1. Удаляем ВСЕ OAuth настройки
var result = db.rocketchat_settings.deleteMany({_id: /OAuth_Custom/});
print("Удалено OAuth настроек: " + result.deletedCount);

// 2. Очищаем возможный кеш сессий OAuth
try {
    db.rocketchat_oauth_apps.drop();
    print("Очищена коллекция oauth_apps");
} catch(e) {
    print("Коллекция oauth_apps не существует");
}

// 3. Ждем
print("\n⏳ Ожидание очистки кеша...");

// 4. Создаем ОДИН правильный провайдер
print("\n🔧 Создание ЕДИНСТВЕННОГО провайдера 'Besedka'...");

var settings = [
    {_id: "Accounts_OAuth_Custom_Besedka", value: true},
    {_id: "Accounts_OAuth_Custom_Besedka_login_style", value: "redirect"}, // НЕ POPUP!
    {_id: "Accounts_OAuth_Custom_Besedka_url", value: "http://127.0.0.1:8001"},
    {_id: "Accounts_OAuth_Custom_Besedka_token_path", value: "/o/token/"},
    {_id: "Accounts_OAuth_Custom_Besedka_identity_path", value: "/api/v1/auth/rocket/identity/"},
    {_id: "Accounts_OAuth_Custom_Besedka_authorize_path", value: "/o/authorize/"},
    {_id: "Accounts_OAuth_Custom_Besedka_id", value: "BesedkaRocketChat2025"},
    {_id: "Accounts_OAuth_Custom_Besedka_secret", value: "BesedkaRocketChatSecret2025VeryLongAndSecure"},
    {_id: "Accounts_OAuth_Custom_Besedka_button_label_text", value: "Войти через Беседку"},
    {_id: "Accounts_OAuth_Custom_Besedka_button_label_color", value: "#FFFFFF"},
    {_id: "Accounts_OAuth_Custom_Besedka_button_color", value: "#007bff"},
    {_id: "Accounts_OAuth_Custom_Besedka_username_field", value: "username"},
    {_id: "Accounts_OAuth_Custom_Besedka_email_field", value: "email"},
    {_id: "Accounts_OAuth_Custom_Besedka_name_field", value: "username"},
    {_id: "Accounts_OAuth_Custom_Besedka_merge_users", value: true},
    {_id: "Accounts_OAuth_Custom_Besedka_show_button", value: true},
    {_id: "Accounts_OAuth_Custom_Besedka_scope", value: "rocketchat"},
    {_id: "Accounts_OAuth_Custom_Besedka_key_field", value: "username"}
];

settings.forEach(function(setting) {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: setting},
        {upsert: true}
    );
});

print("\n✅ Создан провайдер 'Besedka' с login_style = redirect");

// 5. Проверяем результат
var check = db.rocketchat_settings.findOne({_id: "Accounts_OAuth_Custom_Besedka_login_style"});
print("\nПроверка login_style: " + check.value);

print("\n🚀 ТРЕБУЕТСЯ ПЕРЕЗАПУСК ROCKET.CHAT!");
