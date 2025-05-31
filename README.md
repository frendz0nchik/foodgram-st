### Локальный запуск проекта:

**_Клонировать репозиторий_**
```
git@github.com:frendz0nchik/foodgram-st.git
```

**_В корневой папке файл env.env переименовать в .env и заполнить следующими данными:_**
```
POSTGRES_DB=foodgram_db
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_pass

DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

**_Перейти в каталог infra и запустить docker-compose._**
```
docker-compose up --build
```

**_Создать суперпользователя._**
```
docker-compose exec backend python manage.py createsuperuser
```
Вводим любые  данные и переходим в http://localhost/admin, переходим http://localhost/admin/recipes/ingredient/upload-json/, нажимаем на 'выберите файл', находим папку data, выбираем ingredients.json. Нажимаем загрузить json. После выхода из админки проект будет доступен по адресу: http://localhost/
