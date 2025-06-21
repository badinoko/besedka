// ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ПОДПИСОК НА КАНАЛЫ

print('Исправляю подписки пользователя owner на все каналы...');

// Находим пользователя owner
const owner = db.users.findOne({ username: 'owner' });
if (!owner) {
    print('ОШИБКА: Пользователь owner не найден!');
    quit();
}

print('Найден пользователь: ' + owner.username + ' (ID: ' + owner._id + ')');

// Все каналы которые должны быть
const channels = [
    'GENERAL',
    'general',
    'vip',
    'vip-chat',
    'moderators'
];

// Проверяем какие каналы существуют
channels.forEach(channelId => {
    const room = db.rocketchat_room.findOne({ _id: channelId });
    if (room) {
        print('Канал существует: ' + room.name + ' (ID: ' + room._id + ')');

        // Проверяем подписку
        const subscription = db.rocketchat_subscription.findOne({
            'u._id': owner._id,
            rid: room._id
        });

        if (!subscription) {
            print('Создаю подписку на канал: ' + room.name);

            // Создаем подписку
            db.rocketchat_subscription.insertOne({
                _id: owner._id + room._id,
                u: {
                    _id: owner._id,
                    username: owner.username
                },
                rid: room._id,
                name: room.name,
                fname: room.fname || room.name,
                t: room.t,
                ts: new Date(),
                ls: new Date(),
                f: false,
                lr: new Date(),
                open: true,
                alert: false,
                roles: ['owner'],
                unread: 0,
                _updatedAt: new Date()
            });

            print('✅ Подписка создана для канала: ' + room.name);
        } else {
            print('Подписка уже существует для канала: ' + room.name);
        }
    } else {
        print('Канал НЕ НАЙДЕН: ' + channelId);
    }
});

print('\n=== ИТОГОВЫЙ СТАТУС ===');
print('Пользователь owner подписан на каналы:');
db.rocketchat_subscription.find({ 'u._id': owner._id }).forEach(sub => {
    print('- ' + sub.name + ' (ID: ' + sub.rid + ')');
});

print('\nГОТОВО! Все подписки исправлены!');
