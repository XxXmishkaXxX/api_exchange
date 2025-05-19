# Toy Exchange API 

## **Запуск проекта**

1. Клонировать репозиторий проекта:
```bash
git clone https://github.com/XxXmishkaXxX/api_exchange.git
cd api_exchange
```
2. Создайте .env во всех сервисах со своими данными или уберите .example из имени env'ов и добавьте свои данные

3. Запустить проект через Docker Compose:
```bash
docker-compose up --build
```

---
## Сервисы и их URL

### 1. **Auth Service**
| **Метод** | **API v1**       | **Query Parameters / Request Body** |**Описание**|
|-----------|------------------|------------------|-------------------------------------|
| POST      | `/api/v1/public/register`| name | Регистрация нового пользователя.|
| DELETE    | `/api/v1/admin/user/{user_id}`| - |Удалить пользователя (только админ).|

---

### 2. **Market Data Service**

| **Метод** | **API v1**                                            | **Query Parameters / Request Body** |**Описание**             |
|-----------|-------------------------------------------------------|--|------------------------------------------------------------|
| GET       | `/api/v1/public/instrument`                           | - | Получить список всех доступных активов.|
| GET       | `/api/v1/public/orderbook/{ticker}`                   | pair (по дефолту RUB)| Получить стакан ордеров по активу.|
| GET       | `/api/v1/public/transactions/{ticker}`                | pair (по дефолту RUB)| Получить все транзакции по паре активов.|
| GET       | `/api/v1/public/transactions/user/{user_id}/{ticker}` | pair (по дефолту RUB) | Получить транзакции пользователя по конкретной паре активов. |
| GET       | `/api/v1/public/transactions/user/{user_id}`          | - | Получить все транзакции пользователя.|
| POST      | `/api/v1/admin/instrument`                            |name, ticker | Создать новый актив (только админ).|
| DELETE    | `/api/v1/admin/instrument/{ticker}`                            | - | Удалить актив (только админ).|

---

### 3. **Order Service**

| **Метод** | **API v1**                 | **Query Parameters / Request Body** | **Описание**|
|-----------|----------------------------|-------------------------------------|-----------|
| POST      | `/api/v1/orders`           | type (market/limit), direction (buy/sell), ticker, payment_ticker (по дефолту RUB), qty, price | Создать новый ордер.|
| GET       | `/api/v1/orders`           | - | Получить список всех ордеров.                   |
| GET       | `/api/v1/orders/{order_id}`| - | Получить информацию по ордеру по его `order_id`.|
| DELETE    | `/api/v1/orders/{order_id}`| - | Удалить ордер по его `order_id`.                |

---

### 4. **Wallet Service**

| **Метод** | **API v1**                      |**Query Parameters / Request Body** | **Описание**    |
|-----------|---------------------------------|------------------------------------|------------------|
| GET       | `/api/v1/balance`               | - |Получить свои балансы активов.                       |
| POST      | `/api/v1/admin/balance/deposit` | user_id, ticker, amount |Пополнение баланс актива пользователю (только админ).|
| POST      | `/api/v1/admin/balance/withdraw`| user_id, ticker, amount |Вывод средст пользователя (только админ).            |



