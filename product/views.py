from datetime import datetime

from celery.result import AsyncResult
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from .models import *
from .serializers import *
from rest_framework.exceptions import ValidationError


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def perform_destroy(self, instance):  # При каскадном удалении, нам также необходимо вернуть пару значений и добавить возврат к товарам
        for orderitem in instance.items.all():
            product = Product.objects.get(id=orderitem.product.id)  # Ищем экземпляр модели Product
            product.quantity += orderitem.quantity  # Возвращаем исходное кол-во товара
            product.sold -= orderitem.quantity
            product.refund += orderitem.quantity
            product.save()  # Сохраняем объект Product
        instance.delete()  # Удаляем объект OrderItem


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def perform_create(self, serializer):
        serializer.is_valid()  # Проверяем на Валидность введенных данных
        product = Product.objects.get(id=serializer.validated_data['product'].id)  # Ищем экземпляр модели Product

        if product.quantity < serializer.validated_data['quantity']:
            raise ValidationError("Количество товара, требуемого в заказе, превышает его наличие")
        if product.quantity < 0:
            raise ValidationError("Количество товара, требуемого в заказе, отрицательное")

        product.quantity -= serializer.validated_data['quantity']  # Отнимаем кол-во товара
        product.sold += serializer.validated_data['quantity']
        product.save()  # Сохраняем объект Product
        serializer.save()  # Сохраняем объект OrderItem

    def perform_destroy(self, instance):
        product = Product.objects.get(id=instance.product.id)  # Ищем экземпляр модели Product
        product.quantity += instance.quantity  # Возвращаем исходное кол-во товара
        product.sold -= instance.quantity
        product.refund += instance.quantity
        product.save()  # Сохраняем объект Product
        instance.delete()  # Удаляем объект OrderItem


@csrf_exempt
def get_status(request, task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JsonResponse(result, status=200)


@csrf_exempt
def make_a_task_to_report(request):
    from product.tasks import getting_a_summary_report
    task = getting_a_summary_report.delay(request.GET.get("date_from"), request.GET.get("date_to"))
    return JsonResponse({"task_id": task.id}, status=202)
