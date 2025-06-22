// ИСПРАВЛЕНИЕ ДУБЛИРОВАННЫХ ПОДПИСОК ПОЛЬЗОВАТЕЛЯ OWNER

print('🔧 ИСПРАВЛЕНИЕ ДУБЛИРОВАННЫХ ПОДПИСОК...');

// Найти пользователя owner
const owner = db.users.findOne({username: 'owner'});
if (!owner) {
    print('❌ Пользователь owner не найден!');
    quit();
}

print('✅ Пользователь owner найден: ' + owner._id);

// Найти все дублированные подписки
print('\n📋 АНАЛИЗ ТЕКУЩИХ ПОДПИСОК:');
const subscriptions = db.rocketchat_subscription.find({'u.username': 'owner'}).toArray();
subscriptions.forEach(s => {
    print(`  - Канал: ${s.name}, ID: ${s.rid}, Роли: ${JSON.stringify(s.roles || [])}`);
});

// Группировать подписки по каналам
const channelGroups = {};
subscriptions.forEach(sub => {
    if (!channelGroups[sub.rid]) {
        channelGroups[sub.rid] = [];
    }
    channelGroups[sub.rid].push(sub);
});

print('\n🗑️ УДАЛЕНИЕ ДУБЛИРОВАННЫХ ПОДПИСОК:');

Object.keys(channelGroups).forEach(channelId => {
    const subs = channelGroups[channelId];

    if (subs.length > 1) {
        print(`\n📝 Канал ${channelId} имеет ${subs.length} подписок - исправляю:`);

        // Удалить ВСЕ подписки для этого канала
        const deleteResult = db.rocketchat_subscription.deleteMany({
            'u._id': owner._id,
            rid: channelId
        });
        print(`  ✅ Удалено ${deleteResult.deletedCount} дублированных подписок`);

        // Создать ОДНУ правильную подписку
        const room = db.rocketchat_room.findOne({_id: channelId});
        if (room) {
            // Определить роли для канала
            let roles = ['owner'];
            if (channelId === 'vip') {
                roles.push('vip');
            }
            if (channelId === 'moderators') {
                roles.push('moderator');
            }

            const newSubscription = {
                _id: owner._id + channelId,
                u: {
                    _id: owner._id,
                    username: owner.username,
                    name: owner.name || 'owner'
                },
                rid: channelId,
                name: room.name,
                fname: room.fname || room.name,
                t: room.t,
                open: true,
                alert: false,
                unread: 0,
                userMentions: 0,
                groupMentions: 0,
                ts: new Date(),
                ls: new Date(),
                lr: new Date(),
                roles: roles,
                _updatedAt: new Date()
            };

            db.rocketchat_subscription.insertOne(newSubscription);
            print(`  ✅ Создана единая подписка с ролями: ${JSON.stringify(roles)}`);
        }
    } else {
        print(`✅ Канал ${channelId} - подписка уникальна`);
    }
});

// Применить настройки автоматического присоединения
print('\n⚙️ НАСТРОЙКА АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ:');

const autoJoinSettings = [
    {_id: 'Accounts_Default_User_Preferences_joinDefaultChannels', value: true},
    {_id: 'Accounts_OAuth_Custom-besedka-map_channels', value: true}
];

autoJoinSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {value: setting.value, _updatedAt: new Date()}},
        {upsert: true}
    );
    print(`✅ Настройка: ${setting._id} = ${setting.value}`);
});

// Проверить финальный результат
print('\n🎯 ФИНАЛЬНАЯ ПРОВЕРКА:');
const finalSubs = db.rocketchat_subscription.find({'u.username': 'owner'}).toArray();
finalSubs.forEach(s => {
    print(`  ✅ ${s.name}: роли ${JSON.stringify(s.roles || [])}`);
});

print('\n🎉 ГОТОВО! Дублированные подписки исправлены, кнопка Join Channel должна исчезнуть!')
