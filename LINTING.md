# Linting Guide

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

This will install pylint and all necessary linting dependencies.

## Running Pylint

### Basic Linting

Run pylint on the entire codebase (excluding tests and simulation):

```bash
pylint .
```

### Generate Reports

```bash
pylint . --output-format=json  | pylint-json2html -o reports/pylint_report.html
```

#### Colorized Terminal Output

For colorized output in the terminal:

```bash
pylint . --output-format=colorized
```

#### Parseable Format (for CI/CD)

For easy parsing in scripts or CI/CD pipelines:

```bash
pylint . --output-format=parseable
```

## Understanding Pylint Output

Pylint assigns a score out of 10 based on code quality. Message types include:

- **C**: Convention - Programming standard violation
- **R**: Refactor - Code smell or design issue
- **W**: Warning - Potential bug or minor issue
- **E**: Error - Probable bug
- **F**: Fatal - Error preventing further processing

## Configuration

The project's pylint configuration is defined in [.pylintrc](.pylintrc). Key settings include:

- **Ignored directories**: tests, simulation, .venv, __pycache__, etc.
- **Maximum line length**: 120 characters
- **Naming conventions**: snake_case for functions/variables, PascalCase for classes
- **Disabled checks**: Missing docstrings, too-few-public-methods, and others

## Common Workflow

1. **Before committing code**:
   ```bash
   pylint .
   ```

2. **Generate HTML report for review**:
   ```bash
   mkdir -p reports
   pylint . --output-format=json | pylint-json2html -o reports/pylint_report.html
   ```

3. **Check specific module**:
   ```bash
   pylint modules/github/
   ```

## Continuous Integration

For CI/CD pipelines, use the exit code to fail builds on errors:

```bash
pylint . --fail-under=8.0
```

This will fail if the code score is below 8.0 out of 10.

## Reports Directory

Linting reports are stored in the `reports/` directory:

- `reports/pylint_report.txt` - Text format report
- `reports/pylint_report.json` - JSON format report
- `reports/pylint_report.html` - HTML format report (requires pylint-json2html)

Make sure the `reports/` directory exists before generating reports:

```bash
mkdir -p reports
```

## Available Output Formats

Pylint supports the following output formats:

- **text** (default) - Standard text output
- **parseable** - Easy to parse format for scripts
- **colorized** - Color-coded terminal output
- **json** - Machine-readable JSON format
- **msvs** - Microsoft Visual Studio format

