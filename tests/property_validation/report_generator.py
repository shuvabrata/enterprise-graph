"""
Generate reports for property validation results.
"""

import json
from pathlib import Path
from typing import List
from tests.property_validation.models import ValidationReport, PropertyValidationResult, PopulationCategory


# ANSI color codes for console output
class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def generate_console_report(report: ValidationReport) -> None:
    """
    Generate and print console report with colored output.
    
    Args:
        report: ValidationReport to display
    """
    print(f"\n{Colors.BOLD}{'='*100}")
    print(f"PROPERTY VALIDATION REPORT")
    print(f"Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}{Colors.RESET}\n")
    
    # Summary
    summary = report._generate_summary()
    print(f"{Colors.BOLD}SUMMARY{Colors.RESET}")
    print(f"  Entity Types: {summary['total_entity_types']}")
    print(f"  Relationship Types: {summary['total_relationship_types']}")
    print(f"  Total Properties: {summary['total_properties_validated']}")
    print(f"  {Colors.GREEN}✓ Full Population (100%): {summary['full_population']}{Colors.RESET}")
    print(f"  {Colors.YELLOW}⚠ Partial Population (1-99%): {summary['partial_population']}{Colors.RESET}")
    print(f"  {Colors.RED}✗ Empty (0%): {summary['empty_population']}{Colors.RESET}")
    if summary['failures'] > 0:
        print(f"  {Colors.RED}{Colors.BOLD}❌ FAILURES (Required properties at 0%): {summary['failures']}{Colors.RESET}")
    else:
        print(f"  {Colors.GREEN}✓ No failures{Colors.RESET}")
    print()
    
    # Entity results
    if report.entity_results:
        print(f"{Colors.BOLD}{'='*100}")
        print(f"ENTITY PROPERTIES")
        print(f"{'='*100}{Colors.RESET}\n")
        
        for entity_type in sorted(report.entity_results.keys()):
            results = report.entity_results[entity_type]
            _print_entity_table(entity_type, results)
    
    # Relationship results
    if report.relationship_results:
        print(f"{Colors.BOLD}{'='*100}")
        print(f"RELATIONSHIP PROPERTIES")
        print(f"{'='*100}{Colors.RESET}\n")
        
        for rel_type in sorted(report.relationship_results.keys()):
            results = report.relationship_results[rel_type]
            _print_relationship_table(rel_type, results)


def _print_entity_table(entity_type: str, results: List[PropertyValidationResult]) -> None:
    """Print a table for entity property validation results."""
    print(f"{Colors.BOLD}{Colors.BLUE}{entity_type}{Colors.RESET}")
    print(f"{'-'*100}")
    
    # Header
    header = f"{'Property':<30} {'Required':<10} {'Total':<8} {'Populated':<10} {'Empty':<8} {'%':<8} {'Category':<10}"
    print(header)
    print(f"{'-'*100}")
    
    # Sort by required first, then by category (EMPTY, PARTIAL, FULL)
    sorted_results = sorted(results, key=lambda r: (not r.is_required, r.category.value))
    
    for result in sorted_results:
        req_str = "YES" if result.is_required else "no"
        
        # Color code the category
        if result.category == PopulationCategory.FULL:
            category_str = f"{Colors.GREEN}FULL{Colors.RESET}"
            pct_str = f"{Colors.GREEN}{result.population_percentage:6.2f}%{Colors.RESET}"
        elif result.category == PopulationCategory.PARTIAL:
            category_str = f"{Colors.YELLOW}PARTIAL{Colors.RESET}"
            pct_str = f"{Colors.YELLOW}{result.population_percentage:6.2f}%{Colors.RESET}"
        else:
            category_str = f"{Colors.RED}EMPTY{Colors.RESET}"
            pct_str = f"{Colors.RED}{result.population_percentage:6.2f}%{Colors.RESET}"
            if result.is_required:
                category_str = f"{Colors.RED}{Colors.BOLD}EMPTY ❌{Colors.RESET}"
        
        row = f"{result.property_name:<30} {req_str:<10} {result.total_count:<8} {result.populated_count:<10} {result.empty_count:<8} {pct_str:<15} {category_str}"
        print(row)
    
    print()


def _print_relationship_table(rel_type: str, results: List[PropertyValidationResult]) -> None:
    """Print a table for relationship property validation results."""
    print(f"{Colors.BOLD}{Colors.BLUE}{rel_type}{Colors.RESET}")
    print(f"{'-'*100}")
    
    # Header (no "Required" column for relationships)
    header = f"{'Property':<30} {'Total':<8} {'Populated':<10} {'Empty':<8} {'%':<8} {'Category':<10}"
    print(header)
    print(f"{'-'*100}")
    
    # Sort by category
    sorted_results = sorted(results, key=lambda r: r.category.value)
    
    for result in sorted_results:
        # Color code the category
        if result.category == PopulationCategory.FULL:
            category_str = f"{Colors.GREEN}FULL{Colors.RESET}"
            pct_str = f"{Colors.GREEN}{result.population_percentage:6.2f}%{Colors.RESET}"
        elif result.category == PopulationCategory.PARTIAL:
            category_str = f"{Colors.YELLOW}PARTIAL{Colors.RESET}"
            pct_str = f"{Colors.YELLOW}{result.population_percentage:6.2f}%{Colors.RESET}"
        else:
            category_str = f"{Colors.RED}EMPTY{Colors.RESET}"
            pct_str = f"{Colors.RED}{result.population_percentage:6.2f}%{Colors.RESET}"
        
        row = f"{result.property_name:<30} {result.total_count:<8} {result.populated_count:<10} {result.empty_count:<8} {pct_str:<15} {category_str}"
        print(row)
    
    print()


def generate_json_report(report: ValidationReport, output_path: Path) -> None:
    """
    Generate JSON report file.
    
    Args:
        report: ValidationReport to save
        output_path: Path to write JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    print(f"{Colors.GREEN}✓ JSON report saved to: {output_path}{Colors.RESET}")


def generate_html_report(report: ValidationReport, output_path: Path) -> None:
    """
    Generate HTML report file with interactive tables.
    
    Args:
        report: ValidationReport to save
        output_path: Path to write HTML file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = report._generate_summary()
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property Validation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 8px;
        }}
        .summary {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .summary-item {{
            padding: 10px;
            border-left: 4px solid #4CAF50;
        }}
        .summary-item strong {{
            display: block;
            font-size: 0.9em;
            color: #666;
        }}
        .summary-item .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95em;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .entity-section {{
            margin: 30px 0;
        }}
        .entity-name {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2196F3;
            margin: 15px 0 10px 0;
        }}
        .category-FULL {{
            background-color: #4CAF50;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .category-PARTIAL {{
            background-color: #FF9800;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .category-EMPTY {{
            background-color: #f44336;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .required-yes {{
            font-weight: bold;
            color: #d32f2f;
        }}
        .required-no {{
            color: #999;
        }}
        .failure-badge {{
            background-color: #f44336;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            margin-left: 5px;
            font-size: 0.85em;
        }}
        .timestamp {{
            color: #999;
            font-size: 0.9em;
        }}
        .search-box {{
            margin: 20px 0;
            padding: 10px;
            width: 100%;
            font-size: 1em;
            border: 2px solid #ddd;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Property Validation Report</h1>
        <p class="timestamp">Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="summary-item">
                <strong>Entity Types</strong>
                <div class="value">{summary['total_entity_types']}</div>
            </div>
            <div class="summary-item">
                <strong>Relationship Types</strong>
                <div class="value">{summary['total_relationship_types']}</div>
            </div>
            <div class="summary-item">
                <strong>Total Properties</strong>
                <div class="value">{summary['total_properties_validated']}</div>
            </div>
            <div class="summary-item" style="border-left-color: #4CAF50;">
                <strong>Full Population</strong>
                <div class="value" style="color: #4CAF50;">{summary['full_population']}</div>
            </div>
            <div class="summary-item" style="border-left-color: #FF9800;">
                <strong>Partial Population</strong>
                <div class="value" style="color: #FF9800;">{summary['partial_population']}</div>
            </div>
            <div class="summary-item" style="border-left-color: #f44336;">
                <strong>Empty</strong>
                <div class="value" style="color: #f44336;">{summary['empty_population']}</div>
            </div>
            <div class="summary-item" style="border-left-color: {'#f44336' if summary['failures'] > 0 else '#4CAF50'};">
                <strong>Failures</strong>
                <div class="value" style="color: {'#f44336' if summary['failures'] > 0 else '#4CAF50'};">{summary['failures']}</div>
            </div>
        </div>
        
        <input type="text" class="search-box" id="searchBox" placeholder="Search entities, properties, or categories..." onkeyup="searchTable()">
        
        <h2>Entity Properties</h2>
"""
    
    # Add entity tables
    for entity_type in sorted(report.entity_results.keys()):
        results = report.entity_results[entity_type]
        html_content += _generate_entity_table_html(entity_type, results)
    
    # Add relationship tables
    html_content += "<h2>Relationship Properties</h2>\n"
    for rel_type in sorted(report.relationship_results.keys()):
        results = report.relationship_results[rel_type]
        html_content += _generate_relationship_table_html(rel_type, results)
    
    # Add JavaScript for search
    html_content += """
        <script>
            function searchTable() {
                const input = document.getElementById('searchBox');
                const filter = input.value.toLowerCase();
                const sections = document.getElementsByClassName('entity-section');
                
                for (let section of sections) {
                    const entityName = section.querySelector('.entity-name').textContent.toLowerCase();
                    const table = section.querySelector('table');
                    const rows = table.getElementsByTagName('tr');
                    let sectionHasMatch = false;
                    
                    for (let i = 1; i < rows.length; i++) {
                        const row = rows[i];
                        const text = row.textContent.toLowerCase();
                        
                        if (text.includes(filter) || entityName.includes(filter)) {
                            row.style.display = '';
                            sectionHasMatch = true;
                        } else {
                            row.style.display = 'none';
                        }
                    }
                    
                    section.style.display = sectionHasMatch || filter === '' ? '' : 'none';
                }
            }
        </script>
    </div>
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"{Colors.GREEN}✓ HTML report saved to: {output_path}{Colors.RESET}")


def _generate_entity_table_html(entity_type: str, results: List[PropertyValidationResult]) -> str:
    """Generate HTML table for entity properties."""
    html = f'<div class="entity-section">\n'
    html += f'<div class="entity-name">{entity_type}</div>\n'
    html += '<table>\n<thead>\n<tr>\n'
    html += '<th>Property</th><th>Required</th><th>Total</th><th>Populated</th><th>Empty</th><th>%</th><th>Category</th>\n'
    html += '</tr>\n</thead>\n<tbody>\n'
    
    sorted_results = sorted(results, key=lambda r: (not r.is_required, r.category.value))
    
    for result in sorted_results:
        req_class = 'required-yes' if result.is_required else 'required-no'
        req_text = 'YES' if result.is_required else 'no'
        failure_badge = '<span class="failure-badge">FAILURE</span>' if result.is_required and result.category == PopulationCategory.EMPTY else ''
        
        html += '<tr>\n'
        html += f'<td>{result.property_name}{failure_badge}</td>\n'
        html += f'<td class="{req_class}">{req_text}</td>\n'
        html += f'<td>{result.total_count}</td>\n'
        html += f'<td>{result.populated_count}</td>\n'
        html += f'<td>{result.empty_count}</td>\n'
        html += f'<td>{result.population_percentage:.2f}%</td>\n'
        html += f'<td><span class="category-{result.category.value}">{result.category.value}</span></td>\n'
        html += '</tr>\n'
    
    html += '</tbody>\n</table>\n</div>\n'
    return html


def _generate_relationship_table_html(rel_type: str, results: List[PropertyValidationResult]) -> str:
    """Generate HTML table for relationship properties."""
    html = f'<div class="entity-section">\n'
    html += f'<div class="entity-name">{rel_type}</div>\n'
    html += '<table>\n<thead>\n<tr>\n'
    html += '<th>Property</th><th>Total</th><th>Populated</th><th>Empty</th><th>%</th><th>Category</th>\n'
    html += '</tr>\n</thead>\n<tbody>\n'
    
    sorted_results = sorted(results, key=lambda r: r.category.value)
    
    for result in sorted_results:
        html += '<tr>\n'
        html += f'<td>{result.property_name}</td>\n'
        html += f'<td>{result.total_count}</td>\n'
        html += f'<td>{result.populated_count}</td>\n'
        html += f'<td>{result.empty_count}</td>\n'
        html += f'<td>{result.population_percentage:.2f}%</td>\n'
        html += f'<td><span class="category-{result.category.value}">{result.category.value}</span></td>\n'
        html += '</tr>\n'
    
    html += '</tbody>\n</table>\n</div>\n'
    return html
