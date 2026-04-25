"""
Tests for Person-to-Person Collaboration queries.

Focuses on uncovering relationships, shared work, and bottlenecks
between two specific people.

Specify nodes using environment variables: 
PERSON1_ID, PERSON2_ID, and optionally CONDITION_NODE_ID.
If not specified, the tests will fallback to two randomly connected people.
"""

import os
import pytest


def get_p2p_match_clause():
    """Helper to inject the starting MATCH clause for the 2 persons."""
    p1_id = os.getenv("PERSON1_ID")
    p2_id = os.getenv("PERSON2_ID")
    
    if p1_id and p2_id:
        return f"""
        MATCH (p1:Person {{id: '{p1_id}'}}), (p2:Person {{id: '{p2_id}'}})
        """
    else:
        # Fallback: Find any two people who are connected by 1 to 3 hops (e.g. shared a PR or Issue)
        return """
        MATCH path = (p1:Person)-[*1..3]-(p2:Person)
        WHERE p1 <> p2
        WITH p1, p2 LIMIT 1
        """


def get_condition_node_match():
    """Helper to inject the 3rd intermediary node match."""
    cond_id = os.getenv("CONDITION_NODE_ID")
    if cond_id:
        return f"MATCH (c {{id: '{cond_id}'}})"
    else:
        # Fallback: Pick a node right in the middle of their baseline shortest path
        return """
        MATCH base_path = shortestPath((p1)-[*..6]-(p2))
        WITH p1, p2, nodes(base_path)[size(nodes(base_path))/2] as c
        """


def test_shortest_path_collaboration(query_executor, expectations, track_result):
    """
    Find the shortest path of collaboration between two people.
    
    Purpose: Answers the question "What is the shortest general path of 
    collaboration between these two people across any domain?"
    """
    query = get_p2p_match_clause() + """
    MATCH path = shortestPath((p1)-[*..6]-(p2))
    RETURN p1.name as person1, 
           p2.name as person2,
           length(path) as degrees_of_separation,
           [n IN nodes(path) | coalesce(n.name, n.key, n.title, n.path, labels(n)[0])] as connection_path,
           [r IN relationships(path) | type(r)] as relationship_types
    """
    
    result = query_executor.execute(
        query_name="Shortest Path Collaboration",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Shortest Path Collaboration")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_all_shortest_paths_collaboration(query_executor, expectations, track_result):
    """
    Find ALL shortest paths if multiple connections of the same length exist.
    
    Purpose: While shortestPath() returns only one path, allShortestPaths() finds 
    all paths that are tied for the shortest length. This is useful for seeing if 
    two people are connected in multiple ways with the same degree of separation.
    """
    query = get_p2p_match_clause() + """
    MATCH paths = allShortestPaths((p1)-[*..6]-(p2))
    UNWIND paths as path
    RETURN p1.name as person1, 
           p2.name as person2,
           length(path) as degrees_of_separation,
           [n IN nodes(path) | coalesce(n.name, n.key, n.title, n.path, labels(n)[0])] as connection_path,
           [r IN relationships(path) | type(r)] as relationship_types
    LIMIT 10 // Limit to 10 paths to avoid excessive output
    """
    
    result = query_executor.execute(
        query_name="All Shortest Paths Collaboration",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("All Shortest Paths Collaboration")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_shortest_path_through_code(query_executor, expectations, track_result):
    """
    Find the shortest connection between two people based purely on
    code artifacts (Commits, PRs, Files, Repos).
    
    Purpose: This query restricts the search to relationships that represent 
    direct code collaboration. It answers the question: "What is the most direct 
    technical connection between these two developers?"
    """
    query = get_p2p_match_clause() + """
    MATCH path = shortestPath(
      (p1)-[:AUTHORED_BY|REVIEWED_BY|CREATED_BY|COLLABORATOR|MODIFIES|INCLUDES*..10]-(p2)
    )
    RETURN p1.name as person1, 
           p2.name as person2,
           length(path) as degrees_of_separation,
           [n IN nodes(path) | coalesce(n.name, n.key, n.title, n.path, n.sha, labels(n)[0])] as connection_path,
           [r IN relationships(path) | type(r)] as relationship_types
    """
    
    result = query_executor.execute(
        query_name="Shortest Path Through Code",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Shortest Path Through Code")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_shortest_path_through_work_items(query_executor, expectations, track_result):
    """
    Find the shortest connection between two people based purely on
    Jira work items (Issues, Epics, Sprints).
    
    Purpose: This provides the project management perspective. It finds the 
    shortest connection by traversing only through Jira artifacts. It answers: 
    "How are these two individuals connected from a work-planning standpoint?"
    """
    query = get_p2p_match_clause() + """
    MATCH path = shortestPath(
      (p1)-[:ASSIGNED_TO|REPORTED_BY|REFERENCES|PART_OF|TEAM|IN_SPRINT*..10]-(p2)
    )
    RETURN p1.name as person1, 
           p2.name as person2,
           length(path) as degrees_of_separation,
           [n IN nodes(path) | coalesce(n.name, n.key, n.title, labels(n)[0])] as connection_path,
           [r IN relationships(path) | type(r)] as relationship_types
    """
    
    result = query_executor.execute(
        query_name="Shortest Path Through Work Items",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Shortest Path Through Work Items")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_shortest_path_via_specific_node(query_executor, expectations, track_result):
    """
    Find the shortest path between two people that goes THROUGH a specific 3rd node.
    
    Purpose: Allows analyzing connections through a specific "lens".
    - If Person: Identifies human bridges/bottlenecks.
    - If Issue/Epic: Maps collaboration based on specific business deliverables.
    - If PR/Commit: Highlights precise technical/code review touchpoints.
    """
    query = get_p2p_match_clause() + get_condition_node_match() + """
    // Split the path into two to efficiently force traversal through node 'c'
    MATCH path1 = shortestPath((p1)-[*..6]-(c))
    MATCH path2 = shortestPath((c)-[*..6]-(p2))
    
    RETURN p1.name as person1, 
           p2.name as person2,
           coalesce(c.name, c.key, c.title, c.number, labels(c)[0]) as intermediary_node,
           labels(c)[0] as intermediary_type,
           length(path1) + length(path2) as total_degrees_of_separation,
           // Concatenate the nodes and relationships, slicing path2[1..] to avoid duplicating 'c'
           [n IN nodes(path1) | coalesce(n.name, n.key, n.title, n.path, labels(n)[0])] + 
           [n IN nodes(path2)[1..] | coalesce(n.name, n.key, n.title, n.path, labels(n)[0])] as full_connection_path,
           [r IN relationships(path1) | type(r)] + [r IN relationships(path2) | type(r)] as full_relationship_path
    """
    
    result = query_executor.execute(
        query_name="Shortest Path Via Specific Node",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Shortest Path Via Specific Node")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_direct_code_reviews(query_executor, expectations, track_result):
    """
    Find all PRs created by one and reviewed by the other.
    
    Purpose: Answers the question "How frequently do these two developers 
    review each other's code?"
    """
    query = get_p2p_match_clause() + """
    MATCH (author:Person)-[:CREATED_BY]-(pr:PullRequest)-[:REVIEWED_BY]-(reviewer:Person)
    WHERE (author = p1 AND reviewer = p2) OR (author = p2 AND reviewer = p1)
    RETURN author.name as author, 
           reviewer.name as reviewer, 
           count(pr) as review_count,
           collect(pr.number)[0..5] as sample_prs
    ORDER BY review_count DESC
    """
    
    result = query_executor.execute(
        query_name="Direct Code Reviews",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Direct Code Reviews")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_shared_jira_work(query_executor, expectations, track_result):
    """
    Find Jira issues reported by one and assigned to the other.
    
    Purpose: Answers the question "How often does one person report a Jira 
    issue that is assigned to the other?"
    """
    query = get_p2p_match_clause() + """
    MATCH (reporter:Person)-[:REPORTED_BY]-(issue:Issue)-[:ASSIGNED_TO]-(assignee:Person)
    WHERE (reporter = p1 AND assignee = p2) OR (reporter = p2 AND assignee = p1)
    RETURN reporter.name as reporter, 
           assignee.name as assignee, 
           count(issue) as issue_count, 
           collect(issue.key)[0..5] as sample_issues
    ORDER BY issue_count DESC
    """
    
    result = query_executor.execute(
        query_name="Shared Jira Work",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Shared Jira Work")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_shared_code_hotspots(query_executor, expectations, track_result):
    """
    Find files (hotspots) that both developers have modified.
    
    Purpose: Answers the question "Which specific files have both developers 
    modified, indicating shared technical context or potential merge conflicts?"
    """
    query = get_p2p_match_clause() + """
    MATCH (p1)-[:AUTHORED_BY]-(c1:Commit)-[:MODIFIES]->(f:File)<-[:MODIFIES]-(c2:Commit)-[:AUTHORED_BY]-(p2)
    RETURN f.path as shared_file, 
           f.language as language,
           count(DISTINCT c1) as person1_commits,
           count(DISTINCT c2) as person2_commits,
           count(DISTINCT c1) + count(DISTINCT c2) as total_shared_churn
    ORDER BY total_shared_churn DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Shared Code Hotspots",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Shared Code Hotspots")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_shared_repositories(query_executor, expectations, track_result):
    """
    Find repositories both developers collaborate on.
    
    Purpose: Answers the question "Which codebases do both developers have 
    access to and collaborate on?"
    """
    query = get_p2p_match_clause() + """
    MATCH (p1)-[c1:COLLABORATOR]-(r:Repository)-[c2:COLLABORATOR]-(p2)
    RETURN r.name as repository, 
           c1.permission as person1_permission,
           c2.permission as person2_permission
    ORDER BY repository
    """
    
    result = query_executor.execute(
        query_name="Shared Repositories",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Shared Repositories")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_shared_teams(query_executor, expectations, track_result):
    """
    Find teams that both people belong to.
    
    Purpose: Answers the question "Are these two people members of any of 
    the same teams?"
    """
    query = get_p2p_match_clause() + """
    MATCH (p1)-[:MEMBER_OF]-(t:Team)-[:MEMBER_OF]-(p2)
    RETURN p1.name as person1, 
           p2.name as person2, 
           t.name as shared_team
    """
    
    result = query_executor.execute(
        query_name="Shared Teams",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Shared Teams")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_org_chart_relationship(query_executor, expectations, track_result):
    """
    Check direct or indirect management relationship between the two people.
    
    Purpose: Answers the question "Is there a direct or indirect reporting 
    line between these two individuals?"
    """
    query = get_p2p_match_clause() + """
    OPTIONAL MATCH path_up = (p1)-[:REPORTS_TO*..5]->(p2)
    OPTIONAL MATCH path_down = (p2)-[:REPORTS_TO*..5]->(p1)
    RETURN p1.name as person1, 
           p2.name as person2,
           CASE 
             WHEN path_up IS NOT NULL THEN p1.name + ' reports to ' + p2.name
             WHEN path_down IS NOT NULL THEN p2.name + ' reports to ' + p1.name
             ELSE 'No direct reporting line within 5 levels'
           END as reporting_relationship,
           coalesce(length(path_up), length(path_down), 0) as levels_apart
    """
    
    result = query_executor.execute(
        query_name="Org Chart Relationship",
        section="Person-to-Person",
        query_text=query,
        expectation=expectations.get("Org Chart Relationship")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"