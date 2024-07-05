from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from app.deps import get_session
from app.models.product_model import Product
import json
from app.crud.product_crud import validate_product_by_id

async def inventory_consume_messages(topic, bootstrap_servers):
    # Create a consumer instance
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id="inventory-add-group",
    #    auto_offset_reset='earliest'
    )

    # start the consumer
    await consumer.start()
    try:
        # Continuosly listen messages
        async for message in consumer:
            print("\n\n RAW INVENTORY MESSAGE\n\n ")
            print(f"Recieved message on topic {message.topic}")
            print(f"Message value {message.value}")

            # Extract product id
            inventory_data = json.loads(message.value.decode())
            product_id = inventory_data["product_id"]
            print("PRODUCT ID :", product_id)

            # check if product id is valid
            with next(get_session()) as session:
                product = validate_product_by_id(
                    product_id=product_id, session=session
                )
                print("PRODUCT :", product)

                # if valid
                if product is None:
                    #  email_body = chat_completion(f"Admin has Sent InCorrect Product. Write Email to Admin {product_id}")
                    return None
                
                if product is not None:
                    # write a new producer and send data to topic
                    print("Product is valid")

                    producer =  AIOKafkaProducer(bootstrap_servers='broker:19092')
                    await producer.start()
                    try:
                        await producer.send_and_wait(
                            "inventory-add-stock-response",
                            message.value
                        )
                    finally:
                        await producer.stop()

    finally:
        await consumer.stop()