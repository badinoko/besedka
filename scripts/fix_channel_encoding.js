// Скрипт для исправления кодировки описаний каналов Rocket.Chat
// Исправляет поломанные UTF-8 символы в описаниях каналов

print("=== ИСПРАВЛЕНИЕ КОДИРОВКИ КАНАЛОВ ===");

try {
    // Подключение к базе данных
    db = db.getSiblingDB('rocketchat');

    // Исправляем описание канала VIP
    const vipResult = db.rocketchat_room.updateOne(
        { _id: 'vip' },
        {
            $set: {
                description: 'Эксклюзивный VIP чат для премиум пользователей',
                fname: 'VIP'
            }
        }
    );
    print("VIP канал обновлен: " + vipResult.modifiedCount + " документов");

    // Исправляем описание канала модераторов
    const moderatorsResult = db.rocketchat_room.updateOne(
        { _id: 'moderators' },
        {
            $set: {
                description: 'Канал для модераторов и администраторов',
                fname: 'Модераторы'
            }
        }
    );
    print("Канал модераторов обновлен: " + moderatorsResult.modifiedCount + " документов");

    // Проверяем результат
    print("\n=== РЕЗУЛЬТАТ ОБНОВЛЕНИЯ ===");
    const channels = db.rocketchat_room.find({t: 'c'}, {name: 1, fname: 1, description: 1});

    channels.forEach(function(channel) {
        print("Канал: " + channel.name);
        print("  Название: " + (channel.fname || 'НЕТ'));
        print("  Описание: " + (channel.description || 'НЕТ'));
        print("---");
    });

    print("\n=== ИСПРАВЛЕНИЕ ЗАВЕРШЕНО ===");

} catch (error) {
    print("ОШИБКА: " + error.message);
}
