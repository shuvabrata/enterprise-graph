# Enterprise Graph - User Guide

This guide will help you set up and run the Enterprise Graph data synchronization tool. No programming experience required!

## What Does This Tool Do?

Enterprise Graph connects to your Jira and GitHub accounts, downloads information about your projects, issues, repositories, and commits, and stores them in a graph database (Neo4j) where you can analyze relationships and patterns.

## Prerequisites

Before you begin, make sure you have:

1. **Docker Desktop** installed on your computer
   - Download from: https://www.docker.com/products/docker-desktop
   - Follow the installation instructions for your operating system
   - Make sure Docker Desktop is running (you should see a Docker icon in your system tray)

2. **Git** installed (if you haven't cloned the repository yet)
   - Download from: https://git-scm.com/downloads

3. **Access credentials** for your services:
   - Jira Cloud API token
   - GitHub Personal Access Token (if syncing private repositories)

---

## Step 1: Get the Code

If you haven't already cloned the repository, open a terminal/command prompt and run:

```bash
git clone https://github.com/shuvabrata/enterprise-graph
cd enterprise-graph
```

---

## Step 2: Create Configuration Files

You need to create two configuration files that tell the tool which projects and repositories to sync.

### 2.1 Create Jira Configuration File

1. Navigate to the `app/modules/jira/` folder in the repository
2. Create a new file named `.config.json` in that folder
3. Copy and paste the following template into the file:

```json
{
  "account": [
    {
      "url": "https://your-company.atlassian.net",
      "email": "your-email@company.com",
      "api_token": "your-jira-api-token-here"
    }
  ]
}
```

4. Replace the placeholder values:
   - `your-company.atlassian.net` - Your Jira Cloud URL
   - `your-email@company.com` - Your Jira account email
   - `your-jira-api-token-here` - Your Jira API token

**How to get a Jira API token:**
- Go to https://id.atlassian.com/manage-profile/security/api-tokens
- Click "Create API token"
- Give it a name (e.g., "Enterprise Graph Sync")
- Copy the token and paste it into your config file

### 2.2 Create GitHub Configuration File

1. Navigate to the `app/modules/github/` folder in the repository
2. Create a new file named `.config.json` in that folder
3. Copy and paste the following template into the file:

```json
{
  "repos": [
    {
      "url": "https://github.com/your-org/your-repo",
      "token": "your-github-token-here"
    },
    {
      "url": "https://github.com/your-org/*",
      "token": "your-github-token-here"
    }
  ]
}
```

4. Replace the placeholder values:
   - `your-org/your-repo` - Specific repository you want to sync
   - `your-org/*` - Use asterisk (*) to sync all repositories in an organization
   - `your-github-token-here` - Your GitHub Personal Access Token

**How to get a GitHub Personal Access Token:**
- Go to https://github.com/settings/tokens
- Click "Generate new token" → "Generate new token (classic)"
- Give it a name (e.g., "Enterprise Graph Sync")
- Select scopes: `repo` (for private repos) or `public_repo` (for public only)
- Click "Generate token"
- Copy the token and paste it into your config file

**Note:** You can add multiple repositories or use wildcards. For example:
- Specific repo: `"https://github.com/mycompany/backend"`
- All repos in org: `"https://github.com/mycompany/*"`
- Multiple entries: Just add more objects in the `repos` array

---

## Step 3: Create Environment Configuration File

1. In the root folder of the repository, find the file named `.env.example`
2. Make a copy of this file and name it `.env` (without the `.example`)
3. Open the `.env` file in a text editor
4. Update the following values:

```bash
# Neo4j Connection - Keep these defaults for Docker
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=choose-a-secure-password

# GitHub Token (if you have one, otherwise leave as is)
GITHUB_TOKEN_FOR_PUBLIC_REPOS=your-github-token-here

# How many days of history to fetch from Jira
JIRA_LOOKBACK_DAYS=90

# Logging settings - Keep defaults
LOG_LEVEL=INFO
LOG_FORMAT=JSON
ENABLE_FILE_LOGGING=1
```

**Important changes:**
- `NEO4J_PASSWORD` - Choose a strong password for your database
- `GITHUB_TOKEN_FOR_PUBLIC_REPOS` - Paste your GitHub token (same as in step 2.2)
- `JIRA_LOOKBACK_DAYS` - Number of days of history to fetch (90 = last 3 months)

**Keep these as default:**
- `NEO4J_URI=bolt://neo4j:7687` (Docker service name)
- `NEO4J_USERNAME=neo4j` (default username)

---

## Step 4: Start the Database

The tool uses Neo4j as its database. Let's start it using Docker:

1. Open a terminal/command prompt
2. Navigate to the repository folder:
   ```bash
   cd enterprise-graph
   ```
3. Start Neo4j:
   ```bash
   docker compose up -d neo4j
   ```
4. Wait about 30 seconds for Neo4j to fully start
5. Verify it's running:
   ```bash
   docker compose ps
   ```
   You should see `enterprise-graph-neo4j` with status "Up"

**Accessing Neo4j Browser:**
- Open your web browser
- Go to: http://localhost:7474
- Login with:
  - Username: `neo4j`
  - Password: (the password you set in your `.env` file)

---

## Step 5: Run Data Synchronization

Now you're ready to sync data from Jira and GitHub!

### 5.1 Sync Jira Data

Run this command to fetch data from Jira:

```bash
docker compose run --rm jira-sync
```

**What happens:**
- Connects to your Jira account
- Fetches projects, initiatives, epics, sprints, and issues
- Processes all the data and stores it in Neo4j
- This may take several minutes depending on how much data you have

**You'll see output like:**
```
[INFO] ================================================================================
[INFO] Jira Integration - Full Data Loader
[INFO] ================================================================================
[INFO] Connecting to Jira: https://your-company.atlassian.net
[INFO] Successfully authenticated as: Your Name
[INFO] Fetching projects...
...
[INFO] ✓ Successfully processed: 42
```

### 5.2 Sync GitHub Data

Run this command to fetch data from GitHub:

```bash
docker compose run --rm github-sync
```

**What happens:**
- Connects to your GitHub account
- Fetches repositories, branches, commits, pull requests
- Processes all the data and stores it in Neo4j
- This may take several minutes to hours for large repositories

**You'll see output like:**
```
[INFO] GitHub Repository Information Fetcher
[INFO] ==================================================
[INFO] Connecting to Neo4j at bolt://neo4j:7687...
[INFO] Processing: https://github.com/yourorg/yourrepo
...
[INFO] ✓ Successfully processed: 15
```

---

## Step 6: Verify Your Data

After both syncs complete, let's verify the data was loaded:

1. Open Neo4j Browser: http://localhost:7474
2. Login with your credentials
3. Run this query in the query box:
   ```cypher
   MATCH (n) RETURN labels(n) as Type, count(*) as Count
   ```
4. Click the blue "Run" button (or press Ctrl+Enter)

**You should see:**
- Person, Team, Project, Issue, Repository, Commit, etc.
- Each with a count showing how many were loaded

---

## Step 7: Schedule Automated Syncs (Optional)

To keep your data up-to-date, you can schedule the syncs to run automatically.

### On Mac/Linux (using cron):

1. Open terminal and run:
   ```bash
   crontab -e
   ```
2. Add these lines (replace `/path/to/` with actual path):
   ```bash
   # Sync Jira data daily at 2 AM
   0 2 * * * cd /path/to/enterprise-graph && docker compose run --rm jira-sync

   # Sync GitHub data daily at 3 AM
   0 3 * * * cd /path/to/enterprise-graph && docker compose run --rm github-sync
   ```
3. Save and exit

### On Windows (using Task Scheduler):

1. Open Task Scheduler
2. Create a new task
3. Set trigger: Daily at your preferred time
4. Set action: Start a program
   - Program: `docker`
   - Arguments: `compose run --rm jira-sync`
   - Start in: `C:\path\to\enterprise-graph`
5. Repeat for GitHub sync

---

## Checking Logs

If something goes wrong, you can check the logs:

### View persistent log files (Primary method):
Logs are saved to files in the `logs/` folder in your repository directory. This is the primary way to check Jira and GitHub sync logs.

**How to view logs:**
1. Navigate to the `logs/` folder in your repository
2. Open the log files with any text editor
3. Log files are named with timestamps for easy identification

**Note:** Log files are only created if you have these settings in your `.env` file:
- `ENABLE_FILE_LOGGING=1` (enabled by default)
- `LOG_DIR=/var/log/enterprise-graph` (set automatically for Docker)

### View Docker container logs:
Docker container logs are **only available while containers are running**. Since `jira-sync` and `github-sync` containers exit after completing their tasks, their logs are **not available** via `docker compose logs`.

However, you can view Neo4j logs (which runs continuously):
```bash
# View Neo4j logs (always available)
docker compose logs neo4j

# Follow Neo4j logs in real-time
docker compose logs -f neo4j
```

**For jira-sync and github-sync logs, always check the `logs/` folder.**

---

## Troubleshooting

### "Could not find .config.json file"
- Make sure you created the `.config.json` files in the correct folders:
  - `app/modules/jira/.config.json`
  - `app/modules/github/.config.json`
- File names must start with a dot (.)
- On Windows, you may need to use command prompt to create files starting with dot

### "Authentication failed" (Jira)
- Double-check your Jira URL (should be `https://yourcompany.atlassian.net`)
- Verify your email address is correct
- Regenerate your API token if needed

### "Bad credentials" (GitHub)
- Make sure your GitHub token is still valid (they can expire)
- Verify the token has the correct permissions (repo or public_repo scope)
- Check for extra spaces when copying the token

### "Connection refused" (Neo4j)
- Make sure Docker Desktop is running
- Verify Neo4j container is running: `docker compose ps`
- If Neo4j is not running, start it: `docker compose up -d neo4j`
- Wait 30 seconds and try again

### "Timed out trying to establish connection"
- Neo4j might still be starting up - wait a minute and try again
- Check if Neo4j is healthy: `docker compose ps`
- Restart Neo4j if needed: `docker compose restart neo4j`

### Sync is very slow
- This is normal for large repositories with many commits
- The first sync takes the longest
- Subsequent syncs will be faster (only fetching new data)
- You can reduce `COMMIT_DAYS_LIMIT` in `.env` to fetch less history

### Out of memory errors
- Large repositories may require more memory
- Increase Docker Desktop memory limit:
  - Docker Desktop → Settings → Resources → Memory
  - Increase to 4GB or more

---

## Stopping Everything

When you're done, you can stop the database:

```bash
# Stop all containers
docker compose down

# Stop and remove all data (⚠️ This deletes your database!)
docker compose down -v
```

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the `QUICK_START.md` file for technical details
2. Review the logs in the `logs/` folder
3. Check the GitHub repository issues page
4. Contact your system administrator

---

## Summary of Files You Created

After completing this guide, you should have created:

- `app/modules/jira/.config.json` - Jira connection settings
- `app/modules/github/.config.json` - GitHub repository list
- `.env` - Environment variables and passwords

**Security Note:** These files contain sensitive information (passwords, tokens). Never commit them to Git or share them publicly.

---

## Next Steps

Now that your data is synced, you can:

1. **Explore data in Neo4j Browser** (http://localhost:7474)
   - Try queries from the documentation
   - Visualize relationships between projects, people, and code

2. **Set up automated reports** (if available in your organization)

3. **Schedule regular syncs** to keep data up-to-date

4. **Share insights** with your team about project relationships and resource allocation
