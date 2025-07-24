# Serializer converts model instances to JSON and validates incoming API data.
# It is used to serialize and deserialize data for the model.

from rest_framework import serializers
from .models import DbConfig

class DbConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbConfig
        fields = '__all__'

    # Define required fields explicitly
    user_email = serializers.CharField(required=True)
    db_host = serializers.CharField(required=True)
    db_port = serializers.CharField(required=True)
    db_user_name = serializers.CharField(required=True)
    db_password = serializers.CharField(required=True)
    db_database = serializers.CharField(required=True)

    # Optional fields (no need to declare if using ModelSerializer and field is not `blank=False`)
    db_table_name = serializers.CharField(required=False, allow_blank=True)
    db_type = serializers.CharField(required=False, allow_blank=True)
