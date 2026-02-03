#!/usr/bin/env python3
"""
GitHub Repository Information Fetcher

Loads repository URLs from .config.json and fetches repository properties
using the GitHub API.
"""

import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from db.models import (
    create_constraints
)
from modules.github.get_all_repos_for_owner import get_all_repos_for_owner
from modules.github.process_repo import process_repo
from modules.github.utils import get_github_client

from common.logger import logger

def load_config():
    """Load repository configuration from .config.json"""
    config_path = Path(__file__).parent / ".config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_repo_url(url):
    """
    Extract owner and repo name from GitHub URL.
    
    Example: https://github.com/owner/repo -> (owner, repo)
    Example: https://github.com/owner/* -> (owner, *)
    """
    parts = url.rstrip('/').split('/')
    return parts[-2], parts[-1]


def is_wildcard_url(url):
    """
    Check if the URL is a wildcard pattern (e.g., https://github.com/owner/*)
    """
    return url.rstrip('/').endswith('/*') or url.rstrip('/').endswith('%2F*')


def main():
    """Main execution function"""
    logger.info("GitHub Repository Information Fetcher")
    logger.info("=" * 50)
    
    # Initialize Neo4j connection
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
    
    logger.info(f"\nConnecting to Neo4j at {neo4j_uri}...")
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        # Verify connection
        driver.verify_connectivity()
        logger.info("✓ Neo4j connection established\n")
        
        # Create constraints for layers 1 (Person, Team, IdentityMapping), 5 (Repository), 6 (Branch), 7 (Commit, File), and 8 (PullRequest)
        logger.info("Creating database constraints...")
        with driver.session() as session:
            create_constraints(session, layers=[1, 5, 6, 7, 8])
        logger.info("✓ Constraints created\n")
        
        # Load configuration
        config = load_config()
        logger.info(f"Loaded {len(config['repos'])} repositories from config\n")
        
        # Counters for tracking
        repos_processed = 0
        repos_failed = 0
        
        # Create a session for the entire operation
        with driver.session() as session:
            # Process each repository
            for idx, repo_config in enumerate(config['repos'], 1):
                repo_url = repo_config['url']
                logger.info(f"\n[{idx}] Processing: {repo_url}")
                logger.info("-" * 50)
                
                try:
                    # Get GitHub client
                    client = get_github_client(repo_config)
                    
                    # Check if this is a wildcard URL (e.g., https://github.com/owner/*)
                    if is_wildcard_url(repo_url):
                        # Extract owner and enumerate all repos
                        owner, _ = parse_repo_url(repo_url)
                        logger.info(f"Wildcard pattern detected. Fetching all repositories for: {owner}")
                        
                        repos = get_all_repos_for_owner(client, owner)
                        
                        for repo in repos:
                            try:
                                # Process repository (creates nodes and relationships)
                                logger.info(f"\n  ↳ {repo.name}")
                                process_repo(repo, session)
                                repos_processed += 1
                                
                            except Exception as e:
                                logger.info(f"    ✗ Error processing {repo.name}: {str(e)}")
                                logger.exception(e)
                                repos_failed += 1
                                continue
                                
                    else:
                        # Single repository
                        # Parse URL and get repository
                        owner, repo_name = parse_repo_url(repo_url)
                        repo = client.get_repo(f"{owner}/{repo_name}")
                        
                        # Process repository (creates nodes and relationships)
                        process_repo(repo, session)
                        repos_processed += 1
                    
                except Exception as e:
                    logger.info(f"✗ Error: {str(e)}")
                    logger.exception(e)
                    repos_failed += 1
                    continue
        
        logger.info("\n" + "=" * 50)
        logger.info("\nSummary:")
        logger.info(f"  ✓ Successfully processed: {repos_processed}")
        logger.info(f"  ✗ Failed: {repos_failed}")
        logger.info(f"  Total: {repos_processed + repos_failed}")
        
    finally:
        # Close Neo4j connection
        driver.close()
        logger.info("\n✓ Neo4j connection closed")


if __name__ == "__main__":
    main()
