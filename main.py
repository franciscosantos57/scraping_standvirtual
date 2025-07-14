#!/usr/bin/env python3
"""
StandVirtual Car Price Scraper
Programa principal para pesquisar preços de carros no StandVirtual.com
"""

import sys
from scraper.standvirtual_scraper import StandVirtualScraper
from models.car import CarSearchParams
from utils.helpers import display_results, save_to_csv
from utils.brand_model_validator import validator


def get_user_input():
    """Coleta os parâmetros de pesquisa do utilizador"""
    print("\n=== StandVirtual Car Price Scraper ===")
    print("Insira as características do carro que pretende pesquisar:")
    
    # Mostra estatísticas do validador
    stats = validator.get_stats()
    print(f"📊 Base de dados: {stats['total_brands']} marcas, {stats['total_models']} modelos")
    
    params = CarSearchParams()
    
    # Marca com validação
    while True:
        print(f"\n📋 Marcas disponíveis: {', '.join(validator.get_all_brands()[:8])}...")
        marca = input("\nMarca: ").strip()
        
        if not marca:
            print("ℹ️ Continuando sem especificar marca...")
            break  # Utilizador não quer especificar marca
            
        if validator.is_valid_brand(marca):
            params.marca = marca
            print(f"✅ Marca '{marca}' encontrada")
            break
        else:
            print(f"❌ Marca '{marca}' não encontrada")
            suggestions = validator.suggest_brands(marca)
            if suggestions:
                print(f"💡 Sugestões: {', '.join(suggestions[:5])}")
            
            retry = input("Tentar novamente? (s/n/sair): ").strip().lower()
            if retry in ['sair', 'exit', 'quit', 'q']:
                print("👋 Programa encerrado pelo utilizador.")
                sys.exit(0)
            elif retry not in ['s', 'sim', 'y', 'yes']:
                print("ℹ️ Continuando sem especificar marca...")
                break
    
    # Modelo com validação (só se marca foi especificada)
    if params.marca:
        models = validator.get_models_for_brand(params.marca)
        print(f"\n🚗 {len(models)} modelos disponíveis para {params.marca}")
        
        # Mostra alguns modelos como exemplo
        example_models = [m['text'] for m in models[:8]]
        print(f"📋 Exemplos: {', '.join(example_models)}...")
        
        while True:
            modelo = input(f"\nModelo para {params.marca} (ou Enter para qualquer): ").strip()
            
            if not modelo:
                break  # Utilizador não quer especificar modelo
                
            if validator.is_valid_model(params.marca, modelo):
                params.modelo = modelo
                print(f"✅ Modelo '{modelo}' encontrado para {params.marca}")
                break
            else:
                print(f"❌ Modelo '{modelo}' não encontrado para {params.marca}")
                suggestions = validator.suggest_models(params.marca, modelo)
                if suggestions:
                    suggestion_names = [s['text'] for s in suggestions[:5]]
                    print(f"💡 Sugestões: {', '.join(suggestion_names)}")
                
                retry = input("Tentar novamente? (s/n/sair): ").strip().lower()
                if retry in ['sair', 'exit', 'quit', 'q']:
                    print("👋 Programa encerrado pelo utilizador.")
                    sys.exit(0)
                elif retry not in ['s', 'sim', 'y', 'yes']:
                    print("ℹ️ Continuando sem especificar modelo...")
                    break
    
    # Ano mínimo
    ano_min = input("Ano mínimo (ex: 2015): ").strip()
    if ano_min and ano_min.isdigit():
        params.ano_min = int(ano_min)
    
    # Ano máximo
    ano_max = input("Ano máximo (ex: 2022): ").strip()
    if ano_max and ano_max.isdigit():
        params.ano_max = int(ano_max)
    
    # Quilometragem máxima
    km_max = input("Quilometragem máxima (ex: 100000): ").strip()
    if km_max and km_max.isdigit():
        params.km_max = int(km_max)
    
    # Preço máximo
    preco_max = input("Preço máximo (ex: 25000): ").strip()
    if preco_max and preco_max.isdigit():
        params.preco_max = int(preco_max)
    
    # Tipo de caixa
    print("\nTipo de caixa:")
    print("1 - Manual")
    print("2 - Automática")
    print("3 - Ambas")
    caixa_choice = input("Escolha (1-3): ").strip()
    
    if caixa_choice == "1":
        params.caixa = "manual"
    elif caixa_choice == "2":
        params.caixa = "automatica"
    
    # Combustível
    print("\nTipo de combustível:")
    print("1 - Gasolina")
    print("2 - Gasóleo")
    print("3 - Híbrido")
    print("4 - Elétrico")
    print("5 - Qualquer")
    combustivel_choice = input("Escolha (1-5): ").strip()
    
    combustivel_map = {
        "1": "gasolina",
        "2": "gasoleo",
        "3": "hibrido",
        "4": "eletrico"
    }
    
    if combustivel_choice in combustivel_map:
        params.combustivel = combustivel_map[combustivel_choice]
    
    return params


def main():
    """Função principal"""
    try:
        # Obter parâmetros de pesquisa
        search_params = get_user_input()
        
        # Valida e otimiza os parâmetros usando o validador
        if search_params.marca or search_params.modelo:
            validation_result = validator.validate_search_params(
                search_params.marca, 
                search_params.modelo
            )
            
            if validation_result['valid']:
                # Usa os valores otimizados do validador para a pesquisa
                if validation_result['brand_value']:
                    original_marca = search_params.marca
                    search_params.marca = validation_result['brand_value']
                    print(f"🔧 Marca otimizada: {original_marca} → {search_params.marca}")
                
                if validation_result['model_value']:
                    original_modelo = search_params.modelo
                    search_params.modelo = validation_result['model_value']
                    print(f"🔧 Modelo otimizado: {original_modelo} → {search_params.modelo}")
            else:
                print("⚠️ Parâmetros de pesquisa com problemas:")
                for error in validation_result['errors']:
                    print(f"   • {error}")
        
        print(f"\n🔍 A pesquisar carros com os critérios especificados...")
        
        # Criar o scraper
        scraper = StandVirtualScraper()
        
        # Fazer a pesquisa
        results = scraper.search_cars(search_params)
        
        if not results:
            print("❌ Nenhum carro encontrado com os critérios especificados.")
            return
        
        # Mostrar resultados
        print(f"\n✅ Encontrados {len(results)} carros:")
        display_results(results)
        
        # Perguntar se quer salvar
        save_choice = input("\n💾 Deseja salvar os resultados em CSV? (s/n): ").strip().lower()
        if save_choice in ['s', 'sim', 'y', 'yes']:
            filename = save_to_csv(results)
            print(f"📁 Resultados salvos em: {filename}")
        
        print("\n✨ Pesquisa concluída!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo utilizador.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 