// Добавление маппинга ролей для OAuth провайдера Besedka

// Mapping ролей Django -> Rocket.Chat
const rolesMapping = {
    "owner": "admin,vip",
    "moderator": "admin",
    "user": "user"
};

// Обновляем настройки маппинга
const mappingSettings = [
    { _id: 'Accounts_OAuth_Custom-Besedka-roles_claim', value: 'roles' },
    { _id: 'Accounts_OAuth_Custom-Besedka-groups_claim', value: 'groups' },
    { _id: 'Accounts_OAuth_Custom-Besedka-map_channels', value: false },
    { _id: 'Accounts_OAuth_Custom-Besedka-merge_roles', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-roles_to_sync', value: 'admin,moderator,vip,user' },
    { _id: 'Accounts_OAuth_Custom-Besedka-channels_map', value: JSON.stringify(rolesMapping) }
];

print('🔧 Добавляю маппинг ролей...');

mappingSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        { _id: setting._id },
        { $set: { value: setting.value } },
        { upsert: true }
    );
    print(`✅ ${setting._id}: ${setting.value}`);
});

print('\n📋 ПРОВЕРКА МАППИНГА:');
print('Roles claim: ' + db.rocketchat_settings.findOne({ _id: 'Accounts_OAuth_Custom-Besedka-roles_claim' }).value);
print('Merge roles: ' + db.rocketchat_settings.findOne({ _id: 'Accounts_OAuth_Custom-Besedka-merge_roles' }).value);
print('Roles mapping: ' + db.rocketchat_settings.findOne({ _id: 'Accounts_OAuth_Custom-Besedka-channels_map' }).value);

print('\n🎯 Маппинг ролей настроен!');
