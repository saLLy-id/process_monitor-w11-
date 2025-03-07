# Монитор процессов Windows

Приложение с графическим интерфейсом для мониторинга запущенных процессов и использования системных ресурсов в Windows 11.

## Возможности

- Отображение списка запущенных процессов
- Мониторинг использования CPU, памяти, диска и сети
- Графики использования CPU и памяти в реальном времени
- Сортировка процессов по использованию CPU или памяти
- Периодическое автоматическое обновление данных

## Требования

- Python 3.11 или выше
- Windows 11 (может работать и на Windows 10)
- Библиотеки, указанные в requirements.txt

## Установка

1. Клонируйте репозиторий или скачайте исходный код
2. Создайте виртуальное окружение (рекомендуется):
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

## Запуск

```
python process_monitor.py
```

## Интерфейс

- **Информация о системе**: Отображает общую загрузку CPU, использование памяти, активность диска и сети
- **Графики использования ресурсов**: Показывает графики использования CPU и памяти в реальном времени
- **Запущенные процессы**: Таблица с информацией о каждом процессе (PID, имя, использование CPU и памяти, статус)
- **Кнопки управления**: 
  - "Обновить" - принудительное обновление данных
  - "Сортировать по CPU" - сортировка процессов по использованию CPU
  - "Сортировать по памяти" - сортировка процессов по использованию памяти 