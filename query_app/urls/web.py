from django.urls import path # type: ignore
from query_app import views

# Web Endpoints
urlpatterns = [
    path("", views.index, name="index"),
]
