"""
Tests for Schema inspection queries.
"""

import pytest


def test_view_all_node_types(query_executor, expectations, track_result):
    """Count all nodes by type."""
    query = """
    MATCH (n) 
    RETURN labels(n)[0] as type, count(*) as count
    ORDER BY count DESC
    """
    
    result = query_executor.execute(
        query_name="View All Node Types",
        section="Schema",
        query_text=query,
        expectation=expectations.get("View All Node Types")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_view_all_relationship_types(query_executor, expectations, track_result):
    """Count all relationships by type."""
    query = """
    MATCH ()-[r]->()
    RETURN type(r) as relationship, count(*) as count
    ORDER BY count DESC
    """
    
    result = query_executor.execute(
        query_name="View All Relationship Types",
        section="Schema",
        query_text=query,
        expectation=expectations.get("View All Relationship Types")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


# TODO: Add remaining schema queries
