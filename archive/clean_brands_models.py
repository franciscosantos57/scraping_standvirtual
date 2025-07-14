#!/usr/bin/env python3
"""
Script para limpar e organizar os dados de marcas e modelos extraídos
"""

import json
import re


def is_valid_model(model_text):
    """
    Verifica se um modelo é válido
    """
    # Lista de termos que indicam que não é um modelo válido
    invalid_terms = [
        '- carros', 'carros', 'venda', 'usado', 'novo', 'portugal',
        'aveiro', 'braga', 'porto', 'lisboa', 'beja', 'coimbra',
        'leiria', 'santarem', 'setubal', 'faro', 'viseu', 'guarda',
        'castelo branco', 'portalegre', 'evora', 'viana do castelo',
        'vila real', 'braganca', 'acores', 'madeira', 'faial',
        'saomiguel', 'terceira', 'outros', 'desde', 'ate'
    ]
    
    model_lower = model_text.lower().strip()
    
    # Verifica se é muito curto
    if len(model_lower) <= 2:
        return False
    
    # Verifica se está na lista de termos inválidos
    if model_lower in invalid_terms:
        return False
    
    # Verifica se contém apenas números
    if model_lower.isdigit():
        return False
    
    # Verifica se é um nome de cidade portuguesa
    portuguese_cities = [
        'aveiro', 'braga', 'porto', 'lisboa', 'beja', 'coimbra',
        'leiria', 'santarem', 'setubal', 'faro', 'viseu', 'guarda',
        'castelobranco', 'portalegre', 'evora', 'viana', 'vila real',
        'braganca'
    ]
    
    for city in portuguese_cities:
        if city in model_lower:
            return False
    
    return True


def clean_model_name(model_text):
    """
    Limpa o nome do modelo
    """
    # Remove caracteres especiais desnecessários
    cleaned = re.sub(r'[^\w\s\-\.]', '', model_text)
    
    # Remove espaços extras
    cleaned = ' '.join(cleaned.split())
    
    # Capitaliza corretamente
    cleaned = cleaned.title()
    
    return cleaned


def organize_models_by_brand():
    """
    Organiza e limpa os modelos por marca
    """
    # Carrega dados extraídos
    with open('standvirtual_complete_brands_models.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    cleaned_data = {}
    
    print("🧹 Limpando dados de marcas e modelos...")
    print("="*50)
    
    for brand, brand_data in raw_data.items():
        print(f"\n🔧 Processando {brand}...")
        
        raw_models = brand_data.get('models', [])
        valid_models = []
        
        for model in raw_models:
            model_text = model.get('text', '')
            
            if is_valid_model(model_text):
                cleaned_name = clean_model_name(model_text)
                
                valid_models.append({
                    'value': cleaned_name.lower().replace(' ', '-').replace('.', ''),
                    'text': cleaned_name
                })
        
        # Remove duplicatas
        seen = set()
        unique_models = []
        for model in valid_models:
            if model['text'] not in seen:
                seen.add(model['text'])
                unique_models.append(model)
        
        # Ordena alfabeticamente
        unique_models.sort(key=lambda x: x['text'])
        
        cleaned_data[brand] = {
            'brand_value': brand.lower().replace(' ', '-').replace('/', '-'),
            'models': unique_models
        }
        
        print(f"   ✅ {len(raw_models)} → {len(unique_models)} modelos válidos")
        if unique_models:
            print(f"   📋 Exemplos: {[m['text'] for m in unique_models[:3]]}")
    
    return cleaned_data


def add_common_models():
    """
    Adiciona modelos comuns conhecidos para marcas que têm poucos modelos
    """
    common_models = {
        'Audi': ['A1', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'Q2', 'Q3', 'Q5', 'Q7', 'Q8', 'TT', 'R8'],
        'BMW': ['Serie 1', 'Serie 2', 'Serie 3', 'Serie 4', 'Serie 5', 'Serie 6', 'Serie 7', 'Serie 8', 'X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'X7', 'Z4', 'i3', 'i4', 'iX'],
        'Mercedes-Benz': ['Classe A', 'Classe B', 'Classe C', 'Classe E', 'Classe S', 'CLA', 'CLS', 'GLA', 'GLB', 'GLC', 'GLE', 'GLS', 'SL', 'AMG GT'],
        'Volkswagen': ['Polo', 'Golf', 'Jetta', 'Passat', 'Tiguan', 'Touran', 'Sharan', 'Touareg', 'T-Cross', 'T-Roc', 'Arteon'],
        'Toyota': ['Yaris', 'Corolla', 'Camry', 'Prius', 'Auris', 'Avensis', 'RAV4', 'Highlander', 'Land Cruiser', 'Hilux'],
        'Ford': ['Fiesta', 'Focus', 'Mondeo', 'Mustang', 'Kuga', 'EcoSport', 'Edge', 'Explorer', 'Ranger'],
        'Opel': ['Corsa', 'Astra', 'Insignia', 'Mokka', 'Crossland', 'Grandland', 'Zafira', 'Vivaro'],
        'Renault': ['Clio', 'Megane', 'Scenic', 'Laguna', 'Captur', 'Kadjar', 'Koleos', 'Talisman'],
        'Peugeot': ['108', '208', '308', '408', '508', '2008', '3008', '5008', 'Partner', 'Expert'],
        'Citroën': ['C1', 'C3', 'C4', 'C5', 'C3 Aircross', 'C4 Cactus', 'C5 Aircross', 'Berlingo', 'SpaceTourer']
    }
    
    return common_models


def main():
    """Função principal"""
    print("🚀 Iniciando limpeza de dados de marcas e modelos...")
    print("="*60)
    
    try:
        # Limpa dados extraídos
        cleaned_data = organize_models_by_brand()
        
        # Adiciona modelos comuns para marcas com poucos modelos
        common_models = add_common_models()
        
        print(f"\n🔧 Melhorando dados com modelos comuns...")
        
        for brand, models in common_models.items():
            if brand in cleaned_data:
                existing_models = {m['text'] for m in cleaned_data[brand]['models']}
                
                # Adiciona modelos comuns que não existem
                for model in models:
                    if model not in existing_models:
                        cleaned_data[brand]['models'].append({
                            'value': model.lower().replace(' ', '-'),
                            'text': model
                        })
                
                # Reordena
                cleaned_data[brand]['models'].sort(key=lambda x: x['text'])
        
        # Salva dados limpos
        filename = "standvirtual_brands_models_clean.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Limpeza concluída!")
        print(f"💾 Dados limpos salvos em: {filename}")
        
        # Estatísticas finais
        print(f"\n📊 Estatísticas finais:")
        total_models = 0
        for brand, data in cleaned_data.items():
            model_count = len(data['models'])
            total_models += model_count
            print(f"  {brand}: {model_count} modelos")
        
        print(f"\n📈 Total: {len(cleaned_data)} marcas, {total_models} modelos")
        
        # Mostra exemplo da estrutura final
        print(f"\n📋 Exemplo da estrutura final:")
        example_brand = list(cleaned_data.keys())[0]
        example_data = cleaned_data[example_brand]
        example_models = example_data['models'][:5]
        
        print(json.dumps({
            example_brand: {
                'brand_value': example_data['brand_value'],
                'models': example_models
            }
        }, indent=2, ensure_ascii=False))
        
        print(f"\n💡 Como usar:")
        print("  1. Importe o JSON no seu projeto")
        print("  2. Use 'brand_value' para pesquisas no StandVirtual")
        print("  3. Use 'text' para mostrar ao utilizador")
        print("  4. Use 'value' para valores de formulário")
        
    except FileNotFoundError:
        print("❌ Arquivo 'standvirtual_complete_brands_models.json' não encontrado")
        print("Execute primeiro o script 'extract_complete_brands_models.py'")
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main() 