// УДАЛЕНИЕ ДУБЛИРУЮЩЕГО VIP КАНАЛА

print('Очищаю дублирующие VIP каналы...');

const owner = db.users.findOne({ username: 'owner' });
if (!owner) {
    print('ОШИБКА: Пользователь owner не найден!');
    quit();
}

// Показываем текущие каналы
print('\n=== ТЕКУЩИЕ КАНАЛЫ ===');
db.rocketchat_room.find({ t: 'c' }).forEach(room => {
    const messageCount = db.rocketchat_message.find({ rid: room._id }).count();
    print(`Канал: ${room.name} (ID: ${room._id}, сообщений: ${messageCount})`);
});

// Удаляем канал vip-chat (дублирующий)
print('\nУдаляю дублирующий канал vip-chat...');

// Удаляем подписки на vip-chat
const vipChatSubscriptions = db.rocketchat_subscription.find({ rid: 'vip-chat' }).count();
if (vipChatSubscriptions > 0) {
    db.rocketchat_subscription.deleteMany({ rid: 'vip-chat' });
    print(`Удалено ${vipChatSubscriptions} подписок на vip-chat`);
}

// Удаляем сообщения из vip-chat
const vipChatMessages = db.rocketchat_message.find({ rid: 'vip-chat' }).count();
if (vipChatMessages > 0) {
    db.rocketchat_message.deleteMany({ rid: 'vip-chat' });
    print(`Удалено ${vipChatMessages} сообщений из vip-chat`);
}

// Удаляем сам канал vip-chat
const vipChatRoom = db.rocketchat_room.findOne({ _id: 'vip-chat' });
if (vipChatRoom) {
    db.rocketchat_room.deleteOne({ _id: 'vip-chat' });
    print('✅ Канал vip-chat удален!');
} else {
    print('Канал vip-chat не найден');
}

// Обеспечиваем что пользователь подписан на оставшиеся каналы
print('\nПроверяю подписки на оставшиеся каналы...');

const requiredChannels = ['GENERAL', 'vip', 'moderators'];
requiredChannels.forEach(channelId => {
    const room = db.rocketchat_room.findOne({ _id: channelId });
    if (room) {
        const subscription = db.rocketchat_subscription.findOne({
            'u._id': owner._id,
            rid: channelId
        });

        if (!subscription) {
            print(`Создаю подписку на канал: ${room.name}`);

            db.rocketchat_subscription.insertOne({
                _id: owner._id + channelId,
                u: {
                    _id: owner._id,
                    username: owner.username
                },
                rid: channelId,
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

            print(`✅ Подписка создана для канала: ${room.name}`);
        } else {
            print(`Подписка уже существует для канала: ${room.name}`);
        }
    }
});

print('\n=== ИТОГОВЫЕ КАНАЛЫ ===');
db.rocketchat_room.find({ t: 'c' }).forEach(room => {
    const messageCount = db.rocketchat_message.find({ rid: room._id }).count();
    print(`Канал: ${room.name} (ID: ${room._id}, сообщений: ${messageCount})`);
});

print('\n=== ПОДПИСКИ ПОЛЬЗОВАТЕЛЯ OWNER ===');
db.rocketchat_subscription.find({ 'u._id': owner._id }).forEach(sub => {
    print(`- ${sub.name} (ID: ${sub.rid})`);
});

print('\nГОТОВО! Дублирующий канал удален, подписки исправлены!');
