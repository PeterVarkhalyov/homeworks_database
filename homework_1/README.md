# Домашняя работа № 1

## Структура проекта

```text
homework_1/
├── north_data/
│   ├── customers_data.csv
│   ├── employees_data.csv
│   └── orders_data.csv
├── src/
│   ├── __init__.py
│   ├── customers.py
│   ├── employees.py
│   ├── logging_config.py
│   ├── orders.py
│   └── reads.py
├── tests/
│   ├── conftest.py
│   ├── test_logging_config.py
│   ├── test_main.py
│   ├── test_models.py
│   └── test_reads.py
├── logs/
│   ├── customers.log
│   ├── employees.log
│   ├── main.log
│   ├── orders.log
│   └── reads.log
├── htmlcov/                  # создаётся при формировании HTML-отчёта
├── .env                      # локальные параметры подключения, не хранится в Git
├── .env.example              # пример параметров подключения
├── create_tables.sql
├── main.py
└── README.md
```

### Описание элементов структуры

- `north_data` — исходные CSV-файлы с данными о клиентах, сотрудниках и заказах;
- `src` — пакет с моделями сущностей, чтением файлов и общей настройкой логирования;
- `tests` — тесты `main.py`, моделей, чтения файлов и настройки логирования;
- `logs` — журналы работы модулей;
- `htmlcov` — HTML-отчёт о покрытии кода тестами;
- `create_tables.sql` — SQL-код создания таблиц;
- `.env` — локальные параметры подключения к PostgreSQL (не добавляется в Git);
- `.env.example` — пример заполнения параметров подключения;
- `main.py` — скрипт загрузки данных из `north_data` в PostgreSQL;
- `README.md` — описание задания и его реализации.


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
| contact_name | TEXT | Контактное лицо клиента. Не может быть пустым. |

Скрипт создания таблицы:
``` SQL 
CREATE TABLE public.customers (
    customer_id VARCHAR(255) PRIMARY KEY,
    company_name TEXT NOT NULL,
    contact_name TEXT NOT NULL
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

## Модули

### `main.py`

Содержит конкретные классы `NorthEmployee`, `NorthCustomer` и `NorthOrder`, которые проверяют значения CSV и
преобразуют их в типизированные объекты и кортежи для записи в БД.

Работа с PostgreSQL разделена на функции:

- `get_db_config` — читает и проверяет параметры подключения из `.env`;
- `connect_to_database` — создаёт соединение через `psycopg2`;
- `insert_employees` — добавляет сотрудников в `public.employees`; значение `employee_id` назначается PostgreSQL
  через sequence `employees_employee_id_seq`;
- `insert_customers` — добавляет или обновляет клиентов по `customer_id`;
- `insert_orders` — добавляет или обновляет заказы по `order_id`.

Таблицы заполняются в порядке `employees` → `customers` → `orders` в одной транзакции. При ошибке изменения
откатываются, а соединение закрывается в блоке `finally`. Повторный запуск добавляет новые строки сотрудников, так как
у таблицы `employees` нет уникального ограничения, кроме автоматически создаваемого `employee_id`.

### Модели сущностей

- `src/employees.py` — абстрактный класс `Employee`;
- `src/customers.py` — абстрактный класс `Customer`;
- `src/orders.py` — абстрактный класс `Order`.

Общие методы моделей загружают CSV через `reads.py`, пропускают ошибочные записи и фиксируют результат в отдельных
логах. Абстрактные методы `from_record` и `from_rows` реализуются конкретными классами в `main.py`.

Классы экспортируются через `src/__init__.py`:

```python
from src import Customer, Employee, Order
```

### `src/reads.py`

Содержит функции загрузки данных из файлов:

- `get_transactions_from_csv(file_path, delimiter=";")` — читает CSV-файл с указанным разделителем, пропускает
  пустые строки и возвращает список словарей;
- `get_transactions_from_xls(file_path)` — читает лист `Отчет по операциям` из Excel-файла, пропускает пустые строки
  и возвращает список словарей;
- `get_fields_from_json(file_path)` — читает JSON-файл, корневым элементом которого должен быть объект или массив.

При отсутствии файла, ошибке кодировки или некорректном содержимом функции возвращают пустой список. Сведения о
работе и ошибках записываются в `logs/reads.log`.

### `src/logging_config.py`

Функция `get_file_logger` централизованно создаёт файловые логгеры в каталоге `logs`. При первом обращении в рамках
запуска соответствующий лог открывается в режиме перезаписи. Повторные вызовы используют тот же обработчик.

### Настройка подключения и запуск

В файлах `.env` и `.env.example` используются параметры:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=north
DB_USER=postgres
DB_PASSWORD=your_postgresql_password
```

Перед запуском установите зависимости:

```powershell
poetry install
```

Затем замените значение `DB_PASSWORD` в `homework_1/.env` на пароль локального пользователя PostgreSQL. После
создания таблиц скриптом `create_tables.sql` выполните из корня проекта:

```powershell
poetry run python homework_1/main.py
```

## Тестирование

Тесты находятся в `homework_1/tests` и проверяют:

- успешное чтение CSV, Excel и JSON;
- использование пользовательского разделителя CSV;
- пропуск пустых строк и записей;
- обработку пустых, отсутствующих и повреждённых файлов;
- отклонение скалярного корневого элемента JSON;
- загрузку моделей и пропуск ошибочных записей;
- преобразование сотрудников, клиентов и заказов в строки таблиц;
- создание и повторное использование файловых логгеров;
- чтение и проверку параметров подключения из `.env`;
- успешные и ошибочные сценарии подключения;
- пакетную запись всех трёх таблиц через подменённое соединение;
- фиксацию транзакции, обработку ошибок и закрытие соединения.

Для запуска всех тестов выполните из корня проекта:

```powershell
poetry run pytest
```

Для запуска тестов и формирования HTML-отчёта о покрытии используйте:

```powershell
poetry run pytest --cov-report=html:homework_1/htmlcov
```

Отчёт сохраняется в папке `homework_1/htmlcov`. Для просмотра откройте файл `homework_1/htmlcov/index.html` в
браузере. Настройки `pyproject.toml` включают в измерение `main.py` и весь пакет `src`.

Текущий результат:

```text
49 passed
367 statements — 100%
50 branches — 100%
```

Минимально допустимое покрытие — 100%.
