// АВТОМАТИЧЕСКОЕ ПРИСОЕДИНЕНИЕ КО ВСЕМ КАНАЛАМ

print('🚀 АВТОМАТИЧЕСКОЕ ПРИСОЕДИНЕНИЕ К КАНАЛАМ...');

// Находим пользователя owner
const owner = db.users.findOne({ username: 'owner' });
if (!owner) {
    print('❌ Пользователь owner не найден!');
    quit();
}

print(`✅ Найден пользователь: ${owner.username} (ID: ${owner._id})`);

// Все каналы для присоединения
const channelIds = ['GENERAL', 'vip', 'moderators'];

channelIds.forEach(channelId => {
    const room = db.rocketchat_room.findOne({ _id: channelId });

    if (!room) {
        print(`❌ Канал не найден: ${channelId}`);
        return;
    }

    print(`\n🔄 Обрабатываю канал: ${room.name} (ID: ${room._id})`);

    // Проверяем подписку
    let subscription = db.rocketchat_subscription.findOne({
        'u._id': owner._id,
        rid: room._id
    });

    if (!subscription) {
        print(`  ❌ Подписка не найдена для канала ${room.name}`);
        return;
    }

    // ОБНОВЛЯЕМ ПОДПИСКУ ДЛЯ АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ
    const updateResult = db.rocketchat_subscription.updateOne(
        { _id: subscription._id },
        {
            $set: {
                // Убираем необходимость присоединения
                open: true,              // Канал открыт
                f: false,                // Не избранное (пока)
                ls: new Date(),          // Последнее посещение = сейчас
                lr: new Date(),          // Последнее прочтение = сейчас
                unread: 0,               // Нет непрочитанных
                alert: false,            // Нет алертов
                _updatedAt: new Date(),  // Время обновления

                // КЛЮЧЕВЫЕ ПОЛЯ ДЛЯ АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ
                t: room.t,               // Тип канала
                name: room.name,         // Имя канала
                fname: room.fname || room.name  // Отображаемое имя
            }
        }
    );

    if (updateResult.modifiedCount > 0) {
        print(`  ✅ Подписка обновлена для автоматического присоединения`);
    } else {
        print(`  ⚠️ Подписка не требовала обновления`);
    }

    // ДОБАВЛЯЕМ ПОЛЬЗОВАТЕЛЯ В СПИСОК УЧАСТНИКОВ КАНАЛА
    const roomUpdateResult = db.rocketchat_room.updateOne(
        { _id: room._id },
        {
            $addToSet: {
                usernames: owner.username  // Добавляем в список участников
            },
            $inc: {
                usersCount: 0  // Не увеличиваем счетчик (если уже есть)
            },
            $set: {
                _updatedAt: new Date()
            }
        }
    );

    if (roomUpdateResult.modifiedCount > 0) {
        print(`  ✅ Пользователь добавлен в список участников канала`);
    } else {
        print(`  ℹ️ Пользователь уже в списке участников`);
    }
});

print('\n🎉 ГОТОВО! Все каналы настроены для автоматического доступа!');

// ПРОВЕРКА РЕЗУЛЬТАТА
print('\n=== ПРОВЕРКА РЕЗУЛЬТАТА ===');
channelIds.forEach(channelId => {
    const room = db.rocketchat_room.findOne({ _id: channelId });
    if (!room) return;

    const subscription = db.rocketchat_subscription.findOne({
        'u._id': owner._id,
        rid: room._id
    });

    if (subscription) {
        print(`✅ ${room.name}:`);
        print(`   - Открыт: ${subscription.open}`);
        print(`   - Непрочитанных: ${subscription.unread}`);
        print(`   - В списке участников: ${room.usernames?.includes(owner.username) ? 'Да' : 'Нет'}`);
    }
});

print('\n🚫 КНОПКА "JOIN CHANNEL" БОЛЬШЕ НЕ ДОЛЖНА ПОЯВЛЯТЬСЯ!');
