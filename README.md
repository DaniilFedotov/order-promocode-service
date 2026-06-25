# order-promocode-service

Django-сервис для создания заказов с поддержкой промокодов.

## Запуск

```bash
git clone https://github.com/DaniilFedotov/order-promocode-service.git
cd order-promocode-service

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# опционально: пустая база с нуля (удобно перед первой проверкой)
rm -f db.sqlite3
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

`requirements-dev.txt` включает runtime-зависимости из `requirements.txt` и пакеты для тестов.

`pytest` использует in-memory SQLite (`TEST.NAME` в settings) и **не пишет** в `db.sqlite3`.

Повторный запуск `seed_demo_data` сбрасывает счётчики использования промокодов.

## Конфигурация

Настройки — в `config/settings.py`. Значения читаются из переменных окружения через `os.environ.get()` при старте приложения. Файла `.env` в репозитории нет: локально можно экспортировать переменные вручную или скопировать `.env.example` и подгрузить через `export $(grep -v '^#' .env | xargs)`. Без переменных используются dev-дефолты (SQLite, `DEBUG=true`).

## Тестовые данные (`seed_demo_data`)

**Пользователи:** `user_id` 1–5 (`demo_user_1` … `demo_user_5`).

**Товары:**

| good_id | Название | Цена | Категория | Промокод |
|---------|----------|------|-----------|----------|
| 1 | T-shirt | 100 | clothes | применяется |
| 2 | Book | 50 | books | исключён из акций |
| 3 | Notebook | 30 | stationery | применяется |

**Промокоды:**

| Код | Скидка | Категории | Статус |
|-----|--------|-----------|--------|
| SUMMER2025 | 10% | clothes | активен |
| ALL20 | 20% | все | активен |
| OLD2020 | 10% | все | просрочен |

## Проверка API

### Postman / curl

`POST http://127.0.0.1:8000/api/v1/orders/`

Authorization: **No Auth**, `Content-Type: application/json`.

```json
{
  "user_id": 1,
  "goods": [{"good_id": 1, "quantity": 2}],
  "promo_code": "SUMMER2025"
}
```

### Swagger UI

Откройте `http://127.0.0.1:8000/api/docs/`, выберите `POST /api/v1/orders/`, нажмите **Try it out** — в поле запроса уже подставлен пример с `SUMMER2025`, нажмите **Execute**.

## Примеры запросов

**1. Заказ с промокодом (успех, total=180):**

```json
{"user_id": 1, "goods": [{"good_id": 1, "quantity": 2}], "promo_code": "SUMMER2025"}
```

**2. Заказ без промокода (user 2, чтобы не пересекаться с кейсом 1):**

```json
{"user_id": 2, "goods": [{"good_id": 1, "quantity": 1}]}
```

**3. Просроченный промокод (ошибка 400):**

```json
{"user_id": 3, "goods": [{"good_id": 1, "quantity": 1}], "promo_code": "OLD2020"}
```

**4. Промокод не применился ни к одной позиции (ошибка 400):**

Только исключённый товар + промо на все категории:

```json
{"user_id": 4, "goods": [{"good_id": 2, "quantity": 1}], "promo_code": "ALL20"}
```

**5. Частичная скидка — два товара, промо только на один (успех, total=130):**

Футболка со скидкой 20%, книга без скидки (исключена из акций):

```json
{"user_id": 5, "goods": [{"good_id": 1, "quantity": 1}, {"good_id": 2, "quantity": 1}], "promo_code": "ALL20"}
```

Ожидаемый ответ: `price=150`, `total=130`; у `good_id=1` → `discount=0.20`, `total=80`; у `good_id=2` → `discount=0.00`, `total=50`.

## Тесты

```bash
pytest
```
