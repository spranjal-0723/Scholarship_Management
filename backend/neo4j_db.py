"""Neo4j connection management, isolated from Oracle."""

import os
from functools import lru_cache

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError


def _load_env_if_needed():
    """Load environment variables from a local .env file if NEO4J_PASSWORD is not set."""
    if os.getenv("NEO4J_PASSWORD"):
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.getcwd(), "backend", ".env"),
    ]

    for candidate in candidates:
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            os.environ.setdefault(key.strip(), val.strip())
            except OSError:
                pass
            if os.getenv("NEO4J_PASSWORD"):
                break


@lru_cache(maxsize=1)
def get_driver():
    """Create and reuse a Neo4j driver."""
    _load_env_if_needed()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not password:
        raise RuntimeError(
            "NEO4J_PASSWORD is not set. Configure your environment first."
        )

    return GraphDatabase.driver(uri, auth=(username, password))


def get_database_name():
    """Return the configured Neo4j database name."""
    _load_env_if_needed()
    return os.getenv("NEO4J_DATABASE", "neo4j")


def verify_connection():
    """Verify connectivity and execute a harmless Cypher query."""
    driver = get_driver()

    try:
        driver.verify_connectivity()

        with driver.session(database=get_database_name()) as session:
            record = session.run("RETURN 1 AS result").single()

            if record is None or record["result"] != 1:
                raise RuntimeError(
                    "Neo4j verification query returned an unexpected result."
                )

        return True

    except (Neo4jError, OSError) as exc:
        raise RuntimeError(
            "Neo4j connection verification failed. Check the server, "
            "URI, credentials, and database configuration."
        ) from exc


def close_driver():
    """Close the shared driver."""
    if get_driver.cache_info().currsize:
        get_driver().close()
        get_driver.cache_clear()
