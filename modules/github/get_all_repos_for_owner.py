from typing import List, Any
from github import Github, Organization, Repository, NamedUser
from common.logger import logger

def get_all_repos_for_owner(client: Github, owner: str) -> List[Repository]:
    """
    Get all repositories for a given owner (user or organization).

    Args:
        client (Github): GitHub client instance
        owner (str): GitHub username or organization name

    Returns:
        List[Repository]: List of repository objects
    """
    repos: List[Repository] = []
    try:
        # Try as organization first
        org: Organization = client.get_organization(owner)
        repos = list(org.get_repos())
        logger.info(f"Found {len(repos)} repositories for organization: {owner}")
    except Exception:
        # If not an organization, try as user
        try:
            user: NamedUser = client.get_user(owner)
            repos = list(user.get_repos())
            logger.info(f"Found {len(repos)} repositories for user: {owner}")
        except Exception as e:
            logger.info(f"Error fetching repositories for {owner}: {str(e)}")
            logger.exception(e)

    return repos