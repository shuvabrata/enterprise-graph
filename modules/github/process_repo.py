from modules.github.new_branch_handler import new_branch_handler
from modules.github.new_commit_handler import new_commit_handler
from modules.github.new_pull_request_handler import new_pull_request_handler
from modules.github.new_repo_handler import new_repo_handler
from modules.github.new_team_handler import new_team_handler
from modules.github.new_user_handler import new_user_handler
from modules.github.retry_with_backoff import retry_with_backoff

import os
from datetime import datetime, timedelta, timezone

from common.logger import logger, LogContext


def get_collaborators_needing_refresh(session, collaborators, refresh_days=7):
    """Filter collaborators to only those needing refresh based on last_updated_at.
    
    Args:
        session: Neo4j session
        collaborators: List of GitHub collaborator objects
        refresh_days: Number of days before refreshing identity data (default 7)
        
    Returns:
        tuple: (collaborators_to_process, skip_count)
            - collaborators_to_process: List of collaborators that need processing
            - skip_count: Number of collaborators skipped due to recent update
    """
    if not collaborators:
        return [], 0
    
    # Extract usernames for batch query
    usernames = [c.login for c in collaborators]
    
    # Query Neo4j for IdentityMapping nodes with recent updates
    query = """
    UNWIND $usernames as username
    MATCH (i:IdentityMapping {provider: 'GitHub', username: username})
    WHERE i.last_updated_at IS NOT NULL
      AND i.last_updated_at >= datetime() - duration({days: $refresh_days})
    RETURN collect(i.username) as recent_usernames
    """
    
    result = session.run(query, usernames=usernames, refresh_days=refresh_days).single()
    recent_usernames = set(result['recent_usernames']) if result and result['recent_usernames'] else set()
    
    # Filter collaborators
    collaborators_to_process = [c for c in collaborators if c.login not in recent_usernames]
    skip_count = len(collaborators) - len(collaborators_to_process)
    
    return collaborators_to_process, skip_count

def get_last_synced_at(session, repo_id):
    """Get the last_synced_at timestamp from Repository node.
    
    Args:
        session: Neo4j session
        repo_id: Repository node ID
        
    Returns:
        datetime | None: Last sync timestamp or None if not found/never synced
    """
    query = """
    MATCH (r:Repository {id: $repo_id})
    RETURN r.last_synced_at as last_synced_at
    """
    result = session.run(query, repo_id=repo_id).single()
    
    if result and result['last_synced_at']:
        # Neo4j datetime object - convert to Python datetime
        return result['last_synced_at'].to_native()
    return None


def update_last_synced_at(session, repo_id):
    """Update the last_synced_at timestamp on Repository node.
    
    Args:
        session: Neo4j session
        repo_id: Repository node ID
    """
    query = """
    MATCH (r:Repository {id: $repo_id})
    SET r.last_synced_at = datetime($timestamp)
    RETURN r
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    session.run(query, repo_id=repo_id, timestamp=timestamp)
    logger.info(f"    ✓ Updated last_synced_at to {timestamp}")


def get_existing_branch_metadata(session, repo_id):
    """Get metadata for existing branches to detect changes.
    
    Args:
        session: Neo4j session
        repo_id: Repository node ID
        
    Returns:
        dict: Mapping of branch_name -> {last_commit_sha, is_deleted}
    """
    query = """
    MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository {id: $repo_id})
    RETURN b.name as name, 
           b.last_commit_sha as last_commit_sha,
           b.is_deleted as is_deleted
    """
    result = session.run(query, repo_id=repo_id)
    
    branch_metadata = {}
    for record in result:
        branch_metadata[record['name']] = {
            'last_commit_sha': record['last_commit_sha'],
            'is_deleted': record['is_deleted']
        }
    
    return branch_metadata


def get_fully_synced_commit_shas(session, repo_id):
    """Get list of commit SHAs that are already fully processed in Neo4j.
    
    Args:
        session: Neo4j session
        repo_id: Repository node ID
        
    Returns:
        set: Set of commit SHAs that have fully_synced=true
    """
    query = """
    MATCH (c:Commit)-[:PART_OF]->(b:Branch)-[:BRANCH_OF]->(r:Repository {id: $repo_id})
    WHERE c.fully_synced = true
    RETURN collect(c.sha) as processed_shas
    """
    result = session.run(query, repo_id=repo_id).single()
    
    if result and result['processed_shas']:
        return set(result['processed_shas'])
    return set()


def get_fully_synced_pr_numbers(session, repo_id):
    """Get list of PR numbers for closed/merged PRs already in Neo4j.
    
    Args:
        session: Neo4j session
        repo_id: Repository node ID
        
    Returns:
        set: Set of PR numbers for closed/merged PRs (won't change anymore)
    """
    # Optimization: Only retrieve PRs in terminal states (merged/closed)
    # These states are immutable - once a PR is merged or closed, it won't change anymore
    # This allows us to skip re-processing them on subsequent syncs
    query = """
    MATCH (pr:PullRequest)-[:TARGETS]->(b:Branch)-[:BRANCH_OF]->(r:Repository {id: $repo_id})
    WHERE pr.state IN ['merged', 'closed']
    RETURN collect(pr.number) as processed_pr_numbers
    """
    result = session.run(query, repo_id=repo_id).single()
    
    if result and result['processed_pr_numbers']:
        return set(result['processed_pr_numbers'])
    return set()


def process_repo(repo, session):
    with LogContext(request_id=repo.full_name):
        return process_repo_(repo, session)

def process_repo_(repo, session):
    """Process repository: create repo node, collaborators, teams, branches, and commits in Neo4j."""
    # Step 1: Create Repository node FIRST
    repo_id, repo_created_at = new_repo_handler(session, repo)

    # If repo creation failed, skip collaborators/teams
    if repo_id is None:
        logger.info(f"    Warning: Skipping collaborators/teams due to repo creation failure")
        raise Exception("Repository node creation failed")

    # Step 2: Process collaborators (creates Person, IdentityMapping, and COLLABORATOR relationships)
    try:
        collaborators = repo.get_collaborators()
        logger.info(f"    Found {collaborators.totalCount} collaborators...")
        
        # Convert to list for bulk processing
        collaborator_list = [collab for collab in collaborators if collab.type == 'User']
        
        # Optimization: Filter collaborators to only those needing refresh
        refresh_days = int(os.getenv('IDENTITY_REFRESH_DAYS', '7'))
        collaborators_to_process, skip_count = get_collaborators_needing_refresh(
            session, collaborator_list, refresh_days
        )
        
        if skip_count > 0:
            logger.info(f"    Skipping {skip_count} collaborators (updated within last {refresh_days} days)")
        
        if not collaborators_to_process:
            logger.info(f"    All collaborators are up-to-date, skipping processing")
        else:
            # Get bulk processing threshold from environment (default 100)
            bulk_threshold = int(os.getenv('BULK_PROCESSING_THRESHOLD', '100'))
            batch_size = int(os.getenv('COLLABORATOR_BATCH_SIZE', '50'))
            
            if len(collaborators_to_process) > bulk_threshold:
                # Use bulk processing for large numbers of collaborators
                logger.info(f"    Using bulk processing for {len(collaborators_to_process)} collaborators (threshold: {bulk_threshold})...")
                from modules.github.bulk_user_handler import bulk_user_handler
                bulk_user_handler(session, collaborators_to_process, repo_id, repo_created_at, batch_size)
            else:
                # Use individual processing for smaller numbers
                logger.info(f"    Processing {len(collaborators_to_process)} collaborators individually...")
                for collab in collaborators_to_process:
                    new_user_handler(session, collab, repo_id, repo_created_at)
    except Exception as e:
        # Collaborators might not be accessible for certain repos
        logger.info(f"    Warning: Could not fetch collaborators - {str(e)}")

    # Step 3: Fetch teams (only available for organization repositories)
    try:
        teams = repo.get_teams()
        for team in teams:
            # Create Team node and COLLABORATOR relationship
            new_team_handler(session, team, repo_id, repo_created_at)
    except Exception as e:
        # Teams might not be accessible for personal repos or due to permissions
        logger.info(f"    Warning: Could not fetch teams - {str(e)}")

    # Step 4: Process branches (creates Branch nodes and BRANCH_OF relationships)
    default_branch_id = None
    try:
        branches = list(repo.get_branches())
        logger.info(f"    Found {len(branches)} branches...")
        
        # Optimization: Get existing branch metadata to skip unchanged branches
        existing_branches = get_existing_branch_metadata(session, repo_id)
        
        branches_to_process = []
        for branch in branches:
            existing = existing_branches.get(branch.name)
            
            # Process if: new branch OR last_commit_sha changed OR was marked deleted
            if not existing or existing['last_commit_sha'] != branch.commit.sha or existing['is_deleted']:
                branches_to_process.append(branch)
        
        skip_count = len(branches) - len(branches_to_process)
        if skip_count > 0:
            logger.info(f"    Processing {len(branches_to_process)} branches, skipping {skip_count} unchanged...")
        else:
            logger.info(f"    Processing {len(branches_to_process)} branches...")
        
        for branch in branches_to_process:
            new_branch_handler(session, repo, branch, repo_id, repo.owner.login)
            # Track default branch ID for commit processing
            if branch.name == repo.default_branch:
                default_branch_id = f"branch_{repo.name}_{branch.name.replace('/', '_').replace('-', '_')}"
    except Exception as e:
        logger.info(f"    Warning: Could not fetch branches - {str(e)}")

    # Step 5: Process commits (only for default branch, incremental sync)
    if default_branch_id:
        try:
            # Check last sync timestamp for incremental updates
            last_synced = get_last_synced_at(session, repo_id)
            
            if last_synced:
                # Use last sync timestamp for incremental updates
                since_date = last_synced
                logger.info(f"    Incremental sync: Fetching commits since last sync ({since_date.strftime('%Y-%m-%d %H:%M:%S')}...")
            else:
                # First run: use configurable lookback window
                commit_days_limit = int(os.getenv('COMMIT_DAYS_LIMIT', '60'))
                since_date = datetime.now() - timedelta(days=commit_days_limit)
                logger.info(f"    First sync: Fetching commits from default branch '{repo.default_branch}' (last {commit_days_limit} days)...")

            # Fetch commits with retry logic
            commits = retry_with_backoff(
                lambda: list(repo.get_commits(sha=repo.default_branch, since=since_date))
            )

            # Step 5 optimization: Get already-processed commit SHAs from Neo4j
            existing_shas = get_fully_synced_commit_shas(session, repo_id)
            
            # Filter out commits that are already fully processed
            commits_to_process = [c for c in commits if c.sha not in existing_shas]
            
            if existing_shas:
                logger.info(f"    Found {len(commits)} commits from GitHub, {len(existing_shas)} already processed, {len(commits_to_process)} new to process")
            else:
                logger.info(f"    Processing {len(commits_to_process)} commits...")

            commits_processed = 0
            commits_failed = 0

            for commit in commits_to_process:
                if new_commit_handler(session, repo.name, commit, default_branch_id, repo.owner.login, repo.default_branch):
                    commits_processed += 1
                else:
                    commits_failed += 1

            logger.info(f"    ✓ Processed {commits_processed} commits")
            if commits_failed > 0:
                logger.info(f"    ✗ Failed: {commits_failed} commits")

        except Exception as e:
            logger.info(f"    Warning: Could not fetch commits - {str(e)}")
    else:
        logger.info(f"    Warning: Default branch not encountered in this scan, skipping commit processing")

    # Step 6: Process pull requests (all states, incremental sync)
    try:
        # Check last sync timestamp for incremental updates
        last_synced = get_last_synced_at(session, repo_id)
        
        if last_synced:
            # Use last sync timestamp for incremental updates
            # Convert to timezone-aware datetime if needed
            since_date = last_synced if last_synced.tzinfo else last_synced.replace(tzinfo=timezone.utc)
            logger.info(f"    Incremental sync: Fetching PRs updated since last sync ({since_date.strftime('%Y-%m-%d %H:%M:%S')}...")
        else:
            # First run: use configurable lookback window
            pr_days_limit = int(os.getenv('PULL_REQUEST_DAYS_LIMIT', '60'))
            since_date = datetime.now(timezone.utc) - timedelta(days=pr_days_limit)
            logger.info(f"    First sync: Fetching pull requests (last {pr_days_limit} days)...")

        # Fetch all PRs (open, closed, merged) with retry logic
        # Note: PyGithub doesn't support 'since' parameter for PRs, so we'll fetch and filter
        all_prs = retry_with_backoff(
            lambda: list(repo.get_pulls(state='all', sort='updated', direction='desc'))
        )

        # Filter PRs by updated date (incremental sync)
        recent_prs = [pr for pr in all_prs if pr.updated_at >= since_date]

        # Step 5 optimization: Get already-processed closed/merged PR numbers from Neo4j
        existing_pr_numbers = get_fully_synced_pr_numbers(session, repo_id)
        
        # Filter logic:
        # - Always process open PRs (they can be updated with new commits, reviews, labels, etc.)
        # - Skip closed/merged PRs already in Neo4j (immutable - won't change anymore)
        # This avoids redundant API calls and database writes for terminal-state PRs
        prs_to_process = [pr for pr in recent_prs if pr.number not in existing_pr_numbers or pr.state == 'open']
        
        if existing_pr_numbers:
            logger.info(f"    Found {len(recent_prs)} recent PRs, {len(existing_pr_numbers)} already processed (closed/merged), {len(prs_to_process)} to process")
        else:
            logger.info(f"    Processing {len(prs_to_process)} pull requests...")

        prs_processed = 0
        prs_failed = 0

        for pr in prs_to_process:
            if new_pull_request_handler(session, repo, pr, repo_id, repo.owner.login):
                prs_processed += 1
            else:
                prs_failed += 1

        logger.info(f"    ✓ Processed {prs_processed} pull requests")
        if prs_failed > 0:
            logger.info(f"    ✗ Failed/Skipped: {prs_failed} pull requests")

    except Exception as e:
        logger.info(f"    Warning: Could not fetch pull requests - {str(e)}")
    
    # Step 7: Update last_synced_at timestamp after successful processing
    try:
        update_last_synced_at(session, repo_id)
    except Exception as e:
        logger.info(f"    Warning: Could not update last_synced_at - {str(e)}")