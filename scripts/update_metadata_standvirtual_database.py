#!/usr/bin/env python3
"""
Script para contar marcas e modelos do standvirtual_master_database.json e atualizar o metadata.
"""
import json
import os

def update_metadata(db_file):
    if not os.path.exists(db_file):
        print(f"❌ Arquivo {db_file} não encontrado!")
        return
    with open(db_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    brands = data.get('brands', {})
    total_brands = len(brands)
    total_models = sum(len(brand.get('models', [])) for brand in brands.values())
    data['metadata']['total_brands'] = total_brands
    data['metadata']['total_models'] = total_models
    if 'completion_rate' in data['metadata']:
        data['metadata']['completion_rate'] = round((total_models / (total_brands * 10)) * 100, 1)
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Metadata atualizado! Marcas: {total_brands}, Modelos: {total_models}")

if __name__ == "__main__":
    db_file = "data/json/standvirtual_database.json"
    update_metadata(db_file) 