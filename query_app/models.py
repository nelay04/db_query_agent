from django.db import models

# Create your models here.
class DbConfig(models.Model):
    user_email = models.CharField(max_length=100)
    db_type = models.CharField(max_length=50, null=True, blank=True)
    db_host = models.CharField(max_length=100)
    db_port = models.CharField(max_length=10)
    db_user_name = models.CharField(max_length=100)
    db_password = models.CharField(max_length=100)
    db_database = models.CharField(max_length=100)
    db_table_name = models.CharField(max_length=100)