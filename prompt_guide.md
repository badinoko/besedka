## 🌐 Project: MagicBeans (Warehouse Panel + Telegram Bot)

### 🧠 Purpose

To build a Django-based admin panel for managing a cannabis seed warehouse. Telegram bot (MVP) will support catalog browsing, filtering, and submitting non-payment requests. Long-term: full integration.

---

### 📁 Models & Fields

#### `SeedBank`

* `name`: CharField(max\_length=100)
* `description`: TextField(blank=True, null=True)
* `logo`: ImageField(upload\_to="seedbank\_logos/", blank=True, null=True)
* `is_visible`: BooleanField(default=True)

#### `Strain`

* `name`: CharField(max\_length=100)
* `description`: TextField(blank=True, null=True)
* `strain_type`: CharField(choices=\[("auto", "Auto"), ("photo", "Photo")])
* `seedbank`: ForeignKey to `SeedBank`, on\_delete=CASCADE
* `is_visible`: BooleanField(default=True)

#### `PackSize`

* `strain`: ForeignKey to `Strain`, on\_delete=CASCADE
* `pack_size`: CharField(max\_length=20)
* `price`: DecimalField(max\_digits=10, decimal\_places=2)
* `quantity`: IntegerField

#### `Photo`

* `strain`: ForeignKey to `Strain`, on\_delete=CASCADE
* `image`: ImageField(upload\_to="strain\_photos/")

#### `User`

* Extend with custom role: admin / owner

#### `ActionLog`

* Record admin actions (for owner access)

---

### 👥 Permissions Matrix

| Feature                            | Admin | Owner |
| ---------------------------------- | ----- | ----- |
| Add/edit seeds & packaging         | ✅     | ✅     |
| Toggle visibility of banks/strains | ✅     | ✅     |
| Delete                             | Soft  | Hard  |
| Import/export inventory            | ❌     | ✅     |
| Manage admin users                 | ❌     | ✅     |
| View logs/backups                  | ❌     | ✅     |

---

### ✅ Admin UX — Add New Strain

1. Select type: Auto / Photo
2. Enter name
3. Add pack sizes: 1, 3, 5, 10, or custom (e.g., "5+2")
4. Set price and quantity per pack
5. Optional: Upload photos, write description

Visibility status editable later (not at creation stage)

---

### 🔧 Dev Steps

1. ✅ Confirm model structure
2. ✅ Create Django models (with all field types)
3. ✅ Build admin panel views with usability in mind
4. 🔜 Implement static warehouse interface (no bot yet)

---

### 🤖 Telegram Bot (v2+)

* View catalog
* Filter/search by bank, strain type
* Add to cart
* Submit request (no payment yet)
* Reflect stock from Django DB

---

### 📂 Prompts for Cursor (Admin Automation)

#### ☑️ Автозапуск

```plaintext
Построй миграции и админку для всех моделей, затем автоматически зарегистрируй их.
Укажи путь к `docker-compose.yml`, проверь зависимости в `requirements.txt`, запусти сервер и сообщи ссылку на `http://127.0.0.1:8000/admin/`
```

#### ☑️ Расширение панели администратора

```plaintext
Добавь возможность скрывать/показывать сидбанки и сорта. Сделай это через галочки в списках и отдельное поле в админке (`is_visible`). Убедись, что при скрытии элементы не отображаются в списке.
```

#### ☑️ Проверка данных

```plaintext
Создай тестовые сидбанки, сорта и фасовки. Проверь, как они отображаются в админке и как работает фильтрация. Убедись, что у сортов могут быть одинаковые названия, но разные сидбанки.
```

#### ☑️ Журнал действий

```plaintext
Добавь логирование действий админов (модель `ActionLog`). Записывай: кто и что добавил/изменил/удалил, дату и объект. Показывай только владельцу.
```

#### ☑️ Упрощение интерфейса

```plaintext
Приведи в порядок интерфейс админки:

1. Удали все ненужные разделы и модели из панели администратора, кроме:
   - Сидбанки
   - Сорта
   - Фасовки
   - Изображения сортов
   - Движения товара
   - Журнал действий (виден только владельцу)
   - Импорт/экспорт остатков (виден только владельцу)

2. Размести оставшиеся разделы логично и компактно (например, сгруппируй в 2–3 секции).

3. Настрой порядок отображения в `ModelAdmin` и используемые `list_display`, `list_filter`, `search_fields`.

Не забудь ограничить доступ к разделам владельцу/админу в зависимости от ролей.
```

---

### 🧾 .cursorules (ENGLISH — Project Rules)

```plaintext
- Always reply in Russian.
- The user is a beginner; explain all results in simple terms.
- The project is a Django-based admin panel for warehouse inventory.
- All code must use `models.py`, `admin.py`, `forms.py`, and Docker-based environments.
- Do not ask the user for confirmations unless there's ambiguity.
- Use complete file outputs, never line-by-line edits.
- Consider project root files: `.env`, `requirements.txt`, `docker-compose.yml`.
- PostgreSQL is the default DB.
```

---