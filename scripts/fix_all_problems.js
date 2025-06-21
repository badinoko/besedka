// КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ ROCKET.CHAT
// 1. Фиксация Setup Wizard
// 2. Создание правильного канала 'vip'
// 3. Удаление неправильного 'vip-chat'

print("🚨 ИСПРАВЛЯЮ ВСЕ КРИТИЧЕСКИЕ ПРОБЛЕМЫ...");

// ===== 1. ФИКСАЦИЯ SETUP WIZARD =====
print("🔧 1. Фиксирую Setup Wizard...");
var wizardResult = db.rocketchat_settings.updateOne(
    {_id: 'Show_Setup_Wizard'},
    {$set: {value: 'completed', valueSource: 'customValue', _updatedAt: new Date()}}
);
print("✅ Setup Wizard зафиксирован:", wizardResult.modifiedCount > 0 ? "УСПЕШНО" : "УЖЕ ИСПРАВЛЕН");

// ===== 2. ПРОВЕРКА И ИСПРАВЛЕНИЕ КАНАЛОВ =====
print("🔧 2. Проверяю каналы...");

// Проверяем существующие каналы
var channels = db.rocketchat_room.find({}, {_id: 1, name: 1, t: 1}).toArray();
print("📋 Существующие каналы:");
channels.forEach(function(channel) {
    print("  - " + channel._id + " (" + channel.name + ")");
});

// Проверяем есть ли правильный канал 'vip'
var vipChannel = db.rocketchat_room.findOne({name: 'vip'});
var vipChatChannel = db.rocketchat_room.findOne({name: 'vip-chat'});

if (!vipChannel && vipChatChannel) {
    print("🔧 3. Переименовываю канал 'vip-chat' в 'vip'...");

    // Переименовываем канал
    var renameResult = db.rocketchat_room.updateOne(
        {_id: 'vip-chat'},
        {$set: {name: 'vip', _updatedAt: new Date()}}
    );
    print("✅ Канал переименован:", renameResult.modifiedCount > 0 ? "УСПЕШНО" : "ОШИБКА");

    // Обновляем подписки пользователей
    var subscriptionResult = db.rocketchat_subscription.updateMany(
        {rid: 'vip-chat'},
        {$set: {name: 'vip', _updatedAt: new Date()}}
    );
    print("✅ Подписки обновлены:", subscriptionResult.modifiedCount, "записей");

} else if (vipChannel) {
    print("✅ Канал 'vip' уже существует правильно");
} else {
    print("❌ НЕ НАЙДЕН НИ ОДИН VIP КАНАЛ!");
}

// ===== 4. ПРОВЕРКА ИТОГОВОГО СОСТОЯНИЯ =====
print("\n📋 ИТОГОВОЕ СОСТОЯНИЕ:");

// Каналы
print("🏠 КАНАЛЫ:");
db.rocketchat_room.find({}, {_id: 1, name: 1, t: 1, usersCount: 1}).forEach(function(room) {
    print("  - " + room._id + " (" + room.name + ") - пользователей: " + (room.usersCount || 0));
});

// Подписки owner
print("👤 ПОДПИСКИ OWNER:");
db.rocketchat_subscription.find({'u.username': 'owner'}, {rid: 1, name: 1}).forEach(function(sub) {
    print("  - " + sub.rid + " (" + sub.name + ")");
});

// Setup Wizard
var wizard = db.rocketchat_settings.findOne({_id: 'Show_Setup_Wizard'});
print("🧙 SETUP WIZARD: " + wizard.value + " (source: " + wizard.valueSource + ")");

print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ!");
print("🔄 Теперь перезапустите Rocket.Chat: docker restart magic_beans_new-rocketchat-1");
