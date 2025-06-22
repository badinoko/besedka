// ВОССТАНОВЛЕНИЕ ROCKET.CHAT ПОСЛЕ ПОЛОМКИ
print('🔧 ВОССТАНАВЛИВАЮ ROCKET.CHAT...');

// Восстанавливаем критические настройки
const criticalSettings = [
    {_id: 'API_Iframe_Restriction_Enabled', value: false},
    {_id: 'Iframe_Restrict_Access', value: false},
    {_id: 'Iframe_X_Frame_Options', value: 'sameorigin'},
    {_id: 'Site_Url', value: 'http://127.0.0.1:3000'},
    {_id: 'PORT', value: 3000},
    {_id: 'ROOT_URL', value: 'http://127.0.0.1:3000'},
    {_id: 'MONGO_URL', value: 'mongodb://mongo:27017/rocketchat?replicaSet=rs0'}
];

criticalSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        {_id: setting._id},
        {$set: {value: setting.value, _updatedAt: new Date()}},
        {upsert: true}
    );
    print('✅ Восстановлено: ' + setting._id);
});

print('🎯 ГОТОВО! Критические настройки восстановлены.');
