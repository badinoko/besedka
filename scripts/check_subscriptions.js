// Проверка подписок пользователя owner
print("=== ПРОВЕРКА ПОДПИСОК ПОЛЬЗОВАТЕЛЯ OWNER ===");

// Проверяем подписки
var subscriptions = db.rocketchat_subscription.find({u_id: 'owner'});
print("Найдено подписок:", subscriptions.count());

subscriptions.forEach(function(sub) {
    print("Канал ID:", sub.rid, "| Имя:", sub.name, "| Открыт:", sub.open);
});

print("\n=== ПРОВЕРКА КАНАЛОВ ===");
var channels = db.rocketchat_room.find({t: 'c'});
channels.forEach(function(room) {
    print("Канал:", room._id, "| Имя:", room.name, "| Тип:", room.t);
});

print("\n=== НАСТРОЙКИ АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ ===");
var autoJoinSetting = db.rocketchat_settings.findOne({_id: 'Accounts_Default_User_Preferences_joinDefaultChannels'});
if (autoJoinSetting) {
    print("Автоматическое присоединение:", autoJoinSetting.value);
} else {
    print("Настройка автоматического присоединения не найдена");
}
