#!/usr/bin/env python3
"""
Script para integrar submodelos na base de dados standvirtual_database.json
"""
import json
import os
from typing import Dict, List, Any

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Carrega um arquivo JSON"""
    if not os.path.exists(file_path):
        print(f"❌ Arquivo {file_path} não encontrado!")
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(file_path: str, data: Dict[str, Any]):
    """Salva dados em um arquivo JSON"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_submodel_value(submodel_name: str) -> str:
    """Gera um valor URL-friendly para o submodelo"""
    # Remove caracteres especiais e espaços, converte para minúsculas
    value = submodel_name.lower()
    value = value.replace(' ', '-')
    value = value.replace('(', '')
    value = value.replace(')', '')
    value = value.replace('.', '')
    value = value.replace('/', '-')
    value = value.replace('+', 'plus')
    return value

def integrate_submodels():
    """Integra os submodelos na base de dados"""
    
    # Carregar arquivos
    submodels_data = load_json_file("sub-models.json")
    database_data = load_json_file("data/json/standvirtual_database.json")
    
    if not submodels_data or not database_data:
        return
    
    print("🔄 Integrando submodelos na base de dados...")
    
    brands_updated = 0
    models_with_submodels = 0
    total_submodels_added = 0
    
    # Iterar sobre as marcas que têm submodelos
    for brand_key, brand_submodels in submodels_data.items():
        # Encontrar a marca correspondente na base de dados
        brand_found = False
        
        for db_brand_name, db_brand_data in database_data["brands"].items():
            if db_brand_data.get("brand_value") == brand_key:
                brand_found = True
                brands_updated += 1
                print(f"📝 Processando marca: {db_brand_name}")
                
                # Iterar sobre os modelos que têm submodelos
                for model_key, submodels_list in brand_submodels.items():
                    # Encontrar o modelo correspondente na base de dados
                    for model_data in db_brand_data["models"]:
                        if model_data.get("value") == model_key:
                            models_with_submodels += 1
                            print(f"  └─ Modelo: {model_data['text']} ({len(submodels_list)} submodelos)")
                            
                            # Adicionar estrutura de submodelos
                            if "submodels" not in model_data:
                                model_data["submodels"] = []
                            
                            # Adicionar cada submodelo
                            for submodel_name in submodels_list:
                                submodel_data = {
                                    "text": submodel_name,
                                    "value": generate_submodel_value(submodel_name)
                                }
                                model_data["submodels"].append(submodel_data)
                                total_submodels_added += 1
                            
                            break
                
                break
        
        if not brand_found:
            print(f"⚠️  Marca '{brand_key}' não encontrada na base de dados")
    
    # Atualizar metadata
    if "metadata" in database_data:
        database_data["metadata"]["total_submodels"] = total_submodels_added
        database_data["metadata"]["models_with_submodels"] = models_with_submodels
    
    # Salvar base de dados atualizada
    save_json_file("data/json/standvirtual_database.json", database_data)
    
    print(f"\n✅ Integração concluída!")
    print(f"📊 Resumo:")
    print(f"   • Marcas atualizadas: {brands_updated}")
    print(f"   • Modelos com submodelos: {models_with_submodels}")
    print(f"   • Total de submodelos adicionados: {total_submodels_added}")

if __name__ == "__main__":
    integrate_submodels() 