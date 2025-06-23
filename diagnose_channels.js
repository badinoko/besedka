print('🔍 ДИАГНОСТИКА КАНАЛОВ ROCKET.CHAT');
print('=====================================');

// Найти все каналы
var channels = db.rocketchat_room.find({t: 'c'}).toArray();

print('📊 ВСЕГО КАНАЛОВ: ' + channels.length);
print('');

channels.forEach(function(room) {
    print('📝 КАНАЛ: ' + room.name + ' (ID: ' + room._id + ')');
    print('   - Тип: ' + room.t);
    print('   - Участников: ' + (room.usersCount || 0));
    print('   - Создан: ' + room.ts);
    print('   - Только для чтения: ' + (room.ro || false));
    print('   - Системные настройки: ' + JSON.stringify(room.sysMes || {}));
    print('   - Права на запись: ' + JSON.stringify(room.muted || []));

    // Найти подписки на этот канал
    var subscriptions = db.rocketchat_subscription.find({rid: room._id}).toArray();
    print('   - Подписок: ' + subscriptions.length);

    subscriptions.forEach(function(sub) {
        print('     * ' + sub.u.username + ' (' + sub.u._id + ')');
        print('       - Роли: ' + JSON.stringify(sub.roles || []));
        print('       - Muted: ' + (sub.muted || false));
        print('       - Права: ' + JSON.stringify(sub.permissions || {}));
    });

    print('');
});

// Проверить настройки канала GENERAL конкретно
print('🚨 ДЕТАЛЬНАЯ ДИАГНОСТИКА КАНАЛА GENERAL:');
var general = db.rocketchat_room.findOne({_id: 'GENERAL'});
if (general) {
    print('✅ Канал GENERAL найден');
    print('   - Полная структура: ' + JSON.stringify(general, null, 2));
} else {
    print('❌ Канал GENERAL не найден!');
}

// Проверить подписку owner на GENERAL
print('');
print('🔍 ПОДПИСКА OWNER НА GENERAL:');
var ownerSub = db.rocketchat_subscription.findOne({rid: 'GENERAL', 'u.username': 'owner'});
if (ownerSub) {
    print('✅ Подписка owner на GENERAL найдена');
    print('   - Полная структура: ' + JSON.stringify(ownerSub, null, 2));
} else {
    print('❌ Подписка owner на GENERAL не найдена!');
}

print('');
print('🎯 ДИАГНОСТИКА ЗАВЕРШЕНА');
