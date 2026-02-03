import re
from db.models import Commit, IdentityMapping, Person, Relationship, merge_commit, merge_identity_mapping, merge_person, merge_relationship
from modules.github.new_file_handler import new_file_handler
from modules.github.retry_with_backoff import retry_with_backoff


from datetime import datetime

from common.logger import logger

def get_or_create_commit_author(session, commit_author, repo_created_at):
    """
    Get or create Person and IdentityMapping for a commit author.
    
    Args:
        session: Neo4j session
        commit_author: GitHub commit author object
        repo_created_at: Repository creation date for fallback timestamp
        
    Returns:
        str: Person ID for the author
    """
    try:
        logger.debug(f"      Processing commit author: {commit_author}")
        
        # Extract author information
        # GitHub commit authors can be User objects or just name/email dicts
        if hasattr(commit_author, 'login'):
            # Full user object
            github_login = commit_author.login
            github_name = commit_author.name if hasattr(commit_author, 'name') and commit_author.name else github_login
            github_email = commit_author.email if hasattr(commit_author, 'email') and commit_author.email else ""
            logger.debug(f"        Full user object: login='{github_login}', name='{github_name}', email='{github_email}'")
        elif hasattr(commit_author, 'name'):
            # Name/email only (common for commits)
            github_name = commit_author.name or "Unknown"
            github_email = commit_author.email or ""
            # Create a sanitized login from email or name
            if github_email:
                github_login = github_email.split('@')[0]
            else:
                github_login = github_name.lower().replace(' ', '_')
            logger.debug(f"        Name/email only: derived_login='{github_login}', name='{github_name}', email='{github_email}'")
        else:
            # Fallback for unknown author format
            github_login = "unknown"
            github_name = "Unknown"
            github_email = ""
            logger.debug(f"        Unknown author format, using fallback values")
        
        # Create unique IDs
        person_id = f"person_github_{github_login}"
        identity_id = f"identity_github_{github_login}"
        logger.debug(f"        Generated IDs: person_id='{person_id}', identity_id='{identity_id}'")
        
        # Check if person already exists
        check_query = "MATCH (p:Person {id: $person_id}) RETURN p.id as id LIMIT 1"
        result = session.run(check_query, person_id=person_id)
        if result.single():
            # Person already exists, return the ID
            return person_id
        
        # Create Person node
        person = Person(
            id=person_id,
            name=github_name,
            email=github_email,
            title="",
            role="",
            seniority="",
            hire_date="",
            is_manager=False
        )
        
        # Create IdentityMapping node
        identity = IdentityMapping(
            id=identity_id,
            provider="GitHub",
            username=github_login,
            email=github_email
        )
        
        # Create MAPS_TO relationship
        logger.debug(f"        Creating MAPS_TO relationship: {identity_id} -> {person_id}")
        maps_to_relationship = Relationship(
            type="MAPS_TO",
            from_id=identity.id,
            to_id=person_id,
            from_type="IdentityMapping",
            to_type="Person"
        )
        
        # Merge into Neo4j
        logger.debug(f"        Merging Person and IdentityMapping nodes")
        merge_person(session, person)
        merge_identity_mapping(session, identity, relationships=[maps_to_relationship])
        
        logger.info(f"      ✓ Created commit author: {github_name} ({github_login})")
        logger.debug(f"        Returning person_id: {person_id}")
        
        return person_id
        
    except Exception as e:
        logger.debug(f"        Error creating commit author: {str(e)}", exc_info=True)
        logger.exception(e)
        # Return a fallback person ID
        fallback_id = "person_github_unknown"
        logger.debug(f"        Using fallback person ID: {fallback_id}")
        return fallback_id


def extract_issue_keys(message):
    """
    Extract Jira issue keys from commit message.
    
    Supports patterns:
    - [PROJ-123]
    - PROJ-123:
    - (PROJ-123)
    - PROJ-123 at start or after space
    
    Args:
        message: Commit message string
        
    Returns:
        list: List of unique issue keys found
    """
    # Pattern: Project key (2+ uppercase letters) followed by hyphen and number
    # Matches: PROJ-123, ABC-456, STORY-789, etc.
    pattern = r'\b([A-Z]{2,}-\d+)\b'
    matches = re.findall(pattern, message)
    return list(set(matches))  # Return unique keys


def validate_issue_exists(session, issue_key):
    """
    Check if a Jira issue exists in Neo4j.
    
    Args:
        session: Neo4j session
        issue_key: Issue key to validate (e.g., "PROJ-123")
        
    Returns:
        str: Issue ID if exists, None otherwise
    """
    query = """
    MATCH (i:Issue {key: $issue_key})
    RETURN i.id as issue_id
    LIMIT 1
    """
    result = session.run(query, issue_key=issue_key)
    record = result.single()
    return record["issue_id"] if record else None


def new_commit_handler(session, repo_name, commit, branch_id, repo_owner=None, branch_name="main"):
    """
    Handle a commit by creating Commit node and relationships.

    Args:
        session: Neo4j session
        repo_name: Repository name for ID generation
        commit: GitHub commit object
        branch_id: Branch ID this commit belongs to
        repo_owner: GitHub repository owner (optional, for file URLs)
        branch_name: Branch name (default: "main")

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.debug(f"      Processing commit: {commit.sha[:8]} on branch {branch_name}")
        logger.debug(f"        Repository: {repo_name}, Branch ID: {branch_id}")
        # Generate commit ID
        commit_sha = commit.sha
        commit_id = f"commit_{repo_name}_{commit_sha[:8]}"

        # Check if commit already exists
        check_query = "MATCH (c:Commit {id: $commit_id}) RETURN c.id LIMIT 1"
        result = session.run(check_query, commit_id=commit_id)
        if result.single():
            # Commit already exists, skip
            logger.info(f"      Commit {commit_sha[:8]} already exists, skipping.")
            return True

        # Extract commit information
        commit_message = commit.commit.message or "No message"
        commit_timestamp = commit.commit.author.date.isoformat() if commit.commit.author.date else datetime.now().isoformat()

        # Get commit stats
        stats = commit.stats if hasattr(commit, 'stats') else None
        additions = stats.additions if stats else 0
        deletions = stats.deletions if stats else 0
        total_files = stats.total if stats else 0

        # Get or create commit author
        commit_author = commit.author if commit.author else commit.commit.author
        author_person_id = get_or_create_commit_author(session, commit_author, commit_timestamp[:10])

        # Generate GitHub URL if owner is provided
        github_url = None
        if repo_owner:
            github_url = f"https://github.com/{repo_owner}/{repo_name}/commit/{commit_sha}"

        # Create Commit node
        commit_node = Commit(
            id=commit_id,
            sha=commit_sha,
            message=commit_message,
            timestamp=commit_timestamp,
            additions=additions,
            deletions=deletions,
            files_changed=total_files,
            url=github_url
        )
        logger.info(f"      Creating commit: {github_url if github_url else commit_sha[:8]}")

        # Merge commit into Neo4j
        merge_commit(session, commit_node)

        # Create PART_OF relationship (Commit → Branch)
        part_of_rel = Relationship(
            type="PART_OF",
            from_id=commit_id,
            to_id=branch_id,
            from_type="Commit",
            to_type="Branch"
        )
        merge_relationship(session, part_of_rel)

        # Create AUTHORED_BY relationship (Commit → Person)
        authored_by_rel = Relationship(
            type="AUTHORED_BY",
            from_id=commit_id,
            to_id=author_person_id,
            from_type="Commit",
            to_type="Person"
        )
        merge_relationship(session, authored_by_rel)

        # Extract and validate Jira issue keys from commit message
        issue_keys = extract_issue_keys(commit_message)
        for issue_key in issue_keys:
            issue_id = validate_issue_exists(session, issue_key)
            if issue_id:
                # Create REFERENCES relationship (Commit → Issue)
                references_rel = Relationship(
                    type="REFERENCES",
                    from_id=commit_id,
                    to_id=issue_id,
                    from_type="Commit",
                    to_type="Issue"
                )
                merge_relationship(session, references_rel)

        # Process modified files
        try:
            files = retry_with_backoff(lambda: list(commit.files))
            for file in files:
                # Create File node
                file_id = new_file_handler(
                    session,
                    repo_name,
                    file.filename,
                    commit_timestamp,
                    file.additions + file.deletions if hasattr(file, 'additions') else 0,
                    repo_owner,
                    branch_name
                )

                if file_id:
                    # Create MODIFIES relationship (Commit → File) with per-file stats
                    modifies_rel = Relationship(
                        type="MODIFIES",
                        from_id=commit_id,
                        to_id=file_id,
                        from_type="Commit",
                        to_type="File",
                        properties={
                            "additions": file.additions if hasattr(file, 'additions') else 0,
                            "deletions": file.deletions if hasattr(file, 'deletions') else 0
                        }
                    )
                    merge_relationship(session, modifies_rel)
        except Exception as e:
            logger.info(f"      Warning: Could not fetch files for commit {commit_sha[:8]}: {str(e)}")
            logger.exception(e)

        return True

    except Exception as e:
        logger.info(f"      Warning: Failed to create commit {commit.sha[:8]}: {str(e)}")
        logger.exception(e)
        return False