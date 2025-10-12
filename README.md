# PKB MCP Server

An MCP server for managing a personal knowledge base.

## Description

This project provides a server that implements the Model Context Protocol (MCP) to interact with a personal knowledge base (PKB). It allows users to store, retrieve, and manage their personal information through a standardized protocol. The server supports creating, updating, deleting, and searching notes, as well as managing tags.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/pkb-mcp-server.git
    cd pkb-mcp-server
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To start the server, run the following command:

```bash
pkb-mcp-server
```

The server will start and listen for incoming MCP requests.

## Features

### Tools

The server exposes the following tools:

*   `create_note`: Creates a new note.
*   `get_note`: Retrieves a note by its ID.
*   `update_note`: Updates an existing note.
*   `delete_note`: Deletes a note.
*   `search_notes`: Searches for notes based on a query.
*   `list_notes`: Lists all notes, with an option to filter by tag.
*   `add_tag`: Adds a tag to a note.
*   `remove_tag`: Removes a tag from a note.

### Prompts

The server provides the following prompts:

*   `summarize_notes_about`: Summarizes notes about a specific topic.
*   `find_notes_by_tag`: Finds notes by a specific tag.
*   `search_notes`: Searches notes for specific information.

## Dependencies

*   [mcp](https://pypi.org/project/mcp/): The official Model Context Protocol SDK.
*   [pydantic](https://pypi.org/project/pydantic/): Data validation and settings management.
*   [pytest](https://pypi.org/project/pytest/): Testing framework.

## License

This project is licensed under the MIT License.