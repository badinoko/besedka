// Скрипт диагностики проблемы с полем ввода в канале GENERAL
// Дата: 22 июня 2025 г.
// Цель: Найти причину нерабочего поля ввода в канале GENERAL

print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ С ПОЛЕМ ВВОДА В КАНАЛЕ GENERAL");
print("════════════════════════════════════════════════════════");

// 1. ПРОВЕРКА КАНАЛОВ
print("\n📋 ПРОВЕРКА КАНАЛОВ:");
print("────────────────────");

const channels = db.rocketchat_room.find({
    t: 'c' // публичные каналы
}).toArray();

channels.forEach(channel => {
    print(`✅ Канал: ${channel.name} (ID: ${channel._id})`);
    print(`   - Имя: ${channel.fname || 'НЕ УКАЗАНО'}`);
    print(`   - Тип: ${channel.t}`);
    print(`   - Читать: ${channel.ro ? 'ТОЛЬКО ЧТЕНИЕ' : 'РАЗРЕШЕНО'}`);
    print(`   - Участники: ${channel.usersCount || 0}`);
    print(`   - Создан: ${channel.ts ? new Date(channel.ts).toLocaleString() : 'НЕ УКАЗАНО'}`);

    // Специальная проверка для GENERAL канала
    if (channel._id === 'GENERAL' || channel.name === 'general') {
        print(`   🚨 ЭТО GENERAL КАНАЛ!`);
        print(`   - Режим read-only: ${channel.ro ? 'ДА (ПРОБЛЕМА!)' : 'НЕТ (НОРМА)'}`);
        print(`   - Права записи: ${channel.default ? 'ДА' : 'НЕТ'}`);
    }
    print("");
});

// 2. ПРОВЕРКА ПОДПИСОК ПОЛЬЗОВАТЕЛЯ owner
print("\n👤 ПРОВЕРКА ПОДПИСОК ПОЛЬЗОВАТЕЛЯ 'owner':");
print("─────────────────────────────────────────");

const subscriptions = db.rocketchat_subscription.find({
    u: { $elemMatch: { username: 'owner' } }
}).toArray();

print(`📊 Всего подписок: ${subscriptions.length}`);
subscriptions.forEach(sub => {
    print(`✅ Подписка: ${sub.name} (ID канала: ${sub.rid})`);
    print(`   - Роли: ${sub.roles ? sub.roles.join(', ') : 'ОТСУТСТВУЮТ'}`);
    print(`   - Блокировка: ${sub.blocked ? 'ЗАБЛОКИРОВАН' : 'НЕТ'}`);
    print(`   - Muted: ${sub.muted ? 'ЗАГЛУШЕН' : 'НЕТ'}`);
    print(`   - Может писать: ${sub.disableNotifications ? 'НЕТ' : 'ДА'}`);

    // Специальная проверка для GENERAL канала
    if (sub.rid === 'GENERAL' || sub.name === 'general') {
        print(`   🚨 ЭТО ПОДПИСКА НА GENERAL КАНАЛ!`);
        print(`   - Роли: ${sub.roles ? sub.roles.join(', ') : 'ОТСУТСТВУЮТ (ПРОБЛЕМА!)'}`);
        print(`   - Блокировка: ${sub.blocked ? 'ЗАБЛОКИРОВАН (ПРОБЛЕМА!)' : 'НЕТ (НОРМА)'}`);
        print(`   - Muted: ${sub.muted ? 'ЗАГЛУШЕН (ПРОБЛЕМА!)' : 'НЕТ (НОРМА)'}`);
    }
    print("");
});

// 3. ПРОВЕРКА НАСТРОЕК ПОЛЬЗОВАТЕЛЯ owner
print("\n🔧 ПРОВЕРКА НАСТРОЕК ПОЛЬЗОВАТЕЛЯ 'owner':");
print("─────────────────────────────────────────");

const ownerUser = db.users.findOne({ username: 'owner' });
if (ownerUser) {
    print(`✅ Пользователь найден: ${ownerUser.username}`);
    print(`   - Активен: ${ownerUser.active ? 'ДА' : 'НЕТ (ПРОБЛЕМА!)'}`);
    print(`   - Роли: ${ownerUser.roles ? ownerUser.roles.join(', ') : 'ОТСУТСТВУЮТ'}`);
    print(`   - Email: ${ownerUser.emails ? ownerUser.emails[0].address : 'НЕТ'}`);
    print(`   - Имя: ${ownerUser.name || 'НЕ УКАЗАНО'}`);

    // Проверка настроек пользователя
    if (ownerUser.settings) {
        print(`   - Настройки: ${Object.keys(ownerUser.settings).length} параметров`);
        if (ownerUser.settings.preferences) {
            print(`   - Язык: ${ownerUser.settings.preferences.language || 'НЕ УКАЗАН'}`);
        }
    }
} else {
    print("❌ Пользователь 'owner' НЕ НАЙДЕН!");
}

// 4. ПРОВЕРКА НАСТРОЕК ROCKET.CHAT
print("\n⚙️ ПРОВЕРКА НАСТРОЕК ROCKET.CHAT:");
print("─────────────────────────────────");

const criticalSettings = [
    'Message_AllowEditing',
    'Message_AllowDeleting',
    'Message_AllowPinning',
    'Message_MaxAllowedSize',
    'FileUpload_Enabled',
    'Iframe_Restrict_Access',
    'Accounts_Default_User_Preferences_joinDefaultChannels'
];

criticalSettings.forEach(settingName => {
    const setting = db.rocketchat_settings.findOne({ _id: settingName });
    if (setting) {
        print(`✅ ${settingName}: ${setting.value}`);

        if (settingName === 'Iframe_Restrict_Access' && setting.value === true) {
            print(`   🚨 ПРОБЛЕМА: Iframe_Restrict_Access = true блокирует взаимодействие!`);
        }

        if (settingName === 'Message_AllowEditing' && setting.value === false) {
            print(`   🚨 ПРОБЛЕМА: Message_AllowEditing = false блокирует редактирование!`);
        }
    } else {
        print(`❌ ${settingName}: НЕ НАЙДЕНА`);
    }
});

// 5. ПРОВЕРКА СООБЩЕНИЙ В КАНАЛЕ GENERAL
print("\n💬 ПРОВЕРКА ПОСЛЕДНИХ СООБЩЕНИЙ В КАНАЛЕ GENERAL:");
print("─────────────────────────────────────────────────");

const recentMessages = db.rocketchat_message.find({
    rid: 'GENERAL'
}).sort({ ts: -1 }).limit(3).toArray();

if (recentMessages.length > 0) {
    print(`📊 Найдено ${recentMessages.length} сообщений:`);
    recentMessages.forEach((msg, index) => {
        print(`${index + 1}. ${msg.u.username}: ${msg.msg.substring(0, 50)}...`);
        print(`   Время: ${new Date(msg.ts).toLocaleString()}`);
        print(`   Тип: ${msg.t || 'обычное'}`);
    });
} else {
    print("❌ Сообщений в канале GENERAL не найдено!");
}

print("\n🎯 РЕЗЮМЕ ДИАГНОСТИКИ:");
print("══════════════════════");
print("Если обнаружены проблемы выше, они могут быть причиной нерабочего поля ввода.");
print("Основные возможные причины:");
print("1. Канал GENERAL в режиме read-only (ro: true)");
print("2. Пользователь owner не имеет подписки на канал GENERAL");
print("3. Пользователь owner заблокирован или заглушен в канале");
print("4. Настройка Iframe_Restrict_Access блокирует взаимодействие");
print("5. Настройки сообщений отключены");
print("\n🔧 Следующий шаг: исправить найденные проблемы");
