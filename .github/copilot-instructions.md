# Enterprise Graph - AI Agent Instructions

## Project Overview

A Neo4j-based graph analytics platform that integrates enterprise data from GitHub, Jira, and organizational structures to surface insights about resource allocation, progress tracking, and team efficiency. The graph model uses bidirectional relationships to simplify AI-powered query generation.

## Important focus
The focus is a lot on relationships between entities (people, teams, repos, issues, commits) rather than just the entities themselves. The bidirectional relationship strategy is key to simplifying queries for AI agents. The goal is to be able to get interesting insights by traversing relationships in either direction without worrying about relationship names. Therefore the focus on getting metadata about nodes and relationships is more important than fetching data like source code, Jira description, etc.

## Architecture & Data Model

### Dataclass-Driven Model ([db/models.py](../db/models.py))
- All entities are Python `@dataclass` objects (Person, Team, Repository, Commit, etc.)
- Each has `to_neo4j_properties()` method that converts to dict for Neo4j
- User relationships (assignee, reporter, author) are **NOT stored in dataclasses** - extract separately and create as `Relationship` objects
- Use `merge_<entity>()` functions (e.g., `merge_person()`, `merge_commit()`) - these are idempotent MERGE operations

### Bidirectional Relationship Strategy ([design/RELATIONSHIPS_DESIGN.md](../design/RELATIONSHIPS_DESIGN.md))
**Key Pattern**: Same relationship name works in BOTH directions for symmetric concepts:
- `ASSIGNED_TO` works both ways: `(issue)-[:ASSIGNED_TO]->(person)` AND `(person)-[:ASSIGNED_TO]->(issue)`
- Simplifies Cypher queries - AI only needs to learn ONE name per relationship type
- **Exception**: Hierarchical relationships use different names (`PART_OF` vs `CONTAINS`, `REPORTS_TO` vs `MANAGES`)

Common bidirectional relationships: `ASSIGNED_TO`, `MEMBER_OF`, `COLLABORATOR`, `AUTHORED_BY`, `MODIFIES`, `REVIEWED_BY`, `REFERENCES`

### Identity Resolution Pattern ([common/identity_resolver.py](../common/identity_resolver.py))
**Email-as-Master-Key**: Multiple external identities (GitHub, Jira) map to single Person nodes via email.
```python
from common.identity_resolver import get_or_create_person

person_id, is_new = get_or_create_person(
    session, 
    email="alice@company.com",  # Canonical identifier
    name="Alice Smith",
    provider="github",
    external_id="alice"
)
# Returns: ("person_alice@company.com", True/False)
```
- Creates `IdentityMapping` nodes pointing to Person via `MAPS_TO` relationships
- Falls back to provider-specific IDs when email is unavailable

## Development Workflows

### Environment Setup
```bash
# Neo4j via Docker (uses .env for credentials)
docker compose up -d

# Python environment (3.14+)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Environment Variables** (create `.env` from `.env.example`):
- `NEO4J_URI=bolt://localhost:7687`
- `NEO4J_USERNAME=neo4j`
- `NEO4J_PASSWORD=<your_password>`


### Working with Real Data Sources
Module structure: `modules/github/main.py` and `modules/jira/main.py`
- Config: `.config.json` (not in git) defines repos/projects to fetch
- Pattern: Fetch from API → Transform to dataclass → Merge to Neo4j
- Uses retry/backoff for API calls ([modules/github/retry_with_backoff.py](../modules/github/retry_with_backoff.py))

## Code Patterns & Conventions

### Creating Nodes with Relationships
```python
from db.models import Issue, Relationship, merge_issue

issue = Issue(
    id="issue_proj_123",
    key="PROJ-123",
    type="Story",
    summary="Add authentication",
    # ... other fields, but NO assignee/reporter/epic_id
)

# Extract relationships separately
relationships = [
    Relationship(
        type="PART_OF",
        from_id=issue.id,
        to_id="epic_auth",  # Direct reference to Epic node ID
        from_type="Issue",
        to_type="Epic"
    ),
    Relationship(
        type="ASSIGNED_TO",
        from_id=issue.id,
        to_id="person_alice@company.com",  # Direct reference to Person node ID
        from_type="Issue",
        to_type="Person"
    )
]

merge_issue(session, issue, relationships=relationships)
```

### Logging ([common/logger.py](../common/logger.py))
- Supports JSON and TEXT formats (set `LOG_FORMAT` env var)
- Unicode symbols for log levels: ⚪ DEBUG, 🔵 INFO, 🟡 WARNING, 🔴 ERROR
- Contextual logging with `project_id`, `user_id`, `request_id` via context vars

### Database Constraints & Indexes
- **Constraints**: Created via `create_constraints(session)` - ensures unique IDs for all entity types
- **Indexes**: 87 indexes across 7 priority levels ([design/INDEX_STRATEGY.md](../design/INDEX_STRATEGY.md))
  - Priority 1: Lookup fields (name, email, key)
  - Priority 2: Status/state filters
  - Priority 3: Timestamps
  - Run `python scripts/create_indexes.py` after data load

## Design Documentation

- **[design/high-level-design.md](../design/high-level-design.md)**: Complete vision, use cases, analytical queries
- **[design/RELATIONSHIPS_DESIGN.md](../design/RELATIONSHIPS_DESIGN.md)**: Bidirectional relationship rationale
- **[design/INDEX_STRATEGY.md](../design/INDEX_STRATEGY.md)**: Index priority levels and query optimization
- **[simulation/graph-simulation.md](../simulation/graph-simulation.md)**: Simulation build plan and validation queries

## Common Tasks

**Adding a new entity type**:
1. Add `@dataclass` to [db/models.py](../db/models.py) with `to_neo4j_properties()` method
2. Create `merge_<entity>()` function following existing patterns
3. Add constraint to `create_constraints()` for the new entity type
4. Update relevant simulation `generate_data.py` and `load_to_neo4j.py` scripts

**Querying the graph**: Neo4j Browser at `http://localhost:7474`
- See [simulation/queries.md](../simulation/queries.md) for example Cypher queries
- Bidirectional relationships simplify traversal - don't worry about direction

**Debugging data loading**:
- Check logs (colored terminal output or JSON files in `LOG_DIR`)
- Verify constraints: `SHOW CONSTRAINTS` in Neo4j Browser
- Count nodes: `MATCH (n) RETURN labels(n), count(*) GROUP BY labels(n)`
