from db.models import IdentityMapping, Relationship, merge_identity_mapping, merge_relationship
from modules.github.map_permissions_to_general import map_permissions_to_general
from common.identity_resolver import get_or_create_person
from common.logger import logger

def new_user_handler(session, collaborator, repo_id, repo_created_at):
    """Handle a new user collaborator by creating Person, IdentityMapping nodes and COLLABORATOR relationship.

    Args:
        session: Neo4j session
        collaborator: GitHub collaborator object with attributes like login, name, email, type, permissions
        repo_id: Repository ID to create COLLABORATOR relationship with
        repo_created_at: Repository creation date for relationship timestamp
    """
    try:
        # Extract available information from collaborator
        github_login = collaborator.login
        logger.debug(f"    Processing new user handler for: {github_login}")
        
        github_name = collaborator.name if hasattr(collaborator, 'name') and collaborator.name else github_login
        github_email = collaborator.email if hasattr(collaborator, 'email') and collaborator.email else ""
        logger.debug(f"      User details: name='{github_name}', email='{github_email}'")

        # Get or create Person using email-based identity resolution
        # This ensures a single Person node per individual across all systems
        person_id, is_new = get_or_create_person(
            session,
            email=github_email if github_email else None,
            name=github_name,
            provider="github",
            external_id=github_login
        )
        
        if not person_id:
            logger.error(f"      Failed to get/create person for {github_login}")
            return
        
        logger.debug(f"      {'Created new' if is_new else 'Found existing'} Person: {person_id}")

        # Create IdentityMapping node for GitHub
        identity_id = f"identity_github_{github_login}"
        logger.debug(f"      Creating IdentityMapping node with ID: {identity_id}")
        identity = IdentityMapping(
            id=identity_id,
            provider="GitHub",
            username=github_login,
            email=github_email
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
        identity.print_cli()
        maps_to_relationship.print_cli()

        # Extract permissions and map to general READ/WRITE
        logger.debug(f"      Processing permissions for {github_login}: {collaborator.permissions.__dict__}")
        permission = map_permissions_to_general(collaborator.permissions.__dict__)
        logger.debug(f"      Mapped permission: {permission}")

        # Determine role based on permissions
        role = None
        if collaborator.permissions.admin:
            role = "admin"
        elif collaborator.permissions.maintain:
            role = "maintainer"
        elif collaborator.permissions.push:
            role = "contributor"
        logger.debug(f"      Determined role: {role}")

        # Create COLLABORATOR relationship from Person to Repository
        collab_properties = {
            "permission": permission,
            "granted_at": repo_created_at
        }
        if role:
            collab_properties["role"] = role
        logger.debug(f"      COLLABORATOR relationship properties: {collab_properties}")

        logger.debug(f"      Creating COLLABORATOR relationship: {person_id} -> {repo_id}")
        collaborator_relationship = Relationship(
            type="COLLABORATOR",
            from_id=person_id,
            to_id=repo_id,
            from_type="Person",
            to_type="Repository",
            properties=collab_properties
        )

        logger.debug(f"      Merging COLLABORATOR relationship")
        merge_relationship(session, collaborator_relationship)
        collaborator_relationship.print_cli()
        
        logger.info(f"    ✓ Successfully processed user: {github_login}")
        logger.debug(f"      Final summary: person_id='{person_id}', permission='{permission}', role='{role}'")

    except Exception as e:
        logger.info(f"    ✗ Error: Failed to create user {collaborator.login}: {str(e)}")
        logger.exception(e)
