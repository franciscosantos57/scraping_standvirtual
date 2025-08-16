"""
Configurações do projeto
"""

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env se existir
load_dotenv()

# URLs base
STANDVIRTUAL_BASE_URL = "https://www.standvirtual.com"
STANDVIRTUAL_SEARCH_URL = f"{STANDVIRTUAL_BASE_URL}/carros"

# Headers para requests
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Configurações de scraping
MAX_PAGES = int(os.getenv('MAX_PAGES', 999))  # Máximo de páginas a processar (sem limite prático)
DELAY_BETWEEN_REQUESTS = float(os.getenv('DELAY_BETWEEN_REQUESTS', 1.0))  # Delay em segundos
MAX_RESULTS = int(os.getenv('MAX_RESULTS', 9999))  # Máximo de resultados a retornar (sem limite prático)

# Configurações do Selenium (se necessário)
SELENIUM_TIMEOUT = int(os.getenv('SELENIUM_TIMEOUT', 10))
HEADLESS_BROWSER = os.getenv('HEADLESS_BROWSER', 'True').lower() == 'true'

# Diretório para salvar resultados
RESULTS_DIR = os.getenv('RESULTS_DIR', 'results')
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

# Mapeamento de parâmetros para o site (valores corretos obtidos do HTML do site)
FUEL_TYPE_MAP = {
    'gasolina': 'gaz',              
    'gasoleo': 'diesel',            
    'diesel': 'diesel', 
    'hibrido': 'hibride-gaz',       
    'hibrido_diesel': 'Híbrido (Diesel)',
    'hibrido_plugin': 'plugin-hybrid',  
    'eletrico': 'electric',             
    'gnc': 'GNC',
    'gpl': 'GPL',
    'hidrogenio': 'Hidrogénio'
}

TRANSMISSION_MAP = {
    'manual': 'manual',
    'automatica': 'automatic'
} 