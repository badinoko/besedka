// Отключение Setup Wizard навсегда
print('🔧 Отключение Setup Wizard...');

// Проверяем текущий статус
const wizard = db.rocketchat_settings.findOne({_id: 'Show_Setup_Wizard'});
print('Setup Wizard текущий статус: ' + (wizard ? wizard.value : 'not found'));

// Отключаем навсегда
const result = db.rocketchat_settings.updateOne(
  {_id: 'Show_Setup_Wizard'},
  {$set: {value: 'completed'}},
  {upsert: true}
);

print('Результат операции: ' + JSON.stringify(result));

// Проверяем результат
const wizardAfter = db.rocketchat_settings.findOne({_id: 'Show_Setup_Wizard'});
print('✅ Setup Wizard ПОСЛЕ отключения: ' + wizardAfter.value);

// Дополнительно отключаем другие связанные настройки
db.rocketchat_settings.updateOne(
  {_id: 'First_Channel_After_Login'},
  {$set: {value: ''}},
  {upsert: true}
);

print('✅ Setup Wizard отключен навсегда!');
