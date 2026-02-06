"""
Tests for GitHub queries (sample - showing pattern for all GitHub queries).

NOTE: This is a sample showing the first 5 GitHub queries.
You should add the remaining 22 GitHub queries following this same pattern.
"""

import pytest


def test_repository_ownership(query_executor, expectations, track_result):
    """View repositories with owning teams (WRITE access)."""
    query = """
    MATCH (t:Team)-[c:COLLABORATOR {permission: 'WRITE'}]->(r:Repository)
    RETURN t.name, r.name, r.language
    ORDER BY t.name, r.name
    """
    
    result = query_executor.execute(
        query_name="Repository Ownership",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Repository Ownership")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_repository_maintainers(query_executor, expectations, track_result):
    """Find maintainers (people with WRITE access)."""
    query = """
    MATCH (p:Person)-[c:COLLABORATOR {permission: 'WRITE'}]->(r:Repository)
    RETURN r.name, collect(p.name) as maintainers
    ORDER BY r.name
    """
    
    result = query_executor.execute(
        query_name="Repository Maintainers",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Repository Maintainers")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_cross_team_collaborations(query_executor, expectations, track_result):
    """Teams with READ access to repositories."""
    query = """
    MATCH (t:Team)-[c:COLLABORATOR {permission: 'READ'}]->(r:Repository)
    RETURN r.name, collect(t.name) as read_access_teams
    ORDER BY r.name
    """
    
    result = query_executor.execute(
        query_name="Cross-Team Collaborations",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Cross-Team Collaborations")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_top_contributors(query_executor, expectations, track_result):
    """Top 10 contributors by commit count."""
    query = """
    MATCH (p:Person)<-[:AUTHORED_BY]-(c:Commit)
    RETURN p.name as name, p.title as title, count(c) as commits
    ORDER BY commits DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Top Contributors",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Top Contributors")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_stale_branches(query_executor, expectations, track_result):
    """Stale branches (candidates for cleanup) - Data Quality check."""
    query = """
    MATCH (b:Branch)
    WHERE b.last_commit_timestamp < datetime() - duration({days: 30})
      AND NOT b.is_default
      AND NOT b.is_deleted
    RETURN b.name, b.last_commit_timestamp,
           duration.between(b.last_commit_timestamp, datetime()).days as days_old
    ORDER BY days_old DESC
    """
    
    result = query_executor.execute(
        query_name="Stale Branches",
        section="GitHub - Data Quality",
        query_text=query,
        expectation=expectations.get("Stale Branches")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_branches_by_repository(query_executor, expectations, track_result):
    """View all branches by repository."""
    query = """
    MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository)
    RETURN r.name, collect(b.name) as branches
    ORDER BY r.name
    """
    
    result = query_executor.execute(
        query_name="Branches by Repository",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Branches by Repository")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_active_feature_branches(query_executor, expectations, track_result):
    """Find active non-default branches."""
    query = """
    MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository)
    WHERE NOT b.is_default AND NOT b.is_deleted
    RETURN r.name, b.name, b.last_commit_timestamp
    ORDER BY b.last_commit_timestamp DESC
    """
    
    result = query_executor.execute(
        query_name="Active Feature Branches",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Active Feature Branches")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_protected_branches(query_executor, expectations, track_result):
    """Protected branches across all repos."""
    query = """
    MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository)
    WHERE b.is_protected
    RETURN r.name, collect(b.name) as protected_branches
    ORDER BY r.name
    """
    
    result = query_executor.execute(
        query_name="Protected Branches",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Protected Branches")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_branches_by_work_item(query_executor, expectations, track_result):
    """Branches linked to specific work item."""
    query = """
    MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository)
    WHERE b.name CONTAINS 'PLAT-1'
    RETURN r.name, b.name
    ORDER BY r.name, b.name
    """
    
    result = query_executor.execute(
        query_name="Branches by Work Item",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Branches by Work Item")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_commits_per_repository(query_executor, expectations, track_result):
    """Count commits per repository."""
    query = """
    MATCH (c:Commit)-[:PART_OF]->(b:Branch)-[:BRANCH_OF]->(r:Repository)
    WHERE b.is_default = true
    RETURN r.name as repo, count(c) as commits
    ORDER BY commits DESC
    """
    
    result = query_executor.execute(
        query_name="Commits per Repository",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Commits per Repository")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_commits_with_jira_references(query_executor, expectations, track_result):
    """Commits with Jira references."""
    query = """
    MATCH (c:Commit)-[:REFERENCES]->(i:Issue)
    RETURN count(DISTINCT c) as commits_with_refs,
           count(DISTINCT i) as issues_referenced
    """
    
    result = query_executor.execute(
        query_name="Commits with Jira References",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Commits with Jira References")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_commits_referencing_issues(query_executor, expectations, track_result):
    """Commits referencing Jira issues by issue type."""
    query = """
    MATCH (c:Commit)-[:REFERENCES]->(i:Issue)
    RETURN i.key as issue, i.type as type, count(c) as commits
    ORDER BY commits DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Commits Referencing Issues",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Commits Referencing Issues")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_multi_repository_contributors(query_executor, expectations, track_result):
    """People working across multiple repos."""
    query = """
    MATCH (p:Person)-[c:COLLABORATOR]->(r:Repository)
    WITH p, c.permission as perm, collect(r.name) as repos
    WHERE size(repos) > 1
    RETURN p.name, p.title, perm, repos, size(repos) as repo_count
    ORDER BY repo_count DESC
    """
    
    result = query_executor.execute(
        query_name="Multi-Repository Contributors",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Multi-Repository Contributors")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_hotspot_files(query_executor, expectations, track_result):
    """Files with most modifications."""
    query = """
    MATCH (f:File)<-[:MODIFIES]-(c:Commit)
    RETURN f.path as path, f.language as lang, count(c) as modifications
    ORDER BY modifications DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Hotspot Files",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Hotspot Files")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_test_vs_production_code(query_executor, expectations, track_result):
    """Test vs production code analysis."""
    query = """
    MATCH (f:File)<-[:MODIFIES]-(c:Commit)
    WITH f.is_test as is_test, 
         count(DISTINCT f) as file_count,
         count(c) as commit_count
    RETURN CASE WHEN is_test THEN 'Test Files' ELSE 'Production Files' END as type,
           file_count, commit_count
    """
    
    result = query_executor.execute(
        query_name="Test vs Production Code",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Test vs Production Code")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_code_churn(query_executor, expectations, track_result):
    """Files with most changes (additions + deletions)."""
    query = """
    MATCH (f:File)<-[m:MODIFIES]-(c:Commit)
    RETURN f.path as file, f.language as language,
           sum(m.additions) as total_additions,
           sum(m.deletions) as total_deletions,
           sum(m.additions + m.deletions) as total_churn,
           count(c) as num_commits
    ORDER BY total_churn DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Code Churn",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Code Churn")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_developer_activity_by_language(query_executor, expectations, track_result):
    """Developer activity by programming language."""
    query = """
    MATCH (p:Person)<-[:AUTHORED_BY]-(c:Commit)-[:MODIFIES]->(f:File)
    RETURN p.name as developer, f.language as language, 
           count(DISTINCT c) as commits, count(f) as files_touched
    ORDER BY commits DESC
    """
    
    result = query_executor.execute(
        query_name="Developer Activity by Language",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Developer Activity by Language")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_pr_velocity_by_repository(query_executor, expectations, track_result):
    """PR velocity and merge rate by repository."""
    query = """
    MATCH (pr:PullRequest)-[:TARGETS]->(b:Branch)-[:BRANCH_OF]->(r:Repository)
    RETURN r.name as repository,
           count(pr) as total_prs,
           sum(CASE WHEN pr.state = 'merged' THEN 1 ELSE 0 END) as merged,
           sum(CASE WHEN pr.state = 'open' THEN 1 ELSE 0 END) as open,
           round(sum(CASE WHEN pr.state = 'merged' THEN 1 ELSE 0 END) * 100.0 / count(pr), 1) as merge_rate
    ORDER BY total_prs DESC
    """
    
    result = query_executor.execute(
        query_name="PR Velocity by Repository",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("PR Velocity by Repository")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_top_pr_contributors(query_executor, expectations, track_result):
    """Top PR contributors by creation count."""
    query = """
    MATCH (pr:PullRequest)-[:CREATED_BY]->(p:Person)
    RETURN p.name as developer,
           p.title as title,
           count(pr) as prs_created,
           sum(CASE WHEN pr.state = 'merged' THEN 1 ELSE 0 END) as merged,
           sum(pr.additions) as total_additions,
           sum(pr.deletions) as total_deletions
    ORDER BY prs_created DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Top PR Contributors",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Top PR Contributors")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_most_active_reviewers(query_executor, expectations, track_result):
    """Most active code reviewers."""
    query = """
    MATCH (pr:PullRequest)-[:REVIEWED_BY]->(p:Person)
    RETURN p.name as reviewer,
           p.title as title,
           count(pr) as reviews_given,
           sum(CASE WHEN pr.state = 'merged' THEN 1 ELSE 0 END) as reviewed_and_merged
    ORDER BY reviews_given DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Most Active Reviewers",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Most Active Reviewers")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_pr_size_distribution(query_executor, expectations, track_result):
    """PR size distribution by commit count."""
    query = """
    MATCH (pr:PullRequest)
    WITH pr,
         CASE 
           WHEN pr.commits_count <= 3 THEN 'Small (1-3 commits)'
           WHEN pr.commits_count <= 8 THEN 'Medium (4-8 commits)'
           ELSE 'Large (9+ commits)'
         END as size_category
    RETURN size_category, count(pr) as pr_count
    ORDER BY pr_count DESC
    """
    
    result = query_executor.execute(
        query_name="PR Size Distribution",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("PR Size Distribution")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_cross_team_reviews(query_executor, expectations, track_result):
    """Cross-team code review collaboration."""
    query = """
    MATCH (pr:PullRequest)-[:CREATED_BY]->(author:Person)-[:MEMBER_OF]->(author_team:Team)
    MATCH (pr)-[:REVIEWED_BY]->(reviewer:Person)-[:MEMBER_OF]->(reviewer_team:Team)
    WHERE author_team <> reviewer_team
    RETURN author_team.name as author_team,
           reviewer_team.name as reviewer_team,
           count(pr) as cross_team_reviews
    ORDER BY cross_team_reviews DESC
    """
    
    result = query_executor.execute(
        query_name="Cross-Team Reviews",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("Cross-Team Reviews")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_pr_merge_time_analysis(query_executor, expectations, track_result):
    """Average time to merge PRs."""
    query = """
    MATCH (pr:PullRequest)
    WHERE pr.state = 'merged' AND pr.merged_at IS NOT NULL
    WITH pr, duration.between(pr.created_at, pr.merged_at) as merge_duration
    RETURN avg(merge_duration.days) as avg_days_to_merge,
           min(merge_duration.days) as min_days,
           max(merge_duration.days) as max_days
    """
    
    result = query_executor.execute(
        query_name="PR Merge Time Analysis",
        section="GitHub",
        query_text=query,
        expectation=expectations.get("PR Merge Time Analysis")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_prs_without_reviews(query_executor, expectations, track_result):
    """PRs without reviews - Data Quality check."""
    query = """
    MATCH (pr:PullRequest)
    WHERE NOT (pr)-[:REVIEWED_BY]->()
    RETURN pr.number, pr.title, pr.state, pr.created_at
    ORDER BY pr.created_at DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="PRs Without Reviews",
        section="GitHub - Data Quality",
        query_text=query,
        expectation=expectations.get("PRs Without Reviews")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"


def test_review_bottlenecks(query_executor, expectations, track_result):
    """Review requests not yet completed - Data Quality check."""
    query = """
    MATCH (pr:PullRequest)-[:REQUESTED_REVIEWER]->(p:Person)
    WHERE NOT (pr)-[:REVIEWED_BY]->(p)
    WITH p, count(pr) as pending_reviews
    RETURN p.name as reviewer, pending_reviews
    ORDER BY pending_reviews DESC
    LIMIT 10
    """
    
    result = query_executor.execute(
        query_name="Review Bottlenecks",
        section="GitHub - Data Quality",
        query_text=query,
        expectation=expectations.get("Review Bottlenecks")
    )
    
    track_result(result)
    assert result.status != "FAIL", f"Query failed: {result.error_message}"
