// Проверка пользователей в Rocket.Chat
use rocketchat;

print("=== ПОЛЬЗОВАТЕЛИ В СИСТЕМЕ ===");
db.rocketchat_users.find({}, {username: 1, name: 1, roles: 1}).forEach(function(doc) {
    print("User: " + doc.username + " | Name: " + (doc.name || "N/A") + " | Roles: " + JSON.stringify(doc.roles));
});

print("\n=== ВСЕ ПОДПИСКИ В СИСТЕМЕ ===");
db.rocketchat_subscription.find({}, {u: 1, name: 1, rid: 1, roles: 1}).forEach(function(doc) {
    print("User: " + JSON.stringify(doc.u) + " | Room: " + doc.name + " | RoomID: " + doc.rid + " | Roles: " + JSON.stringify(doc.roles));
});
