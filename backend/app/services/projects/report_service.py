import os
import logging
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from backend.app.schemas.report import ReportRequest, ReportResponse
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

LLM_TIMEOUT = settings.LLM_TIMEOUT
LLM_BASE_URL = settings.LLM_BASE_URL
LLM_MODEL_NAME = settings.LLM_MODEL_NAME

class ReportService:
    """Handles Natural Language to SQL conversion and safe execution."""

    PROMPT_TEMPLATE = """
You are an expert SQLite developer specializing in architectural cost estimation systems. Your task is to convert natural language questions into valid, efficient SQL queries.

### DATABASE SCHEMA:

1. Table: projects
   - id: INTEGER (PK)
   - name: TEXT (Project name)
   - currency: TEXT (e.g., 'USD', 'EUR')
   - location: TEXT

2. Table: rooms
   - id: INTEGER (PK)
   - project_id: INTEGER (FK to projects.id)
   - name: TEXT (Room name, e.g., 'Living Room', 'Kitchen')
   - floor_area_m2: FLOAT
   - wall_area_m2: FLOAT
   - perimeter_m: FLOAT

3. Table: walls
   - id: INTEGER (PK)
   - project_id: INTEGER (FK to projects.id)
   - length_m: FLOAT
   - height_m: FLOAT (default 2.70)
   - area_m2: FLOAT

4. Table: room_objects (Junction table linking Rooms/Walls to Costs)
   - id: INTEGER (PK)
   - project_id: INTEGER (FK)
   - room_id: INTEGER (FK to rooms.id)
   - wall_id: INTEGER (FK to walls.id, nullable)
   - object_type: TEXT ('wall', 'floor', 'ceiling')

5. Table: cost_items (The actual costs)
   - id: INTEGER (PK)
   - relation_id: INTEGER (FK to room_objects.id) <-- KEY JOIN COLUMN
   - item_name: TEXT (e.g., 'Paint', 'Tiles', 'Bricks')
   - category: TEXT (e.g., 'Finishing', 'Structure')
   - quantity: NUMERIC
   - unit: TEXT ('m2', 'm', 'piece', 'kg', 'liter')
   - unit_price: NUMERIC
   - total_price: NUMERIC
   - material_quality: TEXT (e.g., 'High', 'Medium', 'Low')
   - source: TEXT ('manual', 'ai_predicted')

### RELATIONSHIP RULES (CRITICAL):
1. To get costs for a ROOM: 
   JOIN rooms -> room_objects (on rooms.id = room_objects.room_id) -> cost_items (on room_objects.id = cost_items.relation_id)
2. To get costs for a WALL:
   JOIN walls -> room_objects (on walls.id = room_objects.wall_id) -> cost_items (on room_objects.id = cost_items.relation_id)
3. Always filter by project_id if a specific project is mentioned or implied.

### EXAMPLES:

Example 1:
Question: "What is the total cost of painting for the Living Room in Project 'Villa A'?"
SQL: 
SELECT SUM(ci.total_price) 
FROM cost_items ci
JOIN room_objects ro ON ci.relation_id = ro.id
JOIN rooms r ON ro.room_id = r.id
JOIN projects p ON r.project_id = p.id
WHERE p.name = 'Villa A' 
AND r.name = 'Living Room' 
AND ci.item_name LIKE '%paint%';

Example 2:
Question: "Show me all cost items for walls in the Kitchen."
SQL:
SELECT ci.item_name, ci.quantity, ci.unit, ci.total_price
FROM cost_items ci
JOIN room_objects ro ON ci.relation_id = ro.id
JOIN rooms r ON ro.room_id = r.id
WHERE r.name = 'Kitchen'
AND ro.object_type = 'wall';

Example 3:
Question: "What is the average unit price for tiles across all projects?"
SQL:
SELECT AVG(ci.unit_price) 
FROM cost_items ci 
WHERE ci.item_name LIKE '%tile%';

Example 4:
Question: "List all rooms with floor area greater than 20 sqm in Project 'Office B'."
SQL:
SELECT name, floor_area_m2 
FROM rooms 
WHERE project_id = (SELECT id FROM projects WHERE name = 'Office B') 
AND floor_area_m2 > 20;

### RULES:
1. Use LIKE for text matching (case-insensitive).
2. Always check if 'project' is mentioned to add project filtering.
3. Return ONLY the SQL query. No markdown, no explanations.
4. Use standard SQLite syntax.

### NOW CONVERT THIS QUESTION TO SQL:
Question: "{question}"
SQL:
"""

    @staticmethod
    def call_local_llm(prompt: str) -> str:
        """
        Sends the prompt to a local LLM via OpenAI-compatible API.
        """
        url = f"{LLM_BASE_URL}/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": LLM_MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that generates only SQL code."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1, # Low temperature for deterministic SQL generation
            "max_tokens": 500,
            "stop": ["\n\n", "```"] # Stop sequences to prevent extra text
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=LLM_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract content from OpenAI-compatible response structure
            if 'choices' in data and len(data['choices']) > 0:
                sql_query = data['choices'][0]['message']['content'].strip()
                # Clean up any remaining markdown artifacts just in case
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
                return sql_query
            else:
                raise Exception("Invalid response structure from LLM")

        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="Could not connect to Local LLM. Is it running?")
        except Exception as e:
            logger.error(f"LLM Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"LLM Processing Error: {str(e)}")

    @staticmethod
    def generate_and_execute_report(db: Session, request: ReportRequest) -> ReportResponse:
        """
        End-to-end pipeline: LLM → Safety Check → Execution → Response.

        Safety Measures:
            - Only SELECT statements allowed.
            - Forbidden keywords: DROP, DELETE, UPDATE, INSERT, ALTER.
            - Project-scoped filtering enforced via prompt engineering.
        """
        
        # 1. Generate SQL via Local LLM
        final_prompt = ReportService.PROMPT_TEMPLATE.format(question=request.question)
        try:
            generated_sql = ReportService.call_local_llm(final_prompt)
            print(80*"=")
            print("generated_sql:")
            print(generated_sql)
        except HTTPException as e:
            # Re-raise HTTP exceptions from LLM service
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected LLM Error: {str(e)}")

        # 2. Validate Safety
        if not ReportService._is_safe_sql(generated_sql):
            return ReportResponse(
                question=request.question,
                generated_sql=generated_sql,
                data=[],
                message="❌ Generated SQL contains unsafe operations (Only SELECT is allowed)."
            )

        # 3. Execute & Serialize
        try:
            result = db.execute(text(generated_sql))
            
            # Convert rows to list of dicts
            columns = result.keys()
            data = [dict(row._mapping) for row in result.fetchall()]
            
            # Clean non-serializable types (Decimal → float)
            clean_data = []
            for row in data:
                clean_row = {}
                for k, v in row.items():
                    if hasattr(v, '__float__'):
                        clean_row[k] = float(v)
                    else:
                        clean_row[k] = v
                clean_data.append(clean_row)
            result = ReportResponse(
                question=request.question,
                generated_sql=generated_sql,
                data=clean_data,
                message="Report generated successfully."
            )
            print(result)
            print(80*"=")
            return result

        except Exception as e:
            logger.error(f"SQL Execution Error: {str(e)}")
            return ReportResponse(
                question=request.question,
                generated_sql=generated_sql,
                data=[],
                message=f"❌ SQL Execution Error: {str(e)}"
            )

    @staticmethod
    def _is_safe_sql(sql: str) -> bool:
        """
        Simple safety check to ensure only SELECT statements are executed.
        """
        sql_upper = sql.upper().strip()
        forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        
        # Check if it starts with SELECT
        if not sql_upper.startswith("SELECT"):
            return False
            
        # Check for forbidden keywords anywhere in the string
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return False
                
        return True