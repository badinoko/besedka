// Полная очистка и перенастройка OAuth для Rocket.Chat
print("🧹 ПОЛНАЯ ОЧИСТКА ВСЕХ OAUTH ПРОВАЙДЕРОВ...");

// Удаляем ВСЕ Custom OAuth настройки
var deleteResult = db.rocketchat_settings.deleteMany({_id: /^Accounts_OAuth_Custom_/});
print("Удалено настроек: " + deleteResult.deletedCount);

// Ждем немного
print("\n⏳ Ожидание очистки...");

// Теперь создаем ТОЛЬКО ОДИН правильный OAuth провайдер
print("\n🔧 СОЗДАНИЕ ЕДИНСТВЕННОГО OAUTH ПРОВАЙДЕРА...");

var settings = {
    'Accounts_OAuth_Custom_Besedka': true,
    'Accounts_OAuth_Custom_Besedka_login_style': 'redirect',
    'Accounts_OAuth_Custom_Besedka_url': 'http://127.0.0.1:8001',
    'Accounts_OAuth_Custom_Besedka_token_path': '/o/token/',
    'Accounts_OAuth_Custom_Besedka_identity_path': '/api/v1/auth/rocket/identity/',
    'Accounts_OAuth_Custom_Besedka_authorize_path': '/o/authorize/',
    'Accounts_OAuth_Custom_Besedka_scope': 'rocketchat',
    'Accounts_OAuth_Custom_Besedka_id': 'BesedkaRocketChat2025',
    'Accounts_OAuth_Custom_Besedka_secret': 'SecureSecretKey2025BesedkaRocketChatSSO',
    'Accounts_OAuth_Custom_Besedka_button_label_text': 'Sign in with Besedka',
    'Accounts_OAuth_Custom_Besedka_button_label_color': '#FFFFFF',
    'Accounts_OAuth_Custom_Besedka_button_color': '#007bff',
    'Accounts_OAuth_Custom_Besedka_key_field': 'username',
    'Accounts_OAuth_Custom_Besedka_username_field': 'username',
    'Accounts_OAuth_Custom_Besedka_email_field': 'email',
    'Accounts_OAuth_Custom_Besedka_name_field': 'name',
    'Accounts_OAuth_Custom_Besedka_roles_claim': 'role',
    'Accounts_OAuth_Custom_Besedka_merge_users': true,
    'Accounts_OAuth_Custom_Besedka_show_button': true
};

// Применяем настройки
Object.keys(settings).forEach(function(key) {
    var result = db.rocketchat_settings.insertOne({
        _id: key,
        value: settings[key]
    });
    print("✅ " + key + " = " + settings[key]);
});

print("\n🔍 ПРОВЕРКА РЕЗУЛЬТАТА...");

// Считаем количество OAuth провайдеров
var count = db.rocketchat_settings.find({_id: /^Accounts_OAuth_Custom_/}).count();
print("Всего OAuth настроек: " + count);

// Проверяем login_style
var loginStyle = db.rocketchat_settings.findOne({_id: "Accounts_OAuth_Custom_Besedka_login_style"});
if (loginStyle && loginStyle.value === 'redirect') {
    print("✅ login_style = redirect");
} else {
    print("❌ login_style не настроен!");
}

// Проверяем button_label_text
var buttonText = db.rocketchat_settings.findOne({_id: "Accounts_OAuth_Custom_Besedka_button_label_text"});
if (buttonText) {
    print("✅ Текст кнопки: " + buttonText.value);
}

print("\n🎯 ИТОГ: Должна быть ТОЛЬКО ОДНА кнопка 'Sign in with Besedka'!");
print("Требуется перезапуск Rocket.Chat для применения изменений.");
