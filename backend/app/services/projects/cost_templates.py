# backend/app/services/projects/cost_templates.py
"""
Centralized repository for construction cost templates.
Maps room types and object types (wall, floor, ceiling) to standard cost items,
units, and baseline prices for rule-based estimation.
"""
from typing import Dict, List, Tuple

# Keys are tuples of (room_type, object_type)
# object_type values: 'wall', 'floor', 'ceiling'
COST_TEMPLATES: Dict[Tuple[str, str], List[dict]] = {
    # --- Kitchen ---
    ("Kitchen", "wall"): [
        {"item_name": "Antibacterial Tile Purchase", "category": "Tiling", "unit": "m2", "unit_price": 450000, "duration_days": 1},
        {"item_name": "Wall Tile Installation", "category": "Labor", "unit": "m2", "unit_price": 180000, "duration_days": 2},
        {"item_name": "C1 Powder Tile Adhesive", "category": "Material", "unit": "kg", "unit_price": 25000, "duration_days": 1},
        {"item_name": "Antibacterial Grouting", "category": "Finishing", "unit": "m2", "unit_price": 35000, "duration_days": 1},
    ],
    ("Kitchen", "floor"): [
        {"item_name": "Antibacterial Floor Ceramic Purchase", "category": "Tiling", "unit": "m2", "unit_price": 380000, "duration_days": 1},
        {"item_name": "Floor Ceramic Installation", "category": "Labor", "unit": "m2", "unit_price": 150000, "duration_days": 2},
        {"item_name": "Paste Tile Adhesive", "category": "Material", "unit": "kg", "unit_price": 22000, "duration_days": 1},
        {"item_name": "Floor Waterproofing", "category": "Insulation", "unit": "m2", "unit_price": 95000, "duration_days": 1},
    ],
    ("Kitchen", "ceiling"): [
        {"item_name": "Ceiling Oil Paint", "category": "Painting", "unit": "m2", "unit_price": 85000, "duration_days": 1},
        {"item_name": "Ceiling Plaster Preparation", "category": "Preparation", "unit": "m2", "unit_price": 45000, "duration_days": 1},
    ],

    # --- Bathroom ---
    ("Bathroom", "wall"): [
        {"item_name": "Bathroom Tiles", "category": "Tiling", "unit": "m2", "unit_price": 320000, "duration_days": 1},
        {"item_name": "Bathroom Tile Installation", "category": "Labor", "unit": "m2", "unit_price": 190000, "duration_days": 2},
        {"item_name": "Wall Waterproofing (up to 2m)", "category": "Insulation", "unit": "m2", "unit_price": 110000, "duration_days": 1},
    ],
    ("Bathroom", "floor"): [
        {"item_name": "Bathroom Floor Ceramic", "category": "Tiling", "unit": "m2", "unit_price": 300000, "duration_days": 1},
        {"item_name": "Floor Sloping and Waterproofing", "category": "Insulation", "unit": "m2", "unit_price": 140000, "duration_days": 2},
    ],
    ("Bathroom", "ceiling"): [
        {"item_name": "Moisture-Resistant PVC False Ceiling", "category": "Ceiling", "unit": "m2", "unit_price": 280000, "duration_days": 1},
    ],

    # --- Bedroom ---
    ("Bedroom", "wall"): [
        {"item_name": "Plastic/Acrylic Wall Paint", "category": "Painting", "unit": "m2", "unit_price": 65000, "duration_days": 1},
        {"item_name": "Wall Putty and Preparation", "category": "Preparation", "unit": "m2", "unit_price": 35000, "duration_days": 1},
        {"item_name": "Wallpaper (Optional)", "category": "Decoration", "unit": "roll", "unit_price": 450000, "duration_days": 1},
    ],
    ("Bedroom", "floor"): [
        {"item_name": "Laminate Parquet", "category": "Flooring", "unit": "m2", "unit_price": 350000, "duration_days": 1},
        {"item_name": "Parquet + Skirting Board Installation", "category": "Labor", "unit": "m2", "unit_price": 95000, "duration_days": 2},
        {"item_name": "Parquet Underlay Foam", "category": "Material", "unit": "m2", "unit_price": 15000, "duration_days": 1},
    ],
    ("Bedroom", "ceiling"): [
        {"item_name": "Ceiling Plastic Paint", "category": "Painting", "unit": "m2", "unit_price": 55000, "duration_days": 1},
    ],

    # --- Living Room ---
    ("Living Room", "wall"): [
        {"item_name": "Premium Acrylic Paint", "category": "Painting", "unit": "m2", "unit_price": 75000, "duration_days": 1},
        {"item_name": "Decorative Framing or Drywall", "category": "Decoration", "unit": "m2", "unit_price": 220000, "duration_days": 2},
    ],
    ("Living Room", "floor"): [
        {"item_name": "Marble Stone or Large Ceramic", "category": "Flooring", "unit": "m2", "unit_price": 550000, "duration_days": 1},
        {"item_name": "Stone Installation with Mortar", "category": "Labor", "unit": "m2", "unit_price": 160000, "duration_days": 2},
    ],
    ("Living Room", "ceiling"): [
        {"item_name": "Drywall Ceiling with Lighting", "category": "Ceiling", "unit": "m2", "unit_price": 320000, "duration_days": 3},
    ],
}

# Default template for undefined combinations
DEFAULT_TEMPLATE = [
    {"item_name": "General Item", "category": "General", "unit": "piece", "unit_price": 100000, "duration_days": 1}
]

def get_template(room_type: str, object_type: str) -> List[dict]:
    """
    Retrieves a list of cost items based on room type and object type.
    
    Args:
        room_type: Semantic name of the room (e.g., 'Kitchen').
        object_type: Surface type ('wall', 'floor', 'ceiling').
        
    Returns:
        List of dictionaries containing cost item details.
    """
    key = (room_type, object_type)
    return COST_TEMPLATES.get(key, DEFAULT_TEMPLATE)