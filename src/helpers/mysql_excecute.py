from dotenv import dotenv_values
from src.connections import connect_mysql
from mysql.connector import Error as MySQLError

config = dotenv_values(".env")
host = config["MYSQLHOST"]
user = config["MYSQLUSER"]
password = config["MYSQLPASS"]
database = config["MYSQLDB"]
port = int(config["MYSQLPORT"])


def connection_mysql() -> object:
    conn = connect_mysql(host, user, password, database, port)
    if isinstance(conn, str):
        raise Exception(conn)
    return conn


def mysql_execute_query(query: str) -> str:
    conn = connection_mysql()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cur.fetchall()
            if not rows:
                return "Query executed successfully. No results returned."
            headers = rows[0].keys()
            out = " | ".join(headers) + "\n" + "-" * 70 + "\n"
            for row in rows:
                out += " | ".join(str(v) for v in row.values()) + "\n"
            return out
        else:
            conn.commit()
            return f"Query executed successfully. {cur.rowcount} row(s) affected."
    except MySQLError as e:
        return f"MySQL Error: {e}"
    finally:
        cur.close()
        conn.close()


def mysql_list_tables() -> str:
    conn = connection_mysql()
    cur = conn.cursor()
    try:
        cur.execute("SHOW TABLES")
        rows = cur.fetchall()
        if not rows:
            return "No tables found in the database"

        output = "Tables in database '{}':\n".format(database)
        output += "\n".join(row[0] for row in rows)

        cur.close()
        conn.close()
        return output
    except MySQLError as e:
        cur.close()
        conn.close()
        return f"MySQL Error: {e}"


def mysql_list_databases() -> str:
    conn = connection_mysql()
    cur = conn.cursor()
    try:
        cur.execute("SHOW DATABASES")
        rows = cur.fetchall()
        if not rows:
            return "No databases found on the server"

        output = "Databases on server:\n"
        output += "\n".join(row[0] for row in rows)

        cur.close()
        conn.close()
        return output
    except MySQLError as e:
        cur.close()
        conn.close()
        return f"MySQL Error: {e}"


def mysql_describe_table(table: str) -> str:
    conn = connection_mysql()
    cur = conn.cursor()
    try:
        cur.execute(f"DESCRIBE `{table}`")
        rows = cur.fetchall()
        if not rows:
            return f"Table '{table}' not found or has no columns"

        output = "Field | Type | Null | Key | Default | Extra\n"
        output += "-" * 70 + "\n"
        for row in rows:
            output += (
                " | ".join(str(v) if v is not None else "NULL" for v in row) + "\n"
            )

        cur.close()
        conn.close()
        return output
    except MySQLError as e:
        cur.close()
        conn.close()
        return f"MySQL Error: {e}"
