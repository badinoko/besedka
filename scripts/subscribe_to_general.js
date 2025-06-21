// КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Подписка на канал GENERAL

print('Подписываю пользователя owner на канал GENERAL...');

const owner = db.users.findOne({ username: 'owner' });
if (!owner) {
    print('ОШИБКА: Пользователь owner не найден!');
    quit();
}

const generalRoom = db.rocketchat_room.findOne({ _id: 'GENERAL' });
if (!generalRoom) {
    print('ОШИБКА: Канал GENERAL не найден!');
    quit();
}

// Проверяем подписку
const existingSubscription = db.rocketchat_subscription.findOne({
    'u._id': owner._id,
    rid: 'GENERAL'
});

if (!existingSubscription) {
    print('Создаю подписку на канал GENERAL...');

    db.rocketchat_subscription.insertOne({
        _id: owner._id + 'GENERAL',
        u: {
            _id: owner._id,
            username: owner.username
        },
        rid: 'GENERAL',
        name: 'general',
        fname: 'general',
        t: 'c',
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

    print('✅ ПОДПИСКА НА GENERAL СОЗДАНА!');
} else {
    print('Подписка на GENERAL уже существует');
}

// Проверяем итоговый результат
print('\n=== ФИНАЛЬНЫЙ СТАТУС ===');
print('Пользователь owner подписан на каналы:');
db.rocketchat_subscription.find({ 'u._id': owner._id }).forEach(sub => {
    print('- ' + sub.name + ' (ID: ' + sub.rid + ')');
});

print('\nТеперь переключение каналов должно работать!');
