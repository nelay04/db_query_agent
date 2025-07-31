from django.shortcuts import render
import datetime
from django.utils import timezone
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

# Models
from .models import DbConfig

# Services
from .services.response_service import ResponseService
from .services.sql_service import SQLService
from .services.ai_service import AIService

# Serializers
from .serializers import DbConfigSerializer


# Create your views here.

# Index Page
def index(request):
    try:
        # Get currently authenticated user data
        user = request.user

        db_config = DbConfig.objects.filter(user_email=user.email).first()
        # Pass db_config to the template
        return render(request, 'home.html', {'db_config': db_config, 'user_email': user.email})
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)

@api_view(['POST'])
def count_tokens(request):
    try:
        string = request.data.get('string')
        if not string:
            return ResponseService.error('String is required', code=400)

        token_count = AIService.count_tokens_regex(str(string))
        return ResponseService.success('Expected data found', code=200, data={'token_count': token_count})

    except Exception as e:
        return ResponseService.error(f'Error processing query: {str(e)}', code=500)

@api_view(['GET', 'POST'])
def db_config(request):
    if request.method == 'POST':
        try:
            user_email = request.data.get('user_email')
            if not user_email:
                return ResponseService.error('user_email is required', code=400)

            db_config_instance = DbConfig.objects.filter(
                user_email=user_email).first()
            if db_config_instance:
                serializer = DbConfigSerializer(
                    db_config_instance, data=request.data, partial=True)
            else:
                serializer = DbConfigSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                msg = 'Database config updated' if db_config_instance else 'Database config saved'
                return ResponseService.success(msg, data=serializer.data)
            return ResponseService.error('Validation error', code=400, errors=serializer.errors)
        except Exception as e:
            return ResponseService.error(f'Error saving database config: {str(e)}', code=500)
    if request.method == 'GET':
        try:
            configs = DbConfig.objects.all()
            serializer = DbConfigSerializer(configs, many=True)
            return ResponseService.success('Database config list', data=serializer.data)
        except Exception as e:
            return ResponseService.error(f'Error fetching database config: {str(e)}', code=500)


@api_view(['POST'])
def generate_sql(request):
    try:
        user_query = request.data.get('user_query')
        # print(user_query)
        if not user_query:
            return ResponseService.error('Prompt is required', code=400)

        db_config = DbConfig.objects.filter(
            user_email=request.user.email).first()

        schema_string = None
        schema_string = SQLService.fetch_schema(db_config)
        # print(f"Schema string: {schema_string}")

        if not db_config.db_table_name:
            data = AIService.generate_sql_multiple_table(
                prompt=user_query, structure=schema_string)
        else:
            unstructured_fields = SQLService.find_unstructured_fields(
                schema_string)
            # print(f"Unstructured fields: {unstructured_fields}")
            if unstructured_fields is not None:
                sample_unstructured_data = SQLService.get_prominent_unstructured_data(
                    unstructured_fields, db_config)
                # print(f"Sample unstructured data: {sample_unstructured_data}")
            data = AIService.generate_sql_single_table(
                prompt=user_query, structure=schema_string, table_name=db_config.db_table_name, sample_unstructured_data=sample_unstructured_data)

        # print(data)

        return ResponseService.success('success', 200, data=data)
    except Exception as e:
        return ResponseService.error(f'Error processing query: {str(e)}', code=500)


@api_view(['POST'])
def check_atomic_query(request):
    try:
        db_config = DbConfig.objects.filter(
            user_email='snowflake.2k04@gmail.com').first()
        sql_query = request.data.get('query')
        # print(sql_query)
        if not sql_query:
            return ResponseService.error('SQL query is required', code=400)
        if db_config is None:
            return ResponseService.error('No Config found for the given user_email', code=404)
        result = SQLService.execute_sql(db_config, sql_query)

        # Safely unwrap first value if available
        unwrapped_result = result[0][0] if result and result[0] else None
        # print("Unwrapped result:", unwrapped_result)
        if unwrapped_result is False or unwrapped_result is None:
            return ResponseService.error('No data found', code=404)
        else:
            return ResponseService.success('Expected data found', code=200)

    except Exception as e:
        return ResponseService.error(f'Error processing query: {str(e)}', code=500)


@api_view(['POST'])
def gather_information(request):
    try:
        user_query = request.data.get('user_query')
        # return ResponseService.success('success', 200, data=user_query)

        # print(user_query)
        if not user_query:
            return ResponseService.error('Prompt is required', code=400)

        db_config = DbConfig.objects.filter(
            user_email='snowflake.2k04@gmail.com').first()

        schema_string = None
        schema_string = SQLService.fetch_schema(db_config)
        # print(f"Schema string: {schema_string}")


        unstructured_fields = SQLService.find_unstructured_fields(
            schema_string)
        # print(f"Unstructured fields: {unstructured_fields}")
        if unstructured_fields is not None:
            sample_unstructured_data = SQLService.get_prominent_unstructured_data(
                unstructured_fields, db_config)
            # print(sample_unstructured_data)
        discovery_queries = AIService.generate_discovery_queries(
            prompt=user_query, structure=schema_string, table_name=db_config.db_table_name, sample_unstructured_data=sample_unstructured_data)
        
        # print (discovery_queries)

        discovery_data = SQLService.perform_discovery_query(
            discovery_queries=discovery_queries, db_config = db_config
        )

        # print('\n')
        # print(discovery_data)

        data = AIService.generate_sql_single_table_final(
            prompt=user_query,
            structure=schema_string,
            table_name=db_config.db_table_name,
            discovery_query_results=discovery_data,
            sample_unstructured_data=sample_unstructured_data
        )

        # # Get the query result
        # sql_query = data.get("main_query")
        # print('\n' + sql_query)
        # main_query_result = SQLService.execute_sql(db_config, str(sql_query)) if sql_query else None
        # print('\n' + main_query_result)
        # data['main_query_result'] = main_query_result
        # print('\n' + data)

        return ResponseService.success('success', 200, data={'result': data, 'discovery_data': discovery_data})
    except Exception as e:
        return ResponseService.error(f'Error processing query: {str(e)}', code=500)
    


@api_view(['POST'])
def generate_chart(request):
    try:
        sql_query = request.data.get('sql_query')
        email = request.data.get('email')
        # print(sql_query)
        if not sql_query:
            return ResponseService.error('SQL query is required', code=400)

        db_config = DbConfig.objects.filter(
            user_email=email if email else request.user.email).first()
        result = SQLService.execute_sql(db_config, sql_query)
        # print (result)
        chart_data = AIService.generate_chart_data(result)
        # print(chart_data)
        return ResponseService.success('success', 200, data={'result':result, 'chart_data': chart_data})
    except Exception as e:
        return ResponseService.error(f'Error processing query: {str(e)}', code=500)