import os
import google.generativeai as genai
import json
import re
import datetime

# Services
from .response_service import ResponseService


# Setup Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("\033[91mCould not find GEMINI_API_KEY environment variable\033[0m")
else:
    print("\033[92mUsing GEMINI_API_KEY from environment\033[0m")
    genai.configure(api_key=api_key)

    model_name = os.getenv("GENERATIVE_MODEL")
    if not model_name:
        print("\033[91mCould not find GENERATIVE_MODEL environment variable\033[0m")
    else:
        print(f"\033[92mUsing {model_name} as generative model\033[0m\n")
        model = genai.GenerativeModel(model_name)


class AIService:
    @staticmethod
    def generate_sql_single_table(prompt: str, structure: str, table_name=str, sample_unstructured_data=None):
        try:
            # return ('Single table query')

            system_prompt = (
                f"You are a SQL expert. The table is named '{table_name}' and its schema is:\n{structure}\n\n"
            )
            if sample_unstructured_data:
                # If sample_unstructured_data is a list of dicts with column_name, data_type, sample_value
                for col_info in sample_unstructured_data:
                    col_name = col_info.get('column_name')
                    data_type = col_info.get('data_type')
                    sample_value = col_info.get('sample_value')
                    system_prompt += (
                        f"\nSample value for column '{col_name}' (data type: {data_type}):\n{json.dumps(sample_value, indent=2)}\n"
                        "Use this sample to understand the structure and content for this column.\n"
                    )
                system_prompt += "\n"
            system_prompt += (
               "You must convert user prompts into PostgreSQL SELECT queries that return grouped counts suitable for pie charts.\n\n"
                "Your task:\n"
                "1. Generate the main SELECT query.\n"
                "2. Generate minimal atomic validation queries to verify correctness of all values and relationships used in the query.\n\n"
                "Rules:\n"
                "- Identify the most relevant **table** and **categorical column** based on the user's intent.\n"
                "- The main query must count rows grouped by a **single categorical column** (e.g., age, gender, department, city, grade, etc.).\n"
                "- Use `COUNT(*)` to count rows for each distinct value in the column.\n"
                "- If the user specifies a subset of values, use `WHERE <column> IN (...)`.\n"
                "- Always use `GROUP BY <column>` and return results as (label, count).\n"
                "- Do **not** compute ratios, percentages, or numeric divisions.\n"
                "- Do **not** format output in markdown or add explanations.\n"
                "- Do **not** simplify, modify, or rephrase string literals. Use the **exact values from the user prompt** in WHERE clauses (e.g., exact addresses or names).\n"
                "- For atomic checks, use `SELECT EXISTS(SELECT 1 FROM ...) AS <alias>` format.\n"
                "- Each atomic check should validate either:\n"
                "  • A specific value exists (e.g., a city, gender, or blood group), or\n"
                "  • A valid relationship/join exists (e.g., student_id matches between two tables), or\n"
                "  • All filters together produce results.\n"
                "- Return the output in **strict JSON format** with two keys: `main_query` and `atomic_checks`.\n"
                "- `main_query` is a string.\n"
                "- `atomic_checks` is a list of objects with `description` and `query`.\n\n"
                "Output format:\n"
                "{\n"
                '  "main_query": "SELECT ...;",\n'
                '  "atomic_checks": [\n'
                '    {\n'
                '      "description": "Check if ...",\n'
                '      "query": "SELECT EXISTS(SELECT 1 FROM ...) AS ...;"\n'
                '    },\n'
                '    ...\n'
                '  ]\n'
                "}\n\n"
                "Here is the user's request:"
            )

            full_prompt = f"{system_prompt}\n\n{prompt}"

            # print(full_prompt)
            # return full_prompt

            response = model.generate_content(full_prompt)
            # print("\033[94mResponse from Gemini:\033[0m", response.text)
            json_response = response.text.strip()

            # # Optional: remove markdown if Gemini returns ```sql ... ```
            if json_response.startswith("```"):
                json_response = json_response.strip("```sql").strip("```").strip()
            # Also remove a leading 'json' string if present
            if json_response.lower().startswith("json"):
                json_response = json_response[4:].lstrip(":").lstrip()
                
            parsed_data = json.loads(json_response)
            return parsed_data # Return the Python dictionary
        except Exception as e:
            return ResponseService.error(f'Error generation query: {str(e)}', code=500)
        

    @staticmethod
    def generate_sql_multiple_table(prompt: str, structure: str):
        try:        
            # return ('Multiple table query')
            # system_prompt = (
            #     "You are a SQL expert. The database contains the following tables and their schemas:\n"
            #     f"{structure}\n\n"
            #     "You must convert user prompts into PostgreSQL SELECT queries that return grouped counts suitable for pie charts.\n"
            #     "Rules:\n"
            #     "- Identify the most relevant **table** and **categorical column** based on the user's intent.\n"
            #     "- The query must count rows grouped by a **single categorical column** (e.g., age, gender, department, city, grade, etc.).\n"
            #     "- Use `COUNT(*)` to count rows for each distinct value in the column.\n"
            #     "- If the user specifies a subset of values, use `WHERE <column> IN (...)`.\n"
            #     "- Always use `GROUP BY <column>` and return results as (label, count).\n"
            #     "- Do **not** compute ratios, percentages, or numeric divisions.\n"
            #     "- Do **not** format output in markdown or add explanations.\n"
            #     "- **Use the exact phrasing and values from the user's prompt when writing WHERE clauses.** Do not simplify or change string values like addresses.\n\n"
            #     "Your output should look like:\n"
            #     "SELECT <column>, COUNT(*) FROM <table_name> [WHERE ...] GROUP BY <column>;\n\n"
            #     "Here is the user's request:"
            # )

            system_prompt = (
                "You are a SQL expert. The database contains the following tables and their schemas:\n"
                f"{structure}\n\n"
                "You must convert user prompts into PostgreSQL SELECT queries that return grouped counts suitable for pie charts.\n\n"
                "Your task:\n"
                "1. Generate the main SELECT query.\n"
                "2. Generate minimal atomic validation queries to verify correctness of all values and relationships used in the query.\n\n"
                "Rules:\n"
                "- Identify the most relevant **table** and **categorical column** based on the user's intent.\n"
                "- The main query must count rows grouped by a **single categorical column** (e.g., age, gender, department, city, grade, etc.).\n"
                "- Use `COUNT(*)` to count rows for each distinct value in the column.\n"
                "- If the user specifies a subset of values, use `WHERE <column> IN (...)`.\n"
                "- Always use `GROUP BY <column>` and return results as (label, count).\n"
                "- Do **not** compute ratios, percentages, or numeric divisions.\n"
                "- Do **not** format output in markdown or add explanations.\n"
                "- Do **not** simplify, modify, or rephrase string literals. Use the **exact values from the user prompt** in WHERE clauses (e.g., exact addresses or names).\n"
                "- For atomic checks, use `SELECT EXISTS(SELECT 1 FROM ...) AS <alias>` format.\n"
                "- Each atomic check should validate either:\n"
                "  • A specific value exists (e.g., a city, gender, or blood group), or\n"
                "  • A valid relationship/join exists (e.g., student_id matches between two tables), or\n"
                "  • All filters together produce results.\n"
                "- Return the output in **strict JSON format** with two keys: `main_query` and `atomic_checks`.\n"
                "- `main_query` is a string.\n"
                "- `atomic_checks` is a list of objects with `description` and `query`.\n\n"
                "Output format:\n"
                "{\n"
                '  "main_query": "SELECT ...;",\n'
                '  "atomic_checks": [\n'
                '    {\n'
                '      "description": "Check if ...",\n'
                '      "query": "SELECT EXISTS(SELECT 1 FROM ...) AS ...;"\n'
                '    },\n'
                '    ...\n'
                '  ]\n'
                "}\n\n"
                "Here is the user's request:"
            )

            full_prompt = f"{system_prompt}\n\n{prompt}"
            # return (full_prompt)

            response = model.generate_content(full_prompt)
            # print("\033[94mResponse from Gemini:\033[0m", response.text)
            json_response = response.text.strip()

            # # Optional: remove markdown if Gemini returns ```sql ... ```
            if json_response.startswith("```"):
                json_response = json_response.strip("```sql").strip("```").strip()
            # Also remove a leading 'json' string if present
            if json_response.lower().startswith("json"):
                json_response = json_response[4:].lstrip(":").lstrip()
                
            parsed_data = json.loads(json_response)
            return parsed_data # Return the Python dictionary

        except Exception as e:
            return ResponseService.error(f'Error generation query: {str(e)}', code=500)
        


    @staticmethod
    def generate_chart_data(result):
        try:
            if not result:
                chart_data = {"labels": [], "values": []}
            elif isinstance(result[0], tuple):
                # Case: result = [(value1,), (value2,), ...] or [(label1, value1), (label2, value2), ...]
                if len(result[0]) == 1:
                    # Only values with no labels — use default labels
                    chart_data = {
                        "labels": [f"Item {i+1}" for i in range(len(result))],
                        "values": [float(row[0]) for row in result]
                    }
                else:
                    # Standard case: label-value pairs
                    chart_data = {
                        "labels": [str(row[0]) for row in result],
                        "values": [float(row[1]) for row in result]
                    }
            else:
                chart_data = {"labels": ["Result"], "values": [float(result[0])]}
            # print("Single value result:", chart_data)
            return chart_data
        except Exception as e:
            return ResponseService.error(f'Error generation chart data: {str(e)}', code=500)
        


    @staticmethod
    def count_tokens_regex(text):
        """
        Counts tokens in a string using a regular expression.
        A token is defined as a sequence of alphanumeric characters or a single non-whitespace, non-alphanumeric character.
        This is a more robust approach than simple whitespace splitting.
        """
        # This regex matches:
        # 1. Word characters (alphanumeric + underscore)
        # 2. Or, any non-whitespace character that is not a word character (e.g., punctuation)
        tokens = re.findall(r'\b\w+\b|[^ \t\n\r\f\v]', text)
        return len(tokens)
    
    @staticmethod
    def generate_discovery_queries(
        prompt: str,
        structure: str,
        table_name: str,
        sample_unstructured_data: str = None
    ):
        try:
            # Construct system prompt
            system_prompt = (
                f"You are a PostgreSQL SQL and data exploration expert. "
                f"The table is named '{table_name}' and its schema is:\n{structure}\n\n"
            )

            if sample_unstructured_data:
                # If sample_unstructured_data is a list of dicts with column_name, data_type, sample_value
                for col_info in sample_unstructured_data:
                    col_name = col_info.get('column_name')
                    data_type = col_info.get('data_type')
                    sample_value = col_info.get('sample_value')
                    system_prompt += (
                        f"\nSample value for column '{col_name}' (data type: {data_type}):\n{json.dumps(sample_value, indent=2)}\n"
                        "Use this sample to understand the structure and content for this column.\n"
                    )
                system_prompt += "\n"

            system_prompt += (
                "You will receive natural language prompts from the user. Your task is to determine **what specific data values and structures are needed** "
                "to build the correct SQL query later, focusing purely on data exploration.\n\n"
                "Do not generate the final analytical or aggregated SQL for now. Your response must only contain discovery queries.\n"
                "Instead, return a set of **PostgreSQL discovery queries** that help:\n"
                "- **Type 1: Verify Criteria Existence:** Locate and verify important values mentioned by the user (e.g., specific assessment names, questions, answers, tags). Use `COUNT(*)` or `SELECT 1` with `LIMIT 1` for existence checks.\n"
                "  - **Example:** `SELECT COUNT(*) FROM table_name WHERE assessment_name = 'User Assessment' LIMIT 1;`\n"
                "  - **Example for nested JSON:** `SELECT 1 FROM table_name, LATERAL jsonb_array_elements((table_name.json_column::jsonb)->'array_key') AS elem WHERE elem->>'property' = 'User Value' LIMIT 1;`\n"
                "- **Type 2: Discover Distinct Values:** Identify all distinct possible values for a relevant field to understand its cardinality or variations. Use `SELECT DISTINCT`.\n"
                "  - **Example:** `SELECT DISTINCT status FROM table_name LIMIT 10;`\n"
                "  - **Example for nested JSON:** `SELECT DISTINCT elem->>'answer' FROM table_name, LATERAL jsonb_array_elements((table_name.json_column::jsonb)->'array_key') AS elem WHERE elem->>'question' = 'Specific Question' LIMIT 10;`\n"
                "- **Type 3: Retrieve Sample Raw Data:** Pick a small number of rows (e.g., `LIMIT 2` or `LIMIT 5`) that meet the primary criteria, selecting the entire relevant JSON columns or other crucial columns. This helps understand the full context and structure for the next AI call.\n"
                "  - **Example:** `SELECT column_with_json, another_relevant_column FROM table_name WHERE some_condition = 'value' LIMIT 2;`\n\n"
                "Your output must be a JSON with a single key:\n"
                "- `discovery_queries`: a list of objects, each with `description` (a clear explanation of the query's purpose) and `query` (the PostgreSQL SQL query).\n\n"
                "**Strict Rules for Discovery Queries:**\n"
                "- Focus *only* on exploring the data to **find the exact information required** for the next step of query building.\n"
                "- **Do not assume values exist** unless they are explicitly present in the provided `sample_unstructured_data` or the user's prompt directly implies them. If uncertain, write a query to discover.\n"
                "- For `json` type columns containing JSON objects or arrays, you **MUST** explicitly cast the column to `jsonb` first using `::jsonb` before using JSONB operators (`->`, `->>`, `jsonb_array_elements()`).\n"
                "- **CRITICAL for JSON/JSONB Arrays nested within Objects:** If a column (e.g., `column_name`) is a JSON object and contains a nested array under a specific key (e.g., `column_name: {'nested_array_key': [...]}`), you **MUST** first cast the parent JSON column to `jsonb` (e.g., `table_name.column_name::jsonb`), then navigate to the array using `->` (e.g., `(table_name.column_name::jsonb)->'nested_array_key'`) **before** applying `jsonb_array_elements()`. This ensures correct operator precedence. This applies even if the nested array's key has the same name as the parent column (e.g., `result` column containing `(tbl_surv_result.result::jsonb)->'result'`).\n"
                "  Always use `jsonb_array_elements()` in the `FROM` clause with the `LATERAL` keyword and an alias to unnest array elements. Then, access properties of the unnested elements using `->>` on the alias.\n"
                "  **Correct Example for an array nested within an object in a column (e.g., `column_name: {'nested_array_key': [...]}`):** \n"
                "  `SELECT elem->>'property' FROM table_name, LATERAL jsonb_array_elements((table_name.column_name::jsonb)->'nested_array_key') AS elem WHERE ...`\n"
                "  **Correct Example if the column directly contains the array and is `json` type:**\n"
                "  `SELECT elem->>'property' FROM table_name, LATERAL jsonb_array_elements(table_name.column_name::jsonb) AS elem WHERE ...`\n"
                "- Always include `LIMIT` in your discovery queries to avoid retrieving large datasets during exploration.\n"
                "- Use exact user phrases in filters (e.g., `question = 'Have you ever experienced irregular periods?'`) unless the intent is to find partial matches (then use `ILIKE '%phrase%'` for case-insensitivity).\n"
                "- **No complex joins** (only the implicit lateral join created by `jsonb_array_elements()`), **no GROUP BY**, **no aggregations** (like `SUM`, `AVG`, `RATIO`) in discovery queries. These are for the final query, not for exploration.\n"
                "- If the user refers to specific concepts like 'obese', 'irregular', 'PCOS', 'hypertension', etc., generate queries that look inside relevant `question`, `answer`, `tag`, or `assessment_name` fields appropriately to find how these terms are stored.\n"
                "- Always refer to the provided `structure` and `sample_unstructured_data` to infer the correct column names, types, and nested JSON paths.\n\n"
                "Here is the user's request:"
            )

            full_prompt = f"{system_prompt}\n\n{prompt}"

            response = model.generate_content(full_prompt)
            json_response = response.text.strip()

            # Cleanup formatting if needed (e.g., removing markdown code blocks)
            if json_response.startswith("```"):
                json_response = json_response.strip("`").strip()
                if json_response.startswith("sql") or json_response.startswith("json"):
                    json_response = json_response.split("\n", 1)[-1].strip()

            parsed_data = json.loads(json_response)
            return parsed_data

        except Exception as e:
            return ResponseService.error(f"Error generating discovery queries: {str(e)}", code=500)
        

    @staticmethod
    def generate_sql_single_table_final(prompt: str, structure: str, table_name=str, discovery_query_results=None, sample_unstructured_data=None):
        try:
            system_prompt = (
                f"You are a PostgreSQL SQL expert. The table is named '{table_name}' and its schema is:\n{structure}\n\n"
            )

            if sample_unstructured_data:
                for col_info in sample_unstructured_data:
                    col_name = col_info.get('column_name')
                    data_type = col_info.get('data_type')
                    sample_value = col_info.get('sample_value')
                    system_prompt += (
                        f"\nSample value for column '{col_name}' (data type: {data_type}):\n{json.dumps(sample_value, indent=2)}\n"
                        "Use this sample to understand the structure and content for this column.\n"
                    )
                system_prompt += "\n"

            if discovery_query_results:
                system_prompt += (
                    "**IMPORTANT: The following 'discovery_query_results' provide verified information and sample data obtained from previous exploratory queries.** "
                    "You MUST use these results to accurately construct the main query, especially for exact string matching and understanding JSON paths. "
                    "DO NOT generate any atomic checks or re-verify these specific values; their existence is confirmed.\n\n"
                    "Here are the discovery query results:\n"
                )

                def make_json_serializable(obj):
                    if isinstance(obj, (datetime.date, datetime.datetime)):
                        return obj.isoformat()
                    if isinstance(obj, dict):
                        return {k: make_json_serializable(v) for k, v in obj.items()}
                    if isinstance(obj, (list, tuple)):
                        return [make_json_serializable(v) for v in obj]
                    return obj

                for res in discovery_query_results:
                    system_prompt += f"- Description: {res['description']}\n"
                    system_prompt += f"- Query: {res['query']}\n"
                    serializable_result = make_json_serializable(res['query_result'])
                    system_prompt += f"  Query Result: {json.dumps(serializable_result)}\n"
                system_prompt += "\n"


            system_prompt += (
                "You must convert user prompts into a **single PostgreSQL SELECT query** that returns grouped counts suitable for pie charts.\n\n"
                "Your task:\n"
                "1. Generate the **single main SELECT query** based on the user's request and the provided discovery results.\n\n"
                "Rules:\n"
                "- Identify the most relevant **table** and **categorical column** based on the user's intent.\n"
                "- The main query must count rows grouped by a **single categorical column** (e.g., age, gender, department, city, grade, etc.).\n"
                "- Use `COUNT(*)` to count rows for each distinct value in the column.\n"
                "- If the user specifies a subset of values, use `WHERE <column> IN (...)`.\n"
                "- Always use `GROUP BY <column>` and return results as (label, count).\n"
                "- Do **not** compute ratios, percentages, or numeric divisions in the SQL query itself.\n"
                "- Do **not** format output in markdown or add explanations within the SQL query.\n"
                "- Do **not** simplify, modify, or rephrase string literals. Use the **exact values identified from the discovery query results** in WHERE clauses (e.g., exact assessment names, question texts, answer values).\n"
                "- For JSON columns (like 'result'), if the desired array is nested within a key (e.g., `result: {'result': [...]}`), you **MUST** first cast the main JSON column to `jsonb` and then access the nested key: `(column_name::jsonb)->'nested_key'`.\n"
                "- Use `LATERAL jsonb_array_elements(...) AS alias_name(value_column_name)` to unnest arrays. When using `AS alias_name(value_column_name)`, the unnested element is available via `value_column_name`. You will then need to access its properties using `(value_column_name::jsonb)->>'key'`.\n"
                "- Return the output in **strict JSON format** with a single key: `main_query`.\n"
                "- `main_query` is a string containing the PostgreSQL SELECT query.\n\n"
                "Output format:\n"
                "{\n"
                '  "main_query": "SELECT ...;"\n'
                "}\n\n"
                "Here is the user's request:"
            )

            full_prompt = f"{system_prompt}\n\n{prompt}"

            # response = model.generate_content(full_prompt) # Uncomment this when using an actual LLM
            # print(response) # For debugging LLM raw output

            # For the purpose of demonstration, use the corrected Model.generate_content
            response = model.generate_content(full_prompt)

            json_response = response.text.strip()

            if json_response.startswith("```"):
                json_response = json_response.strip("```sql").strip("```").strip()
            if json_response.lower().startswith("json"):
                json_response = json_response[4:].lstrip(":").lstrip()
                
            parsed_data = json.loads(json_response)
            # print(parsed_data) # For debugging parsed data
            
            return parsed_data
        except Exception as e:
            return {"success": False, "message": f"Error generating query: {str(e)}"}