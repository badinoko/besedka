// ПРОВЕРКА И СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ OWNER В ROCKET.CHAT

print('🔍 ПРОВЕРКА ПОЛЬЗОВАТЕЛЕЙ В ROCKET.CHAT');

// Ищем всех пользователей
const allUsers = db.rocketchat_users.find({}, {username: 1, name: 1, active: 1}).toArray();
print(`✅ Всего пользователей в Rocket.Chat: ${allUsers.length}`);

if (allUsers.length > 0) {
    print('\n👥 СПИСОК ПОЛЬЗОВАТЕЛЕЙ:');
    allUsers.forEach(user => {
        print(`  - ${user.username} (${user.name || 'без имени'}) - ${user.active ? 'активен' : 'неактивен'}`);
    });
}

// Проверяем есть ли owner
const ownerUser = db.rocketchat_users.findOne({username: 'owner'});
if (ownerUser) {
    print(`\n✅ Пользователь owner найден: ${ownerUser._id}`);
} else {
    print('\n❌ Пользователь owner НЕ НАЙДЕН! Создаю...');

    // Создаем пользователя owner
    const newUser = {
        _id: 'owner_' + new Date().getTime(),
        username: 'owner',
        name: 'Владелец',
        emails: [{
            address: 'owner@besedka.local',
            verified: true
        }],
        active: true,
        type: 'user',
        roles: ['user', 'admin'],
        avatarOrigin: 'none',
        settings: {
            preferences: {
                language: 'ru'
            }
        },
        createdAt: new Date(),
        _updatedAt: new Date()
    };

    // Вставляем пользователя
    db.rocketchat_users.insertOne(newUser);
    print(`✅ Пользователь owner создан с ID: ${newUser._id}`);

    // Создаем подписки на все каналы
    const channels = db.rocketchat_room.find({t: 'c'}).toArray();
    print(`\n📧 Создаю подписки на ${channels.length} каналов:`);

    channels.forEach(channel => {
        const subscription = {
            _id: newUser._id + channel._id,
            u: {
                _id: newUser._id,
                username: newUser.username,
                name: newUser.name
            },
            rid: channel._id,
            name: channel.name,
            fname: channel.fname || channel.name,
            t: channel.t,
            open: true,
            alert: false,
            unread: 0,
            roles: ['owner'],
            _updatedAt: new Date(),
            ts: new Date()
        };

        db.rocketchat_subscription.insertOne(subscription);
        print(`  ✅ Подписка на канал ${channel.name} создана`);
    });
}

// Финальная проверка
print('\n🎯 ФИНАЛЬНАЯ ПРОВЕРКА:');
const finalOwner = db.rocketchat_users.findOne({username: 'owner'});
if (finalOwner) {
    print(`✅ Пользователь owner существует: ${finalOwner._id}`);

    // Проверяем подписки
    const subscriptions = db.rocketchat_subscription.find({
        'u.username': 'owner'
    }).toArray();
    print(`✅ Подписок у owner: ${subscriptions.length}`);

    subscriptions.forEach(sub => {
        print(`  - ${sub.name} (${sub.rid})`);
    });
} else {
    print('❌ Пользователь owner ВСЕ ЕЩЕ НЕ НАЙДЕН!');
}

print('\nГОТОВО!');
