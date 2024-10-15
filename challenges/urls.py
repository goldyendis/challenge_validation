from django.urls import path
from .views import Challenges


urlpatterns = [
    path("challenges/", Challenges.as_view(), name='challenges'),
]