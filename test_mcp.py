import asyncio
import json
from mcp.client.sse import sse_client
from mcp import ClientSession

async def test_mcp():
    async with sse_client("http://localhost:8080/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            print("Tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # List resources
            resources = await session.list_resources()
            print("\nResources:")
            for resource in resources.resources:
                print(f"  - {resource.name}: {resource.uri}")
            
            # List prompts
            prompts = await session.list_prompts()
            print("\nPrompts:")
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}: {prompt.description}")
            
            # Test search_courses
            print("\n--- Testing search_courses ---")
            result = await session.call_tool("search_courses", {"query": "Introduction"})
            print(f"Result: {result.content[0].text}")
            
            # Test get_prerequisites
            print("\n--- Testing get_prerequisites ---")
            result = await session.call_tool("get_prerequisites", {"course_code": "CS102"})
            print(f"Result: {result.content[0].text}")
            
            # Test lookup_instructor
            print("\n--- Testing lookup_instructor ---")
            result = await session.call_tool("lookup_instructor", {"instructor_name": "Alice"})
            print(f"Result: {result.content[0].text}")
            
            # Test get_prerequisite_graph
            print("\n--- Testing get_prerequisite_graph ---")
            result = await session.call_tool("get_prerequisite_graph", {"course_code": "CS401"})
            print(f"Result: {result.content[0].text}")
            
            # Test course_descriptions resource
            print("\n--- Testing course_descriptions resource ---")
            result = await session.read_resource("course://descriptions")
            print(f"Result (first 500 chars): {result.contents[0].text[:500]}")
            
            # Test department_directory resource
            print("\n--- Testing department_directory resource ---")
            result = await session.read_resource("department://directory")
            print(f"Result: {result.contents[0].text}")
            
            # Test course_comparison_template prompt
            print("\n--- Testing course_comparison_template prompt ---")
            result = await session.get_prompt("course_comparison_template", {"course_code_1": "CS101", "course_code_2": "CS102"})
            print(f"Result: {result.messages[0].content.text}")

if __name__ == "__main__":
    asyncio.run(test_mcp())