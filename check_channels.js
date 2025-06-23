// Проверка каналов в Rocket.Chat
use rocketchat;

print("=== КАНАЛЫ В БАЗЕ ===");
db.rocketchat_room.find({t: "c"}, {name: 1, _id: 1}).forEach(function(doc) {
    print("Канал: " + doc.name + " | ID: " + doc._id);
});

print("\n=== ПОДПИСКИ ПОЛЬЗОВАТЕЛЯ owner ===");
db.rocketchat_subscription.find({u: {$regex: "owner"}}, {name: 1, rid: 1, roles: 1}).forEach(function(doc) {
    print("Подписка: " + doc.name + " | RoomID: " + doc.rid + " | Roles: " + JSON.stringify(doc.roles));
});

print("\n=== НАСТРОЙКИ SETUP WIZARD ===");
db.rocketchat_settings.find({_id: "Show_Setup_Wizard"}, {value: 1}).forEach(function(doc) {
    print("Setup Wizard: " + doc.value);
});
