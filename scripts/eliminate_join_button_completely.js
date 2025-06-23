// Финальный скрипт устранения кнопки "Join the Channel"
// Полностью убирает необходимость нажатия даже при первом входе
// Дата: 23 июня 2025

print("🚀 Финальное устранение кнопки Join the Channel...");

const db = db.getSiblingDB('rocketchat');

// РЕШЕНИЕ 1: Делаем все каналы полностью открытыми для подписанных пользователей
print("\n🔧 РЕШЕНИЕ 1: Настраиваем каналы для автоматического присоединения");

const channels = ['general', 'vip', 'moderators'];
channels.forEach(channelName => {
    const result = db.rocketchat_room.updateOne(
        {name: channelName},
        {
            $set: {
                joinCodeRequired: false,
                default: channelName === 'general',
                // Убираем ограничения на присоединение
                broadcast: false,
                // Автоматическое присоединение для подписанных
                autoJoin: true,
                // Разрешаем всем подписанным пользователям читать
                sysMes: false
            }
        }
    );
    print(`✅ Канал ${channelName} настроен: ${result.modifiedCount > 0}`);
});

// РЕШЕНИЕ 2: Создаем отсутствующих пользователей в Rocket.Chat
print("\n🔧 РЕШЕНИЕ 2: Создаем недостающих пользователей в Rocket.Chat");

const usersToCreate = [
    {
        username: 'admin',
        name: 'Admin User',
        emails: [{address: 'admin@besedka.com', verified: true}],
        roles: ['user'],
        active: true,
        type: 'user'
    },
    {
        username: 'store_owner',
        name: 'Store Owner',
        emails: [{address: 'store.owner@magicbeans.com', verified: true}],
        roles: ['user'],
        active: true,
        type: 'user'
    },
    {
        username: 'store_admin',
        name: 'Store Admin',
        emails: [{address: 'store.admin@magicbeans.com', verified: true}],
        roles: ['user'],
        active: true,
        type: 'user'
    },
    {
        username: 'test_user',
        name: 'Test User',
        emails: [{address: 'test.user@besedka.com', verified: true}],
        roles: ['user'],
        active: true,
        type: 'user'
    }
];

usersToCreate.forEach(userData => {
    const existingUser = db.users.findOne({username: userData.username});
    if (!existingUser) {
        userData._id = userData.username + '_' + new Date().getTime();
        userData.createdAt = new Date();
        userData.services = {};
        userData.status = 'online';

        const result = db.users.insertOne(userData);
        print(`✅ Создан пользователь: ${userData.username}`);
    } else {
        print(`ℹ️ Пользователь ${userData.username} уже существует`);
    }
});

// РЕШЕНИЕ 3: Автоматически подписываем всех пользователей на нужные каналы
print("\n🔧 РЕШЕНИЕ 3: Создаем подписки для всех пользователей");

const allUsers = db.users.find({type: 'user'}).toArray();
const allChannels = db.rocketchat_room.find({name: {$in: channels}}).toArray();

allUsers.forEach(user => {
    print(`👤 Обрабатываем пользователя: ${user.username}`);

    allChannels.forEach(channel => {
        // Определяем должен ли пользователь иметь доступ к каналу
        const shouldHaveAccess = getChannelAccess(user.username, channel.name);

        if (shouldHaveAccess) {
            const existingSub = db.rocketchat_subscription.findOne({
                "u._id": user._id,
                rid: channel._id
            });

            if (!existingSub) {
                const subscription = {
                    _id: `${channel._id}${user._id}`,
                    t: channel.t || "c",
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
                        _id: user._id,
                        username: user.username
                    },
                    roles: getUserRolesInChannel(user.username, channel.name),
                    // КРИТИЧЕСКИ ВАЖНО: автоматическое присоединение
                    autoJoin: true,
                    joined: true
                };

                db.rocketchat_subscription.insertOne(subscription);
                print(`  ✅ Подписан на ${channel.name}`);
            } else {
                // Обновляем существующую подписку
                db.rocketchat_subscription.updateOne(
                    {"u._id": user._id, rid: channel._id},
                    {$set: {autoJoin: true, joined: true}}
                );
                print(`  🔄 Обновлена подписка на ${channel.name}`);
            }
        }
    });
});

// Функция определения доступа к каналам
function getChannelAccess(username, channelName) {
    switch(channelName) {
        case 'general':
            return true; // Все имеют доступ к общему чату
        case 'vip':
            return username === 'owner'; // Только owner
        case 'moderators':
            return username === 'owner' || username === 'admin'; // Owner + admin
        default:
            return false;
    }
}

// Функция определения ролей в канале
function getUserRolesInChannel(username, channelName) {
    switch(channelName) {
        case 'general':
            return username === 'owner' ? ['owner'] : [];
        case 'vip':
            return username === 'owner' ? ['owner', 'vip'] : [];
        case 'moderators':
            return username === 'owner' ? ['owner', 'moderator'] :
                   username === 'admin' ? ['moderator'] : [];
        default:
            return [];
    }
}

// РЕШЕНИЕ 4: Глобальные настройки для полного устранения проблемы
print("\n🔧 РЕШЕНИЕ 4: Глобальные настройки Rocket.Chat");

const globalSettings = [
    {
        _id: "UI_Allow_room_names_with_special_chars",
        value: true,
        type: "boolean"
    },
    {
        _id: "Accounts_RegistrationForm_SecretURL",
        value: "",
        type: "string"
    },
    {
        _id: "UI_Use_Name_Avatar",
        value: true,
        type: "boolean"
    },
    // Автоматическое присоединение к каналам по умолчанию
    {
        _id: "Accounts_Default_User_Preferences_autoChannelJoin",
        value: true,
        type: "boolean"
    }
];

globalSettings.forEach(setting => {
    const result = db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {value: setting.value, type: setting.type}},
        {upsert: true}
    );
    print(`✅ Настройка ${setting._id}: ${setting.value}`);
});

print("\n🎯 ФИНАЛЬНАЯ ПРОВЕРКА:");

// Проверяем пользователей и их подписки
const finalUsers = db.users.find({type: 'user'}, {username: 1, _id: 1}).toArray();
print(`👥 Всего пользователей в Rocket.Chat: ${finalUsers.length}`);

finalUsers.forEach(user => {
    const subs = db.rocketchat_subscription.find({"u._id": user._id}, {name: 1, autoJoin: 1, joined: 1}).toArray();
    print(`   ${user.username}: ${subs.length} подписок`);
    subs.forEach(sub => {
        print(`     - ${sub.name}: autoJoin=${sub.autoJoin}, joined=${sub.joined}`);
    });
});

// Проверяем настройки каналов
const finalChannels = db.rocketchat_room.find({name: {$in: channels}}, {name: 1, autoJoin: 1, default: 1, joinCodeRequired: 1}).toArray();
finalChannels.forEach(channel => {
    print(`📋 ${channel.name}: autoJoin=${channel.autoJoin}, default=${channel.default}, joinCode=${channel.joinCodeRequired}`);
});

print("\n🎉 ФИНАЛЬНОЕ УСТРАНЕНИЕ ЗАВЕРШЕНО!");
print("📝 Теперь должно быть:");
print("   1. Все пользователи автоматически присоединены к нужным каналам");
print("   2. Кнопка Join the Channel не появляется НИКОГДА");
print("   3. Мгновенное переключение между всеми каналами");
print("   4. Правильное распределение ролей и доступов");
print("\n🚀 ROCKET.CHAT ГОТОВ К ПОЛНОЦЕННОМУ ИСПОЛЬЗОВАНИЮ!");
