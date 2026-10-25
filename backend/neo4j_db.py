"""Neo4j connection management, isolated from Oracle."""

import os
from functools import lru_cache

# Ensure SSL CA bundle is loaded for encrypted cloud connections (especially on macOS)
if "SSL_CERT_FILE" not in os.environ:
    if os.path.isfile("/etc/ssl/cert.pem"):
        os.environ["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"
    else:
        try:
            import certifi
            os.environ["SSL_CERT_FILE"] = certifi.where()
        except ImportError:
            pass

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError


def _load_env_if_needed():
    """Load environment variables from a local .env file if NEO4J_PASSWORD is not set."""
    if "SSL_CERT_FILE" not in os.environ:
        try:
            import certifi
            os.environ["SSL_CERT_FILE"] = certifi.where()
        except ImportError:
            if os.path.isfile("/etc/ssl/cert.pem"):
                os.environ["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"

    if os.getenv("NEO4J_PASSWORD"):
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(base_dir, ".."))
    candidates = [
        os.path.join(repo_root, ".env.aura"),
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
    """Create and reuse a Neo4j driver with support for local and AuraDB cloud connections."""
    _load_env_if_needed()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or "neo4j"
    password = os.getenv("NEO4J_PASSWORD")

    if not password:
        raise RuntimeError(
            "NEO4J_PASSWORD is not set. Configure your environment first."
        )

    # AuraDB and cloud resilience options
    # max_connection_lifetime prevents stale connections when cloud databases idle out
    return GraphDatabase.driver(
        uri,
        auth=(username, password),
        max_connection_lifetime=int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "300")),
        keep_alive=True
    )


def get_database_name():
    """Return the configured Neo4j database name, auto-resolving AuraDB instance database when appropriate."""
    _load_env_if_needed()
    db = os.getenv("NEO4J_DATABASE")
    if db and db != "neo4j":
        return db

    uri = os.getenv("NEO4J_URI", "")
    if "databases.neo4j.io" in uri:
        import re
        m = re.search(r"//([a-zA-Z0-9]+)\.databases\.neo4j\.io", uri)
        if m:
            return m.group(1)

    return db or "neo4j"


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
