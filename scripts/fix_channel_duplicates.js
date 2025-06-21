// Скрипт для исправления дублированных подписок в Rocket.Chat
// Использование: docker exec magic_beans_new-mongo-1 mongosh rocketchat < fix_channel_duplicates.js

print("=== ИСПРАВЛЕНИЕ ДУБЛИРОВАННЫХ ПОДПИСОК ===");

// 1. Показать текущие подписки
print("\n--- ТЕКУЩИЕ ПОДПИСКИ ---");
db.rocketchat_subscription.find().forEach(function(s) {
    print("Подписка: " + s.name + " (ID: " + s._id + ", RID: " + s.rid + ")");
});

// 2. Найти пользователя owner
var owner = db.rocketchat_user.findOne({username: "owner"});
if (!owner) {
    print("ОШИБКА: Пользователь owner не найден!");
    quit();
}

print("\nПользователь owner найден: " + owner._id);

// 3. Удалить ВСЕ подписки пользователя owner
print("\n--- УДАЛЕНИЕ ВСЕХ ПОДПИСОК OWNER ---");
var deleteResult = db.rocketchat_subscription.deleteMany({"u._id": owner._id});
print("Удалено подписок: " + deleteResult.deletedCount);

// 4. Найти корректные каналы
var generalRoom = db.rocketchat_room.findOne({name: "general"});
var vipRoom = db.rocketchat_room.findOne({name: "vip"});
var moderatorsRoom = db.rocketchat_room.findOne({name: "moderators"});

if (!generalRoom) print("ОШИБКА: Канал general не найден!");
if (!vipRoom) print("ОШИБКА: Канал vip не найден!");
if (!moderatorsRoom) print("ОШИБКА: Канал moderators не найден!");

// 5. Создать правильные подписки
print("\n--- СОЗДАНИЕ ПРАВИЛЬНЫХ ПОДПИСОК ---");

// Подписка на general
if (generalRoom) {
    db.rocketchat_subscription.insertOne({
        _id: "owner-general-" + Date.now(),
        u: {_id: owner._id, username: owner.username},
        rid: generalRoom._id,
        name: generalRoom.name,
        t: "c",
        ts: new Date(),
        ls: new Date(),
        open: true,
        alert: false,
        unread: 0
    });
    print("✓ Создана подписка на general");
}

// Подписка на vip (ТОЛЬКО ОДНА!)
if (vipRoom) {
    db.rocketchat_subscription.insertOne({
        _id: "owner-vip-" + Date.now(),
        u: {_id: owner._id, username: owner.username},
        rid: vipRoom._id,
        name: vipRoom.name,
        t: "c",
        ts: new Date(),
        ls: new Date(),
        open: true,
        alert: false,
        unread: 0
    });
    print("✓ Создана подписка на vip");
}

// Подписка на moderators
if (moderatorsRoom) {
    db.rocketchat_subscription.insertOne({
        _id: "owner-moderators-" + Date.now(),
        u: {_id: owner._id, username: owner.username},
        rid: moderatorsRoom._id,
        name: moderatorsRoom.name,
        t: "c",
        ts: new Date(),
        ls: new Date(),
        open: true,
        alert: false,
        unread: 0
    });
    print("✓ Создана подписка на moderators");
}

// 6. Проверить результат
print("\n--- ФИНАЛЬНЫЕ ПОДПИСКИ ---");
db.rocketchat_subscription.find().forEach(function(s) {
    print("Подписка: " + s.name + " (ID: " + s._id + ", RID: " + s.rid + ")");
});

var finalCount = db.rocketchat_subscription.find().count();
print("\nИтого подписок: " + finalCount + " (должно быть 3)");

if (finalCount === 3) {
    print("✅ УСПЕХ: Дублированные подписки исправлены!");
} else {
    print("❌ ОШИБКА: Неправильное количество подписок!");
}

print("\n=== ГОТОВО ===");
