# University Course Catalog MCP Server

A Model Context Protocol (MCP) server that exposes a university's course catalog to LLM assistants. This server provides tools for searching courses, retrieving prerequisites, looking up instructors, and getting prerequisite dependency graphs, along with resources for course descriptions and department directories.

## Features

- **Tools** (callable functions for LLMs):
  - `search_courses` - Search courses by keyword with optional department filter
  - `get_prerequisites` - Get direct prerequisites for a course
  - `lookup_instructor` - Find instructor details by name
  - `get_prerequisite_graph` - Get full prerequisite dependency graph (transitive closure)

- **Resources** (contextual data for LLMs):
  - `course_descriptions` - Formatted list of all courses with descriptions
  - `department_directory` - List of all academic departments

- **Prompts** (pre-defined templates):
  - `course_comparison_template` - Template for comparing two courses

## Quick Start

### Using Docker Compose (Recommended)

```bash
docker-compose up --build
```

The server will be available at `http://localhost:8080`.

### Manual Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Seed the database (if not already done):
   ```bash
   cd data && python seed.py
   ```

3. Run the server:
   ```bash
   python src/server.py
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Path to SQLite database | `sqlite:///./data/catalog.db` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8080` |

See `.env.example` for all available variables.

## MCP Tools

### search_courses
Searches the university course catalog for courses matching a query string.

**Input:**
```json
{
  "query": "string",
  "department_code": "string (optional)"
}
```

**Output:**
```json
[
  {
    "course_code": "string",
    "title": "string",
    "credits": "integer"
  }
]
```

### get_prerequisites
Retrieves the direct prerequisites for a given course code.

**Input:**
```json
{
  "course_code": "string"
}
```

**Output:**
```json
{
  "course_code": "string",
  "prerequisites": [
    {
      "course_code": "string",
      "title": "string"
    }
  ]
}
```

### lookup_instructor
Finds an instructor's details by their name.

**Input:**
```json
{
  "instructor_name": "string"
}
```

**Output:**
```json
{
  "name": "string",
  "email": "string",
  "department_name": "string"
}
```

### get_prerequisite_graph
Returns the full prerequisite dependency graph for a given course code as an adjacency list.

**Input:**
```json
{
  "course_code": "string"
}
```

**Output:**
```json
{
  "nodes": [
    {"id": "string"}
  ],
  "edges": [
    {"source": "string", "target": "string"}
  ]
}
```

## MCP Resources

### course_descriptions
A formatted list of all courses and their descriptions.

**URI:** `course://descriptions`

**Example content:**
```
[CS101] Introduction to Programming: A foundational course on programming principles using Python.
[CS102] Data Structures and Algorithms: Covers fundamental data structures and algorithm design techniques.
...
```

### department_directory
A formatted list of all departments and their codes.

**URI:** `department://directory`

**Example content:**
```
Computer Science (CS)
Mathematics (MATH)
Physics (PHYS)
```

## MCP Prompts

### course_comparison_template
A template for comparing two courses side by side.

**Parameters:**
- `course_code_1`: First course code
- `course_code_2`: Second course code

**Example usage:**
```
Create a detailed comparison table for the following two courses: CS101 and CS102.

Include the following columns:
- Course Code
- Title
- Credits
- Description
- Prerequisites
- Instructor
- Department

Format the output as a markdown table for easy reading.
```

## Example Natural Language Queries for LLMs

An LLM connected to this MCP server could handle queries like:

- "What courses are available in Computer Science?"
- "What are the prerequisites for CS401 Machine Learning?"
- "Show me the full prerequisite chain for CS401"
- "Who teaches CS101 and what's their email?"
- "Compare CS101 and CS102 for me"
- "List all courses related to databases"
- "What courses does Dr. Alice Smith teach?"
- "I want to take CS301 Operating Systems - what do I need to complete first?"

## Database Schema

The SQLite database contains four tables:

- **departments**: `id`, `name`, `code`
- **instructors**: `id`, `name`, `email`, `office`, `department_id`
- **courses**: `id`, `course_code`, `title`, `description`, `credits`, `instructor_id`, `department_id`
- **prerequisites**: `course_id`, `prerequisite_id` (many-to-many relationship)

## Seed Data

The database comes pre-seeded with:
- 3 Departments (Computer Science, Mathematics, Physics)
- 5 Instructors
- 10 Courses
- 8 Prerequisite relationships (including multi-level chains)

## Testing with MCP Inspector

You can test the server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector http://localhost:8080/sse
```

## Health Check

The server provides a health endpoint at `GET /health` that returns:
```json
{"status": "healthy"}
```

## License

MIT