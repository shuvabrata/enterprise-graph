"""
Data models for property validation results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class PopulationCategory(Enum):
    """Category for property population status."""
    FULL = "FULL"          # 100% populated
    PARTIAL = "PARTIAL"    # 1-99% populated
    EMPTY = "EMPTY"        # 0% populated


@dataclass
class PropertyMetadata:
    """Metadata about a property from the dataclass definition."""
    name: str
    python_type: str
    is_optional: bool


@dataclass
class EntityMetadata:
    """Metadata about an entity type discovered from models.py."""
    entity_name: str
    properties: List[PropertyMetadata]


@dataclass
class PropertyValidationResult:
    """Validation result for a single property."""
    property_name: str
    entity_or_rel_type: str
    total_count: int
    populated_count: int
    empty_count: int
    population_percentage: float
    category: PopulationCategory
    is_required: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'property_name': self.property_name,
            'entity_or_rel_type': self.entity_or_rel_type,
            'total_count': self.total_count,
            'populated_count': self.populated_count,
            'empty_count': self.empty_count,
            'population_percentage': self.population_percentage,
            'category': self.category.value,
            'is_required': self.is_required
        }


@dataclass
class ValidationReport:
    """Complete validation report for all entities and relationships."""
    timestamp: datetime
    entity_results: Dict[str, List[PropertyValidationResult]]
    relationship_results: Dict[str, List[PropertyValidationResult]]
    failure_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'entity_results': {
                entity_type: [result.to_dict() for result in results]
                for entity_type, results in self.entity_results.items()
            },
            'relationship_results': {
                rel_type: [result.to_dict() for result in results]
                for rel_type, results in self.relationship_results.items()
            },
            'failure_count': self.failure_count,
            'summary': self._generate_summary()
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_properties = sum(len(results) for results in self.entity_results.values())
        total_rel_properties = sum(len(results) for results in self.relationship_results.values())
        
        full_count = 0
        partial_count = 0
        empty_count = 0
        
        for results in self.entity_results.values():
            for result in results:
                if result.category == PopulationCategory.FULL:
                    full_count += 1
                elif result.category == PopulationCategory.PARTIAL:
                    partial_count += 1
                else:
                    empty_count += 1
        
        for results in self.relationship_results.values():
            for result in results:
                if result.category == PopulationCategory.FULL:
                    full_count += 1
                elif result.category == PopulationCategory.PARTIAL:
                    partial_count += 1
                else:
                    empty_count += 1
        
        return {
            'total_entity_types': len(self.entity_results),
            'total_relationship_types': len(self.relationship_results),
            'total_properties_validated': total_properties + total_rel_properties,
            'full_population': full_count,
            'partial_population': partial_count,
            'empty_population': empty_count,
            'failures': self.failure_count
        }
