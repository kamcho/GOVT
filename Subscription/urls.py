from django.urls import path
from .views import *
from . import views

urlpatterns = [

    path('Subscriptions/', Subscribe.as_view(), name='subscription'),
    path('Pay/', Pay.as_view(), name='pay'),
    # path('process-payment/', views.initiate_payment, name='process-payment'),


]