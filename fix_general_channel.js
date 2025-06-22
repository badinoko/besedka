print('🔧 ИСПРАВЛЕНИЕ НАСТРОЕК КАНАЛА GENERAL');
print('======================================');

// Найти канал GENERAL
var general = db.rocketchat_room.findOne({_id: 'GENERAL'});
if (!general) {
    print('❌ Канал GENERAL не найден!');
    quit();
}

print('✅ Канал GENERAL найден');
print('📊 Текущие настройки:');
print('   - sysMes: ' + JSON.stringify(general.sysMes || {}));
print('   - ro (только чтение): ' + (general.ro || false));
print('   - muted: ' + JSON.stringify(general.muted || []));

// Найти работающий канал VIP для сравнения
var vip = db.rocketchat_room.findOne({_id: 'vip'});
if (vip) {
    print('📋 Настройки VIP канала (рабочего):');
    print('   - sysMes: ' + JSON.stringify(vip.sysMes || {}));
    print('   - ro: ' + (vip.ro || false));
    print('   - muted: ' + JSON.stringify(vip.muted || []));
}

print('');
print('🔧 ПРИМЕНЯЮ ИСПРАВЛЕНИЯ...');

// ИСПРАВЛЕНИЕ 1: Установить sysMes как в рабочих каналах
var updateData = {
    $set: {
        'sysMes': true,
        '_updatedAt': new Date()
    }
};

// Убедиться что канал не только для чтения
if (general.ro) {
    updateData.$unset = { 'ro': 1 };
    print('✅ Убираю флаг "только для чтения"');
}

// Убедиться что канал не заглушен
if (general.muted && general.muted.length > 0) {
    updateData.$unset = updateData.$unset || {};
    updateData.$unset.muted = 1;
    print('✅ Убираю заглушение канала');
}

var result = db.rocketchat_room.updateOne(
    {_id: 'GENERAL'},
    updateData
);

if (result.modifiedCount > 0) {
    print('✅ Настройки канала GENERAL обновлены!');
} else {
    print('⚠️ Настройки уже были правильными');
}

// ИСПРАВЛЕНИЕ 2: Проверить подписку owner
var ownerSub = db.rocketchat_subscription.findOne({rid: 'GENERAL', 'u.username': 'owner'});
if (ownerSub && ownerSub.muted) {
    db.rocketchat_subscription.updateOne(
        {_id: ownerSub._id},
        {$unset: {muted: 1}, $set: {_updatedAt: new Date()}}
    );
    print('✅ Снято заглушение с пользователя owner в канале GENERAL');
}

// ИСПРАВЛЕНИЕ 3: Проверить права канала
print('');
print('🔍 ПРОВЕРКА ПРАВ КАНАЛА...');

// Найти настройки прав для канала
var permissions = db.rocketchat_permissions.find({}).toArray();
var channelPermissions = permissions.filter(function(p) {
    return p._id.indexOf('channel') !== -1 || p._id.indexOf('room') !== -1;
});

print('📋 Найдено прав для каналов: ' + channelPermissions.length);

// Проверить конкретные права на отправку сообщений
var postMessagePerm = db.rocketchat_permissions.findOne({_id: 'post-readonly'});
if (postMessagePerm) {
    print('🔍 Права на отправку в read-only каналах: ' + JSON.stringify(postMessagePerm.roles || []));
}

var editMessagePerm = db.rocketchat_permissions.findOne({_id: 'edit-message'});
if (editMessagePerm) {
    print('🔍 Права на редактирование сообщений: ' + JSON.stringify(editMessagePerm.roles || []));
}

print('');
print('✅ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ');
print('');
print('🔄 РЕКОМЕНДАЦИЯ: Перезагрузите Rocket.Chat для применения изменений');
print('   docker restart magic_beans_new-rocketchat-1');
