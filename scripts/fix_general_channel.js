// Скрипт для исправления канала GENERAL - установка правильных настроек sysMes
// Проблема: GENERAL имеет sysMes: {} вместо sysMes: true как в рабочих каналах

use rocketchat

// Сначала проверяем текущее состояние канала GENERAL
print("=== ТЕКУЩЕЕ СОСТОЯНИЕ КАНАЛА GENERAL ===")
const currentGeneral = db.rocketchat_room.findOne({_id: "GENERAL"})
if (currentGeneral) {
    print("Найден канал GENERAL:")
    print("- sysMes:", JSON.stringify(currentGeneral.sysMes))
    print("- ro:", currentGeneral.ro)
    print("- muted:", currentGeneral.muted ? JSON.stringify(currentGeneral.muted) : "undefined")
} else {
    print("ОШИБКА: Канал GENERAL не найден!")
    quit(1)
}

// Исправляем настройки канала GENERAL
print("\n=== ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ ===")

const updateResult = db.rocketchat_room.updateOne(
    {_id: "GENERAL"},
    {
        $set: {
            sysMes: true,  // Устанавливаем как в рабочих каналах
            ro: false      // Убираем read-only если есть
        },
        $unset: {
            muted: ""      // Удаляем ограничения muted если есть
        }
    }
)

if (updateResult.modifiedCount > 0) {
    print("✅ Канал GENERAL успешно исправлен")

    // Проверяем результат
    const updatedGeneral = db.rocketchat_room.findOne({_id: "GENERAL"})
    print("\n=== РЕЗУЛЬТАТ ИСПРАВЛЕНИЯ ===")
    print("- sysMes:", JSON.stringify(updatedGeneral.sysMes))
    print("- ro:", updatedGeneral.ro)
    print("- muted:", updatedGeneral.muted ? JSON.stringify(updatedGeneral.muted) : "undefined")

    print("\n🔄 ТРЕБУЕТСЯ ПЕРЕЗАПУСК ROCKET.CHAT для применения изменений")
} else {
    print("❌ Ошибка при обновлении канала GENERAL")
    quit(1)
}
