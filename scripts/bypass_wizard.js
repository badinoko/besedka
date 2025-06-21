// Этот скрипт обходит мастер первоначальной настройки
print("🚀 Принудительное завершение мастера настройки...");

db.getCollection('rocketchat_settings').updateOne(
  { _id: 'Show_Setup_Wizard' },
  { $set: { value: 'completed' } },
  { upsert: true }
);

print("✅ Статус мастера настройки изменен на 'completed'.");
print("‼️ Теперь необходимо перезапустить Rocket.Chat, чтобы увидеть экран входа.");
