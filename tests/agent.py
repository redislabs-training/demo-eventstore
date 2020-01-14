import json
import random
import string
import threading
import time
import uuid

from event_store_client import EventStoreClient


def get_any_id(_entities, _but=None):
    """
    Get a random id out of entities.

    :param _entities: The entities to chose from.
    :param _but: Exclude this entity.
    :return: The randomly chosen ID.
    """
    _id = None
    while not _id:
        idx = random.randrange(len(_entities))
        entity = _entities[idx]
        _id = entity['id'] if entity['id'] != _but else None
    return _id


def create_billing(_order_id):
    """
    Create a billing entity.

    :param _order_id: The order ID the billing belongs to.
    :return: A dict with the entity properties.
    """
    return {
        'id': str(uuid.uuid4()),
        'order_id': _order_id,
        'done': time.time()
    }


def create_order(_customers, _products):
    """
    Create an order entity.

    :param _customers: The customers of the order.
    :param _products: The products of the order.
    :return: A dict with the entity properties.
    """
    return {
        'id': str(uuid.uuid4()),
        'product_ids': [get_any_id(_products) for _ in range(random.randint(1, 10))],
        'customer_id': get_any_id(_customers)
    }


def create_inventory(_product_id, _amount):
    """
    Create an inventory entity.

    :param _product_id: The product ID the inventory is for.
    :param _amount: The amount of products in the inventory.
    :return: A dict with the entity properties.
    """
    return {
        'id': str(uuid.uuid4()),
        'product_id': _product_id,
        'amount': _amount
    }


def create_customer():
    """
    Create a customer entity.

    :return: A dict with the entity properties.
    """
    name = "".join(random.choice(string.ascii_lowercase) for _ in range(10))
    return {
        'id': str(uuid.uuid4()),
        'name': name.title(),
        'email': "{}@server.com".format(name)
    }


def create_product():
    """
    Create a product entity.

    :return: A dict with the entity properties.
    """
    return {
        'id': str(uuid.uuid4()),
        'name': "".join(random.choice(string.ascii_lowercase) for _ in range(10)),
        'price': random.randint(10, 1000)
    }


def create_event(_action, _data):
    """
    Create an event.

    :param _action: The action happened.
    :param _data: The data describing the action.
    :return: A dict with the event properties.
    """
    return {
        'event_id': str(uuid.uuid4()),
        'event_action': _action,
        'event_data': json.dumps(_data)
    }


es = EventStoreClient()

customers = [create_customer() for _ in range(0, 100)]
products = [create_product() for _ in range(0, 100)]
inventory = [create_inventory(product['id'], 1000) for product in products]
orders = [create_order(customers, products) for _ in range(0, 100)]
billings = [create_billing(order['id']) for order in orders]

for customer in customers:
    es.publish('customer', create_event('created', customer))

for product in products:
    es.publish('product', create_event('created', product))

for inventory in inventory:
    es.publish('inventory', create_event('created', inventory))

for order in orders:
    es.publish('order', create_event('created', order))

for billing in billings:
    es.publish('billing', create_event('created', billing))


def order_service():

    # delete first order
    es.publish('order', create_event('deleted', orders[0]))

    # get all order events
    all_order_events = es.get_all('order')

    # filter 'created' events
    created = filter(lambda x: x[1]['event_action'] == 'created', all_order_events)

    # filter 'deleted' events
    deleted = list(filter(lambda x: x[1]['event_action'] == 'deleted', all_order_events))

    # filter current order entities
    result = filter(lambda r: json.loads(r[1]['event_data'])['id'] not in map(lambda y: json.loads(y[1]['event_data'])['id'], deleted), created)

    assert len(list(result)) == 99


t1 = threading.Thread(target=order_service)
t1.start()
