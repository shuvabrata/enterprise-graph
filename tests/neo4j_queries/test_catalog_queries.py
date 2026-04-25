"""
Dynamic Test Runner for Neo4j Query Catalog.

Reads query definitions from the queries_catalog directory and generates
test cases for each query automatically using pytest.mark.parametrize.
"""
import os
import yaml
import pytest
from pathlib import Path

# Resolve catalog directory relative to this file
CATALOG_DIR = Path(__file__).parent.parent.parent / "queries_catalog"
CATALOG_FILE = CATALOG_DIR / "catalog.yaml"


def load_catalog_queries():
    """Parses the catalog and loads all query YAML files."""
    queries = []
    if not CATALOG_FILE.exists():
        return queries
        
    with open(CATALOG_FILE, "r") as f:
        catalog = yaml.safe_load(f)
        
    for namespace in catalog.get("namespaces", []):
        section_name = namespace["name"]
        ns_dir = CATALOG_DIR / namespace["directory"]
        
        if not ns_dir.exists():
            continue
            
        for yaml_file in ns_dir.glob("*.yaml"):
            with open(yaml_file, "r") as yf:
                query_def = yaml.safe_load(yf)
                query_def["section"] = section_name
                queries.append(query_def)
                
    return queries


CATALOG_QUERIES = load_catalog_queries()


@pytest.mark.parametrize("query_def", CATALOG_QUERIES, ids=lambda q: q["name"])
def test_catalog_query(query_def, query_executor, expectations, track_result):
    """Dynamically execute and validate a catalog query."""
    params = {}
    missing_mandatory = []
    
    # Extract parameters and enforce mandatory constraints
    for param in query_def.get("parameters", []):
        env_var = param.get("env_var", param["name"].upper())
        val = os.getenv(env_var)
        
        if not val and param.get("required", False):
            missing_mandatory.append(env_var)
        elif val:
            params[param["name"]] = val
            
    if missing_mandatory:
        pytest.skip(f"Missing mandatory environment variables: {', '.join(missing_mandatory)}")
        
    # Execute through the established framework
    result = query_executor.execute(
        query_name=query_def["name"],
        section=query_def["section"],
        query_text=query_def["query"],
        expectation=expectations.get(query_def["name"]),
        parameters=params  # NOTE: Ensure QueryExecutor accepts this argument!
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"