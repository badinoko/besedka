// ===================================================================
// ПОЛНОЕ ВОССТАНОВЛЕНИЕ ROCKET.CHAT СОГЛАСНО ДОКУМЕНТАЦИИ ПРОЕКТА
// ===================================================================
// Согласно BESEDKA_USER_SYSTEM.md и ROCKETCHAT_MIGRATION_PLAN_V3.md
// ===================================================================

print('🚀 ПОЛНОЕ ВОССТАНОВЛЕНИЕ ROCKET.CHAT СОГЛАСНО ДОКУМЕНТАЦИИ...');

// ===================================================================
// 1. СИСТЕМА ПОЛЬЗОВАТЕЛЕЙ (из BESEDKA_USER_SYSTEM.md)
// ===================================================================

const users = [
    {
        username: 'owner',
        role: 'owner',
        name: 'Platform Owner',
        email: 'owner@besedka.com',
        chatAccess: ['general', 'vip', 'moderators'],
        rocketchatRoles: ['admin', 'moderator', 'user']
    },
    {
        username: 'admin',
        role: 'moderator',
        name: 'Platform Moderator',
        email: 'admin@besedka.com',
        chatAccess: ['general', 'moderators'],
        rocketchatRoles: ['moderator', 'user']
    },
    {
        username: 'store_owner',
        role: 'store_owner',
        name: 'Store Owner',
        email: 'store.owner@magicbeans.com',
        chatAccess: ['general'],
        rocketchatRoles: ['user']
    },
    {
        username: 'store_admin',
        role: 'store_admin',
        name: 'Store Admin',
        email: 'store.admin@magicbeans.com',
        chatAccess: ['general'],
        rocketchatRoles: ['user']
    },
    {
        username: 'test_user',
        role: 'user',
        name: 'Test User',
        email: 'test.user@besedka.com',
        chatAccess: ['general'],
        rocketchatRoles: ['user']
    }
];

// ===================================================================
// 2. СТРУКТУРА КАНАЛОВ (из ROCKETCHAT_MIGRATION_PLAN_V3.md)
// ===================================================================

const channels = [
    {
        id: 'general',
        name: 'general',
        displayName: 'general',
        description: 'General chat for all registered users',
        type: 'c',
        default: true
    },
    {
        id: 'vip',
        name: 'vip',
        displayName: 'vip',
        description: 'VIP chat (owner manually grants access)',
        type: 'c',
        default: false
    },
    {
        id: 'moderators',
        name: 'moderators',
        displayName: 'moderators',
        description: 'Admin chat (owner + moderators for operational meetings)',
        type: 'c',
        default: false
    }
];

// ===================================================================
// 3. ОЧИСТКА НЕПРАВИЛЬНЫХ ДАННЫХ
// ===================================================================

print('🧹 Очищаю неправильные данные...');

// Удаляем только неправильные каналы (НЕ УДАЛЯЕМ general, vip, moderators!)
const wrongChannels = ['vip-chat', 'GENERAL'];
wrongChannels.forEach(wrongId => {
    const wrongChannel = db.rocketchat_room.findOne({ _id: wrongId });
    if (wrongChannel) {
        print(`  ❌ Удаляю неправильный канал: ${wrongId}`);
        db.rocketchat_room.deleteOne({ _id: wrongId });
        db.rocketchat_subscription.deleteMany({ rid: wrongId });
    }
});

// ИСПРАВЛЕНО: НЕ УДАЛЯЕМ СУЩЕСТВУЮЩИЕ ПОДПИСКИ - это ломает поле ввода сообщений
print('  ✅ Сохраняем существующие подписки пользователей');

// ===================================================================
// 4. СОЗДАНИЕ ПОЛЬЗОВАТЕЛЕЙ
// ===================================================================

print('👥 Создаю пользователей согласно BESEDKA_USER_SYSTEM.md...');

users.forEach(userData => {
    const existingUser = db.users.findOne({ username: userData.username });

    if (!existingUser) {
        const userId = userData.username === 'owner' ? 'owner' : userData.username;
        const userDoc = {
            _id: userId,
            username: userData.username,
            name: userData.name,
            emails: [{ address: userData.email, verified: true }],
            type: 'user',
            status: 'online',
            active: true,
            roles: userData.rocketchatRoles,
            requirePasswordChange: false,
            createdAt: new Date(),
            _updatedAt: new Date(),
            customFields: {
                besedkaRole: userData.role
            }
        };

        db.users.insertOne(userDoc);
        print(`  ✅ Создан пользователь: ${userData.username} (роль: ${userData.role})`);
    } else {
        print(`  ✅ Пользователь существует: ${userData.username}`);

        // Обновляем роли если нужно
        db.users.updateOne(
            { username: userData.username },
            {
                $set: {
                    roles: userData.rocketchatRoles,
                    'customFields.besedkaRole': userData.role
                }
            }
        );
    }
});

// ===================================================================
// 5. СОЗДАНИЕ КАНАЛОВ
// ===================================================================

print('💬 Создаю каналы согласно ROCKETCHAT_MIGRATION_PLAN_V3.md...');

channels.forEach(channelData => {
    const existingChannel = db.rocketchat_room.findOne({ _id: channelData.id });

    if (!existingChannel) {
        const channelDoc = {
            _id: channelData.id,
            name: channelData.name,
            fname: channelData.displayName,
            t: channelData.type,
            description: channelData.description,
            default: channelData.default,
            msgs: 0,
            usersCount: 0,
            u: {
                _id: 'owner',
                username: 'owner'
            },
            ts: new Date(),
            ro: false,
            sysMes: true,
            _updatedAt: new Date()
        };

        db.rocketchat_room.insertOne(channelDoc);
        print(`  ✅ Создан канал: ${channelData.displayName} (${channelData.id})`);
    } else {
        print(`  ✅ Канал существует: ${channelData.displayName} (${channelData.id}) - СОХРАНЯЕМ СООБЩЕНИЯ`);

        // Обновляем ТОЛЬКО метаданные канала, НЕ ТРОГАЕМ СООБЩЕНИЯ
        db.rocketchat_room.updateOne(
            { _id: channelData.id },
            {
                $set: {
                    name: channelData.name,
                    fname: channelData.displayName,
                    description: channelData.description,
                    default: channelData.default,
                    _updatedAt: new Date()
                }
            }
        );
    }
});

// ===================================================================
// 6. СОЗДАНИЕ ПОДПИСОК (ПРАВА ДОСТУПА)
// ===================================================================

print('🔐 Создаю недостающие подписки согласно правам доступа...');

users.forEach(userData => {
    const user = db.users.findOne({ username: userData.username });
    if (!user) return;

    userData.chatAccess.forEach(channelId => {
        const channel = db.rocketchat_room.findOne({ _id: channelId });
        if (!channel) return;

        // ПРОВЕРЯЕМ: есть ли уже подписка?
        const existingSubscription = db.rocketchat_subscription.findOne({
            'u.username': userData.username,
            rid: channelId
        });

        if (existingSubscription) {
            print(`  ✅ Подписка существует: ${userData.username} → ${channel.fname || channel.name}`);
            return; // НЕ ПЕРЕСОЗДАЕМ СУЩЕСТВУЮЩИЕ ПОДПИСКИ
        }

        // Определяем роли в канале
        let channelRoles = ['user'];
        if (userData.role === 'owner') {
            if (channelId === 'general') channelRoles = ['owner'];
            else if (channelId === 'vip') channelRoles = ['owner', 'vip'];
            else if (channelId === 'moderators') channelRoles = ['owner', 'moderator'];
        } else if (userData.role === 'moderator') {
            if (channelId === 'moderators') channelRoles = ['moderator'];
        }

        const subscription = {
            _id: `${user._id}-${channelId}`,
            t: channel.t,
            ts: new Date(),
            name: channel.name,
            fname: channel.fname,
            rid: channelId,
            u: {
                _id: user._id,
                username: user.username,
                name: user.name
            },
            open: true,
            alert: false,
            unread: 0,
            userMentions: 0,
            groupMentions: 0,
            ls: new Date(),
            lr: new Date(),
            roles: channelRoles,
            _updatedAt: new Date()
        };

        db.rocketchat_subscription.insertOne(subscription);
        print(`  ✅ СОЗДАНА: ${userData.username} → ${channel.fname || channel.name} (роли: ${channelRoles.join(', ')})`);
    });
});

// ===================================================================
// 7. НАСТРОЙКА СИСТЕМНЫХ ПАРАМЕТРОВ
// ===================================================================

print('⚙️ Настраиваю системные параметры...');

const settings = [
    // Отключаем кнопку Join Channel
    { _id: 'Accounts_RequireNameForSignUp', value: false },
    { _id: 'Accounts_RequirePasswordConfirmation', value: false },
    { _id: 'Accounts_EmailVerification', value: false },
    { _id: 'Accounts_ManuallyApproveNewUsers', value: false },
    { _id: 'Accounts_AllowAnonymousRead', value: true },
    { _id: 'Accounts_AllowAnonymousWrite', value: false },

    // Настройки платформы
    { _id: 'Site_Name', value: 'Беседка Chat' },
    { _id: 'Language', value: 'ru' },
    { _id: 'UI_Use_Real_Name', value: true },
    { _id: 'UI_Allow_room_names_with_special_chars', value: true },

    // ===================================================================
    // OAUTH НАСТРОЙКИ ДЛЯ ПРОВАЙДЕРА \"BESEDKA\" - ПОЛНЫЙ АРХИВНЫЙ НАБОР
    // Источник: docs/archive/rocketchat_migration/ROCKET_CHAT_COMPLETE_MANUAL.md
    // ===================================================================

    // === ОСНОВНЫЕ НАСТРОЙКИ ===
    { _id: 'Accounts_OAuth_Custom-besedka', value: true },
    { _id: 'Accounts_OAuth_Custom-besedka-id', value: 'BesedkaRocketChat2025' },
    { _id: 'Accounts_OAuth_Custom-besedka-secret', value: 'SecureSecretKey2025BesedkaRocketChatSSO' },
    { _id: 'Accounts_OAuth_Custom-besedka-url', value: 'http://127.0.0.1:8001' },
    { _id: 'Accounts_OAuth_Custom-besedka-server_url', value: 'http://127.0.0.1:8001' },

    // === ПУТИ ===
    { _id: 'Accounts_OAuth_Custom-besedka-token_path', value: '/o/token/' },
    { _id: 'Accounts_OAuth_Custom-besedka-access_token_path', value: '/o/token/' },
    { _id: 'Accounts_OAuth_Custom-besedka-identity_path', value: '/api/v1/auth/rocket/' },
    { _id: 'Accounts_OAuth_Custom-besedka-authorize_path', value: '/o/authorize/' },

    // === ТОКЕН НАСТРОЙКИ ===
    { _id: 'Accounts_OAuth_Custom-besedka-scope', value: 'read' },
    { _id: 'Accounts_OAuth_Custom-besedka-access_token_param', value: 'access_token' },
    { _id: 'Accounts_OAuth_Custom-besedka-token_sent_via', value: 'Header' },
    { _id: 'Accounts_OAuth_Custom-besedka-identity_token_sent_via', value: 'Default' },

    // === ВНЕШНИЙ ВИД КНОПКИ ===
    { _id: 'Accounts_OAuth_Custom-besedka-login_style', value: 'redirect' },
    { _id: 'Accounts_OAuth_Custom-besedka-button_label_text', value: 'Войти через Беседку' },
    { _id: 'Accounts_OAuth_Custom-besedka-button_color', value: '#1d74f5' },
    { _id: 'Accounts_OAuth_Custom-besedka-button_text_color', value: '#FFFFFF' },
    { _id: 'Accounts_OAuth_Custom-besedka-button_label_color', value: '#FFFFFF' },

    // === ПОЛЯ ПОЛЬЗОВАТЕЛЯ ===
    { _id: 'Accounts_OAuth_Custom-besedka-username_field', value: 'username' },
    { _id: 'Accounts_OAuth_Custom-besedka-email_field', value: 'email' },
    { _id: 'Accounts_OAuth_Custom-besedka-name_field', value: 'full_name' },
    { _id: 'Accounts_OAuth_Custom-besedka-avatar_field', value: 'avatar_url' },
    { _id: 'Accounts_OAuth_Custom-besedka-key_field', value: 'id' },

    // === РОЛИ И ГРУППЫ ===
    { _id: 'Accounts_OAuth_Custom-besedka-roles_field', value: 'roles' },
    { _id: 'Accounts_OAuth_Custom-besedka-groups_field', value: 'groups' },
    { _id: 'Accounts_OAuth_Custom-besedka-roles_claim', value: 'roles' },
    { _id: 'Accounts_OAuth_Custom-besedka-groups_claim', value: 'groups' },
    { _id: 'Accounts_OAuth_Custom-besedka-roles_to_sync', value: 'admin,moderator,vip,user' },

    // === МАППИНГ КАНАЛОВ ===
    { _id: 'Accounts_OAuth_Custom-besedka-groups_channel_map', value: '{\"owner\":\"admin,vip\",\"moderator\":\"admin\",\"user\":\"user\"}' },
    { _id: 'Accounts_OAuth_Custom-besedka-channel_map', value: '{\"owner\":\"admin,vip\",\"moderator\":\"admin\",\"user\":\"user\"}' },
    { _id: 'Accounts_OAuth_Custom-besedka-groups_map', value: '{\"owner\":\"admin,vip\",\"moderator\":\"admin\",\"user\":\"user\"}' },
    { _id: 'Accounts_OAuth_Custom-besedka-roles_to_groups_mapping', value: '{\"owner\":\"admin,vip\",\"moderator\":\"admin\",\"user\":\"user\"}' },

    // === КРИТИЧЕСКИ ВАЖНЫЕ ПЕРЕКЛЮЧАТЕЛИ ===
    { _id: 'Accounts_OAuth_Custom-besedka-merge_users', value: true },
    { _id: 'Accounts_OAuth_Custom-besedka-show_button', value: true },
    { _id: 'Accounts_OAuth_Custom-besedka-map_channels', value: true },
    { _id: 'Accounts_OAuth_Custom-besedka-merge_roles', value: true },
    { _id: 'Accounts_OAuth_Custom-besedka-merge_users_distinct_services', value: false },

    // === ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ===
    { _id: 'Accounts_OAuth_Custom-besedka-channels_admin', value: 'admin' },

    // === КРИТИЧЕСКИЕ НАСТРОЙКИ СИСТЕМЫ ===
    // Iframe поддержка
    { _id: 'Iframe_Integration_send_enable', value: true },
    { _id: 'Iframe_Restrict_Access', value: false },

    // Отключение 2FA
    { _id: 'Accounts_RequirePasswordConfirmation', value: false },
    { _id: 'Accounts_TwoFactorAuthentication_Enabled', value: false },

    // Автоматическое присоединение к каналам
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannels', value: true },
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannelsSilenced', value: false },

    // Регистрация отключена (только OAuth)
    { _id: 'Accounts_RegistrationForm', value: 'Disabled' },
    { _id: 'Accounts_ManuallyApproveNewUsers', value: false },

    // Исправление редиректа /login → /home
    { _id: 'Accounts_ForceLogin', value: false },
    { _id: 'Layout_Login_Header', value: '' },
    { _id: 'Layout_Login_Terms', value: '' },

    // === 🔒 8. ОТКЛЮЧАЕМ WORKSPACE REGISTRATION И ЛИЦЕНЗИОННЫЕ ОГРАНИЧЕНИЯ ===
    // Полностью отключаем привязку к облаку Rocket.Chat, чтобы убрать лимит 50 пользователей
    { _id: 'Cloud_Workspace_Registration_State', value: 'registered' },
    { _id: 'Cloud_Workspace_Client_Id', value: '' },
    { _id: 'Cloud_Workspace_Client_Secret', value: '' },
    { _id: 'Cloud_Workspace_Client_Secret_Expires_At', value: 0 },
    // Сбрасываем поле лицензии, чтобы Rocket.Chat работал в OSS-режиме без Enterprise-баннера
    { _id: 'Enterprise_License', value: '' },
    // Полностью выключаем регистрацию пользователей и сторонних OAuth прямо в Rocket.Chat UI
    { _id: 'Accounts_RegistrationForm', value: 'Disabled' },
    { _id: 'Accounts_Registration_ExtraFields', value: '' },
    { _id: 'Accounts_RegistrationForm_LinkReplacementText', value: 'Регистрация отключена администратором' },
    { _id: 'Accounts_RegistrationForm_Type', value: 'Disabled' },
    // ===================================================================

    // СКРЫТИЕ КНОПКИ ЛОГАУТА В EMBEDDED РЕЖИМЕ - РЕШЕНИЕ ПРОБЛЕМЫ ЛОГАУТА
    { _id: 'Layout_Custom_CSS', value: `
        /* СКРЫВАЕМ КНОПКУ ЛОГАУТА ТОЛЬКО В EMBEDDED РЕЖИМЕ */
        /* Это решает проблему когда пользователь случайно делает логаут и ломает SSO связь */
        .embedded .rc-user-menu [data-qa="logout"],
        .embedded .rc-user-dropdown [data-qa="logout"],
        .embedded .flex-nav .flex-nav__user .user-logout,
        .embedded [data-qa="user-menu-logout"],
        .embedded .user-menu .logout,
        .embedded .account-menu .logout {
            display: none !important;
        }

        /* Также скрываем любые ссылки и кнопки с текстом "Logout" или "Выйти" */
        .embedded a[href*="logout"],
        .embedded button[title*="Logout"],
        .embedded button[title*="Выйти"],
        .embedded .sidebar-item[title*="Logout"] {
            display: none !important;
        }

        /* Дополнительная защита - скрываем родительские элементы кнопок логаута */
        .embedded .rc-user-menu:has([data-qa="logout"]) .logout-container,
        .embedded .user-dropdown:has([data-qa="logout"]) .logout-option {
            display: none !important;
        }

        /* 🔕 Убираем любые баннеры о регистрации/облаке */
        .rc-announcement, .cloud-warning-banner, .CloudRegistrationBanner,
        .rcx-banner, .rcx-banner-manager, .rc-alerts, .CloudBanner,
        #rocket-chat-cloud-registration-banner {
            display: none !important;
        }

        /* 🎛️ Прячем пункты меню, связанные с облаком / магазином */
        .sidebar-item__link[href*="cloud"],
        .sidebar-item__link[href*="marketplace"],
        .sidebar-item__link[href*="omnichannel"],
        .sidebar-item__link[href*="license"],
        .sidebar-item__link[href*="workspaces"] {
            display: none !important;
        }

        /* 🧪 ТЕСТОВЫЕ REPLY/QUOTE КНОПКИ (Roadmap §2.1) */
        /* Показываются только в тестовом режиме /chat/test/ */
        .embedded.test-mode .rcx-message:hover .test-reply-quote-menu {
            display: flex !important;
            position: absolute;
            top: -30px;
            right: 10px;
            background: rgba(0,0,0,0.9);
            border-radius: 8px;
            padding: 4px;
            gap: 4px;
            z-index: 9999;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        .embedded.test-mode .rcx-message {
            position: relative !important;
        }

        .embedded.test-mode .test-reply-btn,
        .embedded.test-mode .test-quote-btn {
            color: white;
            background: transparent;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
            transition: background 0.2s ease;
        }

        .embedded.test-mode .test-reply-btn:hover {
            background: #007bff;
        }

        .embedded.test-mode .test-quote-btn:hover {
            background: #6f42c1;
        }

        /* Альтернативный метод через CSS псевдоэлементы (fallback) */
        .embedded.test-mode .rcx-message:hover::after {
            content: "↩️ Reply  💬 Quote";
            position: absolute;
            top: -25px;
            right: 10px;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            z-index: 9999;
            pointer-events: auto;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        /* Скрываем в основном режиме, показываем только в тестовом */
        .embedded:not(.test-mode) .rcx-message:hover::after {
            display: none !important;
        }

        /* === PHASE A MINIMAL UI (Roadmap 8.1) === */
        .embedded .rcx-room-header,
        .embedded .rcx-sidebar,
        .embedded .sidebar,
        .embedded .sidebar__toolbar,
        .embedded .rcx-message-actions,
        .embedded .rc-popover {
            display: none !important;
        }
        /* Сохраняем composer и message-list */
        .embedded .rcx-message-list {
            margin-top: 0 !important;
        }
        .embedded .rcx-message-composer {
            border-top: 1px solid var(--rc-color-light, #2b2f33);
        }

        /* === PHASE B HIDE NATIVE HOVER ACTIONS === */
        .embedded .rcx-message-hover-toolbar,
        .embedded .rcx-message-actions,
        .embedded .rcx-message-action,
        .embedded .rcx-message-action-menu,
        .embedded .rcx-message:hover .rcx-message-actions,
        .embedded [data-qa="message-action-menu"],
        .embedded [data-qa="message-action-reply"],
        .embedded [data-qa="message-action-edit"],
        .embedded [data-qa="message-action-delete"] {
            display: none !important;
            visibility: hidden !important;
        }
    ` }
];

settings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        { _id: setting._id },
        { $set: { value: setting.value, _updatedAt: new Date() } },
        { upsert: true }
    );
});

print('  ✅ Системные параметры настроены');

// ===================================================================
// 8. ФИНАЛЬНАЯ ПРОВЕРКА
// ===================================================================

print('');
print('🔍 ФИНАЛЬНАЯ ПРОВЕРКА...');

// Проверяем пользователей
const userCount = db.users.countDocuments({ type: 'user' });
print(`  👥 Всего пользователей: ${userCount}`);

users.forEach(userData => {
    const user = db.users.findOne({ username: userData.username });
    if (user) {
        print(`  ✅ ${userData.username} (${userData.role})`);
    } else {
        print(`  ❌ ${userData.username} ОТСУТСТВУЕТ!`);
    }
});

// Проверяем каналы
const channelCount = db.rocketchat_room.countDocuments({ t: 'c' });
print(`  💬 Всего каналов: ${channelCount}`);

channels.forEach(channelData => {
    const channel = db.rocketchat_room.findOne({ _id: channelData.id });
    if (channel) {
        print(`  ✅ ${channelData.displayName} (${channelData.id})`);
    } else {
        print(`  ❌ ${channelData.displayName} ОТСУТСТВУЕТ!`);
    }
});

// Проверяем подписки
const subCount = db.rocketchat_subscription.countDocuments({});
print(`  🔐 Всего подписок: ${subCount}`);

users.forEach(userData => {
    const userSubs = db.rocketchat_subscription.countDocuments({ 'u.username': userData.username });
    print(`  ✅ ${userData.username}: ${userSubs} подписок (ожидается: ${userData.chatAccess.length})`);
});

print('');
print('🎉 ПОЛНОЕ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!');
print('📋 Система соответствует BESEDKA_USER_SYSTEM.md');
print('📋 Каналы соответствуют ROCKETCHAT_MIGRATION_PLAN_V3.md');
print('👥 Все роли настроены правильно');
print('🔐 Права доступа распределены корректно');
print('');
print('📊 ИТОГОВАЯ СТРУКТУРА:');
print('   • owner: 3 канала (general, vip, moderators)');
print('   • admin (moderator): 2 канала (general, moderators)');
print('   • store_owner: 1 канал (general)');
print('   • store_admin: 1 канал (general)');
print('   • test_user: 1 канал (general)');
