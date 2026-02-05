# Neo4j Query Testing Framework

Automated testing framework for validating Neo4j Cypher queries with configurable expectations, multiple report formats, and comprehensive metrics tracking.

## 📋 Overview

This framework automates the execution and validation of 60+ Cypher queries across 5 domains:
- **People & Identity**: Organizational structure and identity mappings
- **GitHub**: Repositories, branches, commits, and pull requests
- **Jira**: Projects, initiatives, epics, issues, and sprints
- **Cross-Domain**: Analytics spanning multiple data sources
- **Schema**: Database structure and constraints

## 🎯 Features

- ✅ **Configurable Expectations**: Per-query thresholds for rows, execution time, and required columns
- 📊 **Multi-Format Reports**: JSON (machine-readable), HTML (stakeholder-friendly), Console (terminal)
- 🔍 **Data Quality Checks**: Automated detection of empty columns and missing data
- ⏱️ **Performance Tracking**: Microsecond-precision timing and historical comparison
- 🚦 **Tiered Validation**: PASS/WARNING/CONCERN/FAIL status based on severity
- 📈 **Historical Tracking**: Timestamped JSON reports for trend analysis

## 📦 Prerequisites

### 1. Neo4j Database
- Neo4j instance running (Docker, Desktop, or Cloud)
- Database populated with data (run simulation layers or load real data)
- Accessible via bolt://localhost:7687 (or custom URI)

### 2. Python Environment
Python 3.8+ required with virtual environment activated.

### 3. Environment Variables
Create `.env` file in project root with Neo4j connection details.

## 🚀 Quick Start

See [QUICK_START.md](QUICK_START.md) for 2-minute setup guide.

## 📝 Configuration

### Expectation Levels in queries_config.yaml
- **min_rows**: Minimum expected rows (0 = optional data)
- **max_rows**: Maximum allowed rows (null = unlimited)
- **max_time_ms**: Performance threshold (50ms-5000ms based on complexity)
- **required_columns**: Schema validation (ensures columns exist)
- **allow_empty_columns**: NULL tolerance (prevents false positives)

## 🧪 Running Tests

### All Tests
```bash
pytest tests/neo4j_queries/ -v
```

### By Domain
```bash
pytest tests/neo4j_queries/test_queries_people.py -v      # People & Identity
pytest tests/neo4j_queries/test_queries_github.py -v      # GitHub
pytest tests/neo4j_queries/test_queries_jira.py -v        # Jira
pytest tests/neo4j_queries/test_queries_cross_domain.py -v # Cross-Domain
pytest tests/neo4j_queries/test_queries_schema.py -v      # Schema
```

### Single Test
```bash
pytest tests/neo4j_queries/test_queries_people.py::test_team_distribution -v
```

### Useful Options
- `-v` - Verbose output
- `-s` - Show print statements
- `-x` - Stop on first failure
- `-k "pattern"` - Run tests matching pattern
- `--durations=10` - Show 10 slowest tests

## 📊 Understanding Reports

### Report Locations
After running tests, find reports in `tests/neo4j_queries/results/`:
- `latest.json` - Most recent test run (for scripts/CI)
- `latest.html` - HTML report for stakeholders
- `latest.txt` - Plain text summary
- Timestamped files for historical tracking

### Report Formats

#### JSON Report
Machine-readable format for CI/CD pipelines and historical analysis.

#### HTML Report  
Styled web page with summary statistics, color-coded status indicators, and sortable tables.

#### Console Report
Terminal output with emoji icons and formatted tables.

### Status Meanings

| Status | Icon | Meaning | Action Required |
|--------|------|---------|----------------|
| **PASS** | ✅ | Query executed successfully within all expectations | None |
| **WARNING** | ⚠️ | Query slower than expected OR minor data quality issue | Review performance |
| **CONCERN** | 🔶 | Multiple expectation violations OR significant empty data | Investigate data quality |
| **FAIL** | ❌ | Query execution error OR critical expectation violation | Fix immediately |

### Interpreting Results

**Empty Column Detection**: Framework automatically detects columns with all NULL values to identify incomplete data loads or broken relationships.

**Performance Tracking**: Compare execution times across runs using timestamped JSON files. Slowest queries highlighted for indexing decisions.

**Data Quality**: Queries designed to return 0 rows (like "Unassigned Critical Issues") use `max_rows: 0` expectation to flag when data quality degrades.

## 🔧 Customization

### Adding New Queries

1. Add query to `queries.md`
2. Configure expectations in `queries_config.yaml`
3. Create test function in appropriate `test_queries_*.py` file
4. Run tests to validate

### Modifying Expectations

Edit `queries_config.yaml` to adjust thresholds based on your data scale and performance requirements.

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Neo4j connection errors | Verify Neo4j running, check `.env` credentials |
| Empty database | Load simulation data or real data via modules |
| Slow queries | Run `scripts/create_indexes.py`, review query with PROFILE |
| Missing dependencies | `pip install pytest-html pyyaml` |
| Test failures | Check error in pytest output, run query manually in Neo4j Browser |

## 📈 CI/CD Integration

### Using JSON Reports in Scripts
Load `tests/neo4j_queries/results/latest.json` to check test results, failed queries, or performance metrics programmatically.

### Environment Setup
- Use Neo4j Docker service in CI
- Set environment variables for connection
- Load test data before running tests
- Upload test reports as artifacts

## 📚 Additional Resources

- [QUICK_START.md](QUICK_START.md) - 2-minute setup guide
- [queries.md](queries.md) - Complete query reference
- [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) - Implementation details
- [design/high-level-design.md](../../design/high-level-design.md) - Project architecture
- [design/INDEX_STRATEGY.md](../../design/INDEX_STRATEGY.md) - Index optimization

## 🤝 Contributing

When adding new queries:
1. Document in `queries.md` first
2. Add realistic expectations to `queries_config.yaml`
3. Create test function following existing patterns
4. Ensure tests pass before committing

---

**Framework Version**: 1.0  
**Last Updated**: February 2026  
**Python**: 3.8+  
**Neo4j**: 4.4+
