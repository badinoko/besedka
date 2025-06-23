// ИСПРАВЛЕНИЕ ПРОБЛЕМЫ GENERAL (заглавными) -> general (маленькими)
// Нельзя изменить _id, поэтому создаем новый канал и переносим данные

print("🚨 === ИСПРАВЛЕНИЕ ПРОБЛЕМЫ GENERAL -> general ===");

// 1. Проверяем текущее состояние
const oldChannel = db.rocketchat_room.findOne({_id: "GENERAL"});
const newChannel = db.rocketchat_room.findOne({_id: "general"});

if (!oldChannel) {
    print("❌ Канал GENERAL не найден!");
    quit(1);
}

if (newChannel) {
    print("❌ Канал general уже существует! Отмена операции.");
    quit(1);
}

print(`✅ Найден канал GENERAL: name="${oldChannel.name}", fname="${oldChannel.fname}"`);

// 2. Создаем новый канал с ID "general"
print("🔄 Создаем новый канал с ID 'general'...");

const generalChannelNew = {
    _id: "general",
    name: "general",
    fname: "Общий чат",
    t: "c",
    u: oldChannel.u,
    ts: oldChannel.ts || new Date(),
    ro: false,
    sysMes: true,
    default: true,
    msgs: oldChannel.msgs || 0,
    usersCount: oldChannel.usersCount || 1,
    lm: oldChannel.lm || new Date()
};

try {
    db.rocketchat_room.insertOne(generalChannelNew);
    print("✅ Канал 'general' создан успешно");
} catch (e) {
    print("❌ Ошибка создания канала:", e.message);
    quit(1);
}

// 3. Переносим все сообщения из GENERAL в general
print("🔄 Переносим сообщения из GENERAL в general...");
const msgResult = db.rocketchat_message.updateMany(
    {rid: "GENERAL"},
    {$set: {rid: "general"}}
);
print(`✅ Перенесено ${msgResult.modifiedCount} сообщений`);

// 4. Переносим подписки из GENERAL в general
print("🔄 Переносим подписки из GENERAL в general...");
const subscriptions = db.rocketchat_subscription.find({rid: "GENERAL"});

subscriptions.forEach(function(sub) {
    // Создаем новую подписку с правильным ID канала
    const newSub = {
        _id: sub.u._id + "-general", // новый _id для подписки
        u: sub.u,
        rid: "general", // новый ID канала
        name: "general",
        fname: "general",
        t: sub.t,
        ts: sub.ts,
        ls: sub.ls,
        open: sub.open,
        alert: sub.alert,
        roles: sub.roles,
        unread: sub.unread || 0,
        userMentions: sub.userMentions || 0,
        groupMentions: sub.groupMentions || 0
    };

    try {
        db.rocketchat_subscription.insertOne(newSub);
        print(`   ✅ Подписка перенесена для пользователя: ${sub.u.username}`);
    } catch (e) {
        print(`   ❌ Ошибка переноса подписки для ${sub.u.username}:`, e.message);
    }
});

// 5. Удаляем старые данные
print("🔄 Удаляем старые данные GENERAL...");

// Удаляем старые подписки
const oldSubsResult = db.rocketchat_subscription.deleteMany({rid: "GENERAL"});
print(`✅ Удалено ${oldSubsResult.deletedCount} старых подписок`);

// Удаляем старый канал
const oldChannelResult = db.rocketchat_room.deleteOne({_id: "GENERAL"});
print(`✅ Удален старый канал GENERAL`);

// 6. Финальная проверка
print("\n✅ === ФИНАЛЬНАЯ ПРОВЕРКА ===");

const finalChannel = db.rocketchat_room.findOne({_id: "general"});
if (finalChannel) {
    print(`✅ Канал 'general' работает: name="${finalChannel.name}", fname="${finalChannel.fname}"`);
} else {
    print("❌ ОШИБКА: Канал 'general' не найден!");
}

const finalSubs = db.rocketchat_subscription.find({rid: "general"}).count();
print(`✅ Подписок на канал 'general': ${finalSubs}`);

const ownerSub = db.rocketchat_subscription.findOne({
    "u.username": "owner",
    rid: "general"
});
if (ownerSub) {
    print(`✅ Пользователь owner подписан на 'general'`);
} else {
    print("❌ ОШИБКА: Пользователь owner НЕ подписан на 'general'!");
}

print("\n🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!");
print("📝 Теперь в коде нужно изменить mapping на: 'general': 'general'");
