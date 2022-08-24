Установка:

1. Скачиваем файлы docker-compose.yml и .env-template
2. Вписываем в переменные нужные нам значения и переименовываем файл в .env:
    TELEGRAM_BOT_TOKEN=''                 - Токен телеграмм бота
    AWX_READ_TOKEN=''                     - Токен AWX для чтения
    AWX_WRITE_TOKEN=''                    - Токен AWX для записи
    AWX_URL='http://172.16.100.100'       - URL AWX'a                     

    TEMPLATES='21;22'                     - ID Шаблонов для выполнения
    USERS='375888379;5178466767'          - ID Пользователей 
3. Запускаем docker-compose: docker compose up -d