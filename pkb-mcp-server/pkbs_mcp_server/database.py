import sqlite3
from typing import List, Optional
from .models import Note
import uuid
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id TEXT,
                    tag TEXT,
                    FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tags_note_id ON tags (note_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags (tag)
            ''')
            conn.commit()

    def create_note(self, note: Note) -> Note:
        """Create a new note in the database."""
        note_id = str(uuid.uuid4()) if note.id is None else note.id
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (note_id, note.title, note.content, note.created_at, note.updated_at)
            )
            
            # Insert tags
            for tag in note.tags:
                cursor.execute(
                    "INSERT INTO tags (note_id, tag) VALUES (?, ?)",
                    (note_id, tag)
                )
            
            conn.commit()
        
        # Return the created note with the ID set
        return Note(
            id=note_id,
            title=note.title,
            content=note.content,
            tags=note.tags,
            created_at=note.created_at,
            updated_at=note.updated_at
        )

    def get_note(self, note_id: str) -> Optional[Note]:
        """Get a note by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM notes WHERE id = ?",
                (note_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # Get associated tags
            cursor.execute(
                "SELECT tag FROM tags WHERE note_id = ?",
                (note_id,)
            )
            tags = [tag_row['tag'] for tag_row in cursor.fetchall()]
            
            return Note(
                id=row['id'],
                title=row['title'],
                content=row['content'],
                tags=tags,
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

    def update_note(self, note_id: str, note: Note) -> Optional[Note]:
        """Update an existing note."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update note content
            cursor.execute(
                '''UPDATE notes 
                   SET title = ?, content = ?, updated_at = ? 
                   WHERE id = ?''',
                (note.title, note.content, datetime.now(), note_id)
            )
            
            # Delete existing tags
            cursor.execute("DELETE FROM tags WHERE note_id = ?", (note_id,))
            
            # Insert new tags
            for tag in note.tags:
                cursor.execute(
                    "INSERT INTO tags (note_id, tag) VALUES (?, ?)",
                    (note_id, tag)
                )
            
            if cursor.rowcount == 0:
                return None
            
            conn.commit()
        
        return self.get_note(note_id)

    def delete_note(self, note_id: str) -> bool:
        """Delete a note by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def search_notes(self, query: str) -> List[Note]:
        """Search notes by title or content."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM notes 
                   WHERE title LIKE ? OR content LIKE ?''',
                (f'%{query}%', f'%{query}%')
            )
            rows = cursor.fetchall()
            
            notes = []
            for row in rows:
                # Get associated tags
                cursor.execute(
                    "SELECT tag FROM tags WHERE note_id = ?",
                    (row['id'],)
                )
                tags = [tag_row['tag'] for tag_row in cursor.fetchall()]
                
                note = Note(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    tags=tags,
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                notes.append(note)
            
            return notes

    def list_notes(self, tag_filter: Optional[str] = None) -> List[Note]:
        """List all notes, optionally filtered by tag."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if tag_filter:
                cursor.execute(
                    '''SELECT DISTINCT n.* FROM notes n
                       JOIN tags t ON n.id = t.note_id
                       WHERE t.tag = ?
                       ORDER BY n.created_at DESC''',
                    (tag_filter,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM notes ORDER BY created_at DESC"
                )
            
            rows = cursor.fetchall()
            
            notes = []
            for row in rows:
                # Get associated tags
                cursor.execute(
                    "SELECT tag FROM tags WHERE note_id = ?",
                    (row['id'],)
                )
                tags = [tag_row['tag'] for tag_row in cursor.fetchall()]
                
                note = Note(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    tags=tags,
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                notes.append(note)
            
            return notes

    def add_tag(self, note_id: str, tag: str) -> bool:
        """Add a tag to a note."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO tags (note_id, tag) VALUES (?, ?)",
                (note_id, tag)
            )
            conn.commit()
            return cursor.rowcount > 0

    def remove_tag(self, note_id: str, tag: str) -> bool:
        """Remove a tag from a note."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM tags WHERE note_id = ? AND tag = ?",
                (note_id, tag)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_all_tags(self) -> List[str]:
        """Get all unique tags from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT tag FROM tags ORDER BY tag")
            rows = cursor.fetchall()
            return [row[0] for row in rows]