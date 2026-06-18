# Data_Analysis_AI
This is a Data Analysis project made for PMs using AI

## Описание

Steam Analytics Dashboard — инструмент для продакт-менеджеров в геймдеве. Анализирует данные Steam в реальном времени и предоставляет AI-инсайты для принятия продуктовых решений.

## Возможности

- 📊 Отображение текущего онлайна Steam
- 🏆 Топ-N популярных игр с детальной статистикой
- 📈 Графики трендов и пиковых значений
- 🔥 Тепловые карты активности по жанрам
- 🤖 AI-аналитика через Ollama (инсайты и рекомендации)

## Требования

- Python 3.10+
- Ollama (для AI-аналитики)
- Steam Web API ключ

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repo-url>
cd Data_Analysis_AI
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Установите и запустите Ollama:
```bash
# Скачать с https://ollama.com
ollama pull llama3.2
ollama serve
```

4. Получите Steam API ключ:
- Перейдите на https://steamcommunity.com/dev/apikey
- Зарегистрируйте домен и получите ключ

## Запуск

```bash
streamlit run app.py
```

Откройте http://localhost:8501 в браузере.

## Использование

1. Введите Steam API ключ в боковой панели
2. Выберите модель Ollama (если запущена)
3. Настройте количество игр для анализа
4. Нажмите "Загрузить данные"
5. Изучите графики и таблицы
6. Сгенерируйте AI-аналитику кнопкой "Сгенерировать анализ"

## Структура проекта

```
Data_Analysis_AI/
├── app.py              # Streamlit приложение
├── steam_api.py        # Модуль работы с Steam API
├── ollama_client.py    # Модуль работы с Ollama
├── requirements.txt    # Зависимости Python
└── README.md          # Документация
```

## Технологии

- **Streamlit** — UI фреймворк
- **Pandas** — обработка данных
- **Plotly** — визуализации
- **Ollama** — локальная AI-модель
- **Steam Web API** — источник данных
