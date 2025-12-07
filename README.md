# Telegram Parser

Минималистичное приложение для парсинга сообщений из Telegram с использованием Telethon.

## Возможности

- Авторизация в Telegram по номеру телефона
- Надежное хранение и восстановление сессии (StringSession с AES-шифрованием)
- Выбор чата и парсинг текстовых сообщений за нужный период
- Локальная база данных SQLite (WAL режим) без блокировок
- Простой веб-интерфейс на React

## Архитектура

### Backend
- FastAPI (async)
- Telethon для работы с Telegram API
- SQLite с WAL режимом и SQLAlchemy (async)
- AES-шифрование StringSession
- Логи только ERROR и WARNING

### Frontend
- React 18 + Vite
- Минимальный интерфейс для управления парсером

## Быстрый старт

### Windows
```bash
setup.bat
```

### Linux/Mac
```bash
chmod +x setup.sh
./setup.sh
```

### Ручная установка

1. **Получите API ключи Telegram:**
   - Зайдите на https://my.telegram.org/apps
   - Создайте новое приложение
   - Скопируйте `api_id` и `api_hash`

2. **Настройте .env файл:**
```bash
cp .env.example .env
# Отредактируйте .env:
AES_SECRET_KEY=your-secret-key-here-32-chars
TELETHON_API_ID=your_api_id
TELETHON_API_HASH=your_api_hash
```

3. **Запустите приложение:**

Backend:
```bash
cd backend
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
python run.py
```

Frontend:
```bash
cd frontend
npm run dev
```

4. **Откройте http://localhost:5173**

## Использование

1. **Авторизация:**
   - Введите номер телефона
   - Введите код из Telegram
   - Сессия будет сохранена и зашифрована

3. **Парсинг сообщений:**
   - Нажмите "Загрузить список чатов"
   - Выберите чат из списка
   - Укажите период (опционально)
   - Нажмите "Начать парсинг"
   - Следите за прогрессом в реальном времени
   - Нажмите "Показать сообщения" для просмотра результатов

4. **Управление сессией:**
   - "Сбросить сессию" - удалить сохраненную сессию
   - При проблемах с авторизацией используйте кнопку сброса

## API Endpoints

### Авторизация
- `POST /auth/request-code` - запрос кода
- `POST /auth/confirm-code` - подтверждение кода
- `GET /auth/status` - статус авторизации
- `POST /auth/reset` - сброс сессии

### Telegram
- `GET /telegram/chats` - список чатов
- `POST /telegram/fetch-messages` - начать парсинг
- `GET /telegram/progress` - прогресс парсинга
- `GET /telegram/messages?chat_id=X&limit=50&offset=0` - получить сохраненные сообщения

## Структура проекта

```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI приложение
│   │   ├── config.py        # Конфигурация
│   │   ├── database.py      # Модели и настройки БД
│   │   ├── telegram_manager.py # Управление Telegram
│   │   ├── encryption.py    # AES шифрование
│   │   ├── schemas.py       # Pydantic модели
│   │   └── logger.py        # Настройка логов
│   └── run.py              # Запуск backend
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Главный компонент
│   │   └── index.css       # Стили
│   └── package.json
├── .env.example            # Пример конфига
├── requirements.txt         # Python зависимости
├── setup.sh               # Скрипт установки (Linux/Mac)
├── setup.bat              # Скрипт установки (Windows)
└── README.md              # Документация
```

## Безопасность

- StringSession шифруется с помощью AES-256
- Все чувствительные данные хранятся локально
- Логи содержат только ошибки и предупреждения
- Нет передачи данных на внешние серверы

## Обработка ошибок

Приложение обрабатывает следующие ситуации:
- Потеря сессии и необходимость повторной авторизации
- FloodWait от Telegram
- Блокировки SQLite (автоматический retry)
- Ошибки сети и подключения

## Требования

- Python 3.8+
- Node.js 16+
- Telegram API ключи

## Лицензия

MIT