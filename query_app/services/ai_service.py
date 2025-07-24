import os
import google.generativeai as genai
import json

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
    def generate_sql_single_table(prompt: str, structure: str, table_name=str):
        try:        
            # return ('SELECT age, COUNT(*) FROM students WHERE age IN (18, 19, 21) GROUP BY age;')
            system_prompt = (
                f"You are a SQL expert. The table is named '{table_name}' and its schema is:\n{structure}\n\n"
                "You must convert user prompts into PostgreSQL SELECT queries that return grouped counts suitable for pie charts.\n"
                "Rules:\n"
                "- Always return a query that selects a **single categorical column** (e.g., age, gender, department, city, grade, etc.).\n"
                "- Count the number of rows for each distinct value in that column using `COUNT(*)`.\n"
                "- Use `WHERE ... IN (...)` only if the user specifies a subset of values.\n"
                "- Always use `GROUP BY <column>` to return results like: (label, count).\n"
                "- Do **not** compute ratios, percentages, or numeric divisions in SQL.\n"
                "- Do **not** format output in markdown or add explanations.\n\n"
                "Your output should look like:\n"
                "SELECT <column>, COUNT(*) FROM <table_name> [WHERE ...] GROUP BY <column>;\n\n"
                "Here is the user's request:"
            )

            full_prompt = f"{system_prompt}\n\n{prompt}"

            response = model.generate_content(full_prompt)
            sql = response.text.strip()

            # Optional: remove markdown if Gemini returns ```sql ... ```
            if sql.startswith("```"):
                sql = sql.strip("```sql").strip("```").strip()

            return( sql)
        except Exception as e:
            return ResponseService.error(f'Error generation query: {str(e)}', code=500)
        

    @staticmethod
    def generate_sql_multiple_table(prompt: str, structure: str):
        try:        
            # return ('SELECT age, COUNT(*) FROM students WHERE age IN (18, 19, 21) GROUP BY age;')
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
            print("\033[94mResponse from Gemini:\033[0m", response.text)
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
            print("Single value result:", chart_data)
            return chart_data
        except Exception as e:
            return ResponseService.error(f'Error generation chart data: {str(e)}', code=500)