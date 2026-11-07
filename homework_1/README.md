# Домашняя работа № 1

## Структура
```text
homeworks_database/
├── homework_1/
│   ├── north_data/
│   │   ├── customers_data.csv
│   │   ├── employees_data.csv
│   │   └── orders_data.csv
│   ├── create_tables.sql
│   ├── main.py
│   └── README.md
│ ...
```
### Описание элементов структуры
- `customers_data.csv` - содержит данные для 
  заполнения таблицы, связанной с сущностью `customer`
- `employees_data.csv` - содержит данные для 
  заполнения таблицы, связанной с сущностью `employee`
- `orders_data.csv` - содержит данные для 
  заполнения таблицы, связанной с сущностью `order`
- `create_tables.sql` - содержит SQL-код создания таблиц
- `main.py` - содержит Python-код реализации условий **Домашней работы № 1**
- `README.md` - содержит описание реализации **Домашней работы № 1**

## Условия 
- Установка Postgres
- Создание БД
  - Подключиться к Postgres из командной строки
  - Создать БД с названием `north`
- Создание таблиц
  - Данные расположены в папке `north_data`
  - Создайте три таблицы, используя `query tool` в pgAdmin
    - `employees`
    - `customers`
    - `orders`
  - Столбцы для таблиц и связи между таблицами определите самостоятельно
  - Sql-код для создания таблиц скопируйте в файл `create_tables.sql`
- Заполнение таблиц данными
  - Написать скрипт в `main.py`, который заполнит созданные 
    таблицы данными из `north_data`
  - Для подключения к БД используйте библиотеку `psycopg2`
  - Зайдите в pgAdmin и убедитесь, что данные в таблицах есть
  
## Реализация

### Установка Postgres
Локально выполнено.

### Создание БД
Выполнено для ОС Windows.
Реализация:
1. Нажать Win + R.
2. Ввести cmd или powershell и нажать Enter.
3. Выполнить команду подключения.
	``` text
	psql -h localhost -p 5432 -U postgres -d postgres
	```
	Параметры:
	- `-h localhost` — адрес сервера;
	- `-p 5432` — порт PostgreSQL;
	- `-U postgres` — пользователь;
	- `-d postgres` — база, к которой выполняется первоначальное подключение.
4. После запуска вводим пароль пользователя postgres.
5. Вход осуществлен.
6. В открывшейся консоли `psql` выполняем:
    ``` SQL 
    CREATE DATABASE north;
    ```
    Если база будет создана, то получим сообщение:
    ``` text 
    CREATE DATABASE
    ```
	
### Создание таблиц
В задании представлены следующие сущности:
- `employee`
- `customer`
- `order`

Для каждой сущности созданы таблицы в базе данных `north`.

Создание таблиц происходит в pgAdmin:
1. нужно выбрать базу `north`
2. открыть для неё `Query Tool`
3. открыть (загрузить) файл `create_tables.sql`
4. выполнить скрипт

#### Сущность `employee`
Сущность `employee` предоставляет описание сотрудников организации.

Данные сущности представлены в `north_data\employees_data.csv` и имеют следующую структуру:
```text
first_name,last_name,title,birth_date,notes
```

Для сущности `employee` создана таблица `employees`, следующей структуры:
| FIELD  | TYPE    | DESCRIPTION   |
|--------|---------|------------|
| employee_id  | SERIAL  | Идентификатор записи. Поле является PRIMARY KEY. |
| first_name | TEXT | Имя сотрудника. Не может быть пустым. |
| last_name | TEXT | Фамилия сотрудника. Не может быть пустым. |
| title | TEXT | Должность, которую занимает сотрудник. Не может быть пустым. |
| birth_date | DATE | День рождения сотрудника. Не может быть пустым. |
| notes | TEXT | Пометки. |

Скрипт создания таблицы:
``` SQL 
CREATE TABLE public.employees (
    employee_id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    title TEXT NOT NULL,
    birth_date DATE NOT NULL,
    notes TEXT
);
```

#### Сущность `customer`
Сущность `customer` предоставляет описание клиентов.

Данные сущности представлены в `north_data\customers_data.csv` и имеют следующую 
структуру:
```text
customer_id, company_name, contact_name
```

Для сущности `customer` создана таблица `customers`, следующей структуры:
| FIELD  | TYPE    | DESCRIPTION   |
|--------|---------|------------|
| customer_id  | VARCHAR(255)  | Идентификатор записи. Поле является PRIMARY KEY. |
| company_name | TEXT | Наименование компании клиента. Не может быть пустым. |
| contact_name | TEXT | Контактное лицо клиента. |

Скрипт создания таблицы:
``` SQL 
CREATE TABLE public.customers (
    customer_id VARCHAR(255) PRIMARY KEY,
    company_name TEXT NOT NULL,
    contact_name TEXT
);
```

#### Сущность `order`
Сущность `order` предоставляет описание заказов клиентов.

Данные сущности представлены в `north_data\orders_data.csv` и имеют следующую структуру:
```text
order_id, customer_id, employee_id, order_date, ship_city
```

Для сущности `order` создана таблица `orders`, следующей структуры:
| FIELD  | TYPE    | DESCRIPTION   |
|--------|---------|------------|
| order_id   | INT  | Идентификатор записи. Поле является PRIMARY KEY. |
| customer_id  | VARCHAR(255) | Идентификатор клиента, которому принадлежит заказ. Не может быть пустым. Является FOREIGN KEY связи с таблицей `customers`. Связь customers (1) → orders (много). |
| employee_id  | INT | Идентификатор сотрудника, который принял заказ. Не может быть пустым. Является FOREIGN KEY связи с таблицей `employees`. Связь employees (1) → orders (много). |
| order_date | DATE | Дата заказа. Не может быть пустым. |
| ship_city | TEXT | Город доставки заказа. Не может быть пустым. | 

Скрипт создания таблицы:
``` SQL 
CREATE TABLE public.orders (
    order_id INT PRIMARY KEY,

    customer_id VARCHAR(255) NOT NULL
        REFERENCES public.customers(customer_id),

    employee_id INT NOT NULL
        REFERENCES public.employees(employee_id),

    order_date DATE NOT NULL,
    ship_city TEXT NOT NULL
);


CREATE INDEX idx_orders_customer_id
    ON public.orders(customer_id);

CREATE INDEX idx_orders_employee_id
    ON public.orders(employee_id);
```

### Результат
SQL-код создания таблиц записан в файл `create_tables.sql`.
