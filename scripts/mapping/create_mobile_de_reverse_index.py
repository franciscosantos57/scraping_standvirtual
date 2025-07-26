#!/usr/bin/env python3
"""
Script para criar índice reverso Mobile.de -> StandVirtual
Facilita a busca rápida de modelos/submodelos do Mobile.de
"""

import json
import sys
from pathlib import Path

def load_mapped_database():
    """Carrega a base de dados mapeada"""
    file_path = Path("data/json/mapped_sv_md_database.json")
    
    if not file_path.exists():
        print(f"❌ Erro: Arquivo {file_path} não encontrado")
        sys.exit(1)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        sys.exit(1)

def create_reverse_index(mapped_data):
    """
    Cria índice reverso Mobile.de -> StandVirtual
    
    Formato:
    {
        "120": {
            "brand": "BMW",
            "brand_text": "BMW",
            "parent_model": "serie-1",
            "parent_model_text": "Série 1",
            "text_md": "120",
            "type": "submodel"
        },
        "M135": {
            "brand": "BMW",
            "brand_text": "BMW", 
            "parent_model": "m1",
            "parent_model_text": "M1",
            "text_md": "M135",
            "type": "model"
        }
    }
    """
    reverse_index = {}
    stats = {
        'total_models_mapped': 0,
        'total_submodels_mapped': 0,
        'brands_with_mappings': 0
    }
    
    brands = mapped_data.get('brands', {})
    
    for brand_name, brand_data in brands.items():
        brand_has_mappings = False
        
        # Processar modelos
        for model in brand_data.get('models', []):
            # Se o modelo tem mapeamento Mobile.de
            if 'text_md' in model:
                text_md = model['text_md']
                
                # Verificar se já existe (duplicado)
                if text_md in reverse_index:
                    print(f"⚠️  Duplicado encontrado: '{text_md}' já existe para {reverse_index[text_md]['brand']} {reverse_index[text_md]['parent_model_text']}")
                    print(f"   Tentando adicionar para {brand_name} {model['text']}")
                    continue
                
                reverse_index[text_md] = {
                    'brand': brand_name,
                    'brand_text': brand_data['brand_text'],
                    'parent_model': model['value'],
                    'parent_model_text': model['text'],
                    'text_md': text_md,
                    'type': 'model'
                }
                
                stats['total_models_mapped'] += 1
                brand_has_mappings = True
            
            # Processar submodelos
            for submodel in model.get('submodels', []):
                if 'text_md' in submodel:
                    text_md = submodel['text_md']
                    
                    # Verificar se já existe (duplicado)
                    if text_md in reverse_index:
                        print(f"⚠️  Duplicado encontrado: '{text_md}' já existe para {reverse_index[text_md]['brand']} {reverse_index[text_md]['parent_model_text']}")
                        print(f"   Tentando adicionar para {brand_name} {model['text']} -> {submodel['text']}")
                        continue
                    
                    reverse_index[text_md] = {
                        'brand': brand_name,
                        'brand_text': brand_data['brand_text'],
                        'parent_model': model['value'],
                        'parent_model_text': model['text'],
                        'text_md': text_md,
                        'type': 'submodel',
                        'submodel_value': submodel['value'],
                        'submodel_text': submodel['text']
                    }
                    
                    stats['total_submodels_mapped'] += 1
                    brand_has_mappings = True
        
        if brand_has_mappings:
            stats['brands_with_mappings'] += 1
    
    return reverse_index, stats

def save_reverse_index(reverse_index, stats):
    """Salva o índice reverso em arquivo JSON"""
    output_data = {
        'metadata': {
            'title': 'Índice Reverso Mobile.de -> StandVirtual',
            'description': 'Mapeia modelos/submodelos do Mobile.de para seus pais no StandVirtual para busca rápida',
            'version': '1.0',
            'source': 'Gerado a partir de mapped_sv_md_database.json',
            'creation_date': '2025-07-23',
            'stats': stats
        },
        'index': reverse_index
    }
    
    output_path = Path("data/json/mobile_de_reverse_index.json")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Índice reverso criado com sucesso: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        sys.exit(1)

def show_examples(reverse_index):
    """Mostra alguns exemplos do índice criado"""
    print("\n📋 Exemplos do índice reverso:")
    print("=" * 50)
    
    examples = []
    for key, value in list(reverse_index.items())[:10]:
        examples.append((key, value))
    
    for text_md, mapping in examples:
        if mapping['type'] == 'model':
            print(f"'{text_md}' -> {mapping['brand']} {mapping['parent_model_text']} (modelo)")
        else:
            print(f"'{text_md}' -> {mapping['brand']} {mapping['parent_model_text']} -> {mapping['submodel_text']} (submodelo)")

def main():
    """Função principal"""
    print("🔄 Criando índice reverso Mobile.de -> StandVirtual...")
    
    # Carregar base de dados mapeada
    print("📂 Carregando base de dados mapeada...")
    mapped_data = load_mapped_database()
    
    # Criar índice reverso
    print("🔍 Analisando mapeamentos...")
    reverse_index, stats = create_reverse_index(mapped_data)
    
    # Mostrar estatísticas
    print("\n📊 Estatísticas:")
    print(f"   • Modelos mapeados: {stats['total_models_mapped']}")
    print(f"   • Submodelos mapeados: {stats['total_submodels_mapped']}")
    print(f"   • Total de entradas: {len(reverse_index)}")
    print(f"   • Marcas com mapeamentos: {stats['brands_with_mappings']}")
    
    # Salvar arquivo
    output_path = save_reverse_index(reverse_index, stats)
    
    # Mostrar exemplos
    show_examples(reverse_index)
    
    print(f"\n🎯 Como usar:")
    print(f"   Mobile.de retorna '120' -> consultar index['120'] -> BMW Série 1 (submodelo)")
    print(f"   Mobile.de retorna 'M135' -> consultar index['M135'] -> BMW M1 (modelo)")
    
    print(f"\n✅ Processo concluído! Arquivo salvo em: {output_path}")

if __name__ == "__main__":
    main() 