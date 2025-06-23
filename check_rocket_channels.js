// ДИАГНОСТИКА КАНАЛОВ ROCKET.CHAT
use rocketchat;

print("🚨 ДИАГНОСТИКА ПРОБЛЕМ С КАНАЛАМИ ROCKET.CHAT");
print("=" * 60);

print("\n📋 ВСЕ КАНАЛЫ В БАЗЕ:");
db.rocketchat_room.find({t: "c"}, {_id: 1, name: 1, fname: 1}).forEach(function(doc) {
    print("   ID: " + doc._id + " | name: '" + (doc.name || "НЕТ") + "' | fname: '" + (doc.fname || "НЕТ") + "'");
});

print("\n🎯 ОЖИДАЕМЫЕ КАНАЛЫ (ДОЛЖНЫ БЫТЬ):");
print("   ID: general | name: 'general' | fname: 'Общий'");
print("   ID: vip | name: 'vip' | fname: 'VIP'");
print("   ID: moderators | name: 'moderators' | fname: 'Модераторы'");

print("\n👤 ПОДПИСКИ ПОЛЬЗОВАТЕЛЯ admin:");
db.rocketchat_subscription.find({"u.username": "admin"}, {name: 1, fname: 1, rid: 1}).forEach(function(doc) {
    print("   Канал: '" + (doc.name || "НЕТ") + "' | fname: '" + (doc.fname || "НЕТ") + "' | RoomID: " + doc.rid);
});

print("\n🔍 ПОИСК ПРОБЛЕМНЫХ КАНАЛОВ:");
// Ищем каналы с проблемными названиями
db.rocketchat_room.find({t: "c", $or: [
    {name: {$regex: /◊/}},  // ромбики
    {fname: {$regex: /◊/}}, // ромбики в fname
    {name: {$regex: /[А-Я]/}}, // кириллица в name (должна быть только латиница)
    {name: null},  // пустые name
    {fname: null}  // пустые fname
]}).forEach(function(doc) {
    print("   ПРОБЛЕМНЫЙ КАНАЛ: ID=" + doc._id + ", name='" + (doc.name || "NULL") + "', fname='" + (doc.fname || "NULL") + "'");
});
