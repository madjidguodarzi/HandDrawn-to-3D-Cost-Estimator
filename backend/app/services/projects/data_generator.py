# backend/app/services/projects/data_generator.py
"""
Synthetic Data Generator for Construction Cost Estimation Models.

Generates realistic training data with embedded domain logic:
- Material costs scale with quality tier (Standard/Premium/Luxury).
- Tiling costs include room-specific surcharges (Bathroom/Kitchen).
- Labor costs remain stable across quality tiers to reflect market standards.
- Noise is minimized for labor to simulate standardized wage structures.
"""
import pandas as pd
import numpy as np
import os

def generate_synthetic_data(num_samples: int = 10000) -> pd.DataFrame:
    """
    Generate synthetic construction cost data with domain-aware pricing rules.
    
    Args:
        num_samples: Number of data points to generate. Default is 10000.
        
    Returns:
        DataFrame containing item_name, area_m2, room_type, quality, and unit_price.
    """
    np.random.seed(42)
    
    # Define items with fixed pricing logic and attributes
    items = [
        {
            'name': 'Ceramic Tile Purchase', 
            'type': 'material', 
            'base_price': 45, 
            'affected_by_quality': True,  # Only materials are affected by quality tier
            'affected_by_room': True       # Only tiles are affected by room type
        },
        {
            'name': 'Tile Adhesive', 
            'type': 'material', 
            'base_price': 8, 'affected_by_quality': False, # Adhesive has a fixed base price
            'affected_by_room': False
        },   
        {
            'name': 'Labor Installation', 
            'type': 'labor', 
            'base_price': 12,             # Labor cost must remain constant regardless of material quality
            'affected_by_quality': False, 
            'affected_by_room': False     # Room type has negligible impact on labor cost
        },  
        {
            'name': 'Grout Material', 
            'type': 'material', 
            'base_price': 3, 
            'affected_by_quality': False,
            'affected_by_room': False
        }
    ]
    
    room_types = ['Bedroom', 'Kitchen', 'Bathroom', 'Living Room']
    qualities = ['Standard', 'Premium', 'Luxury']
    
    data = []
    for _ in range(num_samples):
        item = np.random.choice(items)
        r_type = np.random.choice(room_types)
        quality = np.random.choice(qualities)
        area = np.random.uniform(5, 50)
        
        price = item['base_price']
        
        # Rule 1: Quality multiplier applies only to material purchases
        if item['affected_by_quality']:
            if quality == 'Luxury': price *= 1.6
            elif quality == 'Premium': price *= 1.3
            
        # Rule 2: Room type surcharge applies only to tiling items
        if item['affected_by_room'] and 'Tile' in item['name']:
            if r_type == 'Bathroom': price += 5
            if r_type == 'Kitchen': price += 2
            
        # Rule 3: Minimal noise simulation (near-zero for labor to reflect standardized wages)
        noise_std = 0.2 if item['type'] == 'labor' else 1.0
        noise = np.random.normal(0, noise_std)
        
        final_price = max(1, price + noise)
        
        data.append({
            'item_name': item['name'],      
            'area_m2': round(area, 2),
            'room_type': r_type,
            'quality': quality,
            'unit_price': round(final_price, 2)
        })
        
    df = pd.DataFrame(data)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/item_training_data.csv", index=False)
    
    # Print statistics to verify data integrity
    print(f"✅ Generated {num_samples} samples.")
    labor_stats = df[df['item_name']=='Labor Installation']['unit_price'].describe()
    print(f"📊 Labor Installation Stats:\n{labor_stats}")
    
    return df