import time
from datetime import datetime
from celery import shared_task
from django.db.models import Sum
from .models import Product, Order


# Декоратор @shared_task, говорит celery о том, что эта функция является (task-ом) т.е. должна выполнятся в фоне.
@shared_task
def getting_a_summary_report(date_from, date_to):
    date_from = datetime.strptime(date_from, '%Y-%m-%d')
    date_to = datetime.strptime(date_to, '%Y-%m-%d')
    products = {}
    orders_to_report = Order.objects.filter(updated__range=(date_from, date_to))
    for order in orders_to_report:
        for orderitem in order.items.all():
            if orderitem.id in products:
                products[orderitem.product.id]['revenue'] += orderitem.product.price * orderitem.quantity
                products[orderitem.product.id]['profit'] += orderitem.product.price * orderitem.quantity - orderitem.product.cost * orderitem.quantity
                products[orderitem.product.id]['sold'] += orderitem.product.sold
                products[orderitem.product.id]['refund'] += orderitem.product.refund
            else:
                products[orderitem.product.id] = {}
                products[orderitem.product.id]['revenue'] = orderitem.product.price * orderitem.quantity
                products[orderitem.product.id]['profit'] = orderitem.product.price * orderitem.quantity - orderitem.product.cost * orderitem.quantity
                products[orderitem.product.id]['sold'] = orderitem.product.sold
                products[orderitem.product.id]['refund'] = orderitem.product.refund
    products = [{
        "id": product_key,
        "revenue": products[product_key]["revenue"],
        "profit": products[product_key]["profit"],
        "sold": products[product_key]["sold"],
        "refund": products[product_key]["refund"],
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_to": date_to.strftime("%Y-%m-%d"),
    } for product_key in products.keys()]
    return products
