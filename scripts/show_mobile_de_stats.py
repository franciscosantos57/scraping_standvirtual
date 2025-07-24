#!/usr/bin/env python3
"""
Script para mostrar estatísticas dos dados extraídos do mobile.de

Mostra informações sobre as marcas e modelos extraídos
"""

import json
from pathlib import Path


def load_data(filepath):
    """Carrega os dados do arquivo JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def show_stats(data):
    """Mostra estatísticas dos dados"""
    metadata = data['metadata']
    brands = data['brands']
    
    print("="*60)
    print("ESTATÍSTICAS DOS DADOS EXTRAÍDOS DO MOBILE.DE")
    print("="*60)
    print(f"Fonte: {metadata['source']}")
    print(f"Data da extração: {metadata['extraction_date']}")
    print(f"Total de marcas: {metadata['total_brands']}")
    print(f"Total de modelos: {metadata['total_models']}")
    print("="*60)
    
    # Top 10 marcas com mais modelos
    brands_by_models = sorted(
        [(brand_data['name'], brand_data['total_models']) 
         for brand_data in brands.values()],
        key=lambda x: x[1],
        reverse=True
    )
    
    print("\nTOP 10 MARCAS COM MAIS MODELOS:")
    print("-" * 40)
    for i, (name, count) in enumerate(brands_by_models[:10], 1):
        print(f"{i:2d}. {name:<20} {count:3d} modelos")
    
    # Marcas sem modelos
    brands_no_models = [brand_data['name'] for brand_data in brands.values() 
                       if brand_data['total_models'] == 0]
    
    print(f"\nMARCAS SEM MODELOS DISPONÍVEIS ({len(brands_no_models)}):")
    print("-" * 40)
    for name in sorted(brands_no_models):
        print(f"  - {name}")
    
    # Estatísticas gerais
    model_counts = [brand_data['total_models'] for brand_data in brands.values()]
    avg_models = sum(model_counts) / len(model_counts)
    max_models = max(model_counts)
    min_models = min(model_counts)
    
    print(f"\nESTATÍSTICAS GERAIS:")
    print("-" * 40)
    print(f"Média de modelos por marca: {avg_models:.1f}")
    print(f"Máximo de modelos (marca): {max_models}")
    print(f"Mínimo de modelos (marca): {min_models}")
    
    # Exemplos de modelos para algumas marcas principais
    main_brands = ['AUDI', 'BMW', 'MERCEDES-BENZ', 'VOLKSWAGEN', 'FORD']
    
    print(f"\nEXEMPLOS DE MODELOS:")
    print("-" * 40)
    for brand_key in main_brands:
        if brand_key in brands:
            brand_data = brands[brand_key]
            models = [model['name'] for model in brand_data['models'][:5]]
            models_str = ', '.join(models)
            if len(brand_data['models']) > 5:
                models_str += f" (+ {len(brand_data['models']) - 5} outros)"
            print(f"{brand_data['name']}: {models_str}")


def main():
    """Função principal"""
    data_file = "data/json/mobile_de_brands_models.json"
    
    if not Path(data_file).exists():
        print(f"Erro: Arquivo {data_file} não encontrado!")
        print("Execute primeiro: python scripts/extract_mobile_de_brands_models.py")
        return
    
    data = load_data(data_file)
    show_stats(data)


if __name__ == "__main__":
    main() 