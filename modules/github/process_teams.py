from common.logger import logger
from modules.github.new_team_handler import new_team_handler


def process_teams(repo, session, repo_id, repo_created_at, processed_users_cache):
    try:
        teams = repo.get_teams()
        for team in teams:
            new_team_handler(session, team, repo_id, repo_created_at, processed_users_cache)
    except Exception as e:
        logger.info(f"    Warning: Could not fetch teams - {str(e)}")