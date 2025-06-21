// ИСПРАВЛЕНИЕ ID КАНАЛА GENERAL

print('🔧 ИСПРАВЛЕНИЕ ID КАНАЛА GENERAL...');

// Находим канал с ID "GENERAL"
const generalChannel = db.rocketchat_room.findOne({ _id: 'GENERAL' });

if (!generalChannel) {
    print('❌ Канал с ID "GENERAL" не найден!');
    quit();
}

print(`Найден канал: ${generalChannel.name} (ID: ${generalChannel._id})`);

// Проверяем, нет ли уже канала с ID "general"
const existingGeneral = db.rocketchat_room.findOne({ _id: 'general' });
if (existingGeneral) {
    print('❌ ОШИБКА: Канал с ID "general" уже существует!');
    print('   Нужно сначала удалить дублирующий канал');
    quit();
}

print('🔄 Изменяю ID канала с "GENERAL" на "general"...');

// Шаг 1: Создаем новый канал с правильным ID
const newChannelData = {
    ...generalChannel,
    _id: 'general'  // Новый ID
};

// Удаляем поля которые не нужно копировать
delete newChannelData._id;

// Создаем новый канал
db.rocketchat_room.insertOne({
    _id: 'general',
    name: generalChannel.name,
    t: generalChannel.t,
    usernames: generalChannel.usernames || [],
    msgs: generalChannel.msgs || 0,
    usersCount: generalChannel.usersCount || 0,
    ts: generalChannel.ts,
    ro: generalChannel.ro || false,
    default: true,
    sysMes: generalChannel.sysMes || true,
    _updatedAt: new Date()
});

// Шаг 2: Обновляем все подписки
print('🔄 Обновляю подписки пользователей...');
const subscriptions = db.rocketchat_subscription.find({ rid: 'GENERAL' }).toArray();

subscriptions.forEach(sub => {
    // Создаем новую подписку с правильным rid
    const newSubId = sub.u._id + 'general';

    db.rocketchat_subscription.insertOne({
        ...sub,
        _id: newSubId,
        rid: 'general',
        _updatedAt: new Date()
    });

    print(`  ✅ Обновлена подписка для ${sub.u.username}`);
});

// Шаг 3: Обновляем сообщения (если есть)
print('🔄 Обновляю сообщения канала...');
const messagesUpdated = db.rocketchat_message.updateMany(
    { rid: 'GENERAL' },
    { $set: { rid: 'general' } }
);
print(`  ✅ Обновлено сообщений: ${messagesUpdated.modifiedCount}`);

// Шаг 4: Удаляем старый канал и подписки
print('🗑️ Удаляю старый канал и подписки...');
db.rocketchat_subscription.deleteMany({ rid: 'GENERAL' });
db.rocketchat_room.deleteOne({ _id: 'GENERAL' });

print('✅ ГОТОВО! Канал general теперь имеет правильный ID: "general"');

// Проверяем результат
print('\n=== ПРОВЕРКА РЕЗУЛЬТАТА ===');
const updatedChannel = db.rocketchat_room.findOne({ _id: 'general' });
if (updatedChannel) {
    print(`✅ Канал: ${updatedChannel.name} (ID: ${updatedChannel._id})`);

    const subCount = db.rocketchat_subscription.countDocuments({ rid: 'general' });
    print(`✅ Подписок: ${subCount}`);

    const msgCount = db.rocketchat_message.countDocuments({ rid: 'general' });
    print(`✅ Сообщений: ${msgCount}`);
} else {
    print('❌ ОШИБКА: Канал не найден!');
}

print('\n🎉 ПЕРЕКЛЮЧЕНИЕ КАНАЛОВ ТЕПЕРЬ ДОЛЖНО РАБОТАТЬ!');
