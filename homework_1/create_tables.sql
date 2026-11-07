CREATE TABLE public.employees (
    employee_id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    title TEXT NOT NULL,
    birth_date DATE NOT NULL,
    notes TEXT
);

CREATE TABLE public.customers (
    customer_id VARCHAR(255) PRIMARY KEY,
    company_name TEXT NOT NULL,
    contact_name TEXT
);

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
