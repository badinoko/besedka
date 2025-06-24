// Скрипт для удаления символов # из названий каналов в Rocket.Chat
// Использует Custom CSS для скрытия символа # только в embedded режиме
// Дата создания: 25 июня 2025

db = db.getSiblingDB('rocketchat');

print("🎯 Начинаем настройку скрытия символа # в названиях каналов...");

// Проверяем текущие Custom CSS настройки
const currentCSS = db.rocketchat_settings.findOne({_id: 'theme-custom-css'});
print("📋 Текущие Custom CSS настройки:", currentCSS ? "найдены" : "отсутствуют");

// CSS для скрытия символа # в embedded режиме
const hideHashCSS = `
/* Скрытие символа # в названиях каналов для embedded режима */
.embedded .room-title::before,
.embedded .sidebar-item__title::before,
.embedded .rc-room-header-title::before,
.embedded [data-qa="sidebar-item-title"]::before {
  content: none !important;
}

/* Убираем # из текста названий каналов */
.embedded .room-title,
.embedded .sidebar-item__title,
.embedded .rc-room-header-title,
.embedded [data-qa="sidebar-item-title"] {
  font-family: inherit !important;
}

/* Скрываем # если он добавлен как текст */
.embedded .room-title:first-letter,
.embedded .sidebar-item__title:first-letter,
.embedded .rc-room-header-title:first-letter {
  display: none;
}

/* Более точечное скрытие для современной версии RC */
.embedded [data-qa="room-title"]::before,
.embedded .rcx-sidebar-item__title::before {
  display: none !important;
}

.embedded [data-qa="room-title"],
.embedded .rcx-sidebar-item__title {
  position: relative;
}

/* Если # в тексте - скрываем первый символ */
.embedded [data-qa="room-title"]:first-child,
.embedded .rcx-sidebar-item__title:first-child {
  text-indent: -0.6em;
  padding-left: 0.6em;
}
`;

try {
  // Обновляем или создаем Custom CSS настройку
  let finalCSS = hideHashCSS;

  if (currentCSS && currentCSS.value) {
    // Добавляем к существующему CSS
    finalCSS = currentCSS.value + '\n\n' + hideHashCSS;
    print("📝 Добавляем CSS к существующим настройкам");
  } else {
    print("🆕 Создаем новые Custom CSS настройки");
  }

  const result = db.rocketchat_settings.updateOne(
    {_id: 'theme-custom-css'},
    {
      $set: {
        _id: 'theme-custom-css',
        value: finalCSS,
        type: 'code',
        public: true,
        ts: new Date(),
        _updatedAt: new Date(),
        hidden: false,
        blocked: false,
        sorter: 1,
        i18nLabel: 'Custom_CSS',
        i18nDescription: 'Custom_CSS_Description',
        autocomplete: true,
        secret: false
      }
    },
    {upsert: true}
  );

  if (result.modifiedCount > 0 || result.upsertedCount > 0) {
    print("✅ Custom CSS успешно обновлен для скрытия символа #");
    print("🎨 CSS правила применены для embedded режима");
  } else {
    print("❌ Ошибка при обновлении Custom CSS");
  }

  // Проверяем результат
  const updatedCSS = db.rocketchat_settings.findOne({_id: 'theme-custom-css'});
  if (updatedCSS && updatedCSS.value.includes('embedded')) {
    print("🔍 Проверка: CSS правила для embedded режима найдены в настройках");
  }

} catch (error) {
  print("❌ Ошибка при настройке Custom CSS:", error);
}

print("🏁 Скрипт завершен. Перезапустите Rocket.Chat для применения изменений.");
print("📌 Примечание: Символ # будет скрыт только в embedded режиме, основной интерфейс RC останется без изменений.");
