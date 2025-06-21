// Исправление проблемы Site_Url в Rocket.Chat
// Устраняет раздражающее предупреждение

db = db.getSiblingDB('rocketchat');

// Исправляем Site_Url на правильный
db.rocketchat_settings.updateOne(
    { _id: 'Site_Url' },
    { $set: { value: 'http://127.0.0.1:3000' } }
);

// Также исправляем Site_Name если нужно
db.rocketchat_settings.updateOne(
    { _id: 'Site_Name' },
    { $set: { value: 'Беседка Chat' } }
);

print('✅ Site_Url исправлен на http://127.0.0.1:3000');
print('✅ Уведомление о несоответствии URL устранено');
