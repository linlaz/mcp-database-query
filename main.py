from dotenv import dotenv_values
from fastmcp import FastMCP
from src.tools import (
    describe_table_mcp,
    list_database_mcp,
    list_tables_mcp,
    run_query_mcp,
)
import asyncio


config = dotenv_values(".env")
main_mcp = FastMCP(
    name=config["APP_NAME"],
    port=int(config["APP_PORT"]),
)

async def setup():
    await main_mcp.import_server(describe_table_mcp)
    await main_mcp.import_server(list_database_mcp)
    await main_mcp.import_server(list_tables_mcp)
    await main_mcp.import_server(run_query_mcp)


if __name__ == "__main__":
    asyncio.run(setup())
    main_mcp.run(transport="http")
