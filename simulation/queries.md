# Graph Database Query Reference

A comprehensive collection of Cypher queries organized by layer. This document evolves as the graph schema grows.

---

## Layer 1: People & Teams Foundation

### View Teams and Members
```cypher
// View all teams and their members
MATCH (t:Team)<-[:MEMBER_OF]-(p:Person)
RETURN t.name, collect(p.name) as members
```

### Organizational Hierarchy
```cypher
// View organizational hierarchy
MATCH (p:Person)-[:REPORTS_TO]->(m:Person)
RETURN p, m
```

### Identity Mappings
```cypher
// Find all identity mappings for a person
MATCH (p:Person {name: "Add a valid name here"})<-[:MAPS_TO]-(i:IdentityMapping)
RETURN p.name, i.provider, i.username, i.email
```

### Team Distribution
```cypher
// View team sizes and focus areas
MATCH (t:Team)<-[:MEMBER_OF]-(p:Person)
RETURN t.name as team, t.focus_area, count(p) as team_size
ORDER BY team_size DESC
```

---

## Layer 2: Jira Initiatives

### Initiatives with Assignees
```cypher
// View all initiatives with assignees and reporters
MATCH (i:Initiative)-[:ASSIGNED_TO]->(assignee:Person),
      (i)-[:REPORTED_BY]->(reporter:Person)
RETURN i.key, i.summary, 
       assignee.name as assignee, assignee.title as assignee_title,
       reporter.name as reporter, reporter.title as reporter_title,
       i.status
```

### Project Hierarchy
```cypher
// Show project hierarchy
MATCH (p:Project)<-[:PART_OF]-(i:Initiative)
RETURN p.name, collect(i.summary) as initiatives
```

### Initiative Timeline
```cypher
// Initiative timeline
MATCH (i:Initiative)
RETURN i.summary, i.start_date, i.due_date, i.priority
ORDER BY i.start_date
```

---

## Layer 3: Jira Epics

### Epics with Owners and Teams
```cypher
// View all epics with owners and teams
MATCH (e:Epic)-[:ASSIGNED_TO]->(owner:Person)
MATCH (e)-[:TEAM]->(team:Team)
MATCH (e)-[:PART_OF]->(i:Initiative)
RETURN e.key, e.summary, 
       owner.name as owner, owner.title as owner_title,
       team.name as team,
       i.key as initiative,
       e.status, e.priority
ORDER BY i.key, e.key
```

### Epics by Initiative
```cypher
// Epics by initiative
MATCH (e:Epic)-[:PART_OF]->(i:Initiative)
RETURN i.key, i.summary, collect(e.key) as epics
ORDER BY i.key
```

### Epic Ownership Distribution
```cypher
// Epic ownership distribution
MATCH (e:Epic)-[:ASSIGNED_TO]->(p:Person)
RETURN p.name, p.role, count(e) as epic_count
ORDER BY epic_count DESC
```

### Epics by Team
```cypher
// Epics by team
MATCH (e:Epic)-[:TEAM]->(t:Team)
RETURN t.name, count(e) as epic_count, collect(e.key) as epics
ORDER BY epic_count DESC
```

### Epic Timeline
```cypher
// Epic timeline
MATCH (e:Epic)
RETURN e.key, e.summary, e.start_date, e.due_date, e.status
ORDER BY e.start_date, e.key
```

---

## Layer 4: Jira Stories, Bugs, Tasks & Sprints

### Sprint Burndown Data
```cypher
// Sprint burndown data
MATCH (s:Sprint)<-[:IN_SPRINT]-(i:Issue)
RETURN s.name, 
       sum(i.story_points) as total_points,
       sum(CASE WHEN i.status = 'Done' THEN i.story_points ELSE 0 END) as completed_points,
       count(i) as issue_count
ORDER BY s.name
```

### Blocked Work
```cypher
// Find blocked work
MATCH (blocked:Issue {status: 'Blocked'})-[:DEPENDS_ON]->(blocker:Issue)
RETURN blocked.key, blocked.summary, 
       collect(blocker.key) as blocking_issues
```

### Bug Distribution by Epic
```cypher
// Bug distribution by epic
MATCH (bug:Issue {type: 'Bug'})-[:PART_OF]->(e:Epic)
RETURN e.key, e.summary, count(bug) as bug_count
ORDER BY bug_count DESC
```

### Work by Person
```cypher
// Work by person
MATCH (i:Issue)-[:ASSIGNED_TO]->(p:Person)
RETURN p.name, p.title, 
       count(i) as total_issues,
       sum(i.story_points) as total_points
ORDER BY total_points DESC
LIMIT 10
```

### Unassigned Critical Issues
```cypher
// Unassigned critical issues
MATCH (i:Issue)
WHERE i.priority = 'Critical' AND NOT exists((i)-[:ASSIGNED_TO]->())
RETURN i.key, i.summary, i.status
```

### Bugs Related to Stories
```cypher
// Bugs related to stories
MATCH (bug:Issue {type: 'Bug'})-[:RELATES_TO]->(story:Issue {type: 'Story'})
RETURN bug.key, story.key as story, bug.summary
```

### Dependencies and Blockers
```cypher
// Dependencies and blockers
MATCH (i:Issue)-[:BLOCKS]->(blocked:Issue)
RETURN i.key, i.summary, 
       collect(blocked.key) as blocks_issues
```

---

## Layer 5: Git Repositories

### Repository Ownership
```cypher
// View all repositories with their owning teams (WRITE access)
MATCH (t:Team)-[c:COLLABORATOR {permission: 'WRITE'}]->(r:Repository)
RETURN t.name, r.name, r.language
```

### Repository Maintainers
```cypher
// Find maintainers (people with WRITE access)
MATCH (p:Person)-[c:COLLABORATOR {permission: 'WRITE'}]->(r:Repository)
RETURN r.name, collect(p.name) as maintainers
ORDER BY r.name
```

### Cross-Team Collaborations
```cypher
// Cross-team collaborations (teams with READ access)
MATCH (t:Team)-[c:COLLABORATOR {permission: 'READ'}]->(r:Repository)
RETURN r.name, collect(t.name) as read_access_teams
ORDER BY r.name
```

### Multi-Repository Contributors
```cypher
// People working across multiple repos
MATCH (p:Person)-[c:COLLABORATOR]->(r:Repository)
WITH p, c.permission as perm, collect(r.name) as repos
WHERE size(repos) > 1
RETURN p.name, p.title, perm, repos, size(repos) as repo_count
ORDER BY repo_count DESC
```

---

## Layer 6: Git Branches

### Branches by Repository
```cypher
// View all branches by repository
MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository)
RETURN r.name, collect(b.name) as branches
ORDER BY r.name
```

### Active Feature Branches
```cypher
// Find active feature branches
MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository)
WHERE NOT b.is_default AND NOT b.is_deleted
RETURN r.name, b.name, b.last_commit_timestamp
ORDER BY b.last_commit_timestamp DESC
```

### Stale Branches
```cypher
// Find stale branches (candidates for cleanup)
MATCH (b:Branch)
WHERE b.last_commit_timestamp < datetime() - duration({days: 30})
  AND NOT b.is_default
  AND NOT b.is_deleted
RETURN b.name, b.last_commit_timestamp,
       duration.between(b.last_commit_timestamp, datetime()).days as days_old
ORDER BY days_old DESC
```

### Branches by Epic
```cypher
// Branches linked to specific epic
MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository)
WHERE b.name CONTAINS 'PLAT-1'
RETURN r.name, b.name, b.is_deleted
```

### Protected Branches
```cypher
// Protected branches across all repos
MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository)
WHERE b.is_protected
RETURN r.name, collect(b.name) as protected_branches
```

---

## Layer 7: Git Commits & Files

### Top Contributors
```cypher
// Top 10 contributors by commit count
MATCH (p:Person)<-[:AUTHORED_BY]-(c:Commit)
RETURN p.name as name, p.title as title, count(c) as commits
ORDER BY commits DESC
LIMIT 10
```

### Commits per Repository
```cypher
// Commits per repository
MATCH (c:Commit)-[:PART_OF]->(b:Branch)-[:BRANCH_OF]->(r:Repository)
WHERE b.is_default = true
RETURN r.name as repo, count(c) as commits
ORDER BY commits DESC
```

### Hotspot Files
```cypher
// Hotspot files (most modified)
MATCH (f:File)<-[:MODIFIES]-(c:Commit)
RETURN f.path as path, f.language as lang, count(c) as modifications
ORDER BY modifications DESC
LIMIT 10
```

### Commits Referencing Issues
```cypher
// Commits referencing Jira issues
MATCH (c:Commit)-[:REFERENCES]->(i:Issue)
RETURN i.key as issue, i.type as type, count(c) as commits
ORDER BY commits DESC
LIMIT 10
```

### Developer Activity by Language
```cypher
// Developer activity by language
MATCH (p:Person)<-[:AUTHORED_BY]-(c:Commit)-[:MODIFIES]->(f:File)
RETURN p.name as developer, f.language as language, 
       count(DISTINCT c) as commits, count(f) as files_touched
ORDER BY commits DESC
```

### Code Churn
```cypher
// Code churn (files with most changes)
MATCH (f:File)<-[m:MODIFIES]-(c:Commit)
RETURN f.path as file, f.language as language,
       sum(m.additions) as total_additions,
       sum(m.deletions) as total_deletions,
       sum(m.additions + m.deletions) as total_churn,
       count(c) as num_commits
ORDER BY total_churn DESC
LIMIT 10
```

### Test vs Production Code
```cypher
// Test vs production code analysis
MATCH (f:File)<-[:MODIFIES]-(c:Commit)
WITH f.is_test as is_test, 
     count(DISTINCT f) as file_count,
     count(c) as commit_count
RETURN CASE WHEN is_test THEN 'Test Files' ELSE 'Production Files' END as type,
       file_count, commit_count
```

### Commits with Jira References
```cypher
// Commits with Jira references
MATCH (c:Commit)-[:REFERENCES]->(i:Issue)
RETURN count(DISTINCT c) as commits_with_refs,
       count(DISTINCT i) as issues_referenced
```

---

## Layer 8: Pull Requests

### PR Velocity by Repository
```cypher
// PR velocity by repository
MATCH (pr:PullRequest)-[:TARGETS]->(b:Branch)-[:BRANCH_OF]->(r:Repository)
RETURN r.name as repository,
       count(pr) as total_prs,
       sum(CASE WHEN pr.state = 'merged' THEN 1 ELSE 0 END) as merged,
       sum(CASE WHEN pr.state = 'open' THEN 1 ELSE 0 END) as open,
       round(sum(CASE WHEN pr.state = 'merged' THEN 1 ELSE 0 END) * 100.0 / count(pr), 1) as merge_rate
ORDER BY total_prs DESC
```

### Top PR Contributors
```cypher
// Top PR contributors
MATCH (pr:PullRequest)-[:CREATED_BY]->(p:Person)
RETURN p.name as developer,
       p.title as title,
       count(pr) as prs_created,
       sum(CASE WHEN pr.state = 'merged' THEN 1 ELSE 0 END) as merged,
       sum(pr.additions) as total_additions,
       sum(pr.deletions) as total_deletions
ORDER BY prs_created DESC
LIMIT 10
```

### Most Active Reviewers
```cypher
// Most active reviewers
MATCH (pr:PullRequest)-[:REVIEWED_BY]->(p:Person)
RETURN p.name as reviewer,
       p.title as title,
       count(pr) as reviews_given,
       sum(CASE WHEN pr.state = 'merged' THEN 1 ELSE 0 END) as reviewed_and_merged
ORDER BY reviews_given DESC
LIMIT 10
```

### Review Bottlenecks
```cypher
// Review bottlenecks (requested but not reviewed)
MATCH (pr:PullRequest)-[:REQUESTED_REVIEWER]->(p:Person)
WHERE NOT (pr)-[:REVIEWED_BY]->(p)
WITH p, count(pr) as pending_reviews
RETURN p.name as reviewer, pending_reviews
ORDER BY pending_reviews DESC
LIMIT 10
```

### PR Size Distribution
```cypher
// PR size distribution
MATCH (pr:PullRequest)
WITH pr,
     CASE 
       WHEN pr.commits_count <= 3 THEN 'Small (1-3 commits)'
       WHEN pr.commits_count <= 8 THEN 'Medium (4-8 commits)'
       ELSE 'Large (9+ commits)'
     END as size_category
RETURN size_category, count(pr) as pr_count
ORDER BY pr_count DESC
```

### PRs Without Reviews
```cypher
// PRs without reviews (potential quality risk)
MATCH (pr:PullRequest)
WHERE NOT (pr)-[:REVIEWED_BY]->()
RETURN pr.number, pr.title, pr.state, pr.created_at
ORDER BY pr.created_at DESC
```

### Cross-Team Reviews
```cypher
// Cross-team code reviews
MATCH (pr:PullRequest)-[:CREATED_BY]->(author:Person)-[:MEMBER_OF]->(author_team:Team)
MATCH (pr)-[:REVIEWED_BY]->(reviewer:Person)-[:MEMBER_OF]->(reviewer_team:Team)
WHERE author_team <> reviewer_team
RETURN author_team.name as author_team,
       reviewer_team.name as reviewer_team,
       count(pr) as cross_team_reviews
ORDER BY cross_team_reviews DESC
```

### PR Merge Time Analysis
```cypher
// PR merge time analysis
MATCH (pr:PullRequest)
WHERE pr.state = 'merged' AND pr.merged_at IS NOT NULL
WITH pr, duration.between(pr.created_at, pr.merged_at) as merge_duration
RETURN avg(merge_duration.days) as avg_days_to_merge,
       min(merge_duration.days) as min_days,
       max(merge_duration.days) as max_days
```

---

## Cross-Layer Analytics

### End-to-End Traceability
```cypher
// Initiative to PR traceability
MATCH (i:Initiative)<-[:PART_OF]-(e:Epic)<-[:PART_OF]-(issue:Issue)
      <-[:REFERENCES]-(c:Commit)<-[:INCLUDES]-(pr:PullRequest)
RETURN i.key as initiative,
       e.key as epic,
       issue.key as jira_issue,
       pr.number as pr_number,
       pr.state as pr_state
LIMIT 10
```

### Developer Impact Analysis
```cypher
// Developer impact: PRs, commits, and issues
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
```

### Team Workload Analysis
```cypher
// Team workload across all work streams
MATCH (t:Team)<-[:MEMBER_OF]-(p:Person)
OPTIONAL MATCH (p)<-[:ASSIGNED_TO]-(epic:Epic)
OPTIONAL MATCH (p)<-[:ASSIGNED_TO]-(issue:Issue)
OPTIONAL MATCH (p)<-[:AUTHORED_BY]-(commit:Commit)
OPTIONAL MATCH (p)<-[:CREATED_BY]-(pr:PullRequest)
RETURN t.name as team,
       count(DISTINCT p) as team_size,
       count(DISTINCT epic) as epics,
       count(DISTINCT issue) as issues,
       count(DISTINCT commit) as commits,
       count(DISTINCT pr) as prs
ORDER BY team_size DESC
```

### Repository Activity Heatmap
```cypher
// Repository activity across all dimensions
MATCH (r:Repository)
OPTIONAL MATCH (r)<-[:BRANCH_OF]-(b:Branch)<-[:PART_OF]-(c:Commit)
OPTIONAL MATCH (r)<-[:BRANCH_OF]-(target:Branch)<-[:TARGETS]-(pr:PullRequest)
RETURN r.name as repository,
       r.language,
       count(DISTINCT b) as branches,
       count(DISTINCT c) as commits,
       count(DISTINCT pr) as pull_requests
ORDER BY commits DESC
```

### Code Review Collaboration Network
```cypher
// Who reviews whose code
MATCH (author:Person)<-[:CREATED_BY]-(pr:PullRequest)-[:REVIEWED_BY]->(reviewer:Person)
WHERE author <> reviewer
RETURN author.name as author,
       reviewer.name as reviewer,
       count(pr) as reviews
ORDER BY reviews DESC
LIMIT 20
```

### Sprint Delivery Metrics
```cypher
// Sprint delivery with linked commits and PRs
MATCH (s:Sprint)<-[:IN_SPRINT]-(issue:Issue)
OPTIONAL MATCH (issue)<-[:REFERENCES]-(commit:Commit)
OPTIONAL MATCH (commit)<-[:INCLUDES]-(pr:PullRequest {state: 'merged'})
RETURN s.name as sprint,
       count(DISTINCT issue) as total_issues,
       sum(CASE WHEN issue.status = 'Done' THEN 1 ELSE 0 END) as completed_issues,
       count(DISTINCT commit) as commits,
       count(DISTINCT pr) as merged_prs
ORDER BY s.name
```

### Work Item to Code Linkage
```cypher
// How many work items have associated code
MATCH (issue:Issue)
OPTIONAL MATCH (issue)<-[:REFERENCES]-(commit:Commit)
WITH issue.type as issue_type,
     count(issue) as total,
     count(DISTINCT commit) as with_commits
RETURN issue_type,
       total,
       with_commits,
       round(with_commits * 100.0 / total, 1) as percentage_with_code
```

---

## Schema Inspection Queries

### View All Node Types
```cypher
// Count all nodes by type
MATCH (n) 
RETURN labels(n)[0] as type, count(*) as count
ORDER BY count DESC
```

### View All Relationship Types
```cypher
// Count all relationships by type
MATCH ()-[r]->()
RETURN type(r) as relationship, count(*) as count
ORDER BY count DESC
```

### Schema Visualization
```cypher
// Visual schema (shows nodes and relationships)
CALL db.schema.visualization()
```

### Detailed Schema with Properties
```cypher
// Detailed schema with properties and data types
CALL db.schema.nodeTypeProperties()
```

### Sample Node Properties
```cypher
// See actual properties for a specific node type
MATCH (n:Person) 
RETURN properties(n) 
LIMIT 1
```
