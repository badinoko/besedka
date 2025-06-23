// Скрипт для исправления проблемы с кнопкой "Join the Channel"
// Проблема: у некоторых пользователей пустые роли в подписках на каналы
// Решение: исправить роли согласно системе доступа проекта

print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С КНОПКОЙ 'JOIN THE CHANNEL'");
print("=" .repeat(60));

// Подключение к базе данных
use rocketchat;

// 1. Проверяем текущие подписки
print("\n📊 ТЕКУЩИЕ ПОДПИСКИ:");
var currentSubs = db.rocketchat_subscription.find({}, {
    u: 1,
    name: 1,
    roles: 1,
    joined: 1,
    autoJoin: 1
}).toArray();

currentSubs.forEach(function(sub) {
    print(`Пользователь: ${sub.u.username}, Канал: ${sub.name}, Роли: [${sub.roles.join(', ')}], Joined: ${sub.joined}`);
});

// 2. Исправляем роли согласно логике проекта
print("\n🛠️ ИСПРАВЛЕНИЕ РОЛЕЙ:");

// Логика ролей:
// owner: доступ ко всем каналам (general, vip, moderators) + соответствующие роли
// moderator (admin): доступ к general и moderators + роль moderator
// user: доступ только к general + роль user

var fixes = 0;

// Исправляем подписки пользователя owner
print("Исправляем пользователя 'owner'...");
var ownerResult1 = db.rocketchat_subscription.updateOne(
    {u: {username: 'owner'}, name: 'general'},
    {$set: {roles: ['owner'], joined: true, autoJoin: true}}
);
var ownerResult2 = db.rocketchat_subscription.updateOne(
    {u: {username: 'owner'}, name: 'vip'},
    {$set: {roles: ['owner', 'vip'], joined: true, autoJoin: true}}
);
var ownerResult3 = db.rocketchat_subscription.updateOne(
    {u: {username: 'owner'}, name: 'moderators'},
    {$set: {roles: ['owner', 'moderator'], joined: true, autoJoin: true}}
);

if (ownerResult1.modifiedCount > 0 || ownerResult2.modifiedCount > 0 || ownerResult3.modifiedCount > 0) {
    fixes++;
    print("✅ Роли пользователя 'owner' исправлены");
}

// Исправляем подписки пользователя admin (модератор)
print("Исправляем пользователя 'admin'...");
var adminResult1 = db.rocketchat_subscription.updateOne(
    {u: {username: 'admin'}, name: 'general'},
    {$set: {roles: ['user'], joined: true, autoJoin: true}} // admin как модератор имеет базовую роль user в общем чате
);
var adminResult2 = db.rocketchat_subscription.updateOne(
    {u: {username: 'admin'}, name: 'moderators'},
    {$set: {roles: ['moderator'], joined: true, autoJoin: true}}
);

// Удаляем подписку admin на VIP если есть (модератор не должен иметь доступ к VIP)
var adminVipRemoval = db.rocketchat_subscription.deleteMany({u: {username: 'admin'}, name: 'vip'});

if (adminResult1.modifiedCount > 0 || adminResult2.modifiedCount > 0 || adminVipRemoval.deletedCount > 0) {
    fixes++;
    print("✅ Роли пользователя 'admin' исправлены");
    if (adminVipRemoval.deletedCount > 0) {
        print("✅ Убран доступ admin к VIP каналу");
    }
}

// 3. Проверяем каналы на настройки autoJoin
print("\n🔧 ПРОВЕРКА НАСТРОЕК КАНАЛОВ:");
var channels = ['general', 'vip', 'moderators'];
channels.forEach(function(channelName) {
    var channel = db.rocketchat_room.findOne({name: channelName});
    if (channel) {
        var channelUpdated = false;
        var updateData = {};

        if (!channel.autoJoin) {
            updateData.autoJoin = true;
            channelUpdated = true;
        }
        if (channel.joinCodeRequired) {
            updateData.joinCodeRequired = false;
            channelUpdated = true;
        }
        if (channel.broadcast) {
            updateData.broadcast = false;
            channelUpdated = true;
        }

        if (channelUpdated) {
            db.rocketchat_room.updateOne({name: channelName}, {$set: updateData});
            print(`✅ Канал '${channelName}' настроен для автоматического присоединения`);
            fixes++;
        } else {
            print(`✅ Канал '${channelName}' уже настроен правильно`);
        }
    }
});

// 4. Финальная проверка
print("\n📊 ФИНАЛЬНОЕ СОСТОЯНИЕ ПОДПИСОК:");
var finalSubs = db.rocketchat_subscription.find({}, {
    u: 1,
    name: 1,
    roles: 1,
    joined: 1,
    autoJoin: 1
}).toArray();

finalSubs.forEach(function(sub) {
    print(`Пользователь: ${sub.u.username}, Канал: ${sub.name}, Роли: [${sub.roles.join(', ')}], Joined: ${sub.joined}`);
});

// 5. Резюме
print("\n" + "=" .repeat(60));
print(`🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО! Исправлено ${fixes} элементов`);
print("🎯 РЕЗУЛЬТАТ: Кнопка 'Join the Channel' должна исчезнуть");
print("📝 ЛОГИКА РОЛЕЙ:");
print("   - owner: все каналы (general, vip, moderators)");
print("   - admin: общий + модераторы (general, moderators)");
print("   - user: только общий (general)");
print("=" .repeat(60));
