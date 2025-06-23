// ИСПРАВЛЕНИЕ НАЗВАНИЙ КАНАЛОВ ROCKET.CHAT
use rocketchat;

print("🔧 ИСПРАВЛЕНИЕ НАЗВАНИЙ КАНАЛОВ ROCKET.CHAT");
print("=" * 60);

print("\n📋 ТЕКУЩИЕ НАЗВАНИЯ (СЛОМАННЫЕ):");
db.rocketchat_room.find({t: "c"}, {_id: 1, name: 1, fname: 1}).forEach(function(doc) {
    print("   ID: " + doc._id + " | name: '" + (doc.name || "НЕТ") + "' | fname: '" + (doc.fname || "НЕТ") + "'");
});

print("\n🔧 ИСПРАВЛЕНИЕ...");

// 1. Исправляем канал general
var result1 = db.rocketchat_room.updateOne(
    {_id: "general"},
    {$set: {fname: "Общий"}}
);
print("✅ general: " + (result1.modifiedCount > 0 ? "ИСПРАВЛЕН" : "НЕ ИЗМЕНЕН"));

// 2. Исправляем канал vip
var result2 = db.rocketchat_room.updateOne(
    {_id: "vip"},
    {$set: {fname: "VIP"}}
);
print("✅ vip: " + (result2.modifiedCount > 0 ? "ИСПРАВЛЕН" : "НЕ ИЗМЕНЕН"));

// 3. Исправляем канал moderators (КРИТИЧЕСКАЯ ПРОБЛЕМА С КОДИРОВКОЙ)
var result3 = db.rocketchat_room.updateOne(
    {_id: "moderators"},
    {$set: {fname: "Модераторы"}}
);
print("✅ moderators: " + (result3.modifiedCount > 0 ? "ИСПРАВЛЕН" : "НЕ ИЗМЕНЕН"));

// 4. Исправляем подписки пользователей (fname в подписках тоже должны быть правильными)
print("\n🔧 ИСПРАВЛЕНИЕ ПОДПИСОК...");

// Исправляем fname в подписках для general
var sub1 = db.rocketchat_subscription.updateMany(
    {rid: "general"},
    {$set: {fname: "Общий"}}
);
print("✅ Подписки на general: исправлено " + sub1.modifiedCount);

// Исправляем fname в подписках для vip
var sub2 = db.rocketchat_subscription.updateMany(
    {rid: "vip"},
    {$set: {fname: "VIP"}}
);
print("✅ Подписки на vip: исправлено " + sub2.modifiedCount);

// Исправляем fname в подписках для moderators
var sub3 = db.rocketchat_subscription.updateMany(
    {rid: "moderators"},
    {$set: {fname: "Модераторы"}}
);
print("✅ Подписки на moderators: исправлено " + sub3.modifiedCount);

print("\n✅ ПРОВЕРКА РЕЗУЛЬТАТА:");
db.rocketchat_room.find({t: "c"}, {_id: 1, name: 1, fname: 1}).forEach(function(doc) {
    print("   ID: " + doc._id + " | name: '" + (doc.name || "НЕТ") + "' | fname: '" + (doc.fname || "НЕТ") + "'");
});

print("\n🎉 НАЗВАНИЯ КАНАЛОВ ИСПРАВЛЕНЫ!");
print("Теперь в Rocket.Chat должны отображаться:");
print("   📢 Общий");
print("   👑 VIP");
print("   🎭 Модераторы");
print("\nВместо сломанных названий с 'чат' и ромбиков ◊◊◊!");
