// Проверка подписок пользователя owner
print("=== ПРОВЕРКА ПОДПИСОК ПОЛЬЗОВАТЕЛЯ OWNER ===");

// Найти пользователя owner
const user = db.users.findOne({username: "owner"});
if (!user) {
    print("❌ Пользователь owner не найден!");
    quit();
}

print("✅ Пользователь найден: " + user.username + " (ID: " + user._id + ")");

// Найти все подписки пользователя
const subscriptions = db.rocketchat_subscription.find({
    "u._id": user._id
}).toArray();

print("📊 Количество подписок: " + subscriptions.length);
print("");

if (subscriptions.length === 0) {
    print("❌ У пользователя НЕТ подписок на каналы!");
} else {
    print("📋 ПОДПИСКИ ПОЛЬЗОВАТЕЛЯ:");
    subscriptions.forEach(function(sub) {
        print("  - Канал: " + sub.name + " (ID: " + sub.rid + ")");
        print("    Тип: " + sub.t);
        print("    Роль: " + (sub.roles ? sub.roles.join(", ") : "user"));
        print("    Открыт: " + sub.open);
        print("");
    });
}

// Найти все доступные каналы
print("📋 ВСЕ ДОСТУПНЫЕ КАНАЛЫ:");
const rooms = db.rocketchat_room.find({t: "c"}).toArray();
rooms.forEach(function(room) {
    print("  - " + room.name + " (ID: " + room._id + ")");
});
