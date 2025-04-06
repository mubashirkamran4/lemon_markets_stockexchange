# Technical Documentation

## How To Run

PostgreSQL was used as a database to store the incoming orders. It was used because of the following advantages considering our scenario as it offers concurrency during writes, as our API should be able to handle them at a later point in time.



## SQL for setting up DB structure

`CREATE USER lemon_user WITH PASSWORD 'lemon5612'`;

`CREATE DATABASE lemon_market`

`CREATE DATABASE lemon_market`

`psql -U lemon_user -d lemon_market`

```
CREATE TABLE Orders (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type order_type NOT NULL,
    side order_side NOT NULL,
    instrument CHAR(12) NOT NULL,
    limit_price NUMERIC(19,2),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    CONSTRAINT market_order_no_price CHECK (
        (type = 'market' AND limit_price IS NULL) OR
        (type = 'limit' AND limit_price IS NOT NULL)
    )
);
```

`CREATE TYPE order_status AS ENUM ('pending', 'completed', 'failed', 'error');`

`ALTER TABLE Orders DROP COLUMN status;`

`ALTER TABLE Orders;`

`ADD COLUMN status order_status NOT NULL DEFAULT 'pending';`

## Steps to run

Python3.11 must be installed in the system.

1. Go into project directory on terminal.
2. Execute following commands to create a virtual environment and get the server up and running:
    
    `python3.11 -m venv venv`
    
    `source venv/bin/activate`

    `uvicorn app.api:app --reload`

3. Open Postman and point it to  `http://localhost:8000/orders` in URL field, select `Content-Type` to `application/json`, select raw option in body tab and select JSON from dropdown. Paste the following examples and hit send to see the respective results:

    i). Valid Market Order (No Limit Price)
    ```
            {
                "type": "market",
                "side": "buy",
                "instrument": "AAPL_2025_03",
                "quantity": 100
            }
    ```

    ii). Valid Limit Order (With Limit Price)
    ```
        {
            "type": "limit",
            "side": "sell",
            "instrument": "TSLA_2025_06",
            "limit_price": 250.50,
            "quantity": 50
        }
    ```

    iii). Invalid Market Order (With Limit Price)
      ```
       {
            "type": "market",
            "side": "buy",
            "instrument": "GOOG_2025_09",
            "limit_price": 150.75,
            "quantity": 75
        } 
      ```

    iv). Invalid Limit Order(No Limit Price)
      ```
       {
        "type": "limit",
        "side": "sell",
        "instrument": "MSFT_2025_12",
        "quantity": 200
       }
      ```
    
    v). Short Instrument Code (Validation Error)
    ```
        {
            "type": "market",
            "side": "buy",
            "instrument": "NVDA_25",
            "quantity": 30
        }
    ```

## Some Design Considerations

i). The API endpoint has been made independent of reliability of placing orders on stock exchange. If the order could not be placed on stock exchange, we still possibly could have the option to place them on exchange at a later point in time for instance writing a separate worker that scans for non-completed orders and places them on exchange.

ii). `SQLAlchemy` was used for ORM, as it is very easy to model the DB structure as objects and expressiveness to talk to DB in a simple way.

iii). `BackgroundTasks` was used for scheduling and placing the newly executed orders on stock exchange so it separates the API response (immediate acknowledgment) from stock exchange placement (async), improving client-side latency. Failed placements are captured in the database (status='failed', error_message=...) for auditing and retries. 

### Question: How would you change the system if we would receive a high volume of async updates to the orders placed through a socket connection on the stock exchange, e.g. execution information?

We can integrate a queuing system Apache Kafka for instance for getting realtime updates from exchanges, where `producers` will simply write to `orders` topic(just like a db table) and `consumer` will consume(just like read) from `orders` topic and places on stock exchange, and then we have a Update Consumer who would get the updates from websocket and would write to Kafka Topic `order_updates`. In the end we can have a notification service that reads order_updates and pushes to 

#### Proposed Architecutre

1). Order API (Producer)

        Accepts HTTP orders → Validates → Stores in PostgreSQL

        Publishes to `orders` Kafka topic (instead of BackgroundTasks)

        Returns 202 Accepted immediately

2). Exchange Consumer

        Reads from `orders` topic → Places on stock exchange

        Handles retries/exponential backoff

3). Update Consumer

        Listens to exchange WebSocket for executions/updates

        Writes to `order_updates` Kafka topic

4). Notification Service

        Consumes `order_updates` → Pushes to clients via:

        WebSocket (real-time)



