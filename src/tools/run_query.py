from fastmcp import FastMCP
from src.helpers.mysql_excecute import mysql_execute_query
from src.helpers.postgresql_execute import postgresql_execute_query
from src.helpers.mongodb_excecute import mongodb_run_query

run_query_mcp = FastMCP()


@run_query_mcp.tool()
def run_query(
    engine: str,
    query: str,
):
    """
    Execute SQL queries (MySQL/PostgreSQL) or MongoDB operations.

    Parameters:
    -----------
    engine : str
      Database engine type. Valid values: "mysql", "postgres", "mongo"

    query : str
      Query or operation to execute. Format depends on engine:

      MySQL/PostgreSQL:
        Standard SQL queries as strings
        Examples:
          "SELECT * FROM users WHERE status = 'active'"
          "SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01'"
          "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
          "UPDATE users SET status = 'inactive' WHERE last_login < '2024-01-01'"
          "DELETE FROM logs WHERE created_at < '2023-01-01'"

      MongoDB:
        Format: "collection.operation(arguments)"

        Supported Operations:

        1. FIND OPERATIONS:
           - find(): Find all documents
           Examples:
             "users.find()"
             "users.find({})"
             "users.find({\"status\": \"active\"})"
             "users.find({\"age\": {\"$gte\": 18}})"

           - find() with chaining:
           Examples:
             "users.find().limit(10)"
             "users.find().sort({\"created_at\": -1})"
             "users.find().skip(10).limit(5)"
             "users.find({\"country\": \"ID\"}).sort({\"name\": 1}).limit(20)"

           - findOne(): Find single document
           Examples:
             "users.findOne()"
             "users.findOne({\"_id\": \"123\"})"
             "users.findOne({\"email\": \"john@example.com\"})"

        2. COUNT OPERATIONS:
           - countDocuments(): Count documents matching filter
           Examples:
             "users.countDocuments()"
             "users.countDocuments({\"status\": \"active\"})"
             "orders.countDocuments({\"total\": {\"$gt\": 1000}})"

        3. AGGREGATE OPERATIONS:
           - aggregate(): Run aggregation pipeline
           Examples:
             "users.aggregate([{\"$match\": {\"status\": \"active\"}}, {\"$count\": \"total\"}])"
             "orders.aggregate([{\"$group\": {\"_id\": \"$customer_id\", \"total\": {\"$sum\": \"$amount\"}}}])"
             "users.aggregate([{\"$sort\": {\"created_at\": -1}}, {\"$limit\": 10}])"

        4. INSERT OPERATIONS:
           - insertOne(): Insert single document
           Examples:
             "users.insertOne({\"name\": \"John\", \"email\": \"john@test.com\", \"status\": \"active\"})"

           - insertMany(): Insert multiple documents
           Examples:
             "users.insertMany([{\"name\": \"Alice\"}, {\"name\": \"Bob\"}])"

        5. UPDATE OPERATIONS:
           - updateOne(): Update single document
           Examples:
             "users.updateOne({\"_id\": \"123\"}, {\"$set\": {\"status\": \"inactive\"}})"
             "users.updateOne({\"email\": \"john@test.com\"}, {\"$inc\": {\"login_count\": 1}})"

           - updateMany(): Update multiple documents
           Examples:
             "users.updateMany({\"status\": \"old\"}, {\"$set\": {\"status\": \"archived\"}})"
             "products.updateMany({\"price\": {\"$lt\": 10}}, {\"$set\": {\"discount\": 0.1}})"

        6. DELETE OPERATIONS:
           - deleteOne(): Delete single document
           Examples:
             "users.deleteOne({\"_id\": \"123\"})"

           - deleteMany(): Delete multiple documents
           Examples:
             "logs.deleteMany({\"created_at\": {\"$lt\": \"2023-01-01\"}})"
             "users.deleteMany({\"status\": \"inactive\", \"last_login\": {\"$lt\": \"2023-01-01\"}})"

        7. DISTINCT OPERATION:
           - distinct(): Get unique values
           Examples:
             "users.distinct(\"country\")"
             "orders.distinct(\"status\", {\"created_at\": {\"$gte\": \"2024-01-01\"}})"

        MongoDB Query Operators:
          Comparison: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
          Logical: $and, $or, $not, $nor
          Element: $exists, $type
          Array: $all, $elemMatch, $size
          Update: $set, $unset, $inc, $mul, $rename, $push, $pull

        MongoDB Sort:
          1 = ascending, -1 = descending
          Example: {\"created_at\": -1, \"name\": 1}

    Returns:
    --------
    str
      Query results formatted as:
      - MySQL/PostgreSQL SELECT: Table format with headers and rows
      - MySQL/PostgreSQL INSERT/UPDATE/DELETE: Success message with affected row count
      - MongoDB find/aggregate: JSON array of documents
      - MongoDB insert: Success message with inserted ID(s)
      - MongoDB update: Success message with matched/modified counts
      - MongoDB delete: Success message with deleted count
      - MongoDB count: Total count number
      - Errors: Detailed error message

    Example Usage:
    --------------
    MySQL:
      run_query("mysql", "SELECT * FROM users LIMIT 10", "myapp_db", "localhost", "root", "pass")
      run_query("mysql", "SELECT COUNT(*) as total FROM orders WHERE status = 'completed'", "myapp_db", "localhost", "root", "pass")
      run_query("mysql", "UPDATE users SET last_login = NOW() WHERE id = 123", "myapp_db", "localhost", "root", "pass")

    PostgreSQL:
      run_query("postgres", "SELECT * FROM products WHERE price > 100 ORDER BY created_at DESC", "shop_db", "10.0.0.1", "postgres", "pass")
      run_query("postgres", "INSERT INTO logs (message, level) VALUES ('Test', 'INFO')", "app_db", "10.0.0.1", "postgres", "pass")

    MongoDB - Simple Queries:
      run_query("mongo", "users.find()", "database", "127.0.0.1", "user", "pass", 27017)
      run_query("mongo", "users.findOne({\"email\": \"test@example.com\"})", "database", "127.0.0.1", "user", "pass", 27017)
      run_query("mongo", "customers.countDocuments({\"status\": \"active\"})", "database", "127.0.0.1", "user", "pass", 27017)

    MongoDB - Find with Chaining:
      run_query("mongo", "users.find().sort({\"created_at\": -1}).limit(10)", "database", "127.0.0.1", "user", "pass", 27017)
      run_query("mongo", "orders.find({\"status\": \"pending\"}).sort({\"total\": -1}).limit(5)", "database", "127.0.0.1", "user", "pass", 27017)

    MongoDB - Aggregation:
      run_query("mongo", "users.aggregate([{\"$match\": {\"status\": \"active\"}}, {\"$group\": {\"_id\": \"$country\", \"count\": {\"$sum\": 1}}}])", "database", "127.0.0.1", "user", "pass", 27017)
      run_query("mongo", "orders.aggregate([{\"$match\": {\"created_at\": {\"$gte\": \"2024-01-01\"}}}, {\"$group\": {\"_id\": null, \"total\": {\"$sum\": \"$amount\"}}}])", "database", "127.0.0.1", "user", "pass", 27017)

    MongoDB - Insert/Update/Delete:
      run_query("mongo", "users.insertOne({\"name\": \"John Doe\", \"email\": \"john@test.com\", \"status\": \"active\"})", "database", "127.0.0.1", "user", "pass", 27017)
      run_query("mongo", "users.updateMany({\"last_login\": null}, {\"$set\": {\"status\": \"inactive\"}})", "database", "127.0.0.1", "user", "pass", 27017)
      run_query("mongo", "logs.deleteMany({\"created_at\": {\"$lt\": \"2023-01-01\"}})", "database", "127.0.0.1", "user", "pass", 27017)

    MongoDB - Authentication with Different Database:
      run_query("mongo", "users.find()", "database", "127.0.0.1", "admin_user", "pass", 27017, "admin")

    Notes:
    ------
    - For MongoDB, ensure JSON is properly formatted with double quotes
    - MongoDB operations are case-sensitive
    - Use appropriate indexes for better query performance
    - For large result sets in MongoDB, consider using limit() or aggregation with $limit
    - Require user confirmation before executing update, delete, or create operations. Ensure the user understands the action being performed. If the user grants permission, automatically proceed but verify first
    - Always test UPDATE/DELETE queries with SELECT first to verify affected records
    """
    print(f"Running query on {engine} database.")
    print(f"Query: {query}")
    match engine:
        case "mysql":
            return mysql_execute_query(query)
        case "postgres":
            return postgresql_execute_query(query)
        case "mongo":
            return mongodb_run_query(query)
        case _:
            return f"Error: Unsupported database engine '{engine}'. Supported engines are: mysql, postgres, mongo."
