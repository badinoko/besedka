// ПРОВЕРКА OAUTH НАСТРОЕК В ROCKET.CHAT

print('🔍 ПРОВЕРКА OAUTH НАСТРОЕК');

// Ищем все OAuth настройки
const oauthSettings = db.rocketchat_settings.find({
    _id: {$regex: 'OAuth'}
}).toArray();

print(`✅ Найдено OAuth настроек: ${oauthSettings.length}`);

// Важные OAuth настройки для диагностики
const importantSettings = [
    'Accounts_OAuth_Custom-besedka',
    'Accounts_OAuth_Custom-besedka-id',
    'Accounts_OAuth_Custom-besedka-secret',
    'Accounts_OAuth_Custom-besedka-url',
    'Accounts_OAuth_Custom-besedka-token_path',
    'Accounts_OAuth_Custom-besedka-authorize_path',
    'Iframe_Restrict_Access'
];

print('\n📊 КРИТИЧЕСКИ ВАЖНЫЕ НАСТРОЙКИ:');
importantSettings.forEach(setting => {
    const value = db.rocketchat_settings.findOne({_id: setting});
    if (value) {
        print(`✅ ${setting}: ${value.value}`);
    } else {
        print(`❌ ${setting}: НЕ НАЙДЕНО`);
    }
});

// Проверяем настройки iframe
print('\n🖼️ НАСТРОЙКИ IFRAME:');
const iframeSettings = db.rocketchat_settings.find({
    _id: {$regex: 'Iframe'}
}).toArray();

iframeSettings.forEach(setting => {
    print(`  ${setting._id}: ${setting.value}`);
});

// Проверяем есть ли пользователь owner
print('\n👤 ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ OWNER:');
const ownerUser = db.rocketchat_users.findOne({username: 'owner'});
if (ownerUser) {
    print(`✅ Пользователь owner найден: ${ownerUser._id}`);
    print(`   Email: ${ownerUser.emails && ownerUser.emails[0] ? ownerUser.emails[0].address : 'нет'}`);
    print(`   Активен: ${ownerUser.active}`);
} else {
    print('❌ Пользователь owner НЕ НАЙДЕН');
}

print('\nГОТОВО!');
