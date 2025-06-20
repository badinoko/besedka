// Скрипт для настройки автоматического присоединения к каналу general
// Запускать: docker exec -i magic_beans_new-mongo-1 mongo rocketchat < scripts/setup_auto_join_general.js

// Переключаемся на базу данных Rocket.Chat
use rocketchat;

print("=== НАСТРОЙКА АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ К КАНАЛУ GENERAL ===");

// Находим канал general
var generalRoom = db.rocketchat_room.findOne({ name: "general" });
if (!generalRoom) {
    print("❌ Канал 'general' не найден!");
    exit;
}

print("✅ Канал 'general' найден (ID: " + generalRoom._id + ")");

// Настройки для автоматического присоединения
var autoJoinSettings = [
    {
        "_id": "Accounts_Default_User_Preferences_joinDefaultChannels",
        "value": true,
        "ts": new Date(),
        "_updatedAt": new Date()
    },
    {
        "_id": "Accounts_Default_User_Preferences_joinDefaultChannelsSilenced",
        "value": false,
        "ts": new Date(),
        "_updatedAt": new Date()
    },
    {
        "_id": "Accounts_Default_User_Preferences_autoImageLoad",
        "value": true,
        "ts": new Date(),
        "_updatedAt": new Date()
    }
];

// Применяем настройки
print("\n=== ПРИМЕНЕНИЕ НАСТРОЕК ===");
autoJoinSettings.forEach(function(setting) {
    try {
        db.rocketchat_settings.update(
            { "_id": setting._id },
            setting,
            { upsert: true }
        );
        print("✅ Настройка '" + setting._id + "' применена");
    } catch (e) {
        print("❌ Ошибка применения настройки '" + setting._id + "': " + e);
    }
});

// Устанавливаем канал general как канал по умолчанию
print("\n=== НАСТРОЙКА КАНАЛА GENERAL ===");
try {
    db.rocketchat_room.update(
        { name: "general" },
        {
            $set: {
                "default": true,
                "featured": true,
                "broadcast": false
            }
        }
    );
    print("✅ Канал 'general' настроен как канал по умолчанию");
} catch (e) {
    print("❌ Ошибка настройки канала 'general': " + e);
}

// Добавляем настройку для поля "Открыть канал после авторизации"
print("\n=== НАСТРОЙКА ОТКРЫТИЯ КАНАЛА ПОСЛЕ АВТОРИЗАЦИИ ===");
try {
    db.rocketchat_settings.update(
        { "_id": "Accounts_Default_User_Preferences_openMainChannel" },
        {
            "_id": "Accounts_Default_User_Preferences_openMainChannel",
            "value": "general",
            "ts": new Date(),
            "_updatedAt": new Date()
        },
        { upsert: true }
    );
    print("✅ Настройка открытия канала 'general' после авторизации применена");
} catch (e) {
    print("❌ Ошибка настройки открытия канала: " + e);
}

// Проверяем результат
print("\n=== ПРОВЕРКА РЕЗУЛЬТАТА ===");
var settings = db.rocketchat_settings.find({
    "_id": { $in: [
        "Accounts_Default_User_Preferences_joinDefaultChannels",
        "Accounts_Default_User_Preferences_joinDefaultChannelsSilenced",
        "Accounts_Default_User_Preferences_openMainChannel"
    ]}
}).toArray();

settings.forEach(function(setting) {
    print("Настройка: " + setting._id + " = " + setting.value);
});

var updatedRoom = db.rocketchat_room.findOne({ name: "general" });
print("Канал 'general' default: " + updatedRoom.default);
print("Канал 'general' featured: " + updatedRoom.featured);

print("\n=== НАСТРОЙКА ЗАВЕРШЕНА ===");
