from db.models import Branch, Relationship, merge_branch, merge_relationship
from common.logger import logger

def get_branch_created_at(repo, branch_name):
    """Get the creation timestamp of a branch using the first commit on that branch.
    
    Args:
        repo: GitHub repository object
        branch_name: Name of the branch
        
    Returns:
        str: ISO format datetime string of the first commit, or None if not found
    """
    try:
        logger.debug(f"        Determining creation time for branch: {branch_name}")
        # Get commits on this branch
        commits = repo.get_commits(sha=branch_name)
        
        # Get the first (oldest) commit by going through all commits
        # Note: GitHub API returns commits in reverse chronological order
        first_commit = None
        commit_count = 0
        for commit in commits:
            first_commit = commit
            commit_count += 1
        
        logger.debug(f"        Found {commit_count} commits on branch {branch_name}")
        
        if first_commit and first_commit.commit.author.date:
            created_at = first_commit.commit.author.date.isoformat()
            logger.debug(f"        Branch creation time: {created_at}")
            return created_at
        
        logger.debug(f"        Could not determine branch creation time")
        return None
    except Exception as e:
        logger.info(f"        Warning: Could not determine branch creation time - {str(e)}")
        logger.exception(e)
        logger.debug(f"        Branch creation time exception for {branch_name}", exc_info=True)
        return None



def new_branch_handler(session, repo, branch, repo_id, repo_owner=None):
    """Handle a branch by creating Branch node and BRANCH_OF relationship.

    Args:
        session: Neo4j session
        repo: GitHub repository object (for fetching commit history)
        branch: GitHub branch object
        repo_id: Repository ID to create relationship with
        repo_owner: GitHub repository owner (optional, for URL generation)
    """
    try:
        # Get branch properties
        branch_name = branch.name
        logger.info(f"      Processing branch: {branch_name}")
        
        is_default = (branch_name == repo.default_branch)
        is_protected = branch.protected
        logger.debug(f"        Branch properties: default={is_default}, protected={is_protected}")

        # Get last commit info
        last_commit = branch.commit
        last_commit_sha = last_commit.sha
        last_commit_timestamp = last_commit.commit.author.date.isoformat() if last_commit.commit.author.date else None
        logger.debug(f"        Last commit: {last_commit_sha[:8]}, timestamp: {last_commit_timestamp}")

        # Get branch creation timestamp (first commit on this branch)
        created_at = get_branch_created_at(repo, branch_name)

        # If we couldn't get created_at, use last_commit_timestamp as fallback
        if not created_at:
            created_at = last_commit_timestamp
            logger.debug(f"        Using last commit timestamp as creation fallback: {created_at}")
        
        # Generate GitHub URL if owner is provided
        github_url = None
        if repo_owner:
            github_url = f"https://github.com/{repo_owner}/{repo.name}/tree/{branch_name}"
            logger.debug(f"        Generated URL: {github_url}")

        # Create Branch node
        branch_id = f"branch_{repo.name}_{branch_name.replace('/', '_').replace('-', '_')}"
        logger.debug(f"        Creating Branch node with ID: {branch_id}")
        branch_node = Branch(
            id=branch_id,
            name=branch_name,
            is_default=is_default,
            is_protected=is_protected,
            is_deleted=False,  # Only tracking existing branches for now
            is_external=False,  # Branch from this repo
            last_commit_sha=last_commit_sha,
            last_commit_timestamp=last_commit_timestamp,
            created_at=created_at,
            url=github_url
        )

        # Create BRANCH_OF relationship
        logger.debug(f"        Creating BRANCH_OF relationship: {branch_id} -> {repo_id}")
        relationship = Relationship(
            type="BRANCH_OF",
            from_id=branch_id,
            to_id=repo_id,
            from_type="Branch",
            to_type="Repository"
        )

        # Merge into Neo4j
        logger.debug(f"        Merging Branch node and relationship")
        merge_branch(session, branch_node)
        branch_node.print_cli()

        merge_relationship(session, relationship)
        relationship.print_cli()
        
        logger.info(f"      ✓ Successfully processed branch: {branch_name}")
        logger.debug(f"        Branch summary: id='{branch_id}', default={is_default}, protected={is_protected}")

    except Exception as e:
        logger.info(f"      ✗ Error: Failed to create Branch for {branch.name}: {str(e)}")
        logger.exception(e)
