import asyncio
import tempfile
import os
from pkbs_mcp_server.config import ServerConfig
from pkbs_mcp_server.server import PKBMCPServer
from mcp.types import GetPromptRequest, GetPromptRequestParams


async def test_prompts():
    """Test that the MCP prompts work correctly."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Create server config with the temp db
        config = ServerConfig(database_path=tmp_path)
        server = PKBMCPServer(config)
        
        # First, create a test note to work with
        from mcp.types import CallToolRequest, CallToolRequestParams
        create_request = CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="create_note",
                arguments={
                    "title": "Test Note for Prompts",
                    "content": "This is a test note about Python programming. Python is a versatile programming language.",
                    "tags": ["python", "test", "programming"]
                }
            )
        )
        result = await server.handle_call_tool(create_request)
        print(f"Create note for prompts test: {result.content}")
        
        # Now test the summarize_notes_about prompt
        prompt_request = GetPromptRequest(
            method="prompts/get",
            params=GetPromptRequestParams(
                name="summarize_notes_about",
                arguments={"topic": "Python"}
            )
        )
        result = await server.handle_get_prompt_by_name(prompt_request)
        print(f"Summarize notes about Python: {result.messages[0].content.text[:200]}...")
        
        # Test the find_notes_by_tag prompt
        prompt_request = GetPromptRequest(
            method="prompts/get",
            params=GetPromptRequestParams(
                name="find_notes_by_tag",
                arguments={"tag": "python"}
            )
        )
        result = await server.handle_get_prompt_by_name(prompt_request)
        print(f"Find notes by tag 'python': {result.messages[0].content.text[:200]}...")
        
        # Test the search_notes prompt
        prompt_request = GetPromptRequest(
            method="prompts/get",
            params=GetPromptRequestParams(
                name="search_notes",
                arguments={"query": "programming"}
            )
        )
        result = await server.handle_get_prompt_by_name(prompt_request)
        print(f"Search notes for 'programming': {result.messages[0].content.text[:200]}...")
        
        print("All prompt tests passed!")
        return True
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    success = asyncio.run(test_prompts())
    if success:
        print("Prompts test passed!")
    else:
        print("Prompts test failed!")