from django.urls import path
from .views import Challenges, Testing


urlpatterns = [
    path('challenges/', Challenges.as_view(), name='challenges'),
    path('testing/', Testing.as_view(), name='testing'),
]