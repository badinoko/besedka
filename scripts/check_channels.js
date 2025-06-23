// Проверка всех каналов в Rocket.Chat
print("=== ПРОВЕРКА КАНАЛОВ ROCKET.CHAT ===");

// Находим все комнаты
const rooms = db.rocketchat_room.find({}, {_id: 1, name: 1, fname: 1, t: 1}).toArray();

print("\n📊 НАЙДЕНО КАНАЛОВ:", rooms.length);

rooms.forEach(room => {
    print(`\n🏠 Канал: ${room.name || 'unnamed'}`);
    print(`   ID: ${room._id}`);
    print(`   Название: ${room.fname || 'без названия'}`);
    print(`   Тип: ${room.t}`);
});

// Проверяем подписки пользователя owner
print("\n=== ПОДПИСКИ ПОЛЬЗОВАТЕЛЯ OWNER ===");

const subscriptions = db.rocketchat_subscription.find(
    {'u.username': 'owner'},
    {rid: 1, name: 1, fname: 1}
).toArray();

print("\n📊 ПОДПИСОК OWNER:", subscriptions.length);

subscriptions.forEach(sub => {
    print(`\n✅ Подписка на канал: ${sub.name || 'unnamed'}`);
    print(`   ID канала: ${sub.rid}`);
    print(`   Название: ${sub.fname || 'без названия'}`);
});

print("\n=== АНАЛИЗ ЗАВЕРШЕН ===");

// Быстрая проверка каналов и подписок
print("КАНАЛЫ:");
db.rocketchat_room.find({t:'c'}).forEach(function(doc) {
    print(doc._id + " | " + doc.name + " | ro:" + (doc.ro || false));
});

print("\nПОДПИСКИ owner:");
db.rocketchat_subscription.find({"u.username":"owner"}).forEach(function(doc) {
    print(doc.rid + " | " + doc.name + " | roles:" + (doc.roles || []));
});

print("\nНАСТРОЙКИ:");
const settings = ["Iframe_Restrict_Access", "Message_AllowEditing"];
settings.forEach(function(setting) {
    const s = db.rocketchat_settings.findOne({_id: setting});
    if (s) print(setting + ": " + s.value);
});
