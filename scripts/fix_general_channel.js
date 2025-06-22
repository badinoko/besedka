// Исправление канала general
print("=== ИСПРАВЛЕНИЕ КАНАЛА GENERAL ===");

// Обновляем название канала general
const result = db.rocketchat_room.updateOne(
    {_id: 'GENERAL'},
    {$set: {fname: 'Общий чат'}}
);

print("✅ Результат обновления канала general:", result.modifiedCount);

// Проверяем результат
const updatedRoom = db.rocketchat_room.findOne({_id: 'GENERAL'});
print("📋 Обновленный канал:");
print("   ID:", updatedRoom._id);
print("   Name:", updatedRoom.name);
print("   Fname:", updatedRoom.fname);

print("\n🎉 КАНАЛ GENERAL ИСПРАВЛЕН!");
