# MCP Database Query

A powerful Model Context Protocol (MCP) server that provides universal database query and introspection tools. This server supports multiple databases including MySQL, PostgreSQL, and MongoDB, enabling seamless database operations through a unified interface.

## Features

- 🔌 **Multi-Database Support**: Works with MySQL, PostgreSQL, and MongoDB
- 🔍 **Table Introspection**: Get detailed information about table structures and schemas
- 📊 **Database Inspection**: List all databases and tables within a database
- ⚡ **Query Execution**: Execute SQL queries and MongoDB operations
- 🔐 **Secure Connections**: Support for authenticated database connections
- 📦 **FastMCP Integration**: Built on FastMCP for reliable MCP server implementation

## Supported Databases

- **MySQL**: Via `mysql-connector-python`
- **PostgreSQL**: Via `psycopg2-binary`
- **MongoDB**: Via `pymongo`

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Access credentials for your target databases

### Setup

1. **Clone the repository**

```bash
git clone [<repository-url>](https://github.com/linlaz/mcp-database-query.git)
cd mcp-database-query
```

2. **Install dependencies with uv**

```bash
uv sync
```

The `uv` package manager will automatically handle virtual environment creation and dependency installation based on `pyproject.toml`.

3. **Run commands with uv**

Use `uv run` to execute Python scripts:

```bash
uv run python main.py
```

Or activate the virtual environment created by uv:

```bash
source .venv/bin/activate
# or
.venv\Scripts\activate 
```

## Configuration

Create a `.env` file in the project root directory:

```env
APP_NAME=mcp-database-query
APP_PORT=5000
```

You can configure database connections in your client application that uses this MCP server.

## Usage

### Starting the Server

Using `uv run`:

```bash
uv run python main.py
```

Or if you activated the virtual environment:

```bash
python main.py
```

The server will start on the port specified in your `.env` file (default: 5000) using HTTP transport.

### Available Tools

#### 1. **List Databases**
Lists all available databases on the connected database server.

**Parameters:**
- `engine`: Database type (`"mysql"`, `"postgres"`, or `"mongo"`)

**Example:**
```
List all databases on MySQL server
```

#### 2. **List Tables**
Lists all tables/collections in a specific database.

**Parameters:**
- `engine`: Database type
- `databaseOrSchemaName` (optional): Specific database/schema name

**Example:**
```
Show all tables in the "users_db" database
```

#### 3. **Describe Table**
Retrieves the schema and structure information of a specific table or MongoDB collection.

**Parameters:**
- `engine`: Database type
- `table`: Table or collection name

**Returns:**
- Column names and data types
- Constraints and indexes
- Default values
- Nullable status

**Example:**
```
Get the structure of the "users" table
```

#### 4. **Run Query**
Executes SQL queries (MySQL/PostgreSQL) or MongoDB operations.

**Parameters:**
- `engine`: Database type
- `query`: SQL query or MongoDB operation
- Additional connection parameters as needed

**Supported Operations:**

**SQL (MySQL/PostgreSQL):**
- SELECT statements
- INSERT statements
- UPDATE statements
- DELETE statements

**MongoDB:**
- find(), findOne()
- countDocuments()
- aggregate()
- insertOne(), insertMany()
- updateOne(), updateMany()
- deleteOne(), deleteMany()
- distinct()

**Example SQL Query:**
```sql
SELECT * FROM users WHERE status = 'active' LIMIT 10
```

**Example MongoDB Query:**
```
users.find({"status": "active"}).limit(10)
```

## Project Structure

```
mcp-database-query/
├── main.py                 # Entry point for the MCP server
├── pyproject.toml         # Project configuration and dependencies
├── README.md              # This file
├── .env                   # Configuration file (create this)
└── src/
    ├── connections/       # Database connection handlers
    │   ├── mongodb.py
    │   ├── mysql.py
    │   └── postgresql.py
    ├── helpers/          # Query execution helpers
    │   ├── mongodb_execute.py
    │   ├── mysql_execute.py
    │   └── postgresql_execute.py
    └── tools/            # MCP tool implementations
        ├── describe_table.py
        ├── list_databases.py
        ├── list_tables.py
        └── run_query.py
```

## Architecture

This project implements the Model Context Protocol (MCP) specification, enabling AI assistants and other applications to safely interact with databases. The architecture follows a modular design:

- **Connection Layer**: Handles database-specific connection logic
- **Execution Layer**: Executes queries and returns formatted results
- **Tools Layer**: Exposes database operations as MCP tools
- **Server Layer**: FastMCP server manages all tools and client communication

## Error Handling

The server includes comprehensive error handling for:
- Connection failures
- Invalid queries
- Authentication errors
- Database-specific errors

## Security Considerations

- **Credentials**: Store sensitive credentials in `.env` files, never commit them to version control
- **Query Validation**: Always validate and sanitize user inputs before execution
- **Least Privilege**: Use database accounts with minimal required permissions
- **Network Security**: Restrict server access to trusted networks when deployed

## Dependencies

- **fastmcp**: Framework for Model Context Protocol servers
- **mysql-connector-python**: MySQL database driver
- **psycopg2-binary**: PostgreSQL database driver
- **pymongo**: MongoDB database driver
- **python-dotenv**: Environment variable management
