from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, TextResourceContents
import sqlite3
import os
import json
from pydantic import BaseModel, Field
from typing import Optional, List
import networkx as nx
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///../data/catalog.db").replace("sqlite:///", "")

def ensure_db_seeded():
    """Ensure database is seeded on startup."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM departments')
        if cursor.fetchone()[0] == 0:
            print("Database empty, seeding...")
            import subprocess
            seed_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seed.py')
            if not os.path.exists(seed_script):
                seed_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'seed.py')
            result = subprocess.run(['python', seed_script], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
            if result.returncode != 0:
                print(f"Seeding failed: {result.stderr}")
            else:
                print("Database seeded successfully")
        else:
            print("Database already seeded")
    finally:
        conn.close()

ensure_db_seeded()

mcp = FastMCP("University Course Catalog")

class CourseSearchResult(BaseModel):
    course_code: str
    title: str
    credits: int

class PrerequisiteInfo(BaseModel):
    course_code: str
    title: str

class PrerequisitesResponse(BaseModel):
    course_code: str
    prerequisites: List[PrerequisiteInfo]

class InstructorInfo(BaseModel):
    name: str
    email: str
    department_name: str

class GraphNode(BaseModel):
    id: str

class GraphEdge(BaseModel):
    source: str
    target: str

class PrerequisiteGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class ErrorResponse(BaseModel):
    error: str

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@mcp.tool(
    name="search_courses",
    description="Searches the university course catalog for courses matching a query string. Can be filtered by a specific department code."
)
def search_courses(query: str, department_code: Optional[str] = None) -> List[CourseSearchResult] | ErrorResponse:
    conn = get_db_connection()
    try:
        sql = """
            SELECT c.course_code, c.title, c.credits
            FROM courses c
            JOIN departments d ON c.department_id = d.id
            WHERE (c.title LIKE ? OR c.description LIKE ? OR c.course_code LIKE ?)
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]
        
        if department_code:
            sql += " AND d.code = ?"
            params.append(department_code)
        
        sql += " ORDER BY c.course_code"
        
        cursor = conn.execute(sql, params)
        results = cursor.fetchall()
        
        return [
            CourseSearchResult(course_code=row["course_code"], title=row["title"], credits=row["credits"])
            for row in results
        ]
    finally:
        conn.close()

@mcp.tool(
    name="get_prerequisites",
    description="Retrieves the direct prerequisites for a given course code. Returns the course code and title of each prerequisite."
)
def get_prerequisites(course_code: str) -> PrerequisitesResponse | ErrorResponse:
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT id FROM courses WHERE course_code = ?", (course_code,))
        course = cursor.fetchone()
        if not course:
            return ErrorResponse(error="Course not found")
        
        cursor = conn.execute("""
            SELECT c.course_code, c.title
            FROM courses c
            JOIN prerequisites p ON c.id = p.prerequisite_id
            WHERE p.course_id = ?
            ORDER BY c.course_code
        """, (course["id"],))
        
        prerequisites = [
            PrerequisiteInfo(course_code=row["course_code"], title=row["title"])
            for row in cursor.fetchall()
        ]
        
        return PrerequisitesResponse(course_code=course_code, prerequisites=prerequisites)
    finally:
        conn.close()

@mcp.tool(
    name="lookup_instructor",
    description="Finds an instructor's details by their name. Returns the instructor's name, email, and department name."
)
def lookup_instructor(instructor_name: str) -> InstructorInfo | ErrorResponse:
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT i.name, i.email, d.name as department_name
            FROM instructors i
            JOIN departments d ON i.department_id = d.id
            WHERE i.name LIKE ?
        """, (f"%{instructor_name}%",))
        
        instructor = cursor.fetchone()
        if not instructor:
            return ErrorResponse(error="Instructor not found")
        
        return InstructorInfo(
            name=instructor["name"],
            email=instructor["email"],
            department_name=instructor["department_name"]
        )
    finally:
        conn.close()

@mcp.tool(
    name="get_prerequisite_graph",
    description="Returns the full prerequisite dependency graph for a given course code as an adjacency list. Includes all transitive prerequisites."
)
def get_prerequisite_graph(course_code: str) -> PrerequisiteGraphResponse | ErrorResponse:
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT id FROM courses WHERE course_code = ?", (course_code,))
        course = cursor.fetchone()
        if not course:
            return ErrorResponse(error="Course not found")
        
        cursor = conn.execute("SELECT course_code FROM courses")
        all_courses = {row["course_code"]: row["course_code"] for row in cursor.fetchall()}
        
        cursor = conn.execute("""
            SELECT c1.course_code as source, c2.course_code as target
            FROM prerequisites p
            JOIN courses c1 ON p.prerequisite_id = c1.id
            JOIN courses c2 ON p.course_id = c2.id
        """)
        edges = cursor.fetchall()
        
        G = nx.DiGraph()
        for code in all_courses:
            G.add_node(code)
        for edge in edges:
            G.add_edge(edge["source"], edge["target"])
        
        if course_code not in G:
            return ErrorResponse(error="Course not found in graph")
        
        ancestors = nx.ancestors(G, course_code)
        relevant_nodes = ancestors | {course_code}
        
        subgraph = G.subgraph(relevant_nodes)
        
        nodes = [GraphNode(id=node) for node in subgraph.nodes()]
        edges_list = [GraphEdge(source=u, target=v) for u, v in subgraph.edges()]
        
        return PrerequisiteGraphResponse(nodes=nodes, edges=edges_list)
    finally:
        conn.close()

@mcp.resource("course://descriptions", name="course_descriptions")
def course_descriptions() -> str:
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT c.course_code, c.title, c.description
            FROM courses c
            ORDER BY c.course_code
        """)
        courses = cursor.fetchall()
        
        lines = []
        for course in courses:
            lines.append(f"[{course['course_code']}] {course['title']}: {course['description']}")
        
        return "\n".join(lines)
    finally:
        conn.close()

@mcp.resource("department://directory", name="department_directory")
def department_directory() -> str:
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT name, code FROM departments ORDER BY code")
        departments = cursor.fetchall()
        
        lines = []
        for dept in departments:
            lines.append(f"{dept['name']} ({dept['code']})")
        
        return "\n".join(lines)
    finally:
        conn.close()

@mcp.prompt(
    name="course_comparison_template",
    description="A template for comparing two courses side by side. Provide two course codes to generate a structured comparison."
)
def course_comparison_template(course_code_1: str, course_code_2: str) -> str:
    return f"""Create a detailed comparison table for the following two courses: {course_code_1} and {course_code_2}.

Include the following columns:
- Course Code
- Title
- Credits
- Description
- Prerequisites
- Instructor
- Department

Format the output as a markdown table for easy reading."""

async def health_check(request):
    return JSONResponse({"status": "healthy"})

# Create the Starlette app with MCP and health check
app = Starlette(
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Mount("/", app=mcp.sse_app()),
    ]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)