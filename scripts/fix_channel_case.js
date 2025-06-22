// Исправление регистра канала GENERAL -> general
print("=== ИСПРАВЛЕНИЕ РЕГИСТРА КАНАЛА ===");

// Проверяем текущее состояние
print("📋 ТЕКУЩИЕ КАНАЛЫ:");
db.rocketchat_room.find({}, {_id: 1, name: 1}).forEach(room => {
    print(`   ${room.name} (ID: ${room._id})`);
});

// Находим канал GENERAL
const generalRoom = db.rocketchat_room.findOne({_id: 'GENERAL'});

if (!generalRoom) {
    print("❌ Канал GENERAL не найден");
} else {
    print("✅ Найден канал GENERAL, пересоздаем с ID 'general'");

    // Создаем копию с новым _id
    const newRoom = Object.assign({}, generalRoom);
    newRoom._id = 'general';

    // Вставляем новую запись
    db.rocketchat_room.insertOne(newRoom);
    print("✅ Создан канал с ID 'general'");

    // Удаляем старую запись
    db.rocketchat_room.deleteOne({_id: 'GENERAL'});
    print("✅ Удален старый канал GENERAL");

    // Обновляем подписки
    const subResult = db.rocketchat_subscription.updateMany(
        {rid: 'GENERAL'},
        {$set: {rid: 'general'}}
    );
    print("✅ Обновлено подписок:", subResult.modifiedCount);

    // Обновляем сообщения
    const msgResult = db.rocketchat_message.updateMany(
        {rid: 'GENERAL'},
        {$set: {rid: 'general'}}
    );
    print("✅ Обновлено сообщений:", msgResult.modifiedCount);
}

// Проверяем результат
print("\n📋 КАНАЛЫ ПОСЛЕ ИСПРАВЛЕНИЯ:");
db.rocketchat_room.find({}, {_id: 1, name: 1}).forEach(room => {
    print(`   ${room.name} (ID: ${room._id})`);
});

print("\n🎉 РЕГИСТР ИСПРАВЛЕН!");
