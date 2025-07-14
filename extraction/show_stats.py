#!/usr/bin/env python3
"""
Script simples para mostrar estatísticas da base de dados
"""

import json

def load_database(database_path: str = "data/json/standvirtual_master_database.json") -> dict:
    """Carrega a base de dados"""
    try:
        with open(database_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Base de dados não encontrada: {database_path}")
        return None

def main():
    """Mostra estatísticas da base de dados"""
    print("📊 ESTATÍSTICAS DA BASE DE DADOS")
    print("=" * 50)
    
    database = load_database()
    if not database:
        return
    
    # Estatísticas gerais
    metadata = database.get('metadata', {})
    print(f"🏷️  Total de marcas: {metadata.get('total_brands', 0)}")
    print(f"🚗 Total de modelos: {metadata.get('total_models', 0)}")
    print(f"❌ Marcas incompletas: {metadata.get('incomplete_brands', 0)}")
    print(f"✅ Taxa de completude: {metadata.get('completion_rate', 0)}%")
    print(f"📅 Última atualização: {metadata.get('last_update', 'N/A')}")
    
    # Marcas incompletas
    incomplete_brands = []
    for brand_name, brand_data in database['brands'].items():
        models = brand_data.get('models', [])
        if len(models) == 1 and models[0]['text'] == 'Outros modelos':
            incomplete_brands.append(brand_name)
    
    print(f"\n❌ MARCAS INCOMPLETAS ({len(incomplete_brands)} marcas):")
    if incomplete_brands:
        for i, brand in enumerate(incomplete_brands[:10], 1):  # Só primeiras 10
            print(f"   {i}. {brand}")
        if len(incomplete_brands) > 10:
            print(f"   ... e mais {len(incomplete_brands) - 10} marcas")
    else:
        print("   ✅ Todas as marcas têm modelos específicos!")
    
    # Top marcas com mais modelos
    brands_with_counts = []
    for brand_name, brand_data in database['brands'].items():
        models = brand_data.get('models', [])
        if len(models) > 1 or (len(models) == 1 and models[0]['text'] != 'Outros modelos'):
            brands_with_counts.append((brand_name, len(models)))
    
    brands_with_counts.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 TOP 10 MARCAS COM MAIS MODELOS:")
    for i, (brand, count) in enumerate(brands_with_counts[:10], 1):
        print(f"   {i:2}. {brand:<20} - {count:2} modelos")

if __name__ == "__main__":
    main() 