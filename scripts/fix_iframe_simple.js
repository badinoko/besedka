// Скрипт для включения iframe поддержки в Rocket.Chat
// Выполняется напрямую в MongoDB через docker exec

print("🔧 Исправляю iframe настройки...");

// Включаем iframe send
var result1 = db.rocketchat_settings.updateOne(
    {_id: 'Iframe_Integration_send_enable'},
    {$set: {value: true, valueSource: 'customValue', _updatedAt: new Date()}}
);
print("✅ Iframe_Integration_send_enable:", result1.modifiedCount > 0 ? "ВКЛЮЧЕН" : "УЖЕ ВКЛЮЧЕН");

// Включаем iframe receive
var result2 = db.rocketchat_settings.updateOne(
    {_id: 'Iframe_Integration_receive_enable'},
    {$set: {value: true, valueSource: 'customValue', _updatedAt: new Date()}}
);
print("✅ Iframe_Integration_receive_enable:", result2.modifiedCount > 0 ? "ВКЛЮЧЕН" : "УЖЕ ВКЛЮЧЕН");

// Устанавливаем send target origin
var result3 = db.rocketchat_settings.updateOne(
    {_id: 'Iframe_Integration_send_target_origin'},
    {$set: {value: '*', valueSource: 'customValue', _updatedAt: new Date()}}
);
print("✅ Iframe_Integration_send_target_origin:", result3.modifiedCount > 0 ? "УСТАНОВЛЕН" : "УЖЕ УСТАНОВЛЕН");

// Устанавливаем receive origin
var result4 = db.rocketchat_settings.updateOne(
    {_id: 'Iframe_Integration_receive_origin'},
    {$set: {value: '*', valueSource: 'customValue', _updatedAt: new Date()}}
);
print("✅ Iframe_Integration_receive_origin:", result4.modifiedCount > 0 ? "УСТАНОВЛЕН" : "УЖЕ УСТАНОВЛЕН");

print("\n🎉 IFRAME ПОДДЕРЖКА ВКЛЮЧЕНА!");
print("🔄 Теперь нужно перезапустить Rocket.Chat:");
print("   docker restart magic_beans_new-rocketchat-1");

// Проверяем результат
print("\n📋 Текущие iframe настройки:");
db.rocketchat_settings.find({section: 'Iframe_Integration'}).forEach(function(doc) {
    print("  " + doc._id + ": " + doc.value);
});
