# Виртуальный деканат

Учебная веб-система управления студенческой практикой. Реализует идентификацию и аутентификацию, ролевой контроль доступа (ACL) и личный кабинет с разным содержимым для каждой роли.

**Стек:** Python 3 · Flask · Flask-Login · Flask-SQLAlchemy · PostgreSQL · Bootstrap 5

---

## Сборка и запуск

### 1. Зависимости

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. База данных

Создайте БД в PostgreSQL и примените схему:

```bash
psql -U postgres -c "CREATE DATABASE virtual_dekanat;"
psql -U postgres virtual_dekanat < schema.sql
```

По умолчанию приложение подключается как `postgres:postgres@localhost:5432/virtual_dekanat`. Чтобы использовать другие параметры — задайте переменную окружения:

```bash
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
```

### 3. Тестовые данные

```bash
python seed.py
```

Скрипт пересоздаёт все таблицы и добавляет по одному пользователю каждой роли.

### 4. Запуск сервера

```bash
flask --app app:create_app run --debug
```

Приложение будет доступно по адресу <http://localhost:5000>.

---

## Вход в систему

Откройте <http://localhost:5000/login>.

| Логин | Пароль | Роль |
|---|---|---|
| `admin` | `admin123` | Администратор |
| `teacher` | `teacher123` | Преподаватель |
| `curator` | `curator123` | Куратор |
| `student` | `student123` | Студент |

После успешного входа происходит автоматический редирект на `/dashboard`.

---

## Маршруты

### Аутентификация

| Метод | URL | Описание |
|---|---|---|
| `GET` | `/login` | Страница входа |
| `POST` | `/login` | Отправка формы (логин + пароль) |
| `GET` | `/logout` | Завершение сессии, редирект на `/login` |

### Личный кабинет

| Метод | URL | Кто имеет доступ | Описание |
|---|---|---|---|
| `GET` | `/` | все авторизованные | Редирект на `/dashboard` |
| `GET` | `/dashboard` | все авторизованные | Личный кабинет — содержимое зависит от роли |

### Панель администратора

| Метод | URL | Кто имеет доступ | Описание |
|---|---|---|---|
| `GET` | `/admin/users` | `admin` | Список всех пользователей |
| `GET` | `/admin/users/new` | `admin` | Форма создания пользователя |
| `POST` | `/admin/users/new` | `admin` | Создание нового пользователя |
| `POST` | `/admin/users/<id>/role` | `admin` | Смена роли пользователя |
| `POST` | `/admin/users/<id>/toggle` | `admin` | Активация / деактивация пользователя |

Обращение к маршрутам `/admin/*` с любой ролью кроме `admin` возвращает страницу **403 Forbidden**.

---

## Содержимое личного кабинета по ролям

**Студент** — ФИО, группа, направление подготовки; организация, период практики, руководители; таблица заданий со статусом выполнения.

**Куратор** — ФИО, организация; таблица закреплённых студентов с прогрессом по заданиям.

**Преподаватель** — ФИО, кафедра; таблица студентов с указанием организации, периода практики и прогресса.

**Администратор** — таблица всех пользователей с возможностью сменить роль и деактивировать/активировать учётную запись, а также создать нового пользователя.

---

## Структура проекта

```
├── app.py                        # Фабрика Flask-приложения
├── config.py                     # DATABASE_URL, SECRET_KEY
├── models.py                     # SQLAlchemy-модели (User, Student, Teacher, Curator, Organization, Task)
├── schema.sql                    # DDL для создания таблиц
├── seed.py                       # Тестовые данные
├── requirements.txt
├── access/
│   └── decorators.py             # Декоратор @requires_role
├── auth/
│   └── routes.py                 # /login, /logout
├── dashboard/
│   └── routes.py                 # /dashboard, /admin/users
└── templates/
    ├── base.html                 # Общий шаблон (navbar, Bootstrap 5)
    ├── login.html
    ├── 403.html / 404.html
    └── dashboard/
        ├── student.html
        ├── curator.html
        ├── teacher.html
        ├── admin.html
        └── admin_user_form.html
```
