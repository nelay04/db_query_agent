from .response_service import ResponseService
import psycopg2 # PostgreSQL adapter
from ..models import DbConfig


class SQLService:
    @staticmethod
    def fetch_schema(db_config):
        try:
            schema_string_b = None
            if db_config.db_type == 'postgresql':
                # schema_string_b = SQLService.fetch_pgsql_table_schema(db_config)
                schema_string_b = SQLService.fetch_pgsql_all_table_schemas(db_config)
            else:
                raise ValueError(f"Unsupported db_type: {db_config.db_type}")

            return schema_string_b
        except Exception as e:
            raise e
        
    @staticmethod
    def fetch_pgsql_table_schema(db_config):
        try:
           # Fill these with your credentials
            conn = psycopg2.connect(
                host=db_config.db_host,
                port=db_config.db_port,
                user=db_config.db_user_name,
                password=db_config.db_password,
                dbname=db_config.db_database
            )

            cursor = conn.cursor()

            table_name = db_config.db_table_name

            query = f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}';
            """
            cursor.execute(query)

            columns = cursor.fetchall()

            # Build schema string
            schema_parts = [f'"{table_name}"']

            for col_name, data_type, is_nullable, col_default in columns:
                schema_parts.append(f'"{col_name}" {data_type}')

            schema_string_c = " ".join(schema_parts)

            cursor.close()
            conn.close()

            return schema_string_c
        
        except Exception as e:
            raise e

    @staticmethod
    def fetch_pgsql_all_table_schemas(db_config):
        try:
            conn = psycopg2.connect(
                host=db_config.db_host,
                port=db_config.db_port,
                user=db_config.db_user_name,
                password=db_config.db_password,
                dbname=db_config.db_database
            )

            cursor = conn.cursor()

            # Fetch column metadata for all tables in 'public' schema (you can generalize it)
            query = """
            SELECT 
                table_name, 
                column_name, 
                data_type, 
                is_nullable, 
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
            """
            cursor.execute(query)
            columns = cursor.fetchall()

            # Build a dict of table -> schema string
            schema_map = {}
            for table_name, col_name, data_type, is_nullable, col_default in columns:
                if table_name not in schema_map:
                    schema_map[table_name] = []
                schema_map[table_name].append(f'"{col_name}" {data_type}')

            # Convert to table-wise schema string format
            result = {}
            for table_name, col_list in schema_map.items():
                schema_string = f'"{table_name}" ' + " ".join(col_list)
                result[table_name] = schema_string

            cursor.close()
            conn.close()

            return result  # returns dict: {table_name: schema_string}

        except Exception as e:
            raise e

    @staticmethod
    def execute_sql(db_config, query:str):
        try:
            conn = psycopg2.connect(
                host=db_config.db_host,
                port=db_config.db_port,
                user=db_config.db_user_name,
                password=db_config.db_password,
                dbname=db_config.db_database
            )
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchall()
            cur.close()
            conn.close()
            return result
        except Exception as e:
            return ResponseService.error(f'Error executing query: {str(e)}', code=500)