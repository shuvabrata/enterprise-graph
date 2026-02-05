"""
Tests for Cross-Domain analytics queries (sample).

NOTE: This is a sample. Add remaining cross-domain queries.
"""

import pytest


def test_developer_impact_analysis(query_executor, expectations, track_result):
    """Developer contributions across all domains."""
    query = """
    MATCH (p:Person)
    OPTIONAL MATCH (p)<-[:CREATED_BY]-(pr:PullRequest)
    OPTIONAL MATCH (p)<-[:AUTHORED_BY]-(c:Commit)
    OPTIONAL MATCH (p)<-[:ASSIGNED_TO]-(i:Issue)
    RETURN p.name as developer,
           p.title,
           count(DISTINCT pr) as prs,
           count(DISTINCT c) as commits,
           count(DISTINCT i) as issues
    ORDER BY commits DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Developer Impact Analysis",
        section="Cross-Domain",
        query_text=query,
        expectation=expectations.get("Developer Impact Analysis")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_team_workload_overview(query_executor, expectations, track_result):
    """Team workload across GitHub and Jira."""
    query = """
    MATCH (t:Team)<-[:MEMBER_OF]-(p:Person)
    OPTIONAL MATCH (p)<-[:ASSIGNED_TO]-(i:Issue)
    OPTIONAL MATCH (p)<-[:AUTHORED_BY]-(c:Commit)
    RETURN t.name as team,
           count(DISTINCT p) as members,
           count(DISTINCT i) as assigned_issues,
           count(DISTINCT c) as commits
    ORDER BY assigned_issues DESC
    """
    
    result = query_executor.execute(
        query_name="Team Workload Overview",
        section="Cross-Domain",
        query_text=query,
        expectation=expectations.get("Team Workload Overview")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_epic_to_repository_traceability(query_executor, expectations, track_result):
    """Map epics to repositories via commits."""
    query = """
    MATCH (e:Epic)<-[:PART_OF]-(i:Issue)<-[:REFERENCES]-(c:Commit)
    MATCH (c)-[:PART_OF]->(b:Branch)-[:BRANCH_OF]->(r:Repository)
    RETURN e.key as epic, e.summary,
           collect(DISTINCT r.name) as repositories,
           count(DISTINCT c) as commits
    ORDER BY commits DESC
    """
    
    result = query_executor.execute(
        query_name="Epic to Repository Traceability",
        section="Cross-Domain",
        query_text=query,
        expectation=expectations.get("Epic to Repository Traceability")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_issue_to_code_linkage(query_executor, expectations, track_result):
    """Issues linked to actual code commits."""
    query = """
    MATCH (i:Issue)<-[:REFERENCES]-(c:Commit)
    RETURN i.key, i.type, i.summary,
           count(c) as commit_count
    ORDER BY commit_count DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Issue to Code Linkage",
        section="Cross-Domain",
        query_text=query,
        expectation=expectations.get("Issue to Code Linkage")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_pr_to_jira_mapping(query_executor, expectations, track_result):
    """PRs linked to Jira issues via commits."""
    query = """
    MATCH (pr:PullRequest)-[:INCLUDES]->(c:Commit)-[:REFERENCES]->(i:Issue)
    RETURN pr.number as pr_number, pr.title,
           collect(DISTINCT i.key) as jira_issues,
           size(collect(DISTINCT i.key)) as issue_count
    ORDER BY issue_count DESC
    """
    
    result = query_executor.execute(
        query_name="PR to Jira Mapping",
        section="Cross-Domain",
        query_text=query,
        expectation=expectations.get("PR to Jira Mapping")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_end_to_end_traceability(query_executor, expectations, track_result):
    """Complete Initiative → Epic → Issue → Commit → PR chain."""
    query = """
    MATCH (init:Initiative)<-[:PART_OF]-(e:Epic)<-[:PART_OF]-(i:Issue)
    MATCH (i)<-[:REFERENCES]-(c:Commit)<-[:INCLUDES]-(pr:PullRequest)
    RETURN init.key as initiative, e.key as epic, i.key as issue,
           c.sha as commit_sha, pr.number as pr_number
    LIMIT 20
    """
    
    result = query_executor.execute(
        query_name="End-to-End Traceability",
        section="Cross-Domain",
        query_text=query,
        expectation=expectations.get("End-to-End Traceability")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_work_without_code(query_executor, expectations, track_result):
    """Issues marked Done but no code commits - Data Quality check."""
    query = """
    MATCH (i:Issue {status: 'Done'})
    WHERE NOT (i)<-[:REFERENCES]-(:Commit)
    RETURN i.key, i.type, i.summary, i.status
    LIMIT 20
    """
    
    result = query_executor.execute(
        query_name="Work Without Code",
        section="Cross-Domain - Data Quality",
        query_text=query,
        expectation=expectations.get("Work Without Code")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"
