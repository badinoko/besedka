// Полное исправление всех проблем с ролями пользователей
db = db.getSiblingDB('rocketchat');

print('=== ПОЛНОЕ ИСПРАВЛЕНИЕ ВСЕХ РОЛЕЙ ===');

// Исправляем всех пользователей с пустыми ролями в general канале
print('\nИсправляем пустые роли в канале general...');

// store_owner получает роль user в general
var result1 = db.rocketchat_subscription.updateOne(
    {'u.username': 'store_owner', 'name': 'general'},
    {$set: {'roles': ['user'], 'joined': true, 'autoJoin': true}}
);
print('Обновлено записей store_owner/general: ' + result1.modifiedCount);

// store_admin получает роль user в general
var result2 = db.rocketchat_subscription.updateOne(
    {'u.username': 'store_admin', 'name': 'general'},
    {$set: {'roles': ['user'], 'joined': true, 'autoJoin': true}}
);
print('Обновлено записей store_admin/general: ' + result2.modifiedCount);

// test_user получает роль user в general
var result3 = db.rocketchat_subscription.updateOne(
    {'u.username': 'test_user', 'name': 'general'},
    {$set: {'roles': ['user'], 'joined': true, 'autoJoin': true}}
);
print('Обновлено записей test_user/general: ' + result3.modifiedCount);

// Убеждаемся что у owner есть подписка на moderators
print('\nПроверяем подписку owner на moderators...');
var ownerModExists = db.rocketchat_subscription.findOne({'u.username': 'owner', 'name': 'moderators'});
if (!ownerModExists) {
    print('Создаем подписку owner на moderators...');
    // Нужно получить ID пользователя owner
    var ownerUser = db.rocketchat_subscription.findOne({'u.username': 'owner'});
    if (ownerUser) {
        var newSub = {
            '_id': ownerUser.u._id + '-moderators',
            't': 'c',
            'ts': new Date(),
            'name': 'moderators',
            'fname': 'Модераторы',
            'rid': 'moderators',
            'u': ownerUser.u,
            'open': true,
            'alert': false,
            'unread': 0,
            'roles': ['owner', 'moderator'],
            'ls': new Date(),
            '_updatedAt': new Date(),
            'groupMentions': 0,
            'userMentions': 0,
            'autoJoin': true,
            'joined': true
        };
        db.rocketchat_subscription.insertOne(newSub);
        print('Создана подписка owner на moderators');
    }
} else {
    // Обновляем существующую подписку
    var result4 = db.rocketchat_subscription.updateOne(
        {'u.username': 'owner', 'name': 'moderators'},
        {$set: {'roles': ['owner', 'moderator'], 'joined': true, 'autoJoin': true}}
    );
    print('Обновлено записей owner/moderators: ' + result4.modifiedCount);
}

// Финальная проверка всех подписок
print('\n=== ФИНАЛЬНЫЕ ПОДПИСКИ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ===');
db.rocketchat_subscription.find().sort({'u.username': 1, 'name': 1}).forEach(function(sub) {
    print('Пользователь: ' + sub.u.username + ', Канал: ' + sub.name + ', Роли: [' + sub.roles.join(', ') + '], Joined: ' + sub.joined);
});

print('\n=== ВСЕ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ ===');
