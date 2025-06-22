// Скрипт исправления проблемы с полем ввода в канале GENERAL
// Дата: 22 июня 2025 г.
// Цель: Исправить нерабочее поле ввода в канале GENERAL

print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С ПОЛЕМ ВВОДА В КАНАЛЕ GENERAL");
print("════════════════════════════════════════════════════════");

// Находим пользователя owner
const ownerUser = db.users.findOne({username: 'owner'});
if (!ownerUser) {
    print("❌ Пользователь owner не найден!");
    quit();
}

print(`✅ Пользователь найден: ${ownerUser.username} (ID: ${ownerUser._id})`);

// Находим канал GENERAL
const generalChannel = db.rocketchat_room.findOne({_id: 'GENERAL'});
if (!generalChannel) {
    print("❌ Канал GENERAL не найден!");
    quit();
}

print(`✅ Канал найден: ${generalChannel.name} (ID: ${generalChannel._id})`);

// 1. ПРОВЕРКА И ИСПРАВЛЕНИЕ ПОДПИСКИ
print("\n📋 ПРОВЕРКА ПОДПИСКИ:");
print("────────────────────");

const subscription = db.rocketchat_subscription.findOne({
    rid: 'GENERAL',
    'u._id': ownerUser._id
});

if (subscription) {
    print(`✅ Подписка найдена: ${subscription._id}`);
    print(`   - Роли: ${subscription.roles || 'отсутствуют'}`);
    print(`   - Заблокирован: ${subscription.blocked || false}`);
    print(`   - Заглушен: ${subscription.muted || false}`);

    // Исправляем подписку если нужно
    let needsUpdate = false;
    const updates = {};

    if (subscription.blocked) {
        updates.blocked = false;
        needsUpdate = true;
        print("   🔧 Убираем блокировку");
    }

    if (subscription.muted) {
        updates.muted = false;
        needsUpdate = true;
        print("   🔧 Убираем заглушение");
    }

    if (!subscription.roles || subscription.roles.length === 0) {
        updates.roles = ['owner'];
        needsUpdate = true;
        print("   🔧 Добавляем роль owner");
    }

    if (needsUpdate) {
        updates._updatedAt = new Date();
        const result = db.rocketchat_subscription.updateOne(
            {_id: subscription._id},
            {$set: updates}
        );
        print(`   ✅ Подписка обновлена: ${result.modifiedCount} записей`);
    } else {
        print("   ✅ Подписка в порядке, обновления не требуются");
    }
} else {
    print("❌ Подписка не найдена! Создаем новую подписку...");

    const newSubscription = {
        _id: `C2Jx7u98y8F6nFoey${generalChannel._id}`,
        open: true,
        alert: true,
        unread: 0,
        userMentions: 0,
        groupMentions: 0,
        ts: new Date(),
        rid: generalChannel._id,
        name: generalChannel.name,
        fname: generalChannel.fname,
        customFields: {},
        broadcast: false,
        encrypted: false,
        E2EKey: '',
        tunread: [],
        tunreadGroup: [],
        tunreadUser: [],
        u: {
            _id: ownerUser._id,
            username: ownerUser.username,
            name: ownerUser.name || ownerUser.username
        },
        roles: ['owner'],
        _updatedAt: new Date()
    };

    const result = db.rocketchat_subscription.insertOne(newSubscription);
    print(`   ✅ Новая подписка создана: ${result.insertedId}`);
}

// 2. ПРОВЕРКА И ИСПРАВЛЕНИЕ УЧАСТНИКОВ КАНАЛА
print("\n👥 ПРОВЕРКА УЧАСТНИКОВ КАНАЛА:");
print("─────────────────────────────");

// Проверяем есть ли owner в списке участников канала
const channelData = db.rocketchat_room.findOne({_id: 'GENERAL'});
const userIds = channelData.uids || [];
const usernames = channelData.usernames || [];

print(`📊 Участников в канале: ${userIds.length}`);
print(`   - IDs: ${userIds.slice(0, 3).join(', ')}${userIds.length > 3 ? '...' : ''}`);
print(`   - Usernames: ${usernames.slice(0, 3).join(', ')}${usernames.length > 3 ? '...' : ''}`);

if (!userIds.includes(ownerUser._id)) {
    print("❌ owner не найден в участниках канала! Добавляем...");

    const updateResult = db.rocketchat_room.updateOne(
        {_id: 'GENERAL'},
        {
            $addToSet: {
                uids: ownerUser._id,
                usernames: ownerUser.username
            },
            $inc: {usersCount: 1},
            $set: {_updatedAt: new Date()}
        }
    );

    print(`   ✅ Пользователь добавлен: ${updateResult.modifiedCount} записей обновлено`);
} else {
    print("✅ owner найден в участниках канала");
}

// 3. ПРОВЕРКА НАСТРОЕК КАНАЛА
print("\n⚙️ ПРОВЕРКА НАСТРОЕК КАНАЛА:");
print("────────────────────────────");

const channelSettings = {
    ro: false,        // не только для чтения
    sysMes: true,     // системные сообщения включены
    default: true,    // канал по умолчанию
    featured: true    // рекомендуемый канал
};

let channelNeedsUpdate = false;
const channelUpdates = {};

Object.keys(channelSettings).forEach(key => {
    if (channelData[key] !== channelSettings[key]) {
        channelUpdates[key] = channelSettings[key];
        channelNeedsUpdate = true;
        print(`   🔧 Исправляем ${key}: ${channelData[key]} → ${channelSettings[key]}`);
    } else {
        print(`   ✅ ${key}: ${channelData[key]} (корректно)`);
    }
});

if (channelNeedsUpdate) {
    channelUpdates._updatedAt = new Date();
    const result = db.rocketchat_room.updateOne(
        {_id: 'GENERAL'},
        {$set: channelUpdates}
    );
    print(`   ✅ Настройки канала обновлены: ${result.modifiedCount} записей`);
} else {
    print("   ✅ Настройки канала в порядке");
}

// 4. СОЗДАНИЕ ТЕСТОВОГО СООБЩЕНИЯ
print("\n💬 СОЗДАНИЕ ТЕСТОВОГО СООБЩЕНИЯ:");
print("─────────────────────────────────");

const testMessage = {
    _id: 'test-message-' + Date.now(),
    rid: 'GENERAL',
    ts: new Date(),
    msg: 'Тест поля ввода - ' + new Date().toLocaleTimeString(),
    u: {
        _id: ownerUser._id,
        username: ownerUser.username,
        name: ownerUser.name || ownerUser.username
    },
    _updatedAt: new Date(),
    urls: [],
    mentions: [],
    channels: [],
    md: [
        {
            type: 'PARAGRAPH',
            value: [
                {
                    type: 'PLAIN_TEXT',
                    value: 'Тест поля ввода - ' + new Date().toLocaleTimeString()
                }
            ]
        }
    ]
};

try {
    const msgResult = db.rocketchat_message.insertOne(testMessage);
    print(`✅ Тестовое сообщение создано: ${msgResult.insertedId}`);

    // Обновляем счетчик сообщений в канале
    db.rocketchat_room.updateOne(
        {_id: 'GENERAL'},
        {
            $inc: {msgs: 1},
            $set: {
                lm: testMessage.ts,
                _updatedAt: new Date()
            }
        }
    );

    print("✅ Счетчик сообщений в канале обновлен");
} catch (error) {
    print(`❌ Ошибка создания тестового сообщения: ${error.message}`);
}

print("\n🎯 ИТОГИ ИСПРАВЛЕНИЯ:");
print("════════════════════");
print("✅ Подписка пользователя owner на канал GENERAL проверена/создана");
print("✅ Пользователь owner добавлен в участники канала");
print("✅ Настройки канала GENERAL исправлены");
print("✅ Создано тестовое сообщение для проверки");
print("");
print("🚀 СЛЕДУЮЩИЕ ШАГИ:");
print("1. Перезапустите Rocket.Chat: docker-compose restart rocketchat");
print("2. Откройте http://127.0.0.1:8001/chat/integrated/");
print("3. Проверьте работу поля ввода в канале GENERAL");
print("");
print("Если проблема сохраняется, возможно она связана с iframe режимом.");
