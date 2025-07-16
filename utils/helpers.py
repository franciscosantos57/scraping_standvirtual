"""
Funções auxiliares para o StandVirtual Scraper
"""

import re
import csv
import pandas as pd
import statistics
from datetime import datetime
from typing import List, Tuple
from models.car import Car
from utils.config import RESULTS_DIR
from utils.logging_config import get_logger

logger = get_logger(__name__)


def clean_price(price_text: str) -> tuple[str, float]:
    """
    Limpa e converte o texto do preço para formato numérico
    
    Args:
        price_text: Texto do preço (ex: "15.000 €", "R$ 15000")
    
    Returns:
        tuple: (preço_formatado, preço_numérico)
    """
    if not price_text:
        return "N/A", 0.0
    
    # Remove espaços e caracteres especiais, mantém apenas números
    clean_text = re.sub(r'[^\d,.]', '', price_text)
    
    try:
        # Trata diferentes formatos de número
        if ',' in clean_text and '.' in clean_text:
            # Formato: 15.000,00 ou 15,000.00
            if clean_text.rfind(',') > clean_text.rfind('.'):
                # Formato europeu: 15.000,00
                clean_text = clean_text.replace('.', '').replace(',', '.')
            else:
                # Formato americano: 15,000.00
                clean_text = clean_text.replace(',', '')
        elif ',' in clean_text:
            # Só vírgula - pode ser decimal ou separador de milhares
            if len(clean_text.split(',')[-1]) <= 2:
                # Provavelmente decimal
                clean_text = clean_text.replace(',', '.')
            else:
                # Provavelmente separador de milhares
                clean_text = clean_text.replace(',', '')
        
        numeric_price = float(clean_text)
        formatted_price = f"{numeric_price:,.0f} €".replace(',', '.')
        
        return formatted_price, numeric_price
    
    except (ValueError, AttributeError):
        return price_text, 0.0


def detect_outliers(prices):
    """
    Detecta outliers nos preços usando o método IQR (Interquartile Range).
    
    Args:
        prices (list): Lista de preços numéricos
        
    Returns:
        dict: {
            'filtered_prices': lista sem outliers,
            'outliers': lista de outliers removidos,
            'stats': estatísticas do processo
        }
    """
    if len(prices) < 4:
        logger.info(f"Poucos dados para filtrar outliers ({len(prices)} preços). Mantendo todos os valores.")
        return {
            'filtered_prices': prices.copy(),
            'outliers': [],
            'stats': {
                'total_original': len(prices),
                'total_filtered': len(prices),
                'outliers_removed': 0,
                'reason': 'insufficient_data'
            }
        }
    
    # Calcula quartis (compatível com Python < 3.8)
    sorted_prices = sorted(prices)
    n = len(sorted_prices)
    q1_index = int(n * 0.25)
    q3_index = int(n * 0.75)
    
    q1 = sorted_prices[q1_index]
    q3 = sorted_prices[q3_index]
    iqr = q3 - q1
    
    # Limites para outliers
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    logger.info(f"Análise de outliers: Q1={q1:.0f}€, Q3={q3:.0f}€, IQR={iqr:.0f}€")
    logger.info(f"Limites: {lower_bound:.0f}€ - {upper_bound:.0f}€")
    
    # Separa dados válidos de outliers
    filtered_prices = []
    outliers = []
    
    for price in prices:
        if lower_bound <= price <= upper_bound:
            filtered_prices.append(price)
        else:
            outliers.append(price)
    
    # Se todos os valores fossem removidos, mantém os originais
    if not filtered_prices:
        logger.warning("Todos os preços seriam removidos como outliers. Mantendo valores originais.")
        return {
            'filtered_prices': prices.copy(),
            'outliers': [],
            'stats': {
                'total_original': len(prices),
                'total_filtered': len(prices),
                'outliers_removed': 0,
                'reason': 'all_would_be_outliers'
            }
        }
    
    # Log dos resultados
    if outliers:
        logger.info(f"Outliers removidos ({len(outliers)}): {[f'{p:.0f}€' for p in sorted(outliers)]}")
        logger.info(f"Dados válidos: {len(filtered_prices)} preços entre {min(filtered_prices):.0f}€ - {max(filtered_prices):.0f}€")
    else:
        logger.info("Nenhum outlier detectado. Todos os preços estão dentro do intervalo normal.")
    
    return {
        'filtered_prices': filtered_prices,
        'outliers': outliers,
        'stats': {
            'total_original': len(prices),
            'total_filtered': len(filtered_prices),
            'outliers_removed': len(outliers),
            'reason': 'normal_filtering'
        }
    }


def calculate_price_interval(cars):
    """
    Calcula o intervalo de preços (min-max) sem outliers.
    
    Args:
        cars (list): Lista de objetos Car
        
    Returns:
        dict: Dados do intervalo de preços para output JSON
    """
    if not cars:
        logger.warning("Lista de carros vazia para cálculo de intervalo")
        return {
            'min_price': None,
            'max_price': None,
            'total_cars_after_outliers': 0,
            'outliers_removed': 0,
            'extraction_time': 0
        }
    
    # Extrai preços numéricos válidos
    prices = []
    extraction_time = 0
    
    for car in cars:
        if hasattr(car, 'preco_numerico') and car.preco_numerico and car.preco_numerico > 0:
            prices.append(car.preco_numerico)
        
        # Captura tempo de extração se disponível (armazenado no primeiro carro)
        if hasattr(car, 'extraction_time'):
            extraction_time = car.extraction_time
    
    logger.info(f"Calculando intervalo de preços para {len(prices)} carros")
    
    if not prices:
        logger.warning("Nenhum preço válido encontrado")
        return {
            'min_price': None,
            'max_price': None,
            'total_cars_after_outliers': 0,
            'outliers_removed': 0,
            'extraction_time': extraction_time
        }
    
    # Remove outliers
    outlier_result = detect_outliers(prices)
    filtered_prices = outlier_result['filtered_prices']
    
    # Calcula intervalo
    min_price = min(filtered_prices)
    max_price = max(filtered_prices)
    
    result = {
        'min_price': min_price,
        'max_price': max_price,
        'total_cars_after_outliers': len(filtered_prices),
        'outliers_removed': len(outlier_result['outliers']),
        'extraction_time': extraction_time
    }
    
    logger.info(f"Intervalo final: {min_price:.0f}€ - {max_price:.0f}€ (sem {len(outlier_result['outliers'])} outliers)")
    
    return result


def extract_year(date_str: str) -> int:
    """
    Extrai o ano de uma string de data
    
    Args:
        date_str: String contendo data
        
    Returns:
        Ano extraído ou None
    """
    if not date_str:
        return None
    
    # Procura por ano no formato YYYY
    year_match = re.search(r'\b(19|20)\d{2}\b', str(date_str))
    if year_match:
        return int(year_match.group())
    
    return None


def clean_mileage(mileage_text: str) -> tuple[str, int]:
    """
    Limpa e converte quilometragem
    
    Args:
        mileage_text: Texto da quilometragem
        
    Returns:
        tuple: (texto_formatado, valor_numérico)
    """
    if not mileage_text:
        return "N/A", 0
    
    # Extrai números da quilometragem
    numbers = re.findall(r'\d+', str(mileage_text))
    if numbers:
        km_value = int(''.join(numbers))
        formatted_km = f"{km_value:,} km".replace(',', '.')
        return formatted_km, km_value
    
    return mileage_text, 0


def display_results(cars):
    """
    Função obsoleta - agora apenas faz log dos resultados.
    O output real é feito via JSON no main.py
    """
    logger.info(f"display_results() chamada com {len(cars)} carros (função obsoleta)")
    
    if not cars:
        logger.info("Nenhum resultado para mostrar")
        return
    
    # Log resumido dos carros encontrados
    logger.info("=== RESUMO DOS CARROS ENCONTRADOS ===")
    for i, car in enumerate(cars[:5], 1):  # Log apenas os primeiros 5
        logger.info(f"{i}. {car.titulo} - {car.preco} ({car.ano}, {car.quilometragem})")
    
    if len(cars) > 5:
        logger.info(f"... e mais {len(cars) - 5} carros")
    
    # Calcula estatísticas para log
    interval = calculate_price_interval(cars)
    logger.info(f"Estatísticas: {interval}")


def save_to_csv(cars):
    """
    Função obsoleta - funcionalidade de CSV removida.
    Sistema agora retorna apenas JSON.
    """
    logger.warning("save_to_csv() chamada - funcionalidade removida. Sistema agora usa apenas JSON.")
    return None


def build_search_url(base_url: str, params: dict) -> str:
    """
    Constrói a URL de pesquisa com os parâmetros
    
    Args:
        base_url: URL base
        params: Dicionário de parâmetros
    
    Returns:
        URL completa de pesquisa
    """
    if not params:
        return base_url
    
    query_parts = []
    
    for key, value in params.items():
        if value is not None:
            query_parts.append(f"{key}={value}")
    
    if query_parts:
        return f"{base_url}?{'&'.join(query_parts)}"
    
    return base_url 