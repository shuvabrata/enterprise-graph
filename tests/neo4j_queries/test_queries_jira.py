"""
Tests for Jira queries (sample - showing pattern).

NOTE: This is a sample showing the first 3 Jira queries.
You should add the remaining Jira queries following this same pattern.
"""

import pytest


def test_project_hierarchy(query_executor, expectations, track_result):
    """Projects and their initiatives."""
    query = """
    MATCH (p:Project)<-[:PART_OF]-(i:Initiative)
    RETURN p.name, collect(i.summary) as initiatives
    ORDER BY p.name
    """
    
    result = query_executor.execute(
        query_name="Project Hierarchy",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Project Hierarchy")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_unassigned_critical_issues(query_executor, expectations, track_result):
    """Critical issues without assignees - Data Quality check."""
    query = """
    MATCH (i:Issue)
    WHERE i.priority = 'Critical' AND NOT exists((i)-[:ASSIGNED_TO]->())
    RETURN i.key, i.summary, i.status
    """
    
    result = query_executor.execute(
        query_name="Unassigned Critical Issues",
        section="Jira - Data Quality",
        query_text=query,
        expectation=expectations.get("Unassigned Critical Issues")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_initiative_timeline(query_executor, expectations, track_result):
    """Initiative timeline by start date."""
    query = """
    MATCH (i:Initiative)
    RETURN i.summary, i.start_date, i.due_date, i.priority
    ORDER BY i.start_date
    """
    
    result = query_executor.execute(
        query_name="Initiative Timeline",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Initiative Timeline")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_epics_by_initiative(query_executor, expectations, track_result):
    """Epics grouped by initiative."""
    query = """
    MATCH (e:Epic)-[:PART_OF]->(i:Initiative)
    RETURN i.key, i.summary, collect(e.key) as epics
    ORDER BY i.key
    """
    
    result = query_executor.execute(
        query_name="Epics by Initiative",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Epics by Initiative")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_epic_timeline(query_executor, expectations, track_result):
    """Epic timeline by start date."""
    query = """
    MATCH (e:Epic)
    RETURN e.key, e.summary, e.start_date, e.due_date, e.status
    ORDER BY e.start_date, e.key
    """
    
    result = query_executor.execute(
        query_name="Epic Timeline",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Epic Timeline")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_epics_by_team(query_executor, expectations, track_result):
    """Epics assigned to each team."""
    query = """
    MATCH (e:Epic)-[:TEAM]->(t:Team)
    RETURN t.name, count(e) as epic_count, collect(e.key) as epics
    ORDER BY epic_count DESC
    """
    
    result = query_executor.execute(
        query_name="Epics by Team",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Epics by Team")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_epic_ownership_distribution(query_executor, expectations, track_result):
    """Epic ownership by person."""
    query = """
    MATCH (e:Epic)-[:ASSIGNED_TO]->(p:Person)
    RETURN p.name, p.role, count(e) as epic_count
    ORDER BY epic_count DESC
    """
    
    result = query_executor.execute(
        query_name="Epic Ownership Distribution",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Epic Ownership Distribution")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_initiatives_with_assignees(query_executor, expectations, track_result):
    """Initiatives with assignees and reporters."""
    query = """
    MATCH (i:Initiative)-[:ASSIGNED_TO]->(assignee:Person),
          (i)-[:REPORTED_BY]->(reporter:Person)
    RETURN i.key, i.summary, 
           assignee.name as assignee, assignee.title as assignee_title,
           reporter.name as reporter, reporter.title as reporter_title,
           i.status
    ORDER BY i.key
    """
    
    result = query_executor.execute(
        query_name="Initiatives with Assignees",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Initiatives with Assignees")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_sprint_burndown_data(query_executor, expectations, track_result):
    """Sprint progress and burndown metrics."""
    query = """
    MATCH (s:Sprint)<-[:IN_SPRINT]-(i:Issue)
    RETURN s.name, 
           sum(i.story_points) as total_points,
           sum(CASE WHEN i.status = 'Done' THEN i.story_points ELSE 0 END) as completed_points,
           count(i) as issue_count
    ORDER BY s.name
    """
    
    result = query_executor.execute(
        query_name="Sprint Burndown Data",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Sprint Burndown Data")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_work_by_person(query_executor, expectations, track_result):
    """Work assigned to each person."""
    query = """
    MATCH (i:Issue)-[:ASSIGNED_TO]->(p:Person)
    RETURN p.name, p.title, 
           count(i) as total_issues,
           sum(i.story_points) as total_points
    ORDER BY total_points DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Work by Person",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Work by Person")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_bug_distribution_by_epic(query_executor, expectations, track_result):
    """Bugs grouped by epic."""
    query = """
    MATCH (bug:Issue {type: 'Bug'})-[:PART_OF]->(e:Epic)
    RETURN e.key, e.summary, count(bug) as bug_count
    ORDER BY bug_count DESC
    """
    
    result = query_executor.execute(
        query_name="Bug Distribution by Epic",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Bug Distribution by Epic")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_bugs_related_to_stories(query_executor, expectations, track_result):
    """Bugs linked to specific stories."""
    query = """
    MATCH (bug:Issue {type: 'Bug'})-[:RELATES_TO]->(story:Issue {type: 'Story'})
    RETURN bug.key, story.key as story, bug.summary
    """
    
    result = query_executor.execute(
        query_name="Bugs Related to Stories",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Bugs Related to Stories")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_dependencies_and_blockers(query_executor, expectations, track_result):
    """Issues blocking other issues."""
    query = """
    MATCH (i:Issue)-[:BLOCKS]->(blocked:Issue)
    RETURN i.key, i.summary, 
           collect(blocked.key) as blocks_issues
    """
    
    result = query_executor.execute(
        query_name="Dependencies and Blockers",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Dependencies and Blockers")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_epics_with_owners_and_teams(query_executor, expectations, track_result):
    """Complete epic context with owners, teams, and initiatives."""
    query = """
    MATCH (e:Epic)-[:ASSIGNED_TO]->(owner:Person)
    MATCH (e)-[:TEAM]->(team:Team)
    MATCH (e)-[:PART_OF]->(i:Initiative)
    RETURN e.key, e.summary, 
           owner.name as owner, owner.title as owner_title,
           team.name as team,
           i.key as initiative,
           e.status, e.priority
    """
    
    result = query_executor.execute(
        query_name="Epics with Owners and Teams",
        section="Jira",
        query_text=query,
        expectation=expectations.get("Epics with Owners and Teams")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_orphaned_issues(query_executor, expectations, track_result):
    """Issues not linked to any epic - Data Quality check."""
    query = """
    MATCH (i:Issue)
    WHERE NOT (i)-[:PART_OF]->(:Epic)
    RETURN i.key, i.type, i.summary, i.status
    LIMIT 20
    """
    
    result = query_executor.execute(
        query_name="Orphaned Issues",
        section="Jira - Data Quality",
        query_text=query,
        expectation=expectations.get("Orphaned Issues")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"
