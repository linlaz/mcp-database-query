from dotenv import dotenv_values
from src.connections import connect_postgres
from psycopg2 import OperationalError

config = dotenv_values(".env")
host = config["POSTGRESHOST"]
user = config["POSTGRESUSER"]
password = config["POSTGRESPASS"]
database = config["POSTGRESDB"]
port = config["POSTGRESPORT"]


def connection_postgresql() -> object:
    conn = connect_postgres(host, user, password, database, port or 5432)
    if isinstance(conn, str):
        raise Exception(conn)
    return conn


def postgresql_execute_query(query: str) -> str:
    conn = connection_postgresql()
    cur = conn.cursor()
    try:
        cur.execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cur.fetchall()
            if not rows:
                return "Query executed successfully. No results returned."
            headers = [desc[0] for desc in cur.description]
            out = " | ".join(headers) + "\n" + "-" * 70 + "\n"
            for row in rows:
                out += " | ".join(str(v) for v in row) + "\n"
            return out
        else:
            conn.commit()
            return f"Query executed successfully. {cur.rowcount} row(s) affected."
    except OperationalError as e:
        return f"PostgreSQL Error: {e}"
    finally:
        cur.close()
        conn.close()


def postgresql_list_databases() -> str:
    conn = connection_postgresql()
    cur = conn.cursor()
    try:
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        rows = cur.fetchall()
        if not rows:
            return "No databases found on the server"

        output = "Databases on server:\n"
        output += "\n".join(row[0] for row in rows)

        cur.close()
        conn.close()
        return output
    except OperationalError as e:
        cur.close()
        conn.close()
        return f"PostgreSQL Error: {e}"


def postgresql_list_tables() -> str:
    conn = connection_postgresql()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
        )
        rows = cur.fetchall()
        if not rows:
            return "No tables found in the database"

        output = "Tables in database '{}':\n".format(database)
        output += "\n".join(row[0] for row in rows)

        cur.close()
        conn.close()
        return output
    except OperationalError as e:
        cur.close()
        conn.close()
        return f"PostgreSQL Error: {e}"


def postgresql_describe_table(table: str) -> str:
    conn = connection_postgresql()
    cur = conn.cursor()
    try:
        query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """
        cur.execute(query, (table,))
        rows = cur.fetchall()

        if not rows:
            return f"Table '{table}' not found or has no columns"

        output = "column_name | data_type | is_nullable | column_default\n"
        output += "-" * 70 + "\n"
        for row in rows:
            output += " | ".join(str(v) if v is not None else "" for v in row) + "\n"

        cur.close()
        conn.close()
        return output
    except OperationalError as e:
        cur.close()
        conn.close()
        return f"PostgreSQL Error: {e}"
