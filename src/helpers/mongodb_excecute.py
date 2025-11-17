from src.connections import connect_mongo
from pymongo.errors import PyMongoError
from dotenv import dotenv_values
import json
from bson import ObjectId
from datetime import datetime
import traceback
import re

config = dotenv_values(".env")
host = config["MONGODBHOST"]
user = config["MONGODBUSER"]
password = config["MONGODBPASS"]
database = config["MONGODBDB"]
port = config["MONGODBPORT"]


def connection_mongo() -> object:
    client = connect_mongo(host, user, password, database, port or 27017)
    if isinstance(client, str):
        raise Exception(client)
    return client


def parse_objectid(value):
    if isinstance(value, str) and len(value) == 24:
        try:
            return ObjectId(value)
        except:
            return value
    return value


def convert_special_types(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            if key == "$oid" and isinstance(value, str):
                return ObjectId(value)
            
            if key == "$date" and isinstance(value, (str, int)):
                if isinstance(value, str):
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                return datetime.fromtimestamp(value / 1000)
            
            if isinstance(value, dict):
                new_dict[key] = convert_special_types(value)
            elif isinstance(value, list):
                new_dict[key] = [convert_special_types(item) for item in value]
            else:
                new_dict[key] = parse_objectid(value)
        
        return new_dict
    
    elif isinstance(obj, list):
        return [convert_special_types(item) for item in obj]
    
    return parse_objectid(obj)


def mongodb_run_query_json(query_dict: dict) -> str:
    client = connection_mongo()
    
    try:
        if "collection" not in query_dict:
            return "Error: Missing 'collection' field"
        
        if "operation" not in query_dict:
            return "Error: Missing 'operation' field"
        
        collection_name = query_dict["collection"]
        operation = query_dict["operation"]
        
        collection = client[database][collection_name]
        
        query_filter = convert_special_types(query_dict.get("filter", {}))
        options = query_dict.get("options", {})
        projection = query_dict.get("projection")
        
        result = None
        
        if operation == "find":
            cursor = collection.find(query_filter, projection)
            
            if "sort" in options:
                cursor = cursor.sort(list(options["sort"].items()))
            if "skip" in options:
                cursor = cursor.skip(options["skip"])
            if "limit" in options:
                cursor = cursor.limit(options["limit"])
            
            result = list(cursor)
        
        elif operation == "findOne":
            result = collection.find_one(query_filter, projection)
        
        elif operation == "countDocuments":
            result = collection.count_documents(query_filter)
        
        elif operation == "distinct":
            field = query_dict.get("field")
            if not field:
                return "Error: 'distinct' requires 'field' parameter"
            result = collection.distinct(field, query_filter)
        
        elif operation == "insertOne":
            document = convert_special_types(query_dict.get("document", {}))
            result = collection.insert_one(document)
        
        elif operation == "insertMany":
            documents = query_dict.get("documents", [])
            documents = convert_special_types(documents)
            result = collection.insert_many(documents)
        
        elif operation == "updateOne":
            update = convert_special_types(query_dict.get("update", {}))
            result = collection.update_one(query_filter, update)
        
        elif operation == "updateMany":
            update = convert_special_types(query_dict.get("update", {}))
            result = collection.update_many(query_filter, update)
        
        elif operation == "deleteOne":
            result = collection.delete_one(query_filter)
        
        elif operation == "deleteMany":
            result = collection.delete_many(query_filter)
        
        elif operation == "aggregate":
            pipeline = query_dict.get("pipeline", [])
            pipeline = convert_special_types(pipeline)
            result = list(collection.aggregate(pipeline))
        
        else:
            client.close()
            return f"Error: Unsupported operation '{operation}'"
        
        output = format_result(result)
        
        client.close()
        return output
        
    except PyMongoError as e:
        client.close()
        return f"MongoDB Error: {e}"
    except Exception as e:
        client.close()
        return f"Error: {e}\n\nTraceback:\n{traceback.format_exc()}"


def mongodb_run_query(query: str) -> str:
    client = connection_mongo()
    
    try:
        dangerous_patterns = [
            r'__import__',
            r'eval\(',
            r'exec\(',
            r'compile\(',
            r'open\(',
            r'__\w+__',
            r'os\.',
            r'sys\.',
            r'subprocess',
            r'requests\.',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                client.close()
                return f"Security Error: Query contains forbidden pattern '{pattern}'"
        
        if "." not in query:
            client.close()
            return "Error: Invalid format. Use: collection.operation(arguments)"
        
        parts = query.split(".", 1)
        collection_name = parts[0].strip()
        operation_part = parts[1].strip()
        
        if not re.match(r'^[a-zA-Z0-9_]+$', collection_name):
            client.close()
            return "Error: Invalid collection name. Use alphanumeric and underscore only."
        
        match = re.match(r'(\w+)\((.*)\)', operation_part, re.DOTALL)
        if not match:
            client.close()
            return f"Error: Could not parse operation: {operation_part}"
        
        method_name = match.group(1)
        args_str = match.group(2).strip()
        
        if not args_str or args_str == "":
            args_json = {}
        else:
            args_str_normalized = args_str.replace("'", '"')
            
            try:
                args_json = json.loads(args_str_normalized)
            except json.JSONDecodeError:
                try:
                    args_str_fixed = re.sub(r'(\w+)(?=\s*:)', r'"\1"', args_str_normalized)
                    args_json = json.loads(args_str_fixed)
                except:
                    client.close()
                    return f"Error: Invalid JSON in arguments. Use proper JSON format.\nReceived: {args_str}"
        
        query_dict = {
            "collection": collection_name,
            "operation": method_name
        }
        
        if method_name in ["find", "findOne", "countDocuments", "deleteOne", "deleteMany"]:
            query_dict["filter"] = args_json
        
        elif method_name == "distinct":
            if isinstance(args_json, str):
                query_dict["field"] = args_json
            elif isinstance(args_json, list) and len(args_json) > 0:
                query_dict["field"] = args_json[0]
                if len(args_json) > 1:
                    query_dict["filter"] = args_json[1]
        
        elif method_name == "insertOne":
            query_dict["document"] = args_json
        
        elif method_name == "insertMany":
            query_dict["documents"] = args_json if isinstance(args_json, list) else [args_json]
        
        elif method_name in ["updateOne", "updateMany"]:
            if isinstance(args_json, list) and len(args_json) >= 2:
                query_dict["filter"] = args_json[0]
                query_dict["update"] = args_json[1]
            else:
                client.close()
                return f"Error: {method_name} requires [filter, update] arguments"
        
        elif method_name == "aggregate":
            query_dict["pipeline"] = args_json if isinstance(args_json, list) else [args_json]
        
        else:
            client.close()
            return f"Error: Unsupported operation '{method_name}'"
        
        client.close()
        
        return mongodb_run_query_json(query_dict)
        
    except Exception as e:
        client.close()
        return f"Error: {e}\n\nTraceback:\n{traceback.format_exc()}"


def format_result(result) -> str:
    if result is None:
        return "Operation completed successfully. No return value."
    
    if hasattr(result, "inserted_id"):
        return f"Document inserted successfully.\nID: {result.inserted_id}"
    
    if hasattr(result, "inserted_ids"):
        ids = ", ".join(str(id) for id in result.inserted_ids[:5])
        if len(result.inserted_ids) > 5:
            ids += f"... ({len(result.inserted_ids)} total)"
        return f"{len(result.inserted_ids)} document(s) inserted.\nIDs: {ids}"
    
    if hasattr(result, "matched_count"):
        return f"Update successful.\nMatched: {result.matched_count}\nModified: {result.modified_count}"
    
    if hasattr(result, "deleted_count"):
        return f"Delete successful.\n{result.deleted_count} document(s) deleted"
    
    if isinstance(result, (int, float)):
        return f"Result: {result}"
    
    if isinstance(result, dict):
        return json.dumps(result, default=str, indent=2, ensure_ascii=False)
    
    if isinstance(result, list):
        if not result:
            return "Query executed successfully.\nNo results returned."
        return json.dumps(result, default=str, indent=2, ensure_ascii=False)
    
    return f"Result: {str(result)}"


def mongodb_list_tables(database_name: str = None) -> str:
    client = connection_mongo()
    try:
        db_name = database_name or database
        db = client[db_name]
        collection_names = db.list_collection_names()
        client.close()
        
        if not collection_names:
            return f"No collections found in database '{db_name}'."
        
        output = f"MongoDB Collections in '{db_name}':\n\n"
        output += "\n".join(f"  • {name}" for name in sorted(collection_names))
        return output
    except Exception as e:
        client.close()
        return f"Error: {e}"


def mongodb_list_databases() -> str:
    client = connection_mongo()
    try:
        db_names = client.list_database_names()
        client.close()
        
        if not db_names:
            return "No databases found."
        
        output = "MongoDB Databases:\n\n"
        output += "\n".join(f"  • {name}" for name in sorted(db_names))
        return output
    except Exception as e:
        client.close()
        return f"Error: {e}"


def mongodb_describe_tables(collection_name: str) -> str:
    client = connection_mongo()
    try:
        collection = client[database][collection_name]
        
        stats = client[database].command("collStats", collection_name)
        sample = collection.find_one()
        
        if not sample:
            client.close()
            return f"Collection '{collection_name}' is empty."
        
        output = f"Collection: {collection_name}\n\n"
        output += f"Documents: {stats.get('count', 0):,}\n"
        output += f"Size: {stats.get('size', 0):,} bytes\n"
        output += f"Avg Size: {stats.get('avgObjSize', 0):,} bytes\n\n"
        output += "Sample Structure:\n\n"
        
        def describe(obj, indent=0):
            result = ""
            prefix = "  " * indent
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    vtype = type(value).__name__
                    
                    if isinstance(value, dict):
                        result += f"{prefix}{key}: {{\n"
                        result += describe(value, indent + 1)
                        result += f"{prefix}}}\n"
                    elif isinstance(value, list):
                        if value and isinstance(value[0], dict):
                            result += f"{prefix}{key}: [ (array, {len(value)} items)\n"
                            result += describe(value[0], indent + 1)
                            result += f"{prefix}]\n"
                        else:
                            result += f"{prefix}{key}: array ({vtype}, {len(value)} items)\n"
                    else:
                        sample = str(value)[:40] + "..." if len(str(value)) > 40 else str(value)
                        result += f"{prefix}{key}: {vtype} = {sample}\n"
            
            return result
        
        output += describe(sample)
        
        client.close()
        return output
        
    except Exception as e:
        client.close()
        return f"Error: {e}"
