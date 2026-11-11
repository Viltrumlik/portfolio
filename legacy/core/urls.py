from django.urls import path
from .views import HomePageView, ContactFormView

app_name = 'core'

urlpatterns = [
    path('contact/', ContactFormView.as_view(), name='contact'),
]
