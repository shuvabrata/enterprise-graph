import os

from github import Github


def get_github_client(repo_config):
    """
    Get GitHub client with appropriate authentication.
    
    Uses repo-specific token if provided, otherwise falls back to 
    GITHUB_TOKEN_FOR_PUBLIC_REPOS environment variable.
    """
    token = repo_config.get('access_token')
    
    if not token:
        token = os.getenv('GITHUB_TOKEN_FOR_PUBLIC_REPOS')
    
    if not token:
        raise ValueError("No GitHub token found. Please provide token in config or set GITHUB_TOKEN_FOR_PUBLIC_REPOS")
    
    return Github(token)
