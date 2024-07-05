from aiokafka import AIOKafkaConsumer
from app.deps import get_session
from app.crud.inventory_crud import add_new_inventory_item
from app.models.inventory_model import InventoryItem
import json


async def consume_messages(topic, bootstrap_servers):
    # Create a consumer instance
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id="add-stock-consumer-group",
        # auto_offset_reset="earliest",
    )

    # start the consumer
    await consumer.start()
    try:
        # Continuously listen for messages.
        async for message in consumer:
            print("RAW ADD STOCK CONSUMER MESSAGE")
            print(f"Received message on topic {message.topic}")

            inventory_data = json.loads(message.value.decode())
            print("TYPE", (type(inventory_data)))
            print(f"Inventory Data {inventory_data}")

            with next(get_session()) as session:
                print("Adding inventory item in database")
                db_insert_inventory_item = add_new_inventory_item(
                    inventory_item_data=InventoryItem(**inventory_data),
                    session=session
                )

                print("DB INSERT STOCK", db_insert_inventory_item)

    finally:
        await consumer.stop()
