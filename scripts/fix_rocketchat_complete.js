// Комплексное исправление структуры Rocket.Chat
// Использование: Get-Content scripts/fix_rocketchat_complete.js | docker exec -i magic_beans_new-mongo-1 mongosh rocketchat --quiet

print("=== КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ ROCKET.CHAT ===");

// 1. ОЧИСТКА ВСЕХ ПОДПИСОК
print("\n1. Очистка всех подписок...");
var deletedSubs = db.rocketchat_subscription.deleteMany({});
print("Удалено подписок: " + deletedSubs.deletedCount);

// 2. УДАЛЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ (если есть)
print("\n2. Очистка пользователей...");
var deletedUsers = db.rocketchat_user.deleteMany({});
print("Удалено пользователей: " + deletedUsers.deletedCount);

// 3. СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ OWNER
print("\n3. Создание пользователя owner...");
var ownerUserId = "owner-" + Date.now();
var ownerUser = {
    _id: ownerUserId,
    username: "owner",
    name: "Owner",
    emails: [{address: "owner@besedka.local", verified: true}],
    type: "user",
    status: "online",
    active: true,
    roles: ["admin", "user", "owner"],
    requirePasswordChange: false,
    createdAt: new Date(),
    lastLogin: new Date(),
    statusConnection: "online",
    utcOffset: 3,
    settings: {}
};

db.rocketchat_user.insertOne(ownerUser);
print("✓ Пользователь owner создан с ID: " + ownerUserId);

// 4. ПОЛУЧЕНИЕ КАНАЛОВ
print("\n4. Проверка каналов...");
var generalRoom = db.rocketchat_room.findOne({name: "general"});
var vipRoom = db.rocketchat_room.findOne({name: "vip"});
var moderatorsRoom = db.rocketchat_room.findOne({name: "moderators"});

if (generalRoom) print("✓ Канал general найден: " + generalRoom._id);
if (vipRoom) print("✓ Канал vip найден: " + vipRoom._id);
if (moderatorsRoom) print("✓ Канал moderators найден: " + moderatorsRoom._id);

// 5. ИСПРАВЛЕНИЕ VIP КАНАЛА (добавление иконки)
if (vipRoom) {
    print("\n5. Исправление VIP канала...");
    db.rocketchat_room.updateOne(
        {_id: vipRoom._id},
        {$set: {
            description: "VIP чат для привилегированных пользователей",
            default: false,
            featured: true,
            customFields: {},
            avatarETag: "V"
        }}
    );
    print("✓ VIP канал обновлен");
}

// 6. СОЗДАНИЕ ПРАВИЛЬНЫХ ПОДПИСОК
print("\n6. Создание подписок для owner...");

// Подписка на general
if (generalRoom) {
    db.rocketchat_subscription.insertOne({
        _id: ownerUserId + "-general",
        u: {_id: ownerUserId, username: "owner"},
        rid: generalRoom._id,
        name: generalRoom.name,
        t: "c",
        ts: new Date(),
        ls: new Date(),
        open: true,
        alert: false,
        unread: 0,
        userMentions: 0,
        groupMentions: 0,
        f: true
    });
    print("✓ Подписка на general создана");
}

// Подписка на vip
if (vipRoom) {
    db.rocketchat_subscription.insertOne({
        _id: ownerUserId + "-vip",
        u: {_id: ownerUserId, username: "owner"},
        rid: vipRoom._id,
        name: vipRoom.name,
        t: "c",
        ts: new Date(),
        ls: new Date(),
        open: true,
        alert: false,
        unread: 0,
        userMentions: 0,
        groupMentions: 0,
        f: true
    });
    print("✓ Подписка на vip создана");
}

// Подписка на moderators
if (moderatorsRoom) {
    db.rocketchat_subscription.insertOne({
        _id: ownerUserId + "-moderators",
        u: {_id: ownerUserId, username: "owner"},
        rid: moderatorsRoom._id,
        name: moderatorsRoom.name,
        t: "c",
        ts: new Date(),
        ls: new Date(),
        open: true,
        alert: false,
        unread: 0,
        userMentions: 0,
        groupMentions: 0,
        f: true
    });
    print("✓ Подписка на moderators создана");
}

// 7. ОТКЛЮЧЕНИЕ РЕГИСТРАЦИИ
print("\n7. Настройка регистрации...");
db.rocketchat_settings.updateOne(
    {_id: "Accounts_RegistrationForm"},
    {$set: {value: "Disabled"}},
    {upsert: true}
);
print("✓ Регистрация отключена");

// 8. ФИНАЛЬНАЯ ПРОВЕРКА
print("\n=== ФИНАЛЬНАЯ ПРОВЕРКА ===");
var userCount = db.rocketchat_user.find().count();
var subCount = db.rocketchat_subscription.find().count();
var roomCount = db.rocketchat_room.find().count();

print("Пользователей: " + userCount + " (ожидается: 1)");
print("Подписок: " + subCount + " (ожидается: 3)");
print("Каналов: " + roomCount + " (ожидается: 3)");

if (userCount === 1 && subCount === 3 && roomCount === 3) {
    print("\n✅ УСПЕХ: Структура Rocket.Chat восстановлена!");
    print("В интерфейсе должно быть ровно 3 канала без дублирования");
} else {
    print("\n❌ ОШИБКА: Неправильная структура!");
}

print("\n=== ГОТОВО ===");
