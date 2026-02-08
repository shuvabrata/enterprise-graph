def get_fully_synced_commit_shas(session, repo_id):
    """Get list of commit SHAs that are already fully processed in Neo4j.

    Args:
        session: Neo4j session
        repo_id: Repository node ID

    Returns:
        set: Set of commit SHAs that have fully_synced=true
    """
    query = """
    MATCH (c:Commit)-[:PART_OF]->(b:Branch)-[:BRANCH_OF]->(r:Repository {id: $repo_id})
    WHERE c.fully_synced = true
    RETURN collect(c.sha) as processed_shas
    """
    result = session.run(query, repo_id=repo_id).single()

    if result and result['processed_shas']:
        return set(result['processed_shas'])
    return set()