from celery import Celery

app=Celery()
app.config_from_object('src.config.settings')

@app.task()
def process_order(order_id: str):
    print(f"Processing order {order_id}")