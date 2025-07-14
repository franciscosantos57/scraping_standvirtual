#!/usr/bin/env python3
"""
Script de demonstração para o sistema de extração do StandVirtual
Permite testar e demonstrar as funcionalidades sem executar extração completa
"""

import json
import os
from datetime import datetime
from typing import Dict, List


def show_current_database_stats():
    """Mostra estatísticas do database atual"""
    print("📊 ESTATÍSTICAS DO DATABASE ATUAL")
    print("=" * 50)
    
    database_file = "../data/json/standvirtual_master_database.json"
    
    if not os.path.exists(database_file):
        print("❌ Database não encontrado!")
        print(f"   Arquivo esperado: {database_file}")
        print("   Execute a extração primeiro: python run_complete_extraction.py")
        return
    
    try:
        with open(database_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data.get('metadata', {})
        brands = data.get('brands', {})
        
        total_brands = len(brands)
        total_models = sum(brand.get('total_models', 0) for brand in brands.values())
        
        # Marcas com apenas "outros modelos"
        incomplete_brands = [
            name for name, info in brands.items()
            if info.get('total_models', 0) == 1 and 
            any(model.get('text') == 'Outros modelos' for model in info.get('models', []))
        ]
        
        completion_rate = ((total_brands - len(incomplete_brands)) / total_brands) * 100
        
        print(f"📈 Total de marcas: {total_brands}")
        print(f"📈 Total de modelos: {total_models}")
        print(f"📈 Média de modelos por marca: {total_models/total_brands:.1f}")
        print(f"📈 Taxa de completude: {completion_rate:.1f}%")
        print(f"📈 Marcas incompletas: {len(incomplete_brands)}")
        
        if metadata:
            print(f"📅 Criado em: {metadata.get('creation_date', 'N/A')}")
            print(f"📅 Última atualização: {metadata.get('last_update', 'N/A')}")
            print(f"🔢 Versão: {metadata.get('version', 'N/A')}")
        
        return {
            'total_brands': total_brands,
            'total_models': total_models,
            'incomplete_brands': incomplete_brands,
            'completion_rate': completion_rate
        }
        
    except Exception as e:
        print(f"❌ Erro ao ler database: {e}")
        return None


def show_top_brands():
    """Mostra as marcas com mais modelos"""
    print("\n🏆 TOP 10 MARCAS COM MAIS MODELOS")
    print("=" * 50)
    
    database_file = "../data/json/standvirtual_master_database.json"
    
    try:
        with open(database_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        brands = data.get('brands', {})
        
        # Ordena marcas por número de modelos
        brand_counts = [
            (name, info.get('total_models', 0)) 
            for name, info in brands.items()
        ]
        top_brands = sorted(brand_counts, key=lambda x: x[1], reverse=True)[:10]
        
        for i, (brand, count) in enumerate(top_brands, 1):
            print(f"   {i:2d}. {brand}: {count} modelos")
            
    except Exception as e:
        print(f"❌ Erro: {e}")


def show_incomplete_brands():
    """Mostra marcas que ainda precisam de correção"""
    print("\n⚠️ MARCAS QUE PRECISAM DE CORREÇÃO")
    print("=" * 50)
    
    database_file = "../data/json/standvirtual_master_database.json"
    
    try:
        with open(database_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        brands = data.get('brands', {})
        
        incomplete_brands = [
            name for name, info in brands.items()
            if info.get('total_models', 0) == 1 and 
            any(model.get('text') == 'Outros modelos' for model in info.get('models', []))
        ]
        
        if incomplete_brands:
            print(f"📋 {len(incomplete_brands)} marcas com apenas 'Outros modelos':")
            for i, brand in enumerate(incomplete_brands[:20], 1):
                print(f"   {i:2d}. {brand}")
            
            if len(incomplete_brands) > 20:
                print(f"   ... e mais {len(incomplete_brands) - 20} marcas")
                
            print(f"\n💡 Para corrigir: python fix_missing_models.py")
        else:
            print("✅ Todas as marcas têm modelos específicos!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")


def show_brand_details(brand_name: str):
    """Mostra detalhes de uma marca específica"""
    print(f"\n🔍 DETALHES DA MARCA: {brand_name}")
    print("=" * 50)
    
    database_file = "../data/json/standvirtual_master_database.json"
    
    try:
        with open(database_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        brands = data.get('brands', {})
        
        # Busca marca (case insensitive)
        found_brand = None
        for name, info in brands.items():
            if name.lower() == brand_name.lower():
                found_brand = (name, info)
                break
        
        if not found_brand:
            print(f"❌ Marca '{brand_name}' não encontrada")
            print("📋 Marcas disponíveis:")
            available = list(brands.keys())[:10]
            for brand in available:
                print(f"   • {brand}")
            if len(brands) > 10:
                print(f"   ... e mais {len(brands) - 10} marcas")
            return
        
        name, info = found_brand
        models = info.get('models', [])
        
        print(f"📛 Nome: {name}")
        print(f"🔗 Valor: {info.get('brand_value', 'N/A')}")
        print(f"📊 Total de modelos: {len(models)}")
        
        print(f"\n📋 MODELOS:")
        for i, model in enumerate(models, 1):
            model_text = model.get('text', 'N/A')
            model_value = model.get('value', 'N/A')
            print(f"   {i:2d}. {model_text} → {model_value}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")


def demo_extraction_commands():
    """Mostra comandos disponíveis para extração"""
    print("\n🛠️ COMANDOS DE EXTRAÇÃO DISPONÍVEIS")
    print("=" * 50)
    
    commands = [
        {
            'command': 'python run_complete_extraction.py',
            'description': 'Extração completa (recomendado)',
            'time': '30-60 min',
            'what': 'Extrai todas as marcas e modelos automaticamente'
        },
        {
            'command': 'python extract_complete_standvirtual_database.py',
            'description': 'Apenas extração inicial',
            'time': '15-30 min',
            'what': 'Extrai marcas e modelos dos dropdowns'
        },
        {
            'command': 'python fix_missing_models.py',
            'description': 'Apenas correção de modelos',
            'time': '10-20 min',
            'what': 'Corrige marcas com "outros modelos"'
        }
    ]
    
    for cmd in commands:
        print(f"📝 {cmd['command']}")
        print(f"   📄 {cmd['description']}")
        print(f"   ⏱️ Tempo estimado: {cmd['time']}")
        print(f"   🎯 O que faz: {cmd['what']}")
        print()


def interactive_demo():
    """Demo interativo"""
    print("🚗 DEMO INTERATIVO - SISTEMA DE EXTRAÇÃO STANDVIRTUAL")
    print("=" * 60)
    
    while True:
        print("\n📋 OPÇÕES DISPONÍVEIS:")
        print("1. 📊 Ver estatísticas do database")
        print("2. 🏆 Ver top marcas com mais modelos")
        print("3. ⚠️ Ver marcas que precisam correção")
        print("4. 🔍 Ver detalhes de uma marca específica")
        print("5. 🛠️ Ver comandos de extração")
        print("6. 🚪 Sair")
        
        try:
            choice = input("\n👉 Escolha uma opção (1-6): ").strip()
            
            if choice == '1':
                stats = show_current_database_stats()
                
            elif choice == '2':
                show_top_brands()
                
            elif choice == '3':
                show_incomplete_brands()
                
            elif choice == '4':
                brand = input("👉 Digite o nome da marca: ").strip()
                if brand:
                    show_brand_details(brand)
                else:
                    print("❌ Nome da marca não pode estar vazio")
                    
            elif choice == '5':
                demo_extraction_commands()
                
            elif choice == '6':
                print("👋 Até logo!")
                break
                
            else:
                print("❌ Opção inválida. Escolha 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrompido. Até logo!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")


def quick_validation():
    """Validação rápida do sistema"""
    print("✅ VALIDAÇÃO RÁPIDA DO SISTEMA")
    print("=" * 50)
    
    # Verifica arquivos
    required_files = [
        'extract_complete_standvirtual_database.py',
        'fix_missing_models.py',
        'run_complete_extraction.py',
        'main.py',
        'utils/brand_model_validator.py'
    ]
    
    print("📁 Verificando arquivos...")
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (faltando)")
    
    # Verifica diretórios
    print("\n📂 Verificando diretórios...")
    dirs = ['data/json', 'utils', 'scraper', 'models']
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ (faltando)")
    
    # Verifica database
    print("\n💾 Verificando database...")
    database_file = "../data/json/standvirtual_master_database.json"
    if os.path.exists(database_file):
        print(f"   ✅ {database_file}")
        try:
            with open(database_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            brands_count = len(data.get('brands', {}))
            print(f"   📊 {brands_count} marcas no database")
        except:
            print(f"   ⚠️ Database existe mas tem problemas")
    else:
        print(f"   ❌ {database_file} (não encontrado)")
        print("   💡 Execute: python run_complete_extraction.py")
    
    print("\n✅ Validação concluída!")


def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'stats':
            show_current_database_stats()
        elif command == 'top':
            show_top_brands()
        elif command == 'incomplete':
            show_incomplete_brands()
        elif command == 'commands':
            demo_extraction_commands()
        elif command == 'validate':
            quick_validation()
        elif command.startswith('brand:'):
            brand_name = command.split(':', 1)[1]
            show_brand_details(brand_name)
        else:
            print("❌ Comando inválido")
            print("📋 Comandos disponíveis:")
            print("   python demo_extraction.py stats")
            print("   python demo_extraction.py top")
            print("   python demo_extraction.py incomplete")
            print("   python demo_extraction.py commands")
            print("   python demo_extraction.py validate")
            print("   python demo_extraction.py brand:BMW")
            print("   python demo_extraction.py (modo interativo)")
    else:
        interactive_demo()


if __name__ == "__main__":
    main() 