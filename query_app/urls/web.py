from django.urls import path # type: ignore
from query_app import views

# Web Endpoints
urlpatterns = [
    path("", views.index, name="index"),
    path("fast-analyst", views.fast_analyst, name="fast_analyst"),
    path("deep-driver", views.deep_driver, name="deep_driver"),
]
