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
| **Метод** | **API v1**       | **API v2**       | **Query Parameters / Request Body** |**Описание**|
|-----------|------------------|------------------|-------------------------------------|-----------|
| POST      | `/api/v1/public/register`|-| name | Регистрация нового пользователя.|
| DELETE    | `/api/v1/admin/user/{user_id}`| `/api/v2/admin/user/{user_id}` | - |Удалить пользователя (только админ).|
| POST      | -                      | `/api/v2/auth/register` | email, name, password| Регистрация нового пользователя (пользователь после рег не активирован, нужно подтвердить почту)|
| POST      | - | `/api/v2/admin/register` | email, name, password | Регситрация нового админа (только админ)|
| POST      | - | `/api/v2/auth/login` | email, password | Вход в аккаунт (получение jwt токенов)|
| POST      | - | `/api/v2/auth/token/refresh/`| refresh token в куках | Обновление access token|
| POST      | - | `api/v2/mail/verify-email`| email, verification_code | Подтверждение почты с помощью кода. |
| POST      | - | `api/v2/mail/resend-verification-code`| email | Отправка кода для подтверждения почты (Еще раз). |
| GET       | - | `api/v2/oauth/login/google` | - | Аутентификация с помощью google oauth. |
| POST      | - | `api/v2/user/change-password`| old_passwor, new_password, new_password_confirm | Смена пароля |
| POST      | - | `api/v2/user/forgot-password`| email | Сброс пароля |
| POST      | - | `api/v2/user/confirm-reset-code`| code, new_password, new_password_confirm | Установка нового пароля |

---

### 2. **Market Data Service**

| **Метод** | **API v1**                                            | **Описание**                                                 |
|-----------|-------------------------------------------------------|--------------------------------------------------------------|
| GET       | `/api/v1/public/instrument`                           | Получить список всех доступных активов.                      |
| GET       | `/api/v1/public/orderbook/{ticker}`                   | Получить стакан ордеров по активу.                           |
| GET       | `/api/v1/public/transactions/{ticker}`                | Получить все транзакции по паре активов.                     |
| GET       | `/api/v1/public/transactions/user/{user_id}/{ticker}` | Получить транзакции пользователя по конкретной паре активов. |
| GET       | `/api/v1/public/transactions/user/{user_id}`          | Получить все транзакции пользователя.                        |
| POST      | `/api/v1/admin/instrument`                            | Создать новый актив (только админ)                           |
| DELETE    | `/api/v1/admin/instrument`                            | Удалить актив (только админ)                                 |

---

### 3. **Order Service**

| **Метод** | **API v1**                 | **Описание**                                    |
|-----------|----------------------------|-------------------------------------------------|
| POST      | `/api/v1/orders`           | Создать новый ордер.                            |
| GET       | `/api/v1/orders`           | Получить список всех ордеров.                   |
| GET       | `/api/v1/orders/{order_id}`| Получить информацию по ордеру по его `order_id`.|
| DELETE    | `/api/v1/orders/{order_id}`| Удалить ордер по его `order_id`.                |

---

### 4. **Wallet Service**

| **Метод** | **API v1**                      | **Описание**                                         |
|-----------|---------------------------------|------------------------------------------------------|
| GET       | `/api/v1/balance`               | Получить свои балансы активов.                       |
| POST      | `/api/v1/admin/balance/deposit` | Пополнение баланс актива пользователю (только админ).|
| POST      | `/api/v1/admin/balance/withdraw`| Вывод средст пользователя (только админ).            |



