// ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ ROCKET.CHAT
print('🚨 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ...');

// Удаляем все настройки которые могли быть повреждены сегодня
const result = db.rocketchat_settings.deleteMany({
    _updatedAt: {$gte: new Date('2025-06-22T01:15:00.000Z')}
});

print('🗑️ Удалено поврежденных настроек: ' + result.deletedCount);

// Восстанавливаем базовые настройки
const basicSettings = [
    {_id: 'Site_Url', value: 'http://127.0.0.1:3000'},
    {_id: 'Show_Setup_Wizard', value: 'completed'},
    {_id: 'Organization_Type', value: 'community'},
    {_id: 'Server_Type', value: 'privateTeam'},
    {_id: 'Iframe_Restrict_Access', value: false},
    {_id: 'Iframe_X_Frame_Options', value: 'sameorigin'}
];

basicSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {
            value: setting.value,
            valueSource: 'customValue',
            _updatedAt: new Date()
        }},
        {upsert: true}
    );
    print('✅ Восстановлено: ' + setting._id);
});

print('🎯 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!');
