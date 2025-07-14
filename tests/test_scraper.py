#!/usr/bin/env python3
"""
Script de teste para o StandVirtual Scraper
"""

from scraper.standvirtual_scraper import StandVirtualScraper
from models.car import CarSearchParams
from utils.helpers import display_results


def test_basic_search():
    """Teste básico de pesquisa"""
    print("🧪 Testando pesquisa básica...")
    
    # Parâmetros de teste - pesquisa simples por BMW
    params = CarSearchParams()
    params.marca = "BMW"
    params.preco_max = 30000
    
    # Criar scraper
    scraper = StandVirtualScraper()
    
    # Fazer pesquisa
    results = scraper.search_cars(params)
    
    if results:
        print(f"✅ Teste passou! Encontrados {len(results)} carros.")
        display_results(results, max_display=3)
        return True
    else:
        print("❌ Teste falhou! Nenhum resultado encontrado.")
        return False


def test_detailed_search():
    """Teste com parâmetros mais específicos"""
    print("\n🧪 Testando pesquisa detalhada...")
    
    # Parâmetros mais específicos
    params = CarSearchParams()
    params.marca = "Toyota"
    params.modelo = "Corolla"
    params.ano_min = 2015
    params.km_max = 150000
    params.preco_max = 20000
    params.combustivel = "gasolina"
    
    # Criar scraper
    scraper = StandVirtualScraper()
    
    # Fazer pesquisa
    results = scraper.search_cars(params)
    
    if results:
        print(f"✅ Teste passou! Encontrados {len(results)} carros.")
        display_results(results, max_display=2)
        return True
    else:
        print("❌ Teste falhou! Nenhum resultado encontrado.")
        return False


def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do StandVirtual Scraper...")
    
    try:
        # Teste básico
        test1_passed = test_basic_search()
        
        # Teste detalhado
        test2_passed = test_detailed_search()
        
        # Resultado final
        if test1_passed or test2_passed:
            print("\n✅ Pelo menos um teste passou! O scraper está funcionando.")
        else:
            print("\n❌ Todos os testes falharam. Verifique a conectividade e seletores.")
            
    except Exception as e:
        print(f"\n💥 Erro durante os testes: {e}")
        print("Verifique se todas as dependências estão instaladas:")
        print("pip install -r requirements.txt")


if __name__ == "__main__":
    main() 