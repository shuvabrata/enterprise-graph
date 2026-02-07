from datetime import datetime, timezone

from db.models import IdentityMapping, Relationship, merge_identity_mapping
from common.identity_resolver import get_or_create_person
from common.logger import logger

def new_jira_user_handler(session, user_data):
    """Handle a Jira user by creating Person and IdentityMapping nodes.

    Args:
        session: Neo4j session
        user_data: Jira user object with attributes like accountId, displayName, emailAddress

    Returns:
        person_id: The created Person node ID
    """
    try:
        # Extract available information from Jira user
        account_id = user_data.get('accountId')
        display_name = user_data.get('displayName', '')
        email = user_data.get('emailAddress', '')
        
        if not account_id:
            logger.warning("      Jira user missing accountId, skipping")
            return None
        
        logger.debug(f"    Processing new Jira user handler for: {display_name} ({account_id})")
        
        # Get or create Person using email-based identity resolution
        # This ensures a single Person node per individual across all systems
        person_id, is_new = get_or_create_person(
            session,
            email=email if email else None,
            name=display_name,
            provider="jira",
            external_id=account_id
        )
        
        if not person_id:
            logger.error(f"      Failed to get/create person for {display_name}")
            return None
        
        logger.debug(f"      {'Created new' if is_new else 'Found existing'} Person: {person_id}")

        # Create IdentityMapping node for Jira
        identity_id = f"identity_jira_{account_id}"
        logger.debug(f"      Creating IdentityMapping node with ID: {identity_id}")
        identity = IdentityMapping(
            id=identity_id,
            provider="Jira",
            username=display_name,  # Jira uses display name as username
            email=email,
            last_updated_at=datetime.now(timezone.utc).isoformat()
        )

        # Create MAPS_TO relationship from IdentityMapping to Person
        logger.debug(f"      Creating MAPS_TO relationship: {identity_id} -> {person_id}")
        maps_to_relationship = Relationship(
            type="MAPS_TO",
            from_id=identity.id,
            to_id=person_id,
            from_type="IdentityMapping",
            to_type="Person"
        )

        # Merge IdentityMapping node with MAPS_TO relationship
        logger.debug(f"      Merging IdentityMapping node with MAPS_TO relationship")
        merge_identity_mapping(session, identity, relationships=[maps_to_relationship])
        
        logger.debug(f"      ✓ Created/updated Jira user: {display_name}")
        
        return person_id
        
    except Exception as e:
        logger.error(f"      ✗ Error processing Jira user: {str(e)}")
        logger.exception(e)
        return None
