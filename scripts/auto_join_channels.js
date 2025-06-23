// Скрипт для автоматического присоединения пользователей к каналам
// Устраняет проблему с кнопкой "Join the Channel"
// Дата: 23 июня 2025

print("🚀 Начинаем настройку автоматического присоединения к каналам...");

const db = db.getSiblingDB('rocketchat');

// Получаем пользователя owner
const ownerUser = db.users.findOne({username: "owner"});
if (!ownerUser) {
    print("❌ Пользователь owner не найден!");
    quit();
}
print("✅ Найден пользователь owner:", ownerUser.username, ownerUser._id);

// Получаем все каналы
const channels = db.rocketchat_room.find({
    name: {$in: ["general", "vip", "moderators"]}
}, {
    name: 1,
    _id: 1,
    joinCodeRequired: 1,
    broadcast: 1,
    default: 1,
    t: 1
}).toArray();

print("📋 Найденные каналы:");
channels.forEach(channel => {
    print(`   - ${channel.name} (${channel._id})`);
    print(`     Type: ${channel.t}, JoinCode: ${channel.joinCodeRequired}, Default: ${channel.default}`);
});

// РЕШЕНИЕ 1: Убираем требование кода присоединения для всех каналов
print("\n🔧 РЕШЕНИЕ 1: Убираем joinCodeRequired для всех каналов");
const result1 = db.rocketchat_room.updateMany(
    {name: {$in: ["general", "vip", "moderators"]}},
    {$unset: {joinCodeRequired: 1}}
);
print(`✅ Обновлено каналов: ${result1.modifiedCount}`);

// РЕШЕНИЕ 2: Делаем general канал дефолтным для автоматического присоединения
print("\n🔧 РЕШЕНИЕ 2: Делаем general канал дефолтным");
const result2 = db.rocketchat_room.updateOne(
    {name: "general"},
    {$set: {default: true}}
);
print(`✅ General канал сделан дефолтным: ${result2.modifiedCount > 0}`);

// РЕШЕНИЕ 3: Автоматически создаем подписки для owner на все каналы (если их нет)
print("\n🔧 РЕШЕНИЕ 3: Проверяем и создаем подписки для owner");

channels.forEach(channel => {
    const existingSub = db.rocketchat_subscription.findOne({
        "u._id": ownerUser._id,
        rid: channel._id
    });

    if (!existingSub) {
        const subscription = {
            _id: `${channel._id}${ownerUser._id}`,
            t: channel.t || "p",
            ts: new Date(),
            name: channel.name,
            fname: channel.name,
            rid: channel._id,
            open: true,
            alert: false,
            unread: 0,
            userMentions: 0,
            groupMentions: 0,
            u: {
                _id: ownerUser._id,
                username: ownerUser.username
            },
            roles: getChannelRoles(channel.name)
        };

        db.rocketchat_subscription.insertOne(subscription);
        print(`✅ Создана подписка для owner на канал ${channel.name}`);
    } else {
        print(`ℹ️ Подписка на канал ${channel.name} уже существует`);
    }
});

// Функция для определения ролей в канале
function getChannelRoles(channelName) {
    switch(channelName) {
        case "general":
            return ["owner"];
        case "vip":
            return ["owner", "vip"];
        case "moderators":
            return ["owner", "moderator"];
        default:
            return [];
    }
}

// РЕШЕНИЕ 4: Настраиваем OAuth для автоматического присоединения
print("\n🔧 РЕШЕНИЕ 4: Настраиваем OAuth для автоматического присоединения к каналам");

const oauthSettings = [
    {
        _id: "Accounts_OAuth_Custom-BesedkaRocketChat2025-map_channels",
        value: true,
        type: "boolean"
    },
    {
        _id: "Accounts_OAuth_Custom-BesedkaRocketChat2025-channels_default",
        value: "general",
        type: "string"
    }
];

oauthSettings.forEach(setting => {
    const result = db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {value: setting.value, type: setting.type}},
        {upsert: true}
    );
    print(`✅ OAuth настройка ${setting._id}: ${setting.value}`);
});

print("\n🎯 ПРОВЕРКА РЕЗУЛЬТАТОВ:");

// Проверяем финальное состояние каналов
const updatedChannels = db.rocketchat_room.find({
    name: {$in: ["general", "vip", "moderators"]}
}, {
    name: 1,
    _id: 1,
    joinCodeRequired: 1,
    default: 1
}).toArray();

updatedChannels.forEach(channel => {
    print(`📋 ${channel.name}:`);
    print(`   - ID: ${channel._id}`);
    print(`   - Join Code Required: ${channel.joinCodeRequired || "НЕТ"}`);
    print(`   - Default: ${channel.default || false}`);
});

// Проверяем подписки owner
const ownerSubscriptions = db.rocketchat_subscription.find({
    "u._id": ownerUser._id
}, {
    name: 1,
    rid: 1,
    roles: 1
}).toArray();

print(`\n👤 Подписки пользователя owner (всего: ${ownerSubscriptions.length}):`);
ownerSubscriptions.forEach(sub => {
    print(`   - ${sub.name}: роли [${(sub.roles || []).join(", ")}]`);
});

print("\n✅ АВТОМАТИЧЕСКОЕ ПРИСОЕДИНЕНИЕ НАСТРОЕНО!");
print("📝 Изменения:");
print("   1. Убран код присоединения для всех каналов");
print("   2. General сделан дефолтным каналом");
print("   3. Созданы подписки с правильными ролями");
print("   4. Настроен OAuth маппинг каналов");
print("\n🎉 Кнопка 'Join the Channel' больше не должна появляться!");
