"""
Import and analyze relationship definitions from codebase.
"""

import sys
from pathlib import Path
from typing import Dict, Set, Tuple, Optional

# Add project root to path to import db.models
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from db.models import BIDIRECTIONAL_RELATIONSHIPS


def get_expected_relationships() -> Dict[str, str]:
    """
    Get expected relationships from BIDIRECTIONAL_RELATIONSHIPS in db/models.py.
    
    Returns:
        Dictionary mapping relationship type to its reverse type.
        For same-name bidirectional, both forward and reverse map to same name.
        For unidirectional, maps to None.
    """
    return dict(BIDIRECTIONAL_RELATIONSHIPS)


def get_all_relationship_names() -> Set[str]:
    """
    Get all unique relationship names (both forward and reverse).
    
    Returns:
        Set of all unique relationship type names
    """
    all_names = set()
    for forward, reverse in BIDIRECTIONAL_RELATIONSHIPS.items():
        all_names.add(forward)
        if reverse:
            all_names.add(reverse)
    return all_names


def categorize_relationships() -> Tuple[Set[str], Dict[str, Set[str]], Set[str]]:
    """
    Categorize relationships by type.
    
    Returns:
        Tuple of (same_name_bidirectional, different_name_bidirectional, unidirectional)
        - same_name_bidirectional: Set of relationship names that are same in both directions
        - different_name_bidirectional: Dict mapping forward->reverse for directional pairs
        - unidirectional: Set of relationships that only go one way (reverse is None or not bidirectional)
    """
    same_name = set()
    different_name = {}
    unidirectional = set()
    
    processed = set()
    
    for forward, reverse in BIDIRECTIONAL_RELATIONSHIPS.items():
        if forward in processed:
            continue
            
        if forward == reverse:
            # Same name bidirectional
            same_name.add(forward)
            processed.add(forward)
        elif reverse and reverse in BIDIRECTIONAL_RELATIONSHIPS:
            # Different name bidirectional (both directions exist in dict)
            different_name[forward] = reverse
            processed.add(forward)
            processed.add(reverse)
        else:
            # Could be unidirectional or incomplete definition
            # For now, treat as different-name if reverse exists
            if reverse:
                different_name[forward] = reverse
                processed.add(forward)
    
    return same_name, different_name, unidirectional


def get_relationship_pair(rel_type: str) -> Optional[str]:
    """
    Get the paired relationship type for a bidirectional relationship.
    
    Args:
        rel_type: Relationship type name
        
    Returns:
        The reverse relationship type, or None if unidirectional or same-name bidirectional
    """
    if rel_type in BIDIRECTIONAL_RELATIONSHIPS:
        reverse = BIDIRECTIONAL_RELATIONSHIPS[rel_type]
        if reverse == rel_type:
            return None  # Same-name bidirectional
        return reverse
    
    # Check if this is a reverse relationship
    for forward, reverse in BIDIRECTIONAL_RELATIONSHIPS.items():
        if reverse == rel_type and forward != reverse:
            return forward
    
    return None


def is_bidirectional(rel_type: str) -> bool:
    """
    Check if a relationship type is bidirectional.
    
    Args:
        rel_type: Relationship type name
        
    Returns:
        True if relationship is bidirectional (same or different name)
    """
    if rel_type in BIDIRECTIONAL_RELATIONSHIPS:
        return True
    
    # Check if it's a reverse relationship
    for forward, reverse in BIDIRECTIONAL_RELATIONSHIPS.items():
        if reverse == rel_type:
            return True
    
    return False


def is_same_name_bidirectional(rel_type: str) -> bool:
    """
    Check if a relationship uses the same name in both directions.
    
    Args:
        rel_type: Relationship type name
        
    Returns:
        True if relationship uses same name bidirectionally
    """
    return rel_type in BIDIRECTIONAL_RELATIONSHIPS and BIDIRECTIONAL_RELATIONSHIPS[rel_type] == rel_type


def print_relationship_summary():
    """Print summary of expected relationships."""
    same_name, different_name, unidirectional = categorize_relationships()
    all_names = get_all_relationship_names()
    
    print(f"\n{'='*80}")
    print(f"EXPECTED RELATIONSHIPS FROM db/models.py")
    print(f"{'='*80}\n")
    
    print(f"Same-name bidirectional ({len(same_name)}):")
    for name in sorted(same_name):
        print(f"  - {name} ↔ {name}")
    
    print(f"\nDifferent-name bidirectional ({len(different_name)} pairs):")
    processed = set()
    for forward, reverse in sorted(different_name.items()):
        if forward not in processed and reverse not in processed:
            print(f"  - {forward} ↔ {reverse}")
            processed.add(forward)
            processed.add(reverse)
    
    if unidirectional:
        print(f"\nUnidirectional ({len(unidirectional)}):")
        for name in sorted(unidirectional):
            print(f"  - {name} →")
    
    print(f"\nTotal unique relationship names: {len(all_names)}")


if __name__ == "__main__":
    print_relationship_summary()
