#!/usr/bin/env python3
"""
Script para testar o suporte a submodelos no sistema de scraping
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.brand_model_validator import validator
from models.car import CarSearchParams
from scraper.standvirtual_scraper import StandVirtualScraper

def test_validator_submodels():
    """Testa o validador de submodelos"""
    print("🔍 TESTANDO VALIDADOR DE SUBMODELOS")
    print("=" * 50)
    
    # Teste 1: BMW Série 3 - 320
    print("\n📝 Teste 1: BMW Série 3 - 320")
    result = validator.validate_search_params("BMW", "Série 3", "320")
    print(f"Válido: {result['valid']}")
    if result['valid']:
        print(f"Marca: {result['brand']} → {result['brand_value']}")
        print(f"Modelo: {result['model']} → {result['model_value']}")
        print(f"Submodelo: {result['submodel']} → {result['submodel_value']}")
    else:
        print(f"Erros: {result['errors']}")
    
    # Teste 2: Lexus IS - IS 200
    print("\n📝 Teste 2: Lexus IS - IS 200")
    result = validator.validate_search_params("Lexus", "IS", "IS 200")
    print(f"Válido: {result['valid']}")
    if result['valid']:
        print(f"Marca: {result['brand']} → {result['brand_value']}")
        print(f"Modelo: {result['model']} → {result['model_value']}")
        print(f"Submodelo: {result['submodel']} → {result['submodel_value']}")
    else:
        print(f"Erros: {result['errors']}")
    
    # Teste 3: Mercedes-Benz Classe A - A 180
    print("\n📝 Teste 3: Mercedes-Benz Classe A - A 180")
    result = validator.validate_search_params("Mercedes-Benz", "Classe A", "A 180")
    print(f"Válido: {result['valid']}")
    if result['valid']:
        print(f"Marca: {result['brand']} → {result['brand_value']}")
        print(f"Modelo: {result['model']} → {result['model_value']}")
        print(f"Submodelo: {result['submodel']} → {result['submodel_value']}")
    else:
        print(f"Erros: {result['errors']}")
    
    # Teste 4: Submodelo inválido
    print("\n📝 Teste 4: BMW Série 1 - M999 (inválido)")
    result = validator.validate_search_params("BMW", "Série 1", "M999")
    print(f"Válido: {result['valid']}")
    if not result['valid']:
        print(f"Erros: {result['errors']}")
        if result.get('suggestions', {}).get('submodels'):
            print(f"Sugestões: {result['suggestions']['submodels']}")

def test_url_construction():
    """Testa a construção de URLs com submodelos"""
    print("\n\n🔗 TESTANDO CONSTRUÇÃO DE URLs")
    print("=" * 50)
    
    # Teste com BMW Série 3 - 320
    params = CarSearchParams()
    params.marca = "bmw"
    params.modelo = "serie-3"
    params.submodelo = "320"
    
    scraper = StandVirtualScraper(use_selenium=False)
    search_params = scraper._build_search_params(params)
    
    print(f"Parâmetros de pesquisa:")
    for key, value in search_params.items():
        print(f"  {key}: {value}")
    
    # Constrói URL de exemplo
    import urllib.parse
    query_string = urllib.parse.urlencode(search_params)
    url = f"https://www.standvirtual.com/carros?{query_string}"
    print(f"\nURL construída:")
    print(url)

def show_available_submodels():
    """Mostra submodelos disponíveis para algumas marcas"""
    print("\n\n📋 SUBMODELOS DISPONÍVEIS")
    print("=" * 50)
    
    brands_to_show = ["BMW", "Lexus", "Mercedes-Benz"]
    
    for brand in brands_to_show:
        print(f"\n🏭 {brand}:")
        models = validator.get_models_for_brand(brand)
        
        for model in models:
            submodels = model.get('submodels', [])
            if submodels:
                print(f"  └─ {model['text']} ({len(submodels)} submodelos):")
                # Mostra apenas os primeiros 5 submodelos
                for i, submodel in enumerate(submodels[:5]):
                    print(f"     • {submodel['text']}")
                if len(submodels) > 5:
                    print(f"     ... e mais {len(submodels) - 5} submodelos")

if __name__ == "__main__":
    test_validator_submodels()
    test_url_construction()
    show_available_submodels()
    
    print("\n\n✅ TESTES CONCLUÍDOS!")
    print("\nPara testar o scraping completo, use:")
    print("python3 main.py --marca BMW --modelo 'Série 3' --submodelo '320'")
    print("python3 main.py --marca Lexus --modelo IS --submodelo 'IS 200'") 