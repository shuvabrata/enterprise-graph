from common.logger import logger

def get_all_repos_for_owner(client, owner):
    """
    Get all repositories for a given owner (user or organization).

    Args:
        client: GitHub client instance
        owner: GitHub username or organization name

    Returns:
        list: List of repository objects
    """
    repos = []
    try:
        # Try as organization first
        org = client.get_organization(owner)
        repos = list(org.get_repos())
        logger.info(f"Found {len(repos)} repositories for organization: {owner}")
    except Exception:
        # If not an organization, try as user
        try:
            user = client.get_user(owner)
            repos = list(user.get_repos())
            logger.info(f"Found {len(repos)} repositories for user: {owner}")
        except Exception as e:
            logger.info(f"Error fetching repositories for {owner}: {str(e)}")
            logger.exception(e)

    return repos