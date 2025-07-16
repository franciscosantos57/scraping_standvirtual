"""
Funções auxiliares para o projeto
"""

import re
import csv
import pandas as pd
import statistics
from datetime import datetime
from typing import List, Tuple
from models.car import Car
from utils.config import RESULTS_DIR


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


def detect_outliers(prices: List[float]) -> Tuple[List[float], int]:
    """
    Detecta e remove outliers usando o método IQR (Interquartile Range)
    
    Args:
        prices: Lista de preços numéricos
        
    Returns:
        tuple: (preços_sem_outliers, quantidade_outliers_removidos)
    """
    if len(prices) < 4:  # Precisa de pelo menos 4 valores para calcular quartis
        return prices, 0
    
    # Ordena os preços
    sorted_prices = sorted(prices)
    
    # Calcula quartis
    q1 = statistics.quantiles(sorted_prices, n=4)[0]  # Primeiro quartil (25%)
    q3 = statistics.quantiles(sorted_prices, n=4)[2]  # Terceiro quartil (75%)
    
    # Calcula IQR
    iqr = q3 - q1
    
    # Define limites para outliers
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Remove outliers
    filtered_prices = [price for price in prices if lower_bound <= price <= upper_bound]
    outliers_removed = len(prices) - len(filtered_prices)
    
    return filtered_prices, outliers_removed


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


def display_results(cars: List[Car], max_display: int = 10):
    """
    Exibe os resultados de forma formatada
    
    Args:
        cars: Lista de carros encontrados
        max_display: Máximo de carros a exibir
    """
    if not cars:
        print("Nenhum resultado encontrado.")
        return
    
    print(f"\n{'='*80}")
    print(f"RESULTADOS ENCONTRADOS ({len(cars)} carros)")
    print(f"{'='*80}")
    
    # Ordena por preço crescente
    sorted_cars = sorted(cars, key=lambda x: x.preco_numerico)
    
    for i, car in enumerate(sorted_cars[:max_display], 1):
        print(f"\n{i}. {car.titulo}")
        print(f"   💰 Preço: {car.preco}")
        
        if car.ano:
            print(f"   📅 Ano: {car.ano}")
        
        if car.quilometragem and car.quilometragem != "N/A":
            print(f"   🛣️  Quilometragem: {car.quilometragem}")
        
        if car.combustivel:
            print(f"   ⛽ Combustível: {car.combustivel}")
        
        # URL sempre exibida e destacada
        if car.url:
            print(f"   🔗 LINK: {car.url}")
        else:
            print(f"   ⚠️  URL não disponível")
        
        print(f"   {'-'*60}")
    
    if len(cars) > max_display:
        print(f"\n... e mais {len(cars) - max_display} resultados")
        print(f"💡 Para ver todos os resultados e URLs, salve em CSV!")
    
    # Verifica se há tempo de extração (armazenado no primeiro carro)
    extraction_time = getattr(cars[0], '_extraction_time', None) if cars else None
    
    # Estatísticas com remoção de outliers
    prices = [car.preco_numerico for car in cars if car.preco_numerico > 0]
    urls_count = len([car for car in cars if car.url])
    
    if prices:
        # Remove outliers
        filtered_prices, outliers_removed = detect_outliers(prices)
        
        if filtered_prices:
            min_price = min(filtered_prices)
            max_price = max(filtered_prices)
            
            print(f"\n📊 ESTATÍSTICAS (sem outliers):")
            print(f"   💰 Intervalo de preços: {min_price:,.0f} € - {max_price:,.0f} €".replace(',', '.'))
            print(f"   📈 Total de carros: {len(cars)}")
            print(f"   🔗 URLs encontradas: {urls_count}/{len(cars)} carros")
            
            # Mostra tempo de extração se disponível
            if extraction_time is not None:
                print(f"   ⏱️  Tempo de extração: {extraction_time:.2f} segundos")
                if len(cars) > 0:
                    cars_per_second = len(cars) / extraction_time
                    print(f"   📈 Velocidade: {cars_per_second:.1f} carros/segundo")
            
            if outliers_removed > 0:
                print(f"   🚫 Outliers removidos: {outliers_removed} carros (preços muito fora do normal)")
        else:
            print(f"\n📊 ESTATÍSTICAS:")
            print(f"   ⚠️  Não foi possível calcular intervalo (dados insuficientes)")
            
            # Mostra tempo mesmo se não há preços válidos
            if extraction_time is not None:
                print(f"   ⏱️  Tempo de extração: {extraction_time:.2f} segundos")


def save_to_csv(cars: List[Car], filename: str = None) -> str:
    """
    Salva os resultados em arquivo CSV
    
    Args:
        cars: Lista de carros
        filename: Nome do arquivo (opcional)
    
    Returns:
        Nome do arquivo criado
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{RESULTS_DIR}/standvirtual_results_{timestamp}.csv"
    
    # Converte carros para dicionários
    data = [car.to_dict() for car in cars]
    
    if data:
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
    
    return filename


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