from db.models import Sprint, Relationship, merge_sprint
from common.logger import logger


def new_sprint_handler(session, sprint_data, jira_base_url=None):
    """Handle a Jira sprint by creating Sprint node.

    Args:
        session: Neo4j session
        sprint_data: Jira sprint object from Agile API
        jira_base_url: Base URL of Jira instance (e.g., "https://yoursite.atlassian.net")

    Returns:
        sprint_id: The created Sprint node ID
    """
    try:
        # Extract sprint information
        jira_sprint_id = sprint_data.get('id')
        sprint_name = sprint_data.get('name', '')
        
        if not jira_sprint_id:
            logger.warning(f"    Sprint missing id, skipping: {sprint_data}")
            return None
        
        logger.info(f"  Processing sprint: {sprint_name}")
        
        # Create unique sprint ID
        sprint_id = f"sprint_jira_{jira_sprint_id}"
        
        # Extract fields
        goal = sprint_data.get('goal', '')
        state = sprint_data.get('state', 'Unknown')  # 'active', 'closed', 'future'
        
        # Map Jira sprint state to our status
        status_map = {
            'active': 'Active',
            'closed': 'Completed',
            'future': 'Planned'
        }
        status = status_map.get(state.lower(), state)
        
        # Extract dates - API returns ISO datetime, we need date part
        start_date = sprint_data.get('startDate', '')[:10] if sprint_data.get('startDate') else ''
        end_date = sprint_data.get('endDate', '')[:10] if sprint_data.get('endDate') else ''
        
        # Create Sprint object
        sprint = Sprint(
            id=sprint_id,
            name=sprint_name,
            goal=goal,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        # Merge sprint into Neo4j
        merge_sprint(session, sprint)
        
        logger.info(f"    ✓ Created Sprint: {sprint_name} ({status})")
        return sprint_id
        
    except Exception as e:
        logger.error(f"    ✗ Error in new_sprint_handler: {str(e)}")
        logger.exception(e)
        return None
