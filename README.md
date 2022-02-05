# Foodgram - «Продуктовый помощник»

## http://51.250.27.127/

### Описание проекта:
Cервис, где пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

### Технологии:
    Python 3.9.5
    Django 2.2.26
    Django REST framework 3.12.4
    PostgreSQL
    Nginx
    Docker

### Структура .env файла:
```
SECRET_KEY=SUP3R-S3CR3T-K3Y-F0R-MY-PR0J3CT
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

### Подготовка сервера
```
Скопировать файлы docker-compose.yaml и default.conf из проекта на сервер в home/<username>/foodgram/deploy/
Скопировать frontend/ в home/<username>/foodgram/
```

Запускаем:
```
docker-compose up -d
```

При первом развертывании на сервере выполняем миграции cоздаем суперюзера и собираем статику:
```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --no-input 
docker-compose exec web python manage.py createsuperuser
```

Загружаем фикстуры:
```
docker-compose exec web python manage.py importcsv --path "data/ingredients.csv" --model_name "recipes.Ingredient"
docker-compose exec web python manage.py importcsv --path "data/tags.csv" --model_name "recipes.Tag"
```

Остановка:

```
docker-compose down -v
```

### Автор:
Михаил Макаров (Michael M.)

### P.S.
При развертывании на своем серсере не забываем прописать адреса в конфиге nginx!