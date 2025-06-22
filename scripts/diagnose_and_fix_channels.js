// ДИАГНОСТИКА И ИСПРАВЛЕНИЕ ПРОБЛЕМЫ КАНАЛОВ
// Проблема: несоответствие между GENERAL (большими) и general (маленькими)

print("🔍 === ДИАГНОСТИКА КАНАЛОВ ===");

// 1. Ищем все каналы
print("📊 Все каналы в системе:");
db.rocketchat_room.find({t: "c"}, {_id: 1, name: 1, fname: 1}).forEach(function(room) {
    print(`   - ID: "${room._id}", name: "${room.name}", fname: "${room.fname || 'не задано'}"`);
});

// 2. Ищем подписки owner
print("\n📊 Подписки пользователя owner:");
db.rocketchat_subscription.find({"u.username": "owner"}, {rid: 1, name: 1, fname: 1}).forEach(function(sub) {
    print(`   - Подписан на канал ID: "${sub.rid}", name: "${sub.name}", fname: "${sub.fname || 'не задано'}"`);
});

// 3. Проверяем конкретно проблемные каналы
print("\n🚨 СПЕЦИАЛЬНАЯ ПРОВЕРКА:");
const generalBig = db.rocketchat_room.findOne({_id: "GENERAL"});
const generalSmall = db.rocketchat_room.findOne({_id: "general"});

if (generalBig) {
    print(`✅ Найден канал с ID "GENERAL": name="${generalBig.name}", fname="${generalBig.fname}"`);
} else {
    print(`❌ Канал с ID "GENERAL" НЕ НАЙДЕН`);
}

if (generalSmall) {
    print(`✅ Найден канал с ID "general": name="${generalSmall.name}", fname="${generalSmall.fname}"`);
} else {
    print(`❌ Канал с ID "general" НЕ НАЙДЕН`);
}

// 4. ИСПРАВЛЕНИЕ ПРОБЛЕМЫ
print("\n🛠️ === ИСПРАВЛЕНИЕ ПРОБЛЕМЫ ===");

// Если есть канал GENERAL, но нет general - переименовываем
if (generalBig && !generalSmall) {
    print("🔄 ИСПРАВЛЕНИЕ: Переименовываем канал GENERAL -> general");

    // Обновляем ID канала с GENERAL на general
    db.rocketchat_room.updateOne(
        {_id: "GENERAL"},
        {$set: {_id: "general"}}
    );

    // Обновляем все подписки
    db.rocketchat_subscription.updateMany(
        {rid: "GENERAL"},
        {$set: {rid: "general"}}
    );

    // Обновляем все сообщения
    db.rocketchat_message.updateMany(
        {rid: "GENERAL"},
        {$set: {rid: "general"}}
    );

    print("✅ Канал GENERAL переименован в general");
    print("✅ Все подписки обновлены");
    print("✅ Все сообщения перенесены");
}

// Если есть оба канала - удаляем GENERAL и оставляем general
if (generalBig && generalSmall) {
    print("🔄 ИСПРАВЛЕНИЕ: Удаляем дублирующий канал GENERAL, оставляем general");

    // Переносим сообщения из GENERAL в general
    db.rocketchat_message.updateMany(
        {rid: "GENERAL"},
        {$set: {rid: "general"}}
    );

    // Переносим подписки из GENERAL в general (если их нет)
    const generalSubs = db.rocketchat_subscription.find({rid: "GENERAL"});
    generalSubs.forEach(function(sub) {
        const existingSub = db.rocketchat_subscription.findOne({
            "u._id": sub.u._id,
            rid: "general"
        });

        if (!existingSub) {
            // Создаем подписку на general
            sub.rid = "general";
            sub._id = sub.u._id + "-general";
            delete sub._id; // удаляем старый _id для создания нового
            db.rocketchat_subscription.insertOne(sub);
            print(`   - Перенесена подписка для ${sub.u.username}`);
        }
    });

    // Удаляем старые подписки и канал GENERAL
    db.rocketchat_subscription.deleteMany({rid: "GENERAL"});
    db.rocketchat_room.deleteOne({_id: "GENERAL"});

    print("✅ Канал GENERAL удален");
    print("✅ Все данные перенесены в канал general");
}

// Если нет ни одного - создаем general
if (!generalBig && !generalSmall) {
    print("🔄 ИСПРАВЛЕНИЕ: Создаем канал general");

    const newChannel = {
        _id: "general",
        name: "general",
        fname: "Общий чат",
        t: "c",
        u: {_id: "owner", username: "owner"},
        ts: new Date(),
        ro: false,
        sysMes: true,
        default: true
    };

    db.rocketchat_room.insertOne(newChannel);
    print("✅ Канал general создан");
}

// 5. ПРОВЕРЯЕМ ПОДПИСКУ OWNER НА general
print("\n🔍 === ПРОВЕРКА ПОДПИСКИ OWNER ===");
const ownerGeneralSub = db.rocketchat_subscription.findOne({
    "u.username": "owner",
    rid: "general"
});

if (!ownerGeneralSub) {
    print("🔄 Создаем подписку owner на канал general");

    const ownerUser = db.users.findOne({username: "owner"});
    if (ownerUser) {
        const newSub = {
            _id: ownerUser._id + "-general",
            u: {
                _id: ownerUser._id,
                username: "owner"
            },
            rid: "general",
            name: "general",
            fname: "general",
            t: "c",
            ts: new Date(),
            ls: new Date(),
            open: true,
            alert: false,
            roles: ["owner"],
            unread: 0
        };

        db.rocketchat_subscription.insertOne(newSub);
        print("✅ Подписка owner на general создана");
    } else {
        print("❌ Пользователь owner не найден!");
    }
} else {
    print("✅ Подписка owner на general уже существует");
}

// 6. ФИНАЛЬНАЯ ПРОВЕРКА
print("\n✅ === ФИНАЛЬНАЯ ПРОВЕРКА ===");
const finalGeneral = db.rocketchat_room.findOne({_id: "general"});
if (finalGeneral) {
    print(`✅ Канал general найден: name="${finalGeneral.name}", fname="${finalGeneral.fname}"`);
    print(`   - sysMes: ${finalGeneral.sysMes}`);
    print(`   - ro: ${finalGeneral.ro}`);
    print(`   - t: ${finalGeneral.t}`);
} else {
    print("❌ Канал general НЕ НАЙДЕН после исправления!");
}

const finalSub = db.rocketchat_subscription.findOne({
    "u.username": "owner",
    rid: "general"
});
if (finalSub) {
    print(`✅ Подписка owner на general: roles=${JSON.stringify(finalSub.roles)}`);
} else {
    print("❌ Подписка owner на general НЕ НАЙДЕНА!");
}

print("\n🎉 ДИАГНОСТИКА И ИСПРАВЛЕНИЕ ЗАВЕРШЕНЫ!");
print("📝 Теперь в коде нужно использовать mapping: 'general': 'general' (НЕ GENERAL)");
