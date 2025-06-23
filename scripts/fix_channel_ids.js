// Исправление ID каналов в MongoDB Rocket.Chat

// Исправляем канал GENERAL -> general
print('Исправляем канал GENERAL...');
var generalData = db.rocketchat_room.findOne({_id: 'GENERAL'});
if (generalData) {
    generalData._id = 'general';
    db.rocketchat_room.deleteOne({_id: 'GENERAL'});
    db.rocketchat_room.insertOne(generalData);

    // Обновляем подписки
    var subResult = db.rocketchat_subscription.updateMany({rid: 'GENERAL'}, {$set: {rid: 'general'}});
    print('Обновлено подписок: ' + subResult.modifiedCount);

    // Обновляем сообщения
    var msgResult = db.rocketchat_message.updateMany({rid: 'GENERAL'}, {$set: {rid: 'general'}});
    print('Обновлено сообщений: ' + msgResult.modifiedCount);

    print('Канал GENERAL исправлен на general');
} else {
    print('Канал GENERAL не найден');
}

// Исправляем канал vip-chat -> vip
print('Исправляем канал vip-chat...');
var vipData = db.rocketchat_room.findOne({_id: 'vip-chat'});
if (vipData) {
    vipData._id = 'vip';
    vipData.name = 'vip';
    db.rocketchat_room.deleteOne({_id: 'vip-chat'});
    db.rocketchat_room.insertOne(vipData);

    // Обновляем подписки
    var subResult = db.rocketchat_subscription.updateMany({rid: 'vip-chat'}, {$set: {rid: 'vip'}});
    print('Обновлено подписок: ' + subResult.modifiedCount);

    // Обновляем сообщения
    var msgResult = db.rocketchat_message.updateMany({rid: 'vip-chat'}, {$set: {rid: 'vip'}});
    print('Обновлено сообщений: ' + msgResult.modifiedCount);

    print('Канал vip-chat исправлен на vip');
} else {
    print('Канал vip-chat не найден');
}

// Проверяем результат
print('\nИтоговая структура каналов:');
db.rocketchat_room.find({}, {_id:1, name:1, fname:1}).forEach(printjson);
