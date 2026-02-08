def get_existing_branch_metadata(session, repo_id):
    """Get metadata for existing branches to detect changes.

    Args:
        session: Neo4j session
        repo_id: Repository node ID

    Returns:
        dict: Mapping of branch_name -> {last_commit_sha, is_deleted}
    """
    query = """
    MATCH (b:Branch)-[:BRANCH_OF]->(r:Repository {id: $repo_id})
    RETURN b.name as name, 
           b.last_commit_sha as last_commit_sha,
           b.is_deleted as is_deleted
    """
    result = session.run(query, repo_id=repo_id)

    branch_metadata = {}
    for record in result:
        branch_metadata[record['name']] = {
            'last_commit_sha': record['last_commit_sha'],
            'is_deleted': record['is_deleted']
        }

    return branch_metadata