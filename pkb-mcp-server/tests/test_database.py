"""Test the database functionality of PKB MCP Server."""

import pytest
import tempfile
import os
from pkbs_mcp_server.models import Note
from pkbs_mcp_server.database import DatabaseManager


def test_database_creation():
    """Test that the database manager creates the necessary tables."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        db = DatabaseManager(tmp_path)
        
        # Test creating a note
        note = Note(title="Test Note", content="This is a test note.", tags=["test", "example"])
        created_note = db.create_note(note)
        
        assert created_note.id is not None
        assert created_note.title == "Test Note"
        assert created_note.content == "This is a test note."
        assert "test" in created_note.tags
        assert "example" in created_note.tags
        
        # Test getting the note
        retrieved_note = db.get_note(created_note.id)
        assert retrieved_note is not None
        assert retrieved_note.id == created_note.id
        assert retrieved_note.title == "Test Note"
        
        # Test searching notes
        results = db.search_notes("test")
        assert len(results) == 1
        assert results[0].id == created_note.id
        
        # Test listing notes
        notes = db.list_notes()
        assert len(notes) == 1
        assert notes[0].id == created_note.id
        
        # Test adding a tag
        success = db.add_tag(created_note.id, "new-tag")
        assert success
        
        # Get the note again to verify tag was added
        updated_note = db.get_note(created_note.id)
        assert "new-tag" in updated_note.tags
        
        # Test removing a tag
        success = db.remove_tag(created_note.id, "new-tag")
        assert success
        
        # Get the note again to verify tag was removed
        updated_note = db.get_note(created_note.id)
        assert "new-tag" not in updated_note.tags
        
        # Test deleting the note
        success = db.delete_note(created_note.id)
        assert success
        
        # Verify note is deleted
        deleted_note = db.get_note(created_note.id)
        assert deleted_note is None
        
    finally:
        # Clean up the temporary database file
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except PermissionError:
                # On Windows, file may be locked
                pass


if __name__ == "__main__":
    test_database_creation()
    print("All database tests passed!")
