// ПРОВЕРКА ДУБЛИРУЮЩИХ КАНАЛОВ

print('🔍 ПРОВЕРКА ДУБЛИРУЮЩИХ КАНАЛОВ...');

// Ищем все каналы с именем "general"
const generalChannels = db.rocketchat_room.find({ name: 'general' }).toArray();

print(`Найдено каналов с именем "general": ${generalChannels.length}`);
print('');

generalChannels.forEach((channel, index) => {
    print(`Канал ${index + 1}:`);
    print(`  Имя: ${channel.name}`);
    print(`  ID: ${channel._id}`);
    print(`  Тип: ${channel.t}`);
    print(`  Создан: ${channel.ts}`);
    print(`  Сообщений: ${channel.msgs || 0}`);
    print(`  Пользователей: ${channel.usersCount || 0}`);
    print('---');
});

// Проверяем подписки на эти каналы
print('\n📋 ПОДПИСКИ НА КАНАЛЫ:');
generalChannels.forEach((channel, index) => {
    const subscriptions = db.rocketchat_subscription.find({ rid: channel._id }).toArray();
    print(`Канал ${channel._id}: ${subscriptions.length} подписок`);
    subscriptions.forEach(sub => {
        print(`  - ${sub.u.username}`);
    });
});

// Проверяем сообщения
print('\n💬 СООБЩЕНИЯ В КАНАЛАХ:');
generalChannels.forEach((channel, index) => {
    const messages = db.rocketchat_message.countDocuments({ rid: channel._id });
    print(`Канал ${channel._id}: ${messages} сообщений`);
});

print('\n🔧 РЕКОМЕНДАЦИИ:');
if (generalChannels.length > 1) {
    print('⚠️ НАЙДЕНЫ ДУБЛИРУЮЩИЕ КАНАЛЫ!');
    print('   Нужно объединить или удалить один из них');

    // Определяем какой канал основной
    const mainChannel = generalChannels.find(c => c._id === 'GENERAL') || generalChannels[0];
    const duplicateChannels = generalChannels.filter(c => c._id !== mainChannel._id);

    print(`   Основной канал: ${mainChannel._id}`);
    duplicateChannels.forEach(dup => {
        print(`   Дублирующий канал: ${dup._id}`);
    });
}

print('\nГОТОВО!');
