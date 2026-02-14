from common.logger import logger
from modules.github.get_fully_synced_pr_numbers import get_fully_synced_pr_numbers
from modules.github.new_pull_request_handler import new_pull_request_handler
from modules.github.repo_last_synced_at import get_last_synced_at
from modules.github.retry_with_backoff import retry_with_backoff


import os
from datetime import datetime, timedelta, timezone


from typing import Any

def process_pull_requests(
    repo: Any,
    session: Any,
    repo_id: str,
    repo_obj: Any,
    person_cache: Any
) -> None:
    try:
        last_synced = get_last_synced_at(session, repo_id)
        if last_synced:
            since_date = last_synced if last_synced.tzinfo else last_synced.replace(tzinfo=timezone.utc)
            logger.info(f"    Incremental sync: Fetching PRs updated since last sync ({since_date.strftime('%Y-%m-%d %H:%M:%S')}...")
        else:
            pr_days_limit = int(os.getenv('PULL_REQUEST_DAYS_LIMIT', '60'))
            since_date = datetime.now(timezone.utc) - timedelta(days=pr_days_limit)
            logger.info(f"    First sync: Fetching pull requests (last {pr_days_limit} days)...")
        all_prs = retry_with_backoff(
            lambda: list(repo_obj.get_pulls(state='all', sort='updated', direction='desc'))
        )
        recent_prs = [pr for pr in all_prs if pr.updated_at >= since_date]
        existing_pr_numbers = get_fully_synced_pr_numbers(session, repo_id)
        prs_to_process = [pr for pr in recent_prs if pr.number not in existing_pr_numbers or pr.state == 'open']
        if existing_pr_numbers:
            logger.info(f"    Found {len(recent_prs)} recent PRs, {len(existing_pr_numbers)} already processed (closed/merged), {len(prs_to_process)} to process")
        else:
            logger.info(f"    Processing {len(prs_to_process)} pull requests...")
        prs_processed = 0
        prs_failed = 0
        for pr in prs_to_process:
            if new_pull_request_handler(session, repo_obj, pr, repo_id, repo_obj.owner.login, person_cache):
                prs_processed += 1
            else:
                prs_failed += 1
        logger.info(f"    ✓ Processed {prs_processed} pull requests")
        if prs_failed > 0:
            logger.info(f"    ✗ Failed/Skipped: {prs_failed} pull requests")
    except Exception as e:
        logger.info(f"    Warning: Could not fetch pull requests - {str(e)}")