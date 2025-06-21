// ПРОВЕРКА ИНФОРМАЦИИ О КАНАЛАХ

print('=== ПРОВЕРКА КАНАЛОВ В ROCKET.CHAT ===');

// Получаем все каналы
const channels = db.rocketchat_room.find({ t: 'c' }).toArray();

print(`Найдено каналов: ${channels.length}`);
print('');

channels.forEach(channel => {
    print(`Канал: ${channel.name}`);
    print(`  ID: ${channel._id}`);
    print(`  Тип: ${channel.t}`);
    print(`  Описание: ${channel.description || 'Нет описания'}`);
    print(`  Создан: ${channel.ts}`);
    print('---');
});

print('');
print('=== МАППИНГ ДЛЯ ФУНКЦИИ switchChannel ===');
print('Текущие URL в switchChannel:');
print('  general -> /channel/general');
print('  vip -> /channel/vip');
print('  moderators -> /channel/moderators');
print('');

print('Фактические ID каналов:');
channels.forEach(channel => {
    print(`  ${channel.name} -> /channel/${channel._id} (ID: ${channel._id})`);
});

print('');
print('🔧 РЕКОМЕНДАЦИИ:');
if (channels.find(c => c.name === 'general' && c._id === 'GENERAL')) {
    print('⚠️ ПРОБЛЕМА: Канал general имеет ID "GENERAL"');
    print('   Решение: Изменить ID на "general" или обновить switchChannel()');
}

print('ГОТОВО!');
