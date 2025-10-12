#!/usr/bin/env python3
"""
Personal Knowledge Base MCP Server
An MCP server that manages a local knowledge base with notes, tags, and search capabilities.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict

from mcp.server import Server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsResult,
    ListResourcesRequest,
    ListResourcesResult,
    Prompt,
    PromptMessage,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    TextContent,
)
from .models import Note
from .database import DatabaseManager
from .config import ServerConfig


class PKBMCPServer:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.db = DatabaseManager(config.database_path)
        self._server = Server("pkb-mcp-server", version="1.0.0")
        
        # Define and register the handlers with the server
        self._register_handlers()

    def _register_handlers(self):
        """Register handlers with the MCP server."""
        @self._server.list_resources()
        async def handle_list_resources(request: ListResourcesRequest) -> ListResourcesResult:
            return await self.handle_list_resources(request)

        @self._server.read_resource()
        async def handle_read_resource(request: ReadResourceRequest) -> ReadResourceResult:
            return await self.handle_read_resource(request)

        @self._server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            return await self.handle_call_tool(request)

        @self._server.list_prompts()
        async def handle_list_prompts(request) -> ListPromptsResult:
            return await self.handle_get_prompts(request)

        @self._server.get_prompt()
        async def handle_get_prompt(request) -> GetPromptResult:
            return await self.handle_get_prompt_by_name(request)

    @property
    def server(self):
        return self._server

    async def handle_list_resources(self, request: ListResourcesRequest) -> ListResourcesResult:
        """Handle listing available resources."""
        notes = self.db.list_notes()
        resources = []
        
        for note in notes:
            resources.append(Resource(
                uri=f"note://{note.id}",
                name=note.title,
                description=f"Note: {note.title}"
            ))
        
        return ListResourcesResult(resources=resources)

    async def handle_read_resource(self, request: ReadResourceRequest) -> ReadResourceResult:
        """Handle reading a specific resource."""
        if not request.uri.startswith("note://"):
            raise ValueError(f"Invalid note URI: {request.uri}")
        
        note_id = request.uri[7:]  # Remove "note://" prefix
        note = self.db.get_note(note_id)
        
        if not note:
            raise ValueError(f"Note not found: {note_id}")
        
        return ReadResourceResult(contents=json.dumps(note.model_dump(), default=str))

    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool calls."""
        tool_name = request.params.name
        arguments = request.params.arguments or {}
        
        try:
            if tool_name == "create_note":
                return await self.create_note_tool(arguments)
            elif tool_name == "get_note":
                return await self.get_note_tool(arguments)
            elif tool_name == "update_note":
                return await self.update_note_tool(arguments)
            elif tool_name == "delete_note":
                return await self.delete_note_tool(arguments)
            elif tool_name == "search_notes":
                return await self.search_notes_tool(arguments)
            elif tool_name == "list_notes":
                return await self.list_notes_tool(arguments)
            elif tool_name == "add_tag":
                return await self.add_tag_tool(arguments)
            elif tool_name == "remove_tag":
                return await self.remove_tag_tool(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            logging.exception(f"Error in tool {tool_name}")
            return CallToolResult(isError=True, content=[{"type": "text", "text": f"Error: {str(e)}"}])

    async def create_note_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Tool to create a new note."""
        title = arguments.get("title", "")
        content = arguments.get("content", "")
        tags = arguments.get("tags", [])
        
        if not title:
            return CallToolResult(isError=True, content=[{"type": "text", "text": "Title is required"}])
        
        note = Note(title=title, content=content, tags=tags)
        created_note = self.db.create_note(note)
        
        return CallToolResult(content=[{
            "type": "text", 
            "text": f"Created note with ID: {created_note.id}"
        }])

    async def get_note_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Tool to get a note by ID."""
        note_id = arguments.get("note_id")
        
        if not note_id:
            return CallToolResult(isError=True, content=[{"type": "text", "text": "Note ID is required"}])
        
        note = self.db.get_note(note_id)
        
        if not note:
            return CallToolResult(isError=True, content=[{"type": "text", "text": f"Note not found: {note_id}"}])
        
        return CallToolResult(content=[{
            "type": "text", 
            "text": json.dumps(note.model_dump(), default=str)
        }])

    async def update_note_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Tool to update a note."""
        note_id = arguments.get("note_id")
        title = arguments.get("title")
        content = arguments.get("content")
        tags = arguments.get("tags")
        
        if not note_id:
            return CallToolResult(isError=True, content=[{"type": "text", "text": "Note ID is required"}])
        
        existing_note = self.db.get_note(note_id)
        if not existing_note:
            return CallToolResult(isError=True, content=[{"type": "text", "text": f"Note not found: {note_id}"}])
        
        updated_note = Note(
            id=existing_note.id,
            title=title if title is not None else existing_note.title,
            content=content if content is not None else existing_note.content,
            tags=tags if tags is not None else existing_note.tags,
            created_at=existing_note.created_at,
            updated_at=existing_note.updated_at
        )
        
        updated_note = self.db.update_note(note_id, updated_note)
        
        return CallToolResult(content=[{
            "type": "text", 
            "text": f"Updated note with ID: {updated_note.id}"
        }])

    async def delete_note_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Tool to delete a note."""
        note_id = arguments.get("note_id")
        
        if not note_id:
            return CallToolResult(isError=True, content=[{"type": "text", "text": "Note ID is required"}])
        
        success = self.db.delete_note(note_id)
        
        if success:
            return CallToolResult(content=[{
                "type": "text", 
                "text": f"Deleted note with ID: {note_id}"
            }])
        else:
            return CallToolResult(isError=True, content=[{"type": "text", "text": f"Note not found: {note_id}"}])

    async def search_notes_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Tool to search notes."""
        query = arguments.get("query", "")
        
        if not query:
            return CallToolResult(isError=True, content=[{"type": "text", "text": "Query is required"}])
        
        notes = self.db.search_notes(query)
        
        results = []
        for note in notes:
            results.append({
                "id": note.id,
                "title": note.title,
                "content": note.content[:200] + "..." if len(note.content) > 200 else note.content,
                "tags": note.tags
            })
        
        return CallToolResult(content=[{
            "type": "text", 
            "text": json.dumps(results, default=str)
        }])

    async def list_notes_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Tool to list notes."""
        tag_filter = arguments.get("tag_filter")
        
        notes = self.db.list_notes(tag_filter)
        
        results = []
        for note in notes:
            results.append({
                "id": note.id,
                "title": note.title,
                "tags": note.tags
            })
        
        return CallToolResult(content=[{
            "type": "text", 
            "text": json.dumps(results, default=str)
        }])

    async def add_tag_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Tool to add a tag to a note."""
        note_id = arguments.get("note_id")
        tag = arguments.get("tag")
        
        if not note_id or not tag:
            return CallToolResult(isError=True, content=[{"type": "text", "text": "Note ID and tag are required"}])
        
        success = self.db.add_tag(note_id, tag)
        
        if success:
            return CallToolResult(content=[{
                "type": "text", 
                "text": f"Added tag '{tag}' to note with ID: {note_id}"
            }])
        else:
            return CallToolResult(isError=True, content=[{"type": "text", "text": f"Failed to add tag to note: {note_id}"}])

    async def remove_tag_tool(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Tool to remove a tag from a note."""
        note_id = arguments.get("note_id")
        tag = arguments.get("tag")
        
        if not note_id or not tag:
            return CallToolResult(isError=True, content=[{"type": "text", "text": "Note ID and tag are required"}])
        
        success = self.db.remove_tag(note_id, tag)
        
        if success:
            return CallToolResult(content=[{
                "type": "text", 
                "text": f"Removed tag '{tag}' from note with ID: {note_id}"
            }])
        else:
            return CallToolResult(isError=True, content=[{"type": "text", "text": f"Failed to remove tag from note: {note_id}"}])

    async def handle_get_prompts(self, request) -> ListPromptsResult:
        """Handle getting available prompts."""
        return ListPromptsResult(prompts=[
            Prompt(
                name="summarize_notes_about",
                description="Summarize notes about a specific topic",
                arguments={
                    "topic": {
                        "type": "string",
                        "description": "The topic to summarize notes about"
                    }
                }
            ),
            Prompt(
                name="find_notes_by_tag",
                description="Find notes by a specific tag",
                arguments={
                    "tag": {
                        "type": "string",
                        "description": "The tag to search for"
                    }
                }
            ),
            Prompt(
                name="search_notes",
                description="Search notes for specific information",
                arguments={
                    "query": {
                        "type": "string",
                        "description": "The query to search for"
                    }
                }
            )
        ])

    async def handle_get_prompt_by_name(self, request: GetPromptRequest) -> GetPromptResult:
        """Handle getting a specific prompt by name with filled-in arguments."""
        prompt_name = request.params.name
        arguments = request.params.arguments or {}
        
        if prompt_name == "summarize_notes_about":
            topic = arguments.get("topic", "general")
            notes = self.db.search_notes(topic)
            content = f"Here are the notes about {topic}:\n\n"
            for note in notes:
                content += f"Title: {note.title}\nContent: {note.content}\nTags: {', '.join(note.tags)}\n\n"
            content += f"\nPlease summarize the key points from these notes about {topic}."
            
            return GetPromptResult(
                messages=[PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=content)
                )]
            )
        
        elif prompt_name == "find_notes_by_tag":
            tag = arguments.get("tag", "")
            notes = self.db.list_notes(tag_filter=tag)
            content = f"Notes tagged with '{tag}':\n\n"
            for note in notes:
                content += f"- {note.title} (ID: {note.id})\n"
            
            if not notes:
                content = f"No notes found with the tag '{tag}'."
            
            content += f"\nHere's information from notes tagged with {tag}."
            
            return GetPromptResult(
                messages=[PromptMessage(
                    role="user", 
                    content=TextContent(type="text", text=content)
                )]
            )
        
        elif prompt_name == "search_notes":
            query = arguments.get("query", "")
            notes = self.db.search_notes(query)
            content = f"Notes containing '{query}':\n\n"
            for note in notes:
                content += f"Title: {note.title}\nContent: {note.content[:200]}...\nTags: {', '.join(note.tags)}\n\n"
            
            if not notes:
                content = f"No notes found containing '{query}'."
            
            content += f"\nPlease provide information based on these notes about {query}."
            
            return GetPromptResult(
                messages=[PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=content)
                )]
            )
        
        else:
            raise ValueError(f"Unknown prompt: {prompt_name}")

    async def run(self):
        """Run the MCP server with proper streams."""
        from mcp.server import InitializationOptions
        from mcp import stdio_server, types

        try:
            init_options = InitializationOptions(
                server_name="pkb-mcp-server",
                server_version="1.0.0",
                capabilities=types.ServerCapabilities(
                    prompts=types.PromptsCapability(),
                    resources=types.ResourcesCapability(),
                    tools=types.ToolsCapability(),
                )
            )
            async with stdio_server() as (reader, writer):
                await self.server.run(reader, writer, init_options)
        except Exception as e:
            logging.exception("Error in stdio_server")
            raise


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Load configuration
    if len(sys.argv) > 1:
        config = ServerConfig.from_file(sys.argv[1])
    else:
        config = ServerConfig.from_file()
    
    server = PKBMCPServer(config)
    
    logging.info(f"Starting PKB MCP Server with database: {config.database_path}")
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
