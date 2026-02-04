from modules.github.new_branch_handler import new_branch_handler
from modules.github.new_commit_handler import new_commit_handler
from modules.github.new_pull_request_handler import new_pull_request_handler
from modules.github.new_repo_handler import new_repo_handler
from modules.github.new_team_handler import new_team_handler
from modules.github.new_user_handler import new_user_handler
from modules.github.retry_with_backoff import retry_with_backoff

import os
from datetime import datetime, timedelta

from common.logger import logger, LogContext

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
        
        # Get bulk processing threshold from environment (default 100)
        bulk_threshold = int(os.getenv('BULK_PROCESSING_THRESHOLD', '100'))
        batch_size = int(os.getenv('COLLABORATOR_BATCH_SIZE', '50'))
        
        if len(collaborator_list) > bulk_threshold:
            # Use bulk processing for large numbers of collaborators
            logger.info(f"    Using bulk processing for {len(collaborator_list)} collaborators (threshold: {bulk_threshold})...")
            from modules.github.bulk_user_handler import bulk_user_handler
            bulk_user_handler(session, collaborator_list, repo_id, repo_created_at, batch_size)
        else:
            # Use individual processing for smaller numbers
            logger.info(f"    Processing {len(collaborator_list)} collaborators individually...")
            for collab in collaborator_list:
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
        branches = repo.get_branches()
        logger.info(f"    Found {branches.totalCount} branches...")
        for branch in branches:
            new_branch_handler(session, repo, branch, repo_id, repo.owner.login)
            # Track default branch ID for commit processing
            if branch.name == repo.default_branch:
                default_branch_id = f"branch_{repo.name}_{branch.name.replace('/', '_').replace('-', '_')}"
    except Exception as e:
        logger.info(f"    Warning: Could not fetch branches - {str(e)}")

    # Step 5: Process commits (only for default branch, within date limit)
    if default_branch_id:
        try:
            # Get date limit from environment (default 60 days)
            commit_days_limit = int(os.getenv('COMMIT_DAYS_LIMIT', '60'))
            since_date = datetime.now() - timedelta(days=commit_days_limit)

            logger.info(f"    Fetching commits from default branch '{repo.default_branch}' since {since_date.strftime('%Y-%m-%d')}...")

            # Fetch commits with retry logic
            commits = retry_with_backoff(
                lambda: list(repo.get_commits(sha=repo.default_branch, since=since_date))
            )

            logger.info(f"    Processing {len(commits)} commits...")

            commits_processed = 0
            commits_failed = 0

            for commit in commits:
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
        logger.info(f"    Warning: Default branch not found, skipping commit processing")

    # Step 6: Process pull requests (all states, within date limit)
    try:
        # Get date limit from environment (default 60 days)
        pr_days_limit = int(os.getenv('PULL_REQUEST_DAYS_LIMIT', '60'))
        since_date = datetime.now() - timedelta(days=pr_days_limit)

        logger.info(f"    Fetching pull requests since {since_date.strftime('%Y-%m-%d')}...")

        # Fetch all PRs (open, closed, merged) with retry logic
        # Note: PyGithub doesn't support 'since' parameter for PRs, so we'll fetch and filter
        all_prs = retry_with_backoff(
            lambda: list(repo.get_pulls(state='all', sort='updated', direction='desc'))
        )

        # Filter PRs by updated date
        recent_prs = [pr for pr in all_prs if pr.updated_at >= since_date]

        logger.info(f"    Processing {len(recent_prs)} pull requests...")

        prs_processed = 0
        prs_failed = 0

        for pr in recent_prs:
            if new_pull_request_handler(session, repo, pr, repo_id, repo.owner.login):
                prs_processed += 1
            else:
                prs_failed += 1

        logger.info(f"    ✓ Processed {prs_processed} pull requests")
        if prs_failed > 0:
            logger.info(f"    ✗ Failed/Skipped: {prs_failed} pull requests")

    except Exception as e:
        logger.info(f"    Warning: Could not fetch pull requests - {str(e)}")