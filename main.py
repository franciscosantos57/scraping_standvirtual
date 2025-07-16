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
        
        # Validar e otimizar parâmetros
        if search_params.marca or search_params.modelo:
            validation_result = validator.validate_search_params(
                search_params.marca, 
                search_params.modelo
            )
            
            if validation_result['valid']:
                if validation_result['brand_value']:
                    logger.info(f"Marca otimizada: {search_params.marca} → {validation_result['brand_value']}")
                    search_params.marca = validation_result['brand_value']
                
                if validation_result['model_value']:
                    logger.info(f"Modelo otimizado: {search_params.modelo} → {validation_result['model_value']}")
                    search_params.modelo = validation_result['model_value']
            else:
                logger.warning("Parâmetros de pesquisa com problemas:")
                for error in validation_result['errors']:
                    logger.warning(f"  • {error}")
        
        # Criar o scraper
        scraper = StandVirtualScraper()
        
        # Fazer a pesquisa
        logger.info("Iniciando pesquisa de carros...")
        results = scraper.search_cars(search_params)
        
        if not results:
            logger.warning("Nenhum carro encontrado com os critérios especificados")
            output = {"min": None, "max": None}
        else:
            logger.info(f"Encontrados {len(results)} carros")
            
            # Calcular intervalo de preços (sem outliers)
            price_interval = calculate_price_interval(results)
            
            # Log detalhado das estatísticas
            logger.info(f"Total de carros: {len(results)}")
            logger.info(f"Carros após remoção de outliers: {price_interval['total_cars_after_outliers']}")
            logger.info(f"Outliers removidos: {price_interval['outliers_removed']}")
            logger.info(f"Tempo de extração: {price_interval.get('extraction_time', 0):.2f} segundos")
            logger.info(f"Intervalo de preços final: {price_interval['min_price']}€ - {price_interval['max_price']}€")
            
            # Output JSON minimalista
            output = {
                "min": price_interval['min_price'],
                "max": price_interval['max_price']
            }
        
        logger.info("Scraping concluído com sucesso")
        
        # Retornar apenas JSON (sem prints)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except KeyboardInterrupt:
        logger.error("Operação cancelada pelo utilizador")
        output = {"min": None, "max": None}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro durante a execução: {str(e)}", exc_info=True)
        output = {"min": None, "max": None}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main() 