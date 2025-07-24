#!/usr/bin/env python3
"""
StandVirtual Car Price Scraper - Production Version
Sistema de scraping que retorna apenas o intervalo de preços em JSON
"""

import sys
import json
from scraper.standvirtual_scraper import StandVirtualScraper
from models.car import CarSearchParams
from utils.helpers import calculate_price_interval
from utils.brand_model_validator import validator
from utils.logging_config import setup_logging, get_logger


def create_search_params_from_args():
    """
    Cria parâmetros de pesquisa a partir dos argumentos da linha de comando.
    Exemplo: python main.py --marca bmw --modelo x5 --ano_min 2015 --preco_max 25000
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='StandVirtual Car Price Scraper')
    parser.add_argument('--marca', type=str, help='Marca do carro')
    parser.add_argument('--modelo', type=str, help='Modelo do carro')
    parser.add_argument('--submodelo', type=str, help='Submodelo do carro (ex: IS 200, 320i, etc)')
    parser.add_argument('--ano_min', type=int, help='Ano mínimo')
    parser.add_argument('--ano_max', type=int, help='Ano máximo')
    parser.add_argument('--km_max', type=int, help='Quilometragem máxima')
    parser.add_argument('--preco_max', type=int, help='Preço máximo')
    parser.add_argument('--caixa', type=str, choices=['manual', 'automatica'], help='Tipo de caixa')
    parser.add_argument('--combustivel', type=str, choices=['gasolina', 'gasoleo', 'hibrido', 'eletrico'], help='Tipo de combustível')
    
    args = parser.parse_args()
    
    params = CarSearchParams()
    if args.marca:
        params.marca = args.marca
    if args.modelo:
        params.modelo = args.modelo
    if args.submodelo:
        params.submodelo = args.submodelo
    if args.ano_min:
        params.ano_min = args.ano_min
    if args.ano_max:
        params.ano_max = args.ano_max
    if args.km_max:
        params.km_max = args.km_max
    if args.preco_max:
        params.preco_max = args.preco_max
    if args.caixa:
        params.caixa = args.caixa
    if args.combustivel:
        params.combustivel = args.combustivel
    
    return params


def main():
    """Função principal - versão de produção"""
    try:
        # Configurar logging
        setup_logging()
        logger = get_logger(__name__)
        
        logger.info("Iniciando scraping do StandVirtual")
        
        # Obter parâmetros de pesquisa
        search_params = create_search_params_from_args()
        
        # Log dos parâmetros de pesquisa
        logger.info(f"Parâmetros de pesquisa: {search_params.__dict__}")
        
        # Validação restritiva - apenas valores exatos da base de dados
        if search_params.marca or search_params.modelo or search_params.submodelo:
            validation_result = validator.validate_search_params(
                search_params.marca, 
                search_params.modelo,
                search_params.submodelo
            )
            
            if validation_result['valid']:
                if validation_result['brand_value']:
                    logger.info(f"Marca otimizada: {search_params.marca} → {validation_result['brand_value']}")
                    search_params.marca = validation_result['brand_value']
                
                if validation_result['model_value']:
                    logger.info(f"Modelo otimizado: {search_params.modelo} → {validation_result['model_value']}")
                    search_params.modelo = validation_result['model_value']
                
                if validation_result['submodel_value']:
                    logger.info(f"Submodelo otimizado: {search_params.submodelo} → {validation_result['submodel_value']}")
                    search_params.submodelo = validation_result['submodel_value']
            else:
                logger.error("Parâmetros de pesquisa inválidos - valores não encontrados na base de dados:")
                for error in validation_result['errors']:
                    logger.error(f"  • {error}")
                
                # Mostra sugestões se disponíveis
                if validation_result.get('suggestions'):
                    logger.info("Sugestões:")
                    for key, suggestions in validation_result['suggestions'].items():
                        logger.info(f"  {key}: {', '.join(suggestions[:3])}")
                
                output = {
                    "preco_intervalo": {
                        "min": None,
                        "max": None
                    },
                    "media_aproximada": None,
                    "viaturas_consideradas": 0,
                    "anuncios_usados_para_calculo": []
                }
                print(json.dumps(output, ensure_ascii=False, indent=2))
                sys.exit(1)
        
        # Criar o scraper
        scraper = StandVirtualScraper()
        
        # Fazer a pesquisa
        logger.info("Iniciando pesquisa de carros...")
        results = scraper.search_cars(search_params)
        
        if not results:
            logger.warning("Nenhum carro encontrado com os critérios especificados")
            output = {
                "preco_intervalo": {
                    "min": None,
                    "max": None
                },
                "media_aproximada": None,
                "viaturas_consideradas": 0,
                "anuncios_usados_para_calculo": []
            }
        else:
            logger.info(f"Encontrados {len(results)} carros")
            
            # Calcular dados completos (sem outliers)
            output = calculate_price_interval(results)
            
            # Log detalhado das estatísticas
            logger.info(f"Total de carros: {len(results)}")
            logger.info(f"Carros considerados: {output['viaturas_consideradas']}")
            logger.info(f"Média aproximada: {output['media_aproximada']}€")
            
            if output['preco_intervalo']['min'] and output['preco_intervalo']['max']:
                logger.info(f"Intervalo de preços: {output['preco_intervalo']['min']}€ - {output['preco_intervalo']['max']}€")
        
        logger.info("Scraping concluído com sucesso")
        
        # Retornar apenas JSON (sem prints)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except KeyboardInterrupt:
        logger.error("Operação cancelada pelo utilizador")
        output = {
            "preco_intervalo": {
                "min": None,
                "max": None
            },
            "media_aproximada": None,
            "viaturas_consideradas": 0,
            "anuncios_usados_para_calculo": []
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro durante a execução: {str(e)}", exc_info=True)
        output = {
            "preco_intervalo": {
                "min": None,
                "max": None
            },
            "media_aproximada": None,
            "viaturas_consideradas": 0,
            "anuncios_usados_para_calculo": []
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main() 