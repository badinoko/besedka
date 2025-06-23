// Простое исправление проблемы с кнопкой Join the Channel
db = db.getSiblingDB('rocketchat');

print('=== ИСПРАВЛЕНИЕ РОЛЕЙ ПОЛЬЗОВАТЕЛЕЙ ===');

// Проверяем текущие подписки
print('\nТекущие подписки:');
db.rocketchat_subscription.find().forEach(function(sub) {
    print('Пользователь: ' + sub.u.username + ', Канал: ' + sub.name + ', Роли: [' + sub.roles.join(', ') + ']');
});

// Исправляем роль admin в канале general (главная проблема)
print('\nИсправляем роль admin в канале general...');
var result1 = db.rocketchat_subscription.updateOne(
    {'u.username': 'admin', 'name': 'general'},
    {$set: {'roles': ['user'], 'joined': true, 'autoJoin': true}}
);
print('Обновлено записей admin/general: ' + result1.modifiedCount);

// Убеждаемся что owner правильно настроен
print('\nПроверяем настройки owner...');
var result2 = db.rocketchat_subscription.updateOne(
    {'u.username': 'owner', 'name': 'general'},
    {$set: {'roles': ['owner'], 'joined': true, 'autoJoin': true}}
);
print('Обновлено записей owner/general: ' + result2.modifiedCount);

var result3 = db.rocketchat_subscription.updateOne(
    {'u.username': 'owner', 'name': 'vip'},
    {$set: {'roles': ['owner', 'vip'], 'joined': true, 'autoJoin': true}}
);
print('Обновлено записей owner/vip: ' + result3.modifiedCount);

var result4 = db.rocketchat_subscription.updateOne(
    {'u.username': 'owner', 'name': 'moderators'},
    {$set: {'roles': ['owner', 'moderator'], 'joined': true, 'autoJoin': true}}
);
print('Обновлено записей owner/moderators: ' + result4.modifiedCount);

// Финальная проверка
print('\nФинальные подписки:');
db.rocketchat_subscription.find().forEach(function(sub) {
    print('Пользователь: ' + sub.u.username + ', Канал: ' + sub.name + ', Роли: [' + sub.roles.join(', ') + '], Joined: ' + sub.joined);
});

print('\n=== ИСПРАВЛЕНИЕ ЗАВЕРШЕНО ===');
