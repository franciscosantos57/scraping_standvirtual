#!/usr/bin/env python3
"""
Utilitário para ver estatísticas da base de dados de marcas e modelos
"""

import json
from datetime import datetime


def load_database(database_path: str = "data/json/standvirtual_master_database.json") -> dict:
    """Carrega a base de dados"""
    try:
        with open(database_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Base de dados não encontrada: {database_path}")
        return None


def show_general_stats(database: dict):
    """Mostra estatísticas gerais"""
    metadata = database.get('metadata', {})
    
    print("📊 ESTATÍSTICAS GERAIS")
    print("=" * 50)
    print(f"🏷️  Total de marcas: {metadata.get('total_brands', 0)}")
    print(f"🚗 Total de modelos: {metadata.get('total_models', 0)}")
    print(f"❌ Marcas incompletas: {metadata.get('incomplete_brands', 0)}")
    print(f"✅ Taxa de completude: {metadata.get('completion_rate', 0)}%")
    print(f"📅 Última atualização: {metadata.get('last_update', 'N/A')}")
    print(f"🔧 Método usado: {metadata.get('correction_method', 'N/A')}")


def show_incomplete_brands(database: dict):
    """Mostra marcas incompletas (só "Outros modelos")"""
    incomplete_brands = []
    
    for brand_name, brand_data in database['brands'].items():
        models = brand_data.get('models', [])
        if len(models) == 1 and models[0]['text'] == 'Outros modelos':
            incomplete_brands.append(brand_name)
    
    print(f"\n❌ MARCAS INCOMPLETAS ({len(incomplete_brands)} marcas)")
    print("=" * 50)
    
    if incomplete_brands:
        for i, brand in enumerate(incomplete_brands, 1):
            print(f"{i:2}. {brand}")
    else:
        print("✅ Todas as marcas têm modelos específicos!")


def show_complete_brands(database: dict):
    """Mostra marcas completas com mais modelos"""
    complete_brands = []
    
    for brand_name, brand_data in database['brands'].items():
        models = brand_data.get('models', [])
        if len(models) > 1 or (len(models) == 1 and models[0]['text'] != 'Outros modelos'):
            model_count = len(models)
            complete_brands.append((brand_name, model_count))
    
    # Ordena por número de modelos (decrescente)
    complete_brands.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n✅ MARCAS COMPLETAS ({len(complete_brands)} marcas)")
    print("=" * 50)
    print("Top 20 marcas com mais modelos:")
    
    for i, (brand, count) in enumerate(complete_brands[:20], 1):
        print(f"{i:2}. {brand:<20} - {count:2} modelos")


def show_brand_details(database: dict, brand_name: str):
    """Mostra detalhes de uma marca específica"""
    if brand_name not in database['brands']:
        print(f"❌ Marca '{brand_name}' não encontrada!")
        available_brands = list(database['brands'].keys())[:10]
        print(f"💡 Marcas disponíveis (primeiras 10): {', '.join(available_brands)}...")
        return
    
    brand_data = database['brands'][brand_name]
    models = brand_data.get('models', [])
    
    print(f"\n🔍 DETALHES DA MARCA: {brand_name}")
    print("=" * 50)
    print(f"📋 Total de modelos: {len(models)}")
    
    if models:
        print(f"\n🚗 Modelos:")
        for i, model in enumerate(models, 1):
            model_text = model.get('text', 'N/A')
            model_value = model.get('value', 'N/A')
            print(f"{i:2}. {model_text} → {model_value}")
    else:
        print("❌ Nenhum modelo encontrado")


def search_models(database: dict, search_term: str):
    """Busca modelos que contêm o termo de pesquisa"""
    results = []
    
    for brand_name, brand_data in database['brands'].items():
        models = brand_data.get('models', [])
        for model in models:
            model_text = model.get('text', '')
            if search_term.lower() in model_text.lower():
                results.append((brand_name, model_text))
    
    print(f"\n🔍 BUSCA POR MODELOS: '{search_term}'")
    print("=" * 50)
    
    if results:
        print(f"Encontrados {len(results)} modelos:")
        for brand, model in results:
            print(f"• {brand} → {model}")
    else:
        print(f"❌ Nenhum modelo encontrado com '{search_term}'")


def show_top_brands_by_models(database: dict, top_n: int = 10):
    """Mostra as marcas com mais modelos"""
    brands_with_counts = []
    
    for brand_name, brand_data in database['brands'].items():
        models = brand_data.get('models', [])
        # Só conta se não for apenas "Outros modelos"
        if len(models) > 1 or (len(models) == 1 and models[0]['text'] != 'Outros modelos'):
            brands_with_counts.append((brand_name, len(models)))
    
    brands_with_counts.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 TOP {top_n} MARCAS COM MAIS MODELOS")
    print("=" * 50)
    
    for i, (brand, count) in enumerate(brands_with_counts[:top_n], 1):
        print(f"{i:2}. {brand:<20} - {count:2} modelos")


def main():
    """Função principal"""
    print("📊 ESTATÍSTICAS DA BASE DE DADOS")
    print("=" * 60)
    
    database = load_database()
    if not database:
        return
    
    while True:
        print("\n📋 OPÇÕES DISPONÍVEIS:")
        print("1. Estatísticas gerais")
        print("2. Marcas incompletas")
        print("3. Marcas completas")
        print("4. Top marcas com mais modelos")
        print("5. Detalhes de uma marca")
        print("6. Buscar modelos")
        print("0. Sair")
        
        try:
            choice = input("\n🔢 Escolha uma opção (0-6): ").strip()
            
            if choice == "0":
                print("👋 Até à próxima!")
                break
            elif choice == "1":
                show_general_stats(database)
            elif choice == "2":
                show_incomplete_brands(database)
            elif choice == "3":
                show_complete_brands(database)
            elif choice == "4":
                try:
                    top_n = input("🔢 Quantas marcas mostrar? (Enter = 10): ").strip()
                    top_n = int(top_n) if top_n else 10
                    show_top_brands_by_models(database, top_n)
                except ValueError:
                    show_top_brands_by_models(database)
            elif choice == "5":
                brand_name = input("🏷️  Nome da marca: ").strip()
                if brand_name:
                    show_brand_details(database, brand_name)
            elif choice == "6":
                search_term = input("🔍 Termo de busca: ").strip()
                if search_term:
                    search_models(database, search_term)
            else:
                print("❌ Opção inválida!")
                
        except KeyboardInterrupt:
            print("\n\n👋 Programa encerrado pelo utilizador.")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")


if __name__ == "__main__":
    main() 