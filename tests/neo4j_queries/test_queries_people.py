"""
Tests for People & Identity Mapping queries.
"""

import pytest


def test_team_distribution(query_executor, expectations, track_result):
    """View team sizes."""
    query = """
    MATCH (t:Team)<-[:MEMBER_OF]-(p:Person)
    RETURN t.name as team, count(p) as team_size
    ORDER BY team_size DESC
    """
    
    result = query_executor.execute(
        query_name="Team Distribution",
        section="People & Identity",
        query_text=query,
        expectation=expectations.get("Team Distribution")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_teams_and_members(query_executor, expectations, track_result):
    """View all teams and their members."""
    query = """
    MATCH (t:Team)<-[:MEMBER_OF]-(p:Person)
    RETURN t.name, collect(p.name) as members
    ORDER BY t.name
    """
    
    result = query_executor.execute(
        query_name="Teams and Members",
        section="People & Identity",
        query_text=query,
        expectation=expectations.get("Teams and Members")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_identity_mappings(query_executor, expectations, track_result):
    """Find all identity mappings for a person."""
    # Note: This query requires a specific person name, so it may return 0 rows
    query = """
    MATCH (p:Person {name: "Add a valid name here"})<-[:MAPS_TO]-(i:IdentityMapping)
    RETURN p.name, i.provider, i.username, i.email
    """
    
    result = query_executor.execute(
        query_name="Identity Mappings",
        section="People & Identity",
        query_text=query,
        expectation=expectations.get("Identity Mappings")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_organizational_hierarchy(query_executor, expectations, track_result):
    """View reporting structure."""
    query = """
    MATCH (p:Person)-[:REPORTS_TO]->(m:Person)
    RETURN p.name as employee, p.title, m.name as manager, m.title as manager_title
    ORDER BY m.name, p.name
    """
    
    result = query_executor.execute(
        query_name="Organizational Hierarchy",
        section="People & Identity",
        query_text=query,
        expectation=expectations.get("Organizational Hierarchy")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"
