# enterprise-graph

A Neo4j graph database project with a simple movie database example.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.14 or higher 

## Quick Start

### 1. Configure Environment Variables 

Copy the example environment file and update it with your credentials:

```bash
cp .env.example .env
```

Edit the `.env` file and update the Neo4j credentials:
```
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password
```

**Important**: Make sure to update the password before proceeding to the next step.

### 2. Start Neo4j with Docker

Start the Neo4j database using Docker Compose:

```bash
docker compose up -d
```

This will:
- Pull the Neo4j Community Edition image (version 5.26)
- Start Neo4j on ports 7474 (HTTP) and 7687 (Bolt)
- Use the credentials from your `.env` file

### 3. Access Neo4j Browser

Open your web browser and navigate to:
```
http://localhost:7474
```

Login with the credentials you set in your `.env` file:
- **Username**: Value from `NEO4J_USER`
- **Password**: Value from `NEO4J_PASSWORD`

### 4. Install Python Dependencies
Optionally create python venv
```bash
python -m venv .venv
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

All sensitive configuration is stored in the `.env` file. This file is not tracked in git (it's in `.gitignore`).

Available environment variables:
- `NEO4J_USER`: Neo4j database username
- `NEO4J_PASSWORD`: Neo4j database password

To change credentials, simply update the values in your `.env` file and restart the Docker container:

```bash
docker compose restart
```

## Useful Docker Commands

```bash
# Start Neo4j
docker compose up -d

# Stop Neo4j
docker compose down

# View logs
docker compose logs -f neo4j

# Stop and remove all data
docker compose down -v

# Restart Neo4j
docker compose restart
```

## Learn More

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Python Driver](https://neo4j.com/docs/api/python-driver/current/)
- [Graph Database Concepts](https://neo4j.com/docs/getting-started/current/graphdb-concepts/)

## License

See [LICENSE](LICENSE) file for details.
