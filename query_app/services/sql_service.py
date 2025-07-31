from .response_service import ResponseService
import psycopg2 # PostgreSQL adapter
from ..models import DbConfig
import re
from psycopg2 import Error


class SQLService:
    @staticmethod
    def fetch_schema(db_config):
        try:
            schema_string_b = None
            if db_config.db_type == 'postgresql':
                if not db_config.db_table_name:
                    schema_string_b = SQLService.fetch_pgsql_all_table_schemas(db_config)
                else:
                    schema_string_b = SQLService.fetch_pgsql_table_schema(db_config)
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
            print('execute_sql')
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
            print('executed')
            return result
        except Exception as e:
            return ResponseService.error(f'Error executing query: {str(e)}', code=500)
        

    @staticmethod
    def find_unstructured_fields(schema_string):
        """
        Identifies fields with unstructured data types (JSON or ARRAY)
        from a given schema string.

        Args:
            schema_string (str): A string representing the table schema,
                                e.g., '"tbl_name" "id" bigint "data" json "items" ARRAY'.

        Returns:
            list: A list of field names that contain unstructured data.
        """
        try:

            unstructured_fields = []
            # Regex to find pairs of "field_name" and their "data_type".
            # It captures the field name (content inside first quotes)
            # and then the data type (either a quoted string or a word).
            # This approach is more flexible for various data type formats.
            field_type_pairs = re.findall(r'"([^"]+)"\s+(".*?"|\w+)', schema_string)

            for field_name, data_type_raw in field_type_pairs:
                # Clean up the data_type_raw: remove quotes if present and convert to lowercase
                data_type_cleaned = data_type_raw.strip('"').lower()

                if data_type_cleaned == 'json' or data_type_cleaned == 'array':
                # if data_type_cleaned == 'json':
                    unstructured_fields.append(field_name)

            return unstructured_fields
        except Exception as e:
            return ResponseService.error(f'Error finding unstructured data fields: {str(e)}', code=500)
        

    # @staticmethod
    # def get_prominent_unstructured_data(unstructured_fields, db_config):
    #     """
    #     Connects to a PostgreSQL database and retrieves 1 prominent (non-null)
    #     data entry for each specified unstructured field (JSON or ARRAY).

    #     Args:
    #         unstructured_fields (list): A list of field names (strings) to query.
    #         db_config (object): An object with attributes:
    #             db_host, db_port, db_user_name, db_password, db_database, db_table_name

    #     Returns:
    #         list: A list of dictionaries, each containing:
    #             - 'column_name': str
    #             - 'data_type': str
    #             - 'sample_value': any
    #     """
    #     conn = None
    #     result_list = []

    #     try:
    #         # Establish database connection
    #         conn = psycopg2.connect(
    #             host=db_config.db_host,
    #             port=db_config.db_port,
    #             user=db_config.db_user_name,
    #             password=db_config.db_password,
    #             dbname=db_config.db_database
    #         )
    #         cursor = conn.cursor()

    #         table_name = db_config.db_table_name

    #         for field in unstructured_fields:
    #             # Query to get data type
    #             type_query = f"""
    #                 SELECT data_type
    #                 FROM information_schema.columns
    #                 WHERE table_name = %s AND column_name = %s
    #                 LIMIT 1;
    #             """
    #             cursor.execute(type_query, (table_name, field))
    #             type_result = cursor.fetchone()
    #             data_type = type_result[0] if type_result else "unknown"

    #             # Query to get sample value
    #             sample_query = f"""
    #                 SELECT {field}
    #                 FROM {table_name}
    #                 WHERE {field} IS NOT NULL
    #                 LIMIT 1;
    #             """
    #             cursor.execute(sample_query)
    #             data_result = cursor.fetchone()
    #             sample_value = data_result[0] if data_result else None

    #             result_list.append({
    #                 "column_name": field,
    #                 "data_type": data_type,
    #                 "sample_value": sample_value
    #             })

    #     except (Exception, Error) as e:
    #         print(f"Error: {e}")
    #     finally:
    #         if conn:
    #             cursor.close()
    #             conn.close()

    #     return result_list


    @staticmethod
    def get_prominent_unstructured_data(unstructured_fields, db_config):
        """
        Connects to a PostgreSQL database and retrieves sample values and data types
        for specified unstructured fields (e.g., JSON, ARRAY).

        Args:
            unstructured_fields (list): A list of field names to inspect.
            db_config (object): Contains PostgreSQL connection details:
                                'db_host', 'db_port', 'db_user_name',
                                'db_password', 'db_database', 'db_table_name'.

        Returns:
            list: A list of dicts, each containing:
                  - column_name
                  - sample_value (non-null)
                  - data_type (from pg_type)
        """
        conn = None
        results = []
        try:
            conn = psycopg2.connect(
                host=db_config.db_host,
                port=db_config.db_port,
                user=db_config.db_user_name,
                password=db_config.db_password,
                dbname=db_config.db_database
            )
            cursor = conn.cursor()

            table_name = db_config.db_table_name

            for field in unstructured_fields:
                # Retrieve 1 non-null sample value and the PostgreSQL data type
                query = f"""
                    SELECT {field}, pg_typeof({field})::text
                    FROM {table_name}
                    WHERE {field} IS NOT NULL
                    LIMIT 1;
                """
                cursor.execute(query)
                row = cursor.fetchone()
                if row:
                    sample_value, data_type = row
                    results.append({
                        "column_name": field,
                        "sample_value": sample_value,
                        "data_type": data_type
                    })

        except (Exception, Error) as e:
            print(f"Error while connecting to PostgreSQL or querying: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()
        return results


    @staticmethod
    def perform_discovery_query(discovery_queries, db_config):
        try:
            conn = psycopg2.connect(
                host=db_config.db_host,
                port=db_config.db_port,
                user=db_config.db_user_name,
                password=db_config.db_password,
                dbname=db_config.db_database
            )
            cursor = conn.cursor()

            table_name = db_config.db_table_name

            results = []
            for item in discovery_queries.get('discovery_queries', []):
                description = item.get('description')
                query = item.get('query')
                try:
                    cursor.execute(query)
                    query_result = cursor.fetchall()
                except Exception as e:
                    query_result = f"Error executing query: {str(e)}"
                results.append({
                    "description": description,
                    "query": query,
                    "query_result": query_result
                })
        except (Exception, Error) as e:
            print(f"Error while connecting to PostgreSQL or querying: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()
        return results