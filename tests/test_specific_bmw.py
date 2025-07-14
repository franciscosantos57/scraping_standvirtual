#!/usr/bin/env python3
"""
Teste específico para BMW X5 para validar correções de preço
"""

from scraper.standvirtual_scraper import StandVirtualScraper
from models.car import CarSearchParams
from utils.helpers import display_results


def test_bmw_x5_validation():
    """Teste específico para BMW X5 com validação de dados"""
    print("🧪 Testando BMW X5 com validação de dados...")
    
    # Parâmetros específicos para BMW X5
    params = CarSearchParams()
    params.marca = "BMW"
    params.modelo = "X5"
    params.ano_min = 2019
    params.ano_max = 2022
    params.preco_max = 130000
    params.km_max = 100000
    
    # Criar scraper
    scraper = StandVirtualScraper()
    
    # Fazer pesquisa
    results = scraper.search_cars(params)
    
    if results:
        print(f"✅ Encontrados {len(results)} BMW X5!")
        
        # Procura pelo X5 específico que tinha problema
        target_car = None
        for car in results:
            if "45 e xDrive xLine" in car.titulo:
                target_car = car
                break
        
        if target_car:
            print(f"\n🎯 CARRO ESPECÍFICO ENCONTRADO:")
            print(f"   Título: {target_car.titulo}")
            print(f"   Preço: {target_car.preco} (Numérico: {target_car.preco_numerico})")
            print(f"   Ano: {target_car.ano}")
            print(f"   Quilometragem: {target_car.quilometragem}")
            print(f"   URL: {target_car.url}")
            
            # Verifica se o preço foi corrigido
            if target_car.preco_numerico > 55000:
                print(f"   ✅ Preço parece correto (>55k)")
            else:
                print(f"   ⚠️  Preço pode estar incorreto (<55k)")
        else:
            print(f"   ⚠️ Carro específico 'BMW X5 45 e xDrive xLine' não encontrado")
        
        # Mostra primeiros resultados
        display_results(results, max_display=3)
        return True
    else:
        print("❌ Nenhum BMW X5 encontrado.")
        return False


if __name__ == "__main__":
    test_bmw_x5_validation() 