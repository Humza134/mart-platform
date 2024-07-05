from aiokafka import AIOKafkaConsumer
from app import settings
import json
from app.deps import get_session
from app.crud.product_crud import add_new_product
from app.models.product_model import Product


async def consume_messages(topic, bootstrap_servers):
    # Create a consumer instance.
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=settings.KAFKA_CONSUMER_GROUP_ID_FOR_PRODUCT,
     #    auto_offset_reset='earliest'
    )

    # Start the consumer.
    await consumer.start()
    try:
        # Continuously listen for messages.
        async for message in consumer:
             print("RAW")
             print(f"Recieved message on topic {message.topic}")

             product_data = json.loads(message.value.decode())
             print("TYPE", (type(product_data)))
             print(f"Product_data {product_data}")

             with next(get_session()) as session:
                  print("Saving data to database")
                  db_insert_product = add_new_product(
                       product_data=Product(**product_data),session=session
                  )
                  print("DB_INSERT_PRODUCT: ", db_insert_product)

    finally:
        # Ensure to close the consumer when done.
        await consumer.stop()
