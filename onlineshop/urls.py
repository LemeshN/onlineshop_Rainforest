from django.contrib import admin
from django.urls import path, include
from product.views import *

from rest_framework import routers


router = routers.SimpleRouter()
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'orders_item', OrderItemViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/report', make_a_task_to_report),
    path('api/report_status/<slug:task_id>', get_status),
]
