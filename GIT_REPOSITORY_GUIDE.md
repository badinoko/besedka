# 🗂️ Руководство по Git Репозиториям Проекта "Беседка"

**Дата создания:** 21 июня 2025  
**Версия:** 1.0

---

## 📚 СТРУКТУРА РЕПОЗИТОРИЕВ

### 🏠 **Основной репозиторий: [besedka](https://github.com/badinoko/besedka)**
- **Назначение:** Активная разработка и экспериментирование
- **Remote name:** `origin`
- **URL:** `https://github.com/badinoko/besedka.git`
- **Управление:** Полностью под управлением AI ассистента
- **Политика push:** Автоматический push при любых значимых изменениях

### 💾 **Резервный репозиторий: [besedka_copy](https://github.com/badinoko/besedka_copy)**
- **Назначение:** Резервное копирование стабильных версий
- **Remote name:** `backup`
- **URL:** `https://github.com/badinoko/besedka_copy.git`
- **Управление:** Push ТОЛЬКО по команде пользователя
- **Политика push:** Ручное управление пользователем

---

## ⚙️ НАСТРОЙКА ЛОКАЛЬНОЙ СРЕДЫ

### Проверка текущих remote репозиториев:
```bash
git remote -v
```

**Ожидаемый результат:**
```
origin  https://github.com/badinoko/besedka.git (fetch)
origin  https://github.com/badinoko/besedka.git (push)
backup  https://github.com/badinoko/besedka_copy.git (fetch)
backup  https://github.com/badinoko/besedka_copy.git (push)
```

### Если remote не настроены:
```bash
# Добавить основной репозиторий
git remote add origin https://github.com/badinoko/besedka.git

# Добавить резервный репозиторий
git remote add backup https://github.com/badinoko/besedka_copy.git
```

---

## 🚀 РАБОЧИЙ ПРОЦЕСС

### 📝 **Стандартный workflow:**

1. **Подготовка изменений:**
   ```bash
   # Проверить статус
   git status
   
   # Добавить все изменения
   git add -A
   
   # Создать коммит
   git commit -m "Описание изменений"
   ```

2. **Push в основной репозиторий (автоматически):**
   ```bash
   git push origin main
   ```

3. **Push в резервный (только по команде пользователя):**
   ```bash
   git push backup main
   ```

---

## 🔧 СПЕЦИАЛЬНЫЕ КОМАНДЫ

### 🔍 **Проверка состояния:**
```bash
# Статус локального репозитория
git status

# Последние коммиты
git log --oneline -10

# Различия с remote
git fetch origin
git log HEAD..origin/main --oneline
```

### 🔄 **Синхронизация:**
```bash
# Получить последние изменения
git fetch origin

# Объединить изменения (если нужно)
git merge origin/main
```

### 📋 **Полезные алиасы:**
```bash
# Добавить в .gitconfig
git config --global alias.pushall '!git push origin main && echo "✅ Pushed to besedka"'
git config --global alias.pushboth '!git push origin main && git push backup main && echo "✅ Pushed to both repos"'
```

---

## 🛡️ ПРАВИЛА И ОГРАНИЧЕНИЯ

### ✅ **AI АССИСТЕНТ МОЖЕТ:**
- Делать push в `origin` (besedka) в любое время
- Создавать коммиты с изменениями
- Управлять ветками в основном репозитории
- Очищать или реорганизовывать основной репозиторий

### ❌ **AI АССИСТЕНТ НЕ МОЖЕТ:**
- Делать push в `backup` (besedka_copy) без команды пользователя
- Удалять данные из резервного репозитория
- Изменять настройки резервного репозитория

### 👤 **ТОЛЬКО ПОЛЬЗОВАТЕЛЬ МОЖЕТ:**
- Давать команды на push в besedka_copy
- Управлять политикой резервного копирования
- Принимать решения о синхронизации между репозиториями

---

## 🚨 ЭКСТРЕННЫЕ ПРОЦЕДУРЫ

### 💥 **Восстановление из резервного репозитория:**
```bash
# Клонировать резервную копию
git clone https://github.com/badinoko/besedka_copy.git recovery_backup

# Добавить основной remote
cd recovery_backup
git remote add main-repo https://github.com/badinoko/besedka.git

# Force push в основной (ОСТОРОЖНО!)
git push main-repo main --force
```

### 🔄 **Принудительная синхронизация:**
```bash
# Синхронизировать backup с основным
git push backup main --force
```

---

## 📊 МОНИТОРИНГ И СТАТИСТИКА

### 📈 **Полезные команды для отслеживания:**
```bash
# Размер репозитория
git count-objects -vH

# Статистика коммитов
git shortlog -sn

# Различия между репозиториями
git log backup/main..origin/main --oneline
```

---

## 🎯 АВТОМАТИЗАЦИЯ

### 🤖 **AI правила:**
1. **Всегда** делать push в `origin` после значимых изменений
2. **Никогда** не делать push в `backup` без команды пользователя
3. **Создавать** описательные commit messages
4. **Обновлять** это руководство при изменении workflow

### 👨‍💻 **Пользователь должен помнить:**
- Команда для push в backup: `git push backup main`
- Резервный репозиторий - для стабильных версий
- Основной репозиторий - для экспериментов

---

## 📞 БЫСТРЫЕ КОМАНДЫ

```bash
# Проверить все
git status && git log --oneline -5 && git remote -v

# Стандартный push в основной
git add -A && git commit -m "Update" && git push origin main

# Экстренный push в оба (только по команде пользователя)
git push backup main
```

---

**🎉 Репозитории настроены и готовы к работе!** 
