// ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ ЧАТА
print("🚀 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ ЧАТА");
print("=" . repeat(50));

// 1. Найти пользователя owner
const user = db.users.findOne({username: "owner"});
if (!user) {
    print("❌ Пользователь owner не найден!");
    quit();
}
print("✅ Пользователь найден:", user.username);

// 2. Найти все каналы
const channels = db.rocketchat_room.find({t: "c"}).toArray();
print("📋 Найдено каналов:", channels.length);

channels.forEach(function(channel) {
    print("  - " + channel.name + " (ID: " + channel._id + ")");
});

// 3. Удалить существующие подписки пользователя
const deletedSubs = db.rocketchat_subscription.deleteMany({
    "u._id": user._id
});
print("🗑️ Удалено старых подписок:", deletedSubs.deletedCount);

// 4. Создать новые подписки для всех каналов
let createdSubscriptions = 0;

channels.forEach(function(channel) {
    // Определить роли пользователя для канала
    let roles = ["owner"];
    if (channel.name === "vip" || channel._id === "vip") {
        roles.push("vip");
    }
    if (channel.name === "moderators" || channel._id === "moderators") {
        roles.push("moderator");
    }

    // Создать подписку
    const subscription = {
        "_id": new ObjectId(),
        "open": true,
        "alert": true,
        "unread": 0,
        "userMentions": 0,
        "groupMentions": 0,
        "ts": new Date(),
        "rid": channel._id,
        "name": channel.name,
        "fname": channel.fname || channel.name,
        "customFields": {},
        "t": "c",
        "u": {
            "_id": user._id,
            "username": user.username,
            "name": user.name || user.username
        },
        "ls": new Date(),
        "lr": new Date(),
        "roles": roles,
        "_updatedAt": new Date()
    };

    const result = db.rocketchat_subscription.insertOne(subscription);
    if (result.acknowledged) {
        print("✅ Создана подписка на канал:", channel.name);
        createdSubscriptions++;
    } else {
        print("❌ Ошибка создания подписки на канал:", channel.name);
    }
});

print("");
print("📊 ИТОГО СОЗДАНО ПОДПИСОК:", createdSubscriptions);

// 5. Проверка результата
print("");
print("🔍 ПРОВЕРКА РЕЗУЛЬТАТА:");
const finalSubscriptions = db.rocketchat_subscription.find({
    "u._id": user._id
}).toArray();

finalSubscriptions.forEach(function(sub) {
    print("  ✅ " + sub.name + " - роли: " + sub.roles.join(", "));
});

// 6. Убедиться, что пользователь является участником всех каналов
print("");
print("👥 ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ В УЧАСТНИКИ КАНАЛОВ:");

channels.forEach(function(channel) {
    // Добавить пользователя в массив usernames канала (если еще не добавлен)
    const updateResult = db.rocketchat_room.updateOne(
        { _id: channel._id },
        {
            $addToSet: {
                usernames: user.username,
                "u._id": user._id
            },
            $set: {
                msgs: channel.msgs || 0,
                usersCount: (channel.usersCount || 0) + 1,
                "_updatedAt": new Date()
            }
        }
    );

    if (updateResult.modifiedCount > 0) {
        print("  ✅ Добавлен в участники:", channel.name);
    } else {
        print("  ℹ️ Уже участник:", channel.name);
    }
});

print("");
print("🎉 ВСЕ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ!");
print("✅ Пользователь owner теперь автоматически подписан на все каналы");
print("✅ Больше не будет кнопки 'Join the Channel'");
print("✅ Поле ввода сообщений будет доступно");
print("");
print("🔄 Перезапустите Rocket.Chat для применения изменений:")
print("   docker-compose -f docker-compose.local.yml restart rocketchat");
