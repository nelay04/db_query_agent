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
        

    @staticmethod
    def get_prominent_unstructured_data(unstructured_fields, db_config):
        """
        Connects to a PostgreSQL database and retrieves up to 2 prominent (non-null)
        data entries for specified unstructured fields (JSON or ARRAY).

        Args:
            unstructured_fields (list): A list of field names (strings) to query.
            db_config (dict): A dictionary containing database connection parameters:
                            'host', 'port', 'user', 'password', 'dbname', 'tablename'.

        Returns:
            dict: A dictionary where keys are field names and values are lists
                containing the retrieved prominent data. Returns an empty dictionary
                if no data is found or an error occurs.
        """
        conn = None
        results = {}
        try:
            # Establish the database connection
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
                # Construct the query to select up to 2 non-null values.
                # For "prominent" in unstructured data (like JSON or ARRAY),
                # we are simply selecting the first two non-null entries found.
                # If "prominent" implies specific criteria (e.g., largest JSON object,
                # longest array), the query would need to be more complex (e.g.,
                # using ORDER BY LENGTH(CAST(field AS TEXT)) DESC).
                query = f"SELECT {field} FROM {table_name} WHERE {field} IS NOT NULL LIMIT 2;"
                
                # print(f"Executing query for field '{field}': {query}") # For debugging
                cursor.execute(query)
                fetched_data = cursor.fetchall()

                # Extract just the data from the fetched tuples (e.g., [(value,), (value,)])
                field_data = [item[0] for item in fetched_data]
                results[field] = field_data
                # print(f"Retrieved data for '{field}': {field_data}") # For debugging

        except (Exception, Error) as e:
            print(f"Error while connecting to PostgreSQL or querying: {e}")
            # In a real application, you might want to log this error or handle it more gracefully
        finally:
            if conn:
                cursor.close()
                conn.close()
                # print("PostgreSQL connection closed.")
        return results
