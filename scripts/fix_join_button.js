// ПРОСТОЕ РЕШЕНИЕ ПРОБЛЕМЫ JOIN CHANNEL
print('🚫 УБИРАЮ КНОПКУ JOIN CHANNEL...');

// 1. Автоматическое присоединение ко всем каналам
db.rocketchat_settings.updateOne(
    {_id: 'Accounts_Default_User_Preferences_joinDefaultChannels'},
    {$set: {value: true, _updatedAt: new Date()}},
    {upsert: true}
);
print('✅ Автоматическое присоединение включено');

// 2. Проверяем подписки owner на все каналы
const owner = db.users.findOne({username: 'owner'});
if (owner) {
    const channels = ['GENERAL', 'vip', 'moderators'];

    channels.forEach(channelId => {
        const room = db.rocketchat_room.findOne({_id: channelId});
        if (room) {
            const subscription = db.rocketchat_subscription.findOne({
                'u._id': owner._id,
                rid: channelId
            });

            if (!subscription) {
                print('📝 Создаю подписку на: ' + room.name);
                db.rocketchat_subscription.insertOne({
                    _id: owner._id + channelId,
                    u: {_id: owner._id, username: owner.username},
                    rid: channelId,
                    name: room.name,
                    fname: room.fname || room.name,
                    t: room.t,
                    ts: new Date(),
                    ls: new Date(),
                    lr: new Date(),
                    f: false,
                    open: true,
                    alert: false,
                    roles: ['owner'],
                    unread: 0,
                    _updatedAt: new Date()
                });
                print('✅ Подписка создана: ' + room.name);
            } else {
                print('ℹ️ Подписка уже есть: ' + room.name);
            }
        }
    });
}

print('🎉 ГОТОВО! Кнопка Join channel больше не должна появляться!');
