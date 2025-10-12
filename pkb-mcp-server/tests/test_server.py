#!/usr/bin/env python3
"""Test script to verify that the MCP server starts correctly."""

import asyncio
import tempfile
import os
from pkbs_mcp_server.config import ServerConfig
from pkbs_mcp_server.server import PKBMCPServer


async def test_server():
    """Test that the server can be created and configured."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        tmp_path = tmp.name
    
    try:
        # Create server config with the temp db
        config = ServerConfig(database_path=tmp_path)
        
        # Create the server
        server = PKBMCPServer(config)
        
        print("✓ Server created successfully!")
        print(f"  Database path: {config.database_path}")
        
        # Test that we can access the database
        note_count = len(server.db.list_notes())
        print(f"  Initial number of notes in DB: {note_count}")
        
        # Test database operations
        from pkbs_mcp_server.models import Note
        test_note = Note(title="Test Note", content="Test content", tags=["test"])
        created = server.db.create_note(test_note)
        print(f"✓ Test note created with ID: {created.id}")
        
        # Verify retrieval
        retrieved = server.db.get_note(created.id)
        assert retrieved is not None
        print(f"✓ Test note retrieved successfully")
        
        return True
    except Exception as e:
        print(f"✗ Server test failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except PermissionError:
                pass


if __name__ == "__main__":
    success = asyncio.run(test_server())
    if success:
        print("\n✓ All server tests passed!")
    else:
        print("\n✗ Server tests failed!")
        exit(1)
