// Скрипт для создания каналов VIP и Moderators в Rocket.Chat
// Запускать: docker exec -i magic_beans_new-mongo-1 mongo rocketchat < scripts/create_rocketchat_channels.js

// Переключаемся на базу данных Rocket.Chat
use rocketchat;

// Проверяем существующие каналы
print("=== ПРОВЕРКА СУЩЕСТВУЮЩИХ КАНАЛОВ ===");
var existingChannels = db.rocketchat_room.find({ t: { $in: ['c', 'p'] } }).toArray();
existingChannels.forEach(function(channel) {
    var type = channel.t === 'c' ? 'PUBLIC' : 'PRIVATE';
    print("Канал: " + channel.name + " (" + type + ", ID: " + channel._id + ")");
});

// Функция для создания канала
function createChannel(channelName, isPrivate, description) {
    var existing = db.rocketchat_room.findOne({ name: channelName });
    if (existing) {
        print("Канал '" + channelName + "' уже существует");
        return existing;
    }

    var roomId = channelName + Math.random().toString(36).substr(2, 9);
    var room = {
        _id: roomId,
        name: channelName,
        fname: channelName,
        t: isPrivate ? 'p' : 'c', // 'c' = public channel, 'p' = private group
        msgs: 0,
        usersCount: 0,
        u: {
            _id: "owner", // ID владельца
            username: "owner"
        },
        ts: new Date(),
        ro: false, // read-only
        sysMes: true,
        _updatedAt: new Date(),
        description: description
    };

    try {
        db.rocketchat_room.insert(room);
        print("✅ Канал '" + channelName + "' создан успешно (ID: " + roomId + ")");

        // Добавляем владельца в подписчики
        var subId = channelName + "_owner_sub";
        db.rocketchat_subscription.insert({
            _id: subId,
            open: true,
            alert: true,
            unread: 0,
            userMentions: 0,
            groupMentions: 0,
            ts: new Date(),
            rid: roomId,
            name: channelName,
            fname: channelName,
            t: isPrivate ? 'p' : 'c',
            u: {
                _id: "owner",
                username: "owner"
            },
            _updatedAt: new Date()
        });
        print("✅ Подписка для владельца создана (ID: " + subId + ")");

        return room;
    } catch (e) {
        print("❌ Ошибка создания канала '" + channelName + "': " + e);
        return null;
    }
}

// Создаем каналы
print("\n=== СОЗДАНИЕ НОВЫХ КАНАЛОВ ===");

// VIP канал (приватный)
createChannel("vip", true, "VIP чат для премиум пользователей проекта Беседка");

// Moderators канал (приватный)
createChannel("moderators", true, "Приватный канал для модераторов и администраторов");

// Проверяем результат
print("\n=== ФИНАЛЬНАЯ ПРОВЕРКА ===");
var finalChannels = db.rocketchat_room.find({ t: { $in: ['c', 'p'] } }).toArray();
print("Общее количество каналов: " + finalChannels.length);
finalChannels.forEach(function(channel) {
    var type = channel.t === 'c' ? 'PUBLIC' : 'PRIVATE';
    print("Канал: " + channel.name + " (" + type + ")");
});

// Настройка автоматического присоединения к каналу general
print("\n=== НАСТРОЙКА АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ ===");
var generalRoom = db.rocketchat_room.findOne({ name: "general" });
if (generalRoom) {
    db.rocketchat_room.update(
        { name: "general" },
        { $set: {
            "default": true,
            "featured": true
        }}
    );
    print("✅ Канал 'general' настроен как канал по умолчанию");
} else {
    print("❌ Канал 'general' не найден");
}

print("\n=== СОЗДАНИЕ ЗАВЕРШЕНО ===");
