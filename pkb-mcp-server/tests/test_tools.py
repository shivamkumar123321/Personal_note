import asyncio
import tempfile
import os
from pkbs_mcp_server.config import ServerConfig
from pkbs_mcp_server.server import PKBMCPServer
from mcp.types import CallToolRequest


async def test_tools():
    """Test that the MCP tools work correctly."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Create server config with the temp db
        config = ServerConfig(database_path=tmp_path)
        server = PKBMCPServer(config)
        
        # Test create_note tool - CallToolRequest structure has method and params
        from mcp.types import CallToolRequestParams
        
        create_request = CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="create_note",
                arguments={
                    "title": "Test Note",
                    "content": "This is a test note.",
                    "tags": ["test", "example"]
                }
            )
        )
        result = await server.handle_call_tool(create_request)
        print(f"Create note result: {result.content}")
        
        # Extract the note ID from the result
        # This is a simplified test - in a real scenario the result would be parsed properly
        assert result.isError is False, f"Create note failed: {result.content}"
        
        # Test list_notes tool
        list_request = CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="list_notes",
                arguments={}
            )
        )
        result = await server.handle_call_tool(list_request)
        print(f"List notes result: {result.content}")
        assert result.isError is False, f"List notes failed: {result.content}"
        
        # Test search_notes tool
        search_request = CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="search_notes",
                arguments={"query": "test"}
            )
        )
        result = await server.handle_call_tool(search_request)
        print(f"Search notes result: {result.content}")
        assert result.isError is False, f"Search notes failed: {result.content}"
        
        print("All tool tests passed!")
        return True
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    success = asyncio.run(test_tools())
    if success:
        print("Tools test passed!")
    else:
        print("Tools test failed!")