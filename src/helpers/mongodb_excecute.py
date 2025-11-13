from src.connections import connect_mongo
from pymongo.errors import PyMongoError
from dotenv import dotenv_values
import re
import json
from bson import ObjectId
import traceback

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


def convert_objectids(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            if (
                isinstance(value, str)
                and len(value) == 24
                and all(c in "0123456789abcdefABCDEF" for c in value)
            ):
                try:
                    new_dict[key] = ObjectId(value)
                except:
                    new_dict[key] = value
            elif isinstance(value, dict):
                new_dict[key] = convert_objectids(value)
            elif isinstance(value, list):
                new_dict[key] = [
                    convert_objectids(item) if isinstance(item, (dict, list)) else item
                    for item in value
                ]
            else:
                new_dict[key] = value
        return new_dict
    elif isinstance(obj, list):
        return [
            convert_objectids(item) if isinstance(item, (dict, list)) else item
            for item in obj
        ]
    return obj


def flatten_dict(d, parent_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, ("array", v)))
        else:
            items.append((new_key, (type(v).__name__, v)))
        return dict(items)


def mongodb_run_query(query: str) -> str:
    client = connection_mongo()

    try:
        if "." not in query:
            client.close()
            return "Error: Invalid MongoDB query format. Use: collection.operation(arguments)\nExample: users.find({})"

        parts = query.split(".", 1)
        collection_name = parts[0].strip()
        operation_part = parts[1].strip()
        collection = client[collection_name]

        operations = []
        current_pos = 0

        while current_pos < len(operation_part):
            match = re.match(r"(\w+)\((.*?)\)", operation_part[current_pos:], re.DOTALL)
            if not match:
                match = re.match(r"(\w+)\(", operation_part[current_pos:])
                if match:
                    method_name = match.group(1)
                    open_count = 1
                    start = current_pos + match.end()
                    end = start
                    while end < len(operation_part) and open_count > 0:
                        if operation_part[end] == "(":
                            open_count += 1
                        elif operation_part[end] == ")":
                            open_count -= 1
                        end += 1
                    args_str = operation_part[start : end - 1]
                    operations.append((method_name, args_str))
                    current_pos = end
                    if (
                        current_pos < len(operation_part)
                        and operation_part[current_pos] == "."
                    ):
                        current_pos += 1
                else:
                    break
            else:
                method_name = match.group(1)
                args_str = match.group(2)
                operations.append((method_name, args_str))
                current_pos += match.end()
                if (
                    current_pos < len(operation_part)
                    and operation_part[current_pos] == "."
                ):
                    current_pos += 1

        if not operations:
            client.close()
            return f"Error: Could not parse operation: {operation_part}"

        result = None
        cursor = None

        for idx, (method_name, args_str) in enumerate(operations):
            args_str = args_str.strip()

            if not args_str or args_str == "":
                args = {}
                args_list = []
            else:
                try:
                    parsed = json.loads(args_str)
                    parsed = convert_objectids(parsed)

                    if isinstance(parsed, dict):
                        args = parsed
                        args_list = [parsed]
                    elif isinstance(parsed, list):
                        args_list = parsed
                        args = parsed[0] if parsed else {}
                    else:
                        args = {}
                        args_list = [parsed]
                except json.JSONDecodeError:
                    try:
                        args_parts = []
                        bracket_count = 0
                        current_arg = ""
                        for char in args_str:
                            if char in ["{", "["]:
                                bracket_count += 1
                            elif char in ["}", "]"]:
                                bracket_count -= 1
                            elif char == "," and bracket_count == 0:
                                args_parts.append(current_arg.strip())
                                current_arg = ""
                                continue
                            current_arg += char
                        if current_arg.strip():
                            args_parts.append(current_arg.strip())

                        args_list = []
                        for part in args_parts:
                            try:
                                parsed_part = json.loads(part)
                                parsed_part = convert_objectids(parsed_part)
                                args_list.append(parsed_part)
                            except:
                                if part.isdigit():
                                    args_list.append(int(part))
                                else:
                                    args_list.append(part)

                        args = args_list[0] if args_list else {}
                    except:
                        args = {}
                        args_list = []

            if idx == 0:
                if method_name == "find":
                    cursor = collection.find(args)
                    result = cursor
                elif method_name == "findOne":
                    result = collection.find_one(args)
                elif method_name == "countDocuments":
                    result = collection.count_documents(args)
                elif method_name == "aggregate":
                    pipeline = (
                        args_list
                        if isinstance(args_list, list)
                        and all(isinstance(x, dict) for x in args_list)
                        else (args_list if args_list else [])
                    )
                    if isinstance(args, list):
                        pipeline = args
                    cursor = collection.aggregate(pipeline)
                    result = cursor
                elif method_name == "insertOne":
                    result = collection.insert_one(args)
                elif method_name == "insertMany":
                    docs = args_list if isinstance(args_list, list) else [args]
                    result = collection.insert_many(docs)
                elif method_name == "updateOne":
                    filter_doc = args_list[0] if len(args_list) >= 1 else {}
                    update_doc = args_list[1] if len(args_list) >= 2 else {}
                    result = collection.update_one(filter_doc, update_doc)
                elif method_name == "updateMany":
                    filter_doc = args_list[0] if len(args_list) >= 1 else {}
                    update_doc = args_list[1] if len(args_list) >= 2 else {}
                    result = collection.update_many(filter_doc, update_doc)
                elif method_name == "deleteOne":
                    result = collection.delete_one(args)
                elif method_name == "deleteMany":
                    result = collection.delete_many(args)
                elif method_name == "distinct":
                    field = args_list[0] if args_list else args
                    query_filter = args_list[1] if len(args_list) > 1 else {}
                    result = collection.distinct(field, query_filter)
                else:
                    client.close()
                    return f"Error: Unknown or unsupported method '{method_name}'"
            else:
                if cursor is None and result is None:
                    client.close()
                    return f"Error: Cannot chain method '{method_name}' on previous operation"

                if method_name == "limit":
                    limit_val = (
                        int(args_list[0])
                        if args_list
                        else (int(args) if str(args).isdigit() else 10)
                    )
                    if cursor:
                        cursor = cursor.limit(limit_val)
                        result = cursor
                elif method_name == "skip":
                    skip_val = (
                        int(args_list[0])
                        if args_list
                        else (int(args) if str(args).isdigit() else 0)
                    )
                    if cursor:
                        cursor = cursor.skip(skip_val)
                        result = cursor
                elif method_name == "sort":
                    if cursor:
                        if isinstance(args, dict):
                            cursor = cursor.sort(list(args.items()))
                        elif args_list:
                            cursor = cursor.sort(args_list)
                        result = cursor
                elif method_name == "count":
                    if cursor:
                        result = len(list(cursor))

        if result is None:
            client.close()
            return "Error: Operation did not produce any output"

        if hasattr(result, "inserted_id"):
            output = f"Document inserted successfully. ID: {result.inserted_id}"
        elif hasattr(result, "inserted_ids"):
            output = f"{len(result.inserted_ids)} documents inserted successfully"
        elif hasattr(result, "matched_count"):
            output = f"Update successful. Matched: {result.matched_count}, Modified: {result.modified_count}"
        elif hasattr(result, "deleted_count"):
            output = f"Delete successful. {result.deleted_count} document(s) deleted"
        elif isinstance(result, (int, float)):
            output = f"Result: {result}"
        elif isinstance(result, dict):
            output = json.dumps(result, default=str, indent=2, ensure_ascii=False)
        elif isinstance(result, list):
            if not result:
                output = "Query executed successfully. No results returned."
            else:
                output = json.dumps(result, default=str, indent=2, ensure_ascii=False)
        elif hasattr(result, "__iter__") and not isinstance(result, str):
            data = list(result)
            if not data:
                output = "Query executed successfully. No results returned."
            else:
                output = json.dumps(data, default=str, indent=2, ensure_ascii=False)
        else:
            output = f"Result: {str(result)}"

        client.close()
        return output

    except json.JSONDecodeError as e:
        client.close()
        return f"JSON Parse Error: {e}\nEnsure all JSON is properly formatted with double quotes."
    except PyMongoError as e:
        client.close()
        return f"MongoDB Error: {e}"
    except Exception as e:
        client.close()
        return f"Error: {e}\n\nTraceback:\n{traceback.format_exc()}"


def mongodb_list_tables(database: str) -> str:
    client = connection_mongo()
    try:
        db = client[database]
        collection_names = db.list_collection_names()
        client.close()
        if not collection_names:
            return f"No collections found in database '{database}'."
        output = f"MongoDB Collections in '{database}':\n"
        output += "\n".join(collection_names)
        return output
    except PyMongoError as e:
        client.close()
        return f"MongoDB Error: {e}"
    except Exception as e:
        client.close()
        return f"Error: {e}"


def mongodb_list_databases() -> str:
    client = connection_mongo()
    try:
        db_names = client.list_database_names()
        client.close()
        if not db_names:
            return "No databases found on the MongoDB server."
        output = "MongoDB Databases:\n"
        output += "\n".join(db_names)
        return output
    except PyMongoError as e:
        client.close()
        return f"MongoDB Error: {e}"
    except Exception as e:
        client.close()
        return f"Error: {e}"


def mongodb_describe_tables(table: str) -> str:
    client = connection_mongo()
    try:
        collection = client[database][table]
        sample = collection.find_one()

        if not sample:
            client.close()
            return f"Collection '{table}' is empty. No schema to display."

        flattened = flatten_dict(sample)

        output = (
            f"Field Structure of '{table}' collection (sampled from 1 document):\n\n"
        )

        for field, (field_type, value) in flattened.items():
            if field_type == "array":
                if len(value) > 0:
                    output += f"{field}: array (length: {len(value)})\n"
                    first_elem = value[0]
                    if isinstance(first_elem, dict):
                        output += f"  {field}[0]: object\n"
                        for sub_key, sub_val in first_elem.items():
                            sub_type = type(sub_val).__name__
                            display_val = (
                                str(sub_val)[:50] + "..."
                                if len(str(sub_val)) > 50
                                else str(sub_val)
                            )
                            output += f"    {field}[0].{sub_key}: {sub_type} ({display_val})\n"
                    else:
                        elem_type = type(first_elem).__name__
                        output += f"  {field}[0]: {elem_type}\n"
                else:
                    output += f"{field}: array (empty)\n"
            else:
                display_val = (
                    str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                )
                output += f"{field}: {field_type} ({display_val})\n"

            client.close()
            return output
    except PyMongoError as e:
        client.close()
        return f"MongoDB Error: {e}"
    except Exception as e:
        client.close()
        return f"Error: {e}"
