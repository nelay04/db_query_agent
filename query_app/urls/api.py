from django.urls import path  # type: ignore
from query_app import views

# API Endpoints
urlpatterns = [
    path("db_config/", views.db_config, name="db_config"),
    path("generate_sql/", views.generate_sql, name="generate_sql"),
    path("generate_chart/", views.generate_chart, name="generate_chart"),
    path("check-atomic-query/", views.check_atomic_query, name="check_atomic_query"),
]
