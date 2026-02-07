"""
Execute property validation against Neo4j database.
"""

from datetime import datetime
from typing import Dict, List
from neo4j import Session

from tests.property_validation.models import (
    PropertyValidationResult,
    ValidationReport,
    PopulationCategory,
    EntityMetadata
)
from tests.property_validation.model_inspector import discover_entity_types
from tests.property_validation.relationship_inspector import discover_all_relationships
from tests.property_validation.query_generator import (
    generate_node_property_query,
    generate_relationship_property_query
)


class PropertyValidator:
    """Validates property population across Neo4j nodes and relationships."""
    
    def __init__(self, session: Session):
        """
        Initialize the validator.
        
        Args:
            session: Neo4j session to use for queries
        """
        self.session = session
        self.entity_metadata: Dict[str, EntityMetadata] = {}
        self.relationship_metadata: Dict[str, List[str]] = {}
    
    def categorize_result(self, populated_count: int, total_count: int) -> PopulationCategory:
        """
        Categorize a validation result based on population percentage.
        
        Args:
            populated_count: Number of entities with property populated
            total_count: Total number of entities
            
        Returns:
            PopulationCategory (FULL, PARTIAL, or EMPTY)
        """
        if total_count == 0:
            return PopulationCategory.EMPTY
        
        percentage = (populated_count / total_count) * 100
        
        if percentage == 100.0:
            return PopulationCategory.FULL
        elif percentage > 0:
            return PopulationCategory.PARTIAL
        else:
            return PopulationCategory.EMPTY
    
    def validate_entity(self, entity_name: str, metadata: EntityMetadata) -> List[PropertyValidationResult]:
        """
        Validate all properties for a specific entity type.
        
        Args:
            entity_name: The name of the entity (e.g., "Person")
            metadata: Metadata about the entity's properties
            
        Returns:
            List of PropertyValidationResult objects
        """
        results = []
        
        for prop in metadata.properties:
            query = generate_node_property_query(entity_name, prop.name)
            
            try:
                result = self.session.run(query)
                record = result.single()
                
                if record:
                    total = record["total"]
                    populated = record["populated"]
                    empty = record["empty"]
                    
                    if total > 0:
                        percentage = (populated / total) * 100
                    else:
                        percentage = 0.0
                    
                    category = self.categorize_result(populated, total)
                    
                    results.append(PropertyValidationResult(
                        property_name=prop.name,
                        entity_or_rel_type=entity_name,
                        total_count=total,
                        populated_count=populated,
                        empty_count=empty,
                        population_percentage=percentage,
                        category=category,
                        is_required=not prop.is_optional
                    ))
            except Exception as e:
                print(f"Error validating {entity_name}.{prop.name}: {e}")
                # Create a failed result
                results.append(PropertyValidationResult(
                    property_name=prop.name,
                    entity_or_rel_type=entity_name,
                    total_count=0,
                    populated_count=0,
                    empty_count=0,
                    population_percentage=0.0,
                    category=PopulationCategory.EMPTY,
                    is_required=not prop.is_optional
                ))
        
        return results
    
    def validate_relationship(self, rel_type: str, properties: List[str]) -> List[PropertyValidationResult]:
        """
        Validate all properties for a specific relationship type.
        
        Args:
            rel_type: The relationship type (e.g., "COLLABORATOR")
            properties: List of property names to validate
            
        Returns:
            List of PropertyValidationResult objects
        """
        results = []
        
        for prop_name in properties:
            query = generate_relationship_property_query(rel_type, prop_name)
            
            try:
                result = self.session.run(query)
                record = result.single()
                
                if record:
                    total = record["total"]
                    populated = record["populated"]
                    empty = record["empty"]
                    
                    if total > 0:
                        percentage = (populated / total) * 100
                    else:
                        percentage = 0.0
                    
                    category = self.categorize_result(populated, total)
                    
                    results.append(PropertyValidationResult(
                        property_name=prop_name,
                        entity_or_rel_type=rel_type,
                        total_count=total,
                        populated_count=populated,
                        empty_count=empty,
                        population_percentage=percentage,
                        category=category,
                        is_required=False  # All relationship properties treated as optional
                    ))
            except Exception as e:
                print(f"Error validating relationship {rel_type}.{prop_name}: {e}")
                results.append(PropertyValidationResult(
                    property_name=prop_name,
                    entity_or_rel_type=rel_type,
                    total_count=0,
                    populated_count=0,
                    empty_count=0,
                    population_percentage=0.0,
                    category=PopulationCategory.EMPTY,
                    is_required=False
                ))
        
        return results
    
    def validate_all(self) -> ValidationReport:
        """
        Validate all entities and relationships.
        
        Returns:
            ValidationReport containing all validation results
        """
        print("Discovering entity types from db/models.py...")
        self.entity_metadata = discover_entity_types()
        print(f"Found {len(self.entity_metadata)} entity types")
        
        print("\nDiscovering relationship types from Neo4j...")
        self.relationship_metadata = discover_all_relationships(self.session)
        print(f"Found {len(self.relationship_metadata)} relationship types with properties")
        
        entity_results: Dict[str, List[PropertyValidationResult]] = {}
        relationship_results: Dict[str, List[PropertyValidationResult]] = {}
        
        # Validate entities
        print("\nValidating entity properties...")
        for entity_name, metadata in self.entity_metadata.items():
            print(f"  Validating {entity_name}...")
            results = self.validate_entity(entity_name, metadata)
            entity_results[entity_name] = results
        
        # Validate relationships
        print("\nValidating relationship properties...")
        for rel_type, properties in self.relationship_metadata.items():
            print(f"  Validating {rel_type}...")
            results = self.validate_relationship(rel_type, properties)
            relationship_results[rel_type] = results
        
        # Count failures (required properties with 0% population)
        failure_count = 0
        for results in entity_results.values():
            for result in results:
                if result.is_required and result.category == PopulationCategory.EMPTY:
                    failure_count += 1
        
        return ValidationReport(
            timestamp=datetime.now(),
            entity_results=entity_results,
            relationship_results=relationship_results,
            failure_count=failure_count
        )


if __name__ == "__main__":
    # Test validation
    import os
    from neo4j import GraphDatabase
    
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            validator = PropertyValidator(session)
            report = validator.validate_all()
            print(f"\nValidation complete!")
            print(f"Failures: {report.failure_count}")
    finally:
        driver.close()
