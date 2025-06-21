// Создание VIP и moderators каналов в Rocket.Chat
// Если каналы уже существуют, скрипт их пропустит

db = db.getSiblingDB('rocketchat');

// Функция для создания канала
function createChannel(name, displayName, isPrivate, description) {
    // Проверяем, существует ли канал
    const existing = db.rocketchat_room.findOne({name: name});
    if (existing) {
        print(`⚠️ Канал ${name} уже существует`);
        return;
    }

    // Создаем канал
    const channelId = new ObjectId();
    const now = new Date();

    db.rocketchat_room.insertOne({
        _id: channelId,
        fname: displayName,
        name: name,
        t: isPrivate ? "p" : "c", // p = private, c = channel
        u: {
            _id: "owner", // ID создателя
            username: "owner"
        },
        topic: description,
        muted: [],
        jitsiTimeout: now,
        default: false,
        sysMes: true,
        ro: false,
        msgs: 0,
        usersCount: 1,
        lm: now,
        _updatedAt: now,
        ts: now
    });

    print(`✅ Канал ${displayName} создан`);
}

// Создаем каналы
print("=== СОЗДАНИЕ КАНАЛОВ ===");

createChannel("vip", "VIP Беседка", true, "Приватный VIP чат для избранных пользователей");
createChannel("moderators", "Модераторы", true, "Приватный канал для администрации и модераторов");

// Настраиваем автоматическое присоединение к general каналу
db.rocketchat_settings.updateOne(
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannels' },
    { $set: { value: true } }
);

db.rocketchat_settings.updateOne(
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannelsSilenced' },
    { $set: { value: false } }
);

print("✅ Настройки автоматического присоединения обновлены");
print("✅ Все каналы готовы к использованию");
