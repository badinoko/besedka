// ===================================================================
// ДИАГНОСТИКА ПОДПИСОК - ПОИСК ПРИЧИНЫ КНОПКИ "JOIN THE CHANNEL"
// ===================================================================
// Создан: 23 июня 2025, 20:07 MSK
// Цель: Найти причину появления кнопки Join Channel при переключении каналов
// ===================================================================

print('🔍 ДИАГНОСТИКА ПОДПИСОК ПОЛЬЗОВАТЕЛЯ OWNER...');
print('🎯 Цель: Найти причину кнопки "Join the Channel"');
print('');

// ===================================================================
// 1. ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ OWNER
// ===================================================================

const ownerUser = db.users.findOne({ username: 'owner' });
if (!ownerUser) {
    print('❌ КРИТИЧЕСКАЯ ОШИБКА: Пользователь owner не найден!');
    exit(1);
}

print('👤 ПОЛЬЗОВАТЕЛЬ OWNER:');
print(`   ID: ${ownerUser._id}`);
print(`   Username: ${ownerUser.username}`);
print(`   Roles: ${JSON.stringify(ownerUser.roles)}`);
print(`   Status: ${ownerUser.status}`);
print(`   Active: ${ownerUser.active}`);
print('');

// ===================================================================
// 2. ПРОВЕРКА КАНАЛОВ
// ===================================================================

const channels = ['general', 'vip', 'moderators'];
print('💬 КАНАЛЫ:');

channels.forEach(channelId => {
    const channel = db.rocketchat_room.findOne({ _id: channelId });
    if (channel) {
        print(`   ✅ ${channelId}: "${channel.fname}" (${channel.name})`);
        print(`      Type: ${channel.t}, Default: ${channel.default}`);
        print(`      Users: ${channel.usersCount || 0}, Messages: ${channel.msgs || 0}`);
    } else {
        print(`   ❌ ${channelId}: НЕ НАЙДЕН!`);
    }
});
print('');

// ===================================================================
// 3. ДЕТАЛЬНАЯ ПРОВЕРКА ПОДПИСОК OWNER
// ===================================================================

print('🔐 ПОДПИСКИ ПОЛЬЗОВАТЕЛЯ OWNER:');

const ownerSubscriptions = db.rocketchat_subscription.find({ 'u.username': 'owner' }).toArray();
print(`   Всего подписок: ${ownerSubscriptions.length}`);
print('');

if (ownerSubscriptions.length === 0) {
    print('❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: У owner НЕТ ПОДПИСОК!');
    print('   Это объясняет появление кнопки Join Channel');
    print('   Решение: Создать подписки для всех каналов');
} else {
    ownerSubscriptions.forEach((sub, index) => {
        print(`   📋 Подписка ${index + 1}:`);
        print(`      ID: ${sub._id}`);
        print(`      Channel: ${sub.rid} ("${sub.fname}")`);
        print(`      Name: ${sub.name}`);
        print(`      Type: ${sub.t}`);
        print(`      Open: ${sub.open}`);
        print(`      Roles: ${JSON.stringify(sub.roles)}`);
        print(`      Unread: ${sub.unread}`);
        print(`      Last Read: ${sub.lr}`);
        print(`      Last Seen: ${sub.ls}`);
        print('');
    });
}

// ===================================================================
// 4. ПРОВЕРКА ДОСТУПА К КАЖДОМУ КАНАЛУ
// ===================================================================

print('🎯 ПРОВЕРКА ДОСТУПА К КАЖДОМУ КАНАЛУ:');

channels.forEach(channelId => {
    const channel = db.rocketchat_room.findOne({ _id: channelId });
    const subscription = db.rocketchat_subscription.findOne({
        'u.username': 'owner',
        'rid': channelId
    });

    print(`   🔍 Канал ${channelId}:`);

    if (!channel) {
        print(`      ❌ Канал не существует`);
        return;
    }

    if (!subscription) {
        print(`      ❌ НЕТ ПОДПИСКИ - появится кнопка Join Channel!`);
        print(`      📝 Нужно создать подписку для канала ${channelId}`);
    } else {
        print(`      ✅ Подписка существует`);
        print(`      📋 Роли: ${JSON.stringify(subscription.roles)}`);
        print(`      📋 Open: ${subscription.open}`);

        // Проверяем корректность подписки
        if (!subscription.open) {
            print(`      ⚠️ Подписка закрыта (open: false) - может вызывать проблемы`);
        }

        if (!subscription.roles || subscription.roles.length === 0) {
            print(`      ⚠️ Нет ролей в канале - может вызывать проблемы`);
        }
    }
    print('');
});

// ===================================================================
// 5. РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ
// ===================================================================

print('💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:');

const missingSubscriptions = [];
channels.forEach(channelId => {
    const subscription = db.rocketchat_subscription.findOne({
        'u.username': 'owner',
        'rid': channelId
    });

    if (!subscription) {
        missingSubscriptions.push(channelId);
    }
});

if (missingSubscriptions.length > 0) {
    print(`   ❌ Отсутствуют подписки для каналов: ${missingSubscriptions.join(', ')}`);
    print('   🔧 Решение: Выполнить скрипт FINAL_ROCKETCHAT_FIX.js для пересоздания подписок');
} else {
    print('   ✅ Все подписки существуют');
    print('   🤔 Причина кнопки Join Channel может быть в:');
    print('      - Неправильных ролях в подписках');
    print('      - Настройках каналов (приватность, права доступа)');
    print('      - Настройках Rocket.Chat (автоматическое присоединение)');
}

// ===================================================================
// 6. ПРОВЕРКА НАСТРОЕК АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ
// ===================================================================

print('');
print('⚙️ НАСТРОЙКИ АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ:');

const joinSettings = [
    'Accounts_RequireNameForSignUp',
    'Accounts_RequirePasswordConfirmation',
    'Accounts_EmailVerification',
    'Accounts_ManuallyApproveNewUsers',
    'Channels_Max_Allowed',
    'DirectMesssage_maxUsers'
];

joinSettings.forEach(settingId => {
    const setting = db.rocketchat_settings.findOne({ _id: settingId });
    if (setting) {
        print(`   📋 ${settingId}: ${setting.value}`);
    } else {
        print(`   ❓ ${settingId}: НЕ НАЙДЕНО`);
    }
});

print('');
print('🎉 ДИАГНОСТИКА ЗАВЕРШЕНА!');
print('📋 Проверьте результаты выше для выявления проблемы');
