// ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ ПРОБЛЕМЫ GENERAL/general

print('🔍 ДИАГНОСТИКА ПРОБЛЕМЫ КАНАЛА GENERAL');

// Ищем канал с именем general
const generalByName = db.rocketchat_room.findOne({name: 'general'});

if (generalByName) {
    print(`✅ Найден канал с name: "general"`);
    print(`   ID канала: ${generalByName._id}`);
    print(`   fname: ${generalByName.fname || 'нет'}`);

    // Проверяем какой у него ID
    if (generalByName._id === 'GENERAL') {
        print('⚠️ ПРОБЛЕМА НАЙДЕНА: ID = "GENERAL" (большими), но в коде используется "general" (маленькими)');
        print('🔧 ИСПРАВЛЯЮ: Меняю ID с "GENERAL" на "general"');

        // Создаем новый канал с правильным ID
        const newChannel = Object.assign({}, generalByName);
        newChannel._id = 'general';

        // Вставляем новый канал
        db.rocketchat_room.insertOne(newChannel);
        print('✅ Создан канал с ID "general"');

        // Обновляем подписки
        db.rocketchat_subscription.updateMany(
            {rid: 'GENERAL'},
            {$set: {rid: 'general'}}
        );
        print('✅ Обновлены подписки');

        // Обновляем сообщения
        db.rocketchat_message.updateMany(
            {rid: 'GENERAL'},
            {$set: {rid: 'general'}}
        );
        print('✅ Обновлены сообщения');

        // Удаляем старый канал
        db.rocketchat_room.deleteOne({_id: 'GENERAL'});
        print('✅ Удален старый канал GENERAL');

        print('🎉 ПРОБЛЕМА ИСПРАВЛЕНА! Канал теперь имеет ID "general"');

    } else if (generalByName._id === 'general') {
        print('✅ ID канала уже правильный: "general"');
        print('❌ ПРОБЛЕМА В ДРУГОМ МЕСТЕ - возможно в URL или в коде switchChannel');

    } else {
        print(`⚠️ СТРАННАЯ СИТУАЦИЯ: ID канала = "${generalByName._id}"`);
        print('🔧 ИСПРАВЛЯЮ: Меняю ID на "general"');

        // Обновляем ID канала напрямую
        db.rocketchat_room.updateOne(
            {name: 'general'},
            {$set: {_id: 'general'}}
        );
        print('✅ ID канала изменен на "general"');
    }

} else {
    print('❌ КАНАЛ С ИМЕНЕМ "general" НЕ НАЙДЕН!');

    // Проверяем есть ли канал с ID GENERAL
    const generalById = db.rocketchat_room.findOne({_id: 'GENERAL'});
    if (generalById) {
        print(`✅ Найден канал с ID "GENERAL", name: "${generalById.name}"`);
        print('🔧 ПЕРЕИМЕНОВЫВАЮ ID на "general"');

        generalById._id = 'general';
        db.rocketchat_room.insertOne(generalById);
        db.rocketchat_room.deleteOne({_id: 'GENERAL'});

        print('✅ Канал переименован');
    }
}

print('');
print('🎯 ФИНАЛЬНАЯ ПРОВЕРКА:');
const finalCheck = db.rocketchat_room.findOne({name: 'general'});
if (finalCheck) {
    print(`✅ Канал "general" найден с ID: "${finalCheck._id}"`);
} else {
    print('❌ Канал "general" не найден!');
}

print('ГОТОВО!');
