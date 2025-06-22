print('🚨 СРОЧНОЕ ИСПРАВЛЕНИЕ ПОДПИСОК');

// Найти пользователя owner
var owner = db.users.findOne({username: 'owner'});
if (!owner) {
    print('❌ Пользователь owner не найден!');
    quit();
}

print('✅ Пользователь owner найден: ' + owner._id);

// Создать подписки на все каналы
var channels = ['GENERAL', 'vip', 'moderators'];

channels.forEach(function(channelId) {
    var room = db.rocketchat_room.findOne({_id: channelId});
    if (room) {
        print('📝 Обрабатываю канал: ' + room.name);

        // Удалить старую подписку если есть
        db.rocketchat_subscription.deleteMany({
            rid: channelId,
            'u._id': owner._id
        });

        // Создать новую подписку
        var subscriptionId = owner._id + channelId;
        db.rocketchat_subscription.insertOne({
            _id: subscriptionId,
            u: {
                _id: owner._id,
                username: 'owner',
                name: 'owner'
            },
            rid: channelId,
            name: room.name,
            fname: room.name,
            t: 'c',
            ts: new Date(),
            ls: new Date(),
            lr: new Date(),
            f: false,
            open: true,
            alert: false,
            unread: 0,
            userMentions: 0,
            groupMentions: 0,
            _updatedAt: new Date()
        });

        print('✅ Подписка создана для: ' + room.name);
    }
});

// Проверить результат
var count = db.rocketchat_subscription.find({'u._id': owner._id}).count();
print('🎉 ГОТОВО! Создано подписок: ' + count);
