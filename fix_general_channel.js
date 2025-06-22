// Скрипт для унификации канала General
// Переименовываем GENERAL в general для соответствия VIP и moderators

// Подключаемся к базе rocketchat
use rocketchat;

print("=== ИСПРАВЛЕНИЕ КАНАЛА GENERAL ===");

// Проверяем текущее состояние каналов
print("Текущие каналы:");
db.rocketchat_room.find({t: "c"}, {_id: 1, name: 1, fname: 1}).forEach(function(room) {
    print("ID: " + room._id + ", name: " + room.name + ", fname: " + room.fname);
});

// Проверяем существование канала GENERAL
var generalChannel = db.rocketchat_room.findOne({_id: "GENERAL"});
if (generalChannel) {
    print("Найден канал GENERAL, переименовываем в general...");

    // 1. Переименовываем сам канал
    db.rocketchat_room.updateOne(
        {_id: "GENERAL"},
        {
            $set: {
                _id: "general",
                name: "general",
                fname: "general"
            }
        }
    );

    // 2. Обновляем подписки пользователей
    db.rocketchat_subscription.updateMany(
        {rid: "GENERAL"},
        {$set: {rid: "general"}}
    );

    // 3. Обновляем сообщения
    db.rocketchat_message.updateMany(
        {rid: "GENERAL"},
        {$set: {rid: "general"}}
    );

    print("✅ Канал GENERAL переименован в general");
} else {
    print("Канал GENERAL не найден, проверяем general...");
    var generalLower = db.rocketchat_room.findOne({_id: "general"});
    if (generalLower) {
        print("✅ Канал general уже существует");
    } else {
        print("❌ Ни GENERAL, ни general не найдены!");
    }
}

// Показываем финальное состояние
print("Финальное состояние каналов:");
db.rocketchat_room.find({t: "c"}, {_id: 1, name: 1, fname: 1}).forEach(function(room) {
    print("ID: " + room._id + ", name: " + room.name + ", fname: " + room.fname);
});

print("=== ИСПРАВЛЕНИЕ ЗАВЕРШЕНО ===");
