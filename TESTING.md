# Testing Guide

## Setup

### Python Virtual Environment

First, create and activate a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

Install both production and development requirements:

```bash
pip install -r requirements.txt
pip install -r requirements_dev.txt
```

This will install pytest and all necessary testing dependencies.

## Running Tests

### Basic Test Execution

Run all tests with verbose output:

```bash
pytest tests/ -v -s
```

### Generate HTML Report

To generate an HTML test report:

```bash
pytest tests/ -v -s --html=reports/test_report.html --self-contained-html
```

## Test Reports

The test suite generates additional HTML reports in specific test directories:

### Neo4j Query Test Report

Location: `tests/neo4j_queries/results/latest.html`

This report contains validation results for Neo4j queries and graph structure tests.

### Property Validation Report

Location: `tests/property_validation/results/report.html`

This report shows property coverage and validation results for all entity types in the graph model, including:
- Property population percentages
- Required vs optional field validation
- Data completeness metrics

