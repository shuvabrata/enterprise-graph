import os

from db.models import Relationship, Team, merge_relationship, merge_team
from modules.github.process_github_user import process_github_user, get_users_needing_refresh
from common.logger import logger

def new_team_handler(session, team, repo_id, repo_created_at, processed_users_cache=None):
    """Handle a new team by creating Team node and COLLABORATOR relationship to repository.

    Args:
        session: Neo4j session
        team: GitHub team object with attributes like name, slug, permission
        repo_id: Repository ID to create relationship with
        repo_created_at: Repository creation date for relationship timestamp
        processed_users_cache: Optional dict to prevent duplicate user processing in same session
    """
    try:
        # Extract available information from team
        team_slug = team.slug
        team_name = team.name
        logger.info(f"    Processing team: {team_name} ({team_slug})")
        logger.debug(f"      Team permission from GitHub: {team.permission}")

        # Extract team URL (GitHub API provides html_url)
        team_url = team.html_url if hasattr(team, 'html_url') and team.html_url else None
        logger.debug(f"      Team URL: {team_url}")

        # Map GitHub permission to general READ/WRITE
        # GitHub team permissions: pull, push, admin, maintain, triage
        permission_mapping = {
            'pull': 'READ',
            'triage': 'READ',
            'push': 'WRITE',
            'maintain': 'WRITE',
            'admin': 'WRITE'
        }
        permission = permission_mapping.get(team.permission, 'READ')
        logger.debug(f"      Mapped permission: {team.permission} -> {permission}")

        # Create Team node (prefix with team_github_ for global uniqueness)
        team_id = f"team_github_{team_slug}"
        logger.debug(f"      Creating Team node with ID: {team_id}")
        team_node = Team(
            id=team_id,
            name=team_name,
            focus_area="",  # GitHub API doesn't provide this
            target_size=0,   # GitHub API doesn't provide this
            created_at=repo_created_at,  # Use repo creation as proxy
            url=team_url
        )

        # Create COLLABORATOR relationship from Team to Repository
        logger.debug(f"      Creating COLLABORATOR relationship: {team_id} -> {repo_id}")
        logger.debug(f"      Relationship properties: permission='{permission}', granted_at='{repo_created_at}'")
        relationship = Relationship(
            type="COLLABORATOR",
            from_id=team_id,
            to_id=repo_id,
            from_type="Team",
            to_type="Repository",
            properties={
                "permission": permission,
                "granted_at": repo_created_at
            }
        )

        # Merge into Neo4j (MERGE handles deduplication)
        logger.debug(f"      Merging Team node")
        merge_team(session, team_node)
        team_node.print_cli()

        logger.debug(f"      Merging COLLABORATOR relationship")
        merge_relationship(session, relationship)
        relationship.print_cli()
        
        logger.debug(f"      Team node and COLLABORATOR relationship created")

        # Process team members: create Person, IdentityMapping nodes and MEMBER_OF relationships
        try:
            members = team.get_members()
            member_count = members.totalCount
            logger.info(f"    Found {member_count} team members... in team {team_name}")
            
            # Optimization: Filter members to only those needing refresh
            refresh_days = int(os.getenv('IDENTITY_REFRESH_DAYS', '7'))
            member_list = list(members)
            members_to_process, skip_count = get_users_needing_refresh(
                session, member_list, refresh_days
            )
            
            if skip_count > 0:
                logger.info(f"    Skipping {skip_count} members (updated within last {refresh_days} days)")
            
            if not members_to_process:
                logger.info(f"    All team members are up-to-date")
            else:
                logger.info(f"    Processing {len(members_to_process)} team members...")
                
                members_processed = 0
                members_failed = 0
                
                for member in members_to_process:
                    # Process GitHub user: create/update Person and IdentityMapping
                    person_id = process_github_user(session, member, processed_users_cache)
                    
                    if person_id:
                        # Create MEMBER_OF relationship from Person to Team
                        logger.debug(f"      Creating MEMBER_OF relationship: {person_id} -> {team_id}")
                        member_relationship = Relationship(
                            type="MEMBER_OF",
                            from_id=person_id,
                            to_id=team_id,
                            from_type="Person",
                            to_type="Team"
                        )
                        
                        logger.debug(f"      Merging MEMBER_OF relationship")
                        merge_relationship(session, member_relationship)
                        members_processed += 1
                    else:
                        members_failed += 1
                
                logger.info(f"    ✓ Processed {members_processed} team members")
                if members_failed > 0:
                    logger.info(f"    ✗ Failed: {members_failed} team members")
                    
        except Exception as e:
            # Team members might not be accessible due to permissions or API limits
            logger.info(f"    Warning: Could not fetch team members - {str(e)}")
        
        # Final success message after all team processing
        logger.info(f"    ✓ Successfully processed team: {team_name}")
        logger.debug(f"      Team summary: id='{team_id}', permission='{permission}'")

    except Exception as e:
        logger.info(f"    ✗ Error: Failed to create Team for {team.slug}: {str(e)}")
        logger.exception(e)
