"""
Funções auxiliares para o projeto
"""

import re
import csv
import pandas as pd
from datetime import datetime
from typing import List
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


def extract_year(text: str) -> int:
    """Extrai o ano de um texto"""
    if not text:
        return None
    
    # Procura por anos entre 1990 e 2030
    year_match = re.search(r'\b(19[9]\d|20[0-3]\d)\b', text)
    if year_match:
        return int(year_match.group(1))
    
    return None


def clean_mileage(mileage_text: str) -> str:
    """Limpa o texto da quilometragem"""
    if not mileage_text:
        return "N/A"
    
    # Remove caracteres especiais e mantém só números e 'km'
    clean_text = re.sub(r'[^\d\skm]', '', mileage_text.lower())
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text if clean_text else "N/A"


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
        
        if car.caixa:
            print(f"   ⚙️  Caixa: {car.caixa}")
        
        # URL sempre exibida e destacada
        if car.url:
            print(f"   🔗 LINK: {car.url}")
        else:
            print(f"   ⚠️  URL não disponível")
        
        print(f"   {'-'*60}")
    
    if len(cars) > max_display:
        print(f"\n... e mais {len(cars) - max_display} resultados")
        print(f"💡 Para ver todos os resultados e URLs, salve em CSV!")
    
    # Estatísticas
    prices = [car.preco_numerico for car in cars if car.preco_numerico > 0]
    urls_count = len([car for car in cars if car.url])
    
    if prices:
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   Preço médio: {sum(prices)/len(prices):,.0f} €".replace(',', '.'))
        print(f"   Preço mínimo: {min(prices):,.0f} €".replace(',', '.'))
        print(f"   Preço máximo: {max(prices):,.0f} €".replace(',', '.'))
        print(f"   🔗 URLs encontradas: {urls_count}/{len(cars)} carros")


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