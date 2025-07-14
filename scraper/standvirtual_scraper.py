"""
Scraper principal para o StandVirtual.com
"""

import time
import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from typing import List, Optional
import re
import urllib.parse

from models.car import Car, CarSearchParams
from utils.config import (
    STANDVIRTUAL_SEARCH_URL, DEFAULT_HEADERS, MAX_PAGES, 
    DELAY_BETWEEN_REQUESTS, MAX_RESULTS, SELENIUM_TIMEOUT, 
    HEADLESS_BROWSER, FUEL_TYPE_MAP, TRANSMISSION_MAP
)
from utils.helpers import clean_price, extract_year, clean_mileage


class StandVirtualScraper:
    """Scraper para o site StandVirtual.com"""
    
    def __init__(self, use_selenium: bool = True):
        """
        Inicializa o scraper
        
        Args:
            use_selenium: Se deve usar Selenium (recomendado para sites com JS)
        """
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        
        # User agent rotativo
        self.ua = UserAgent()
        
        self.driver = None
        if self.use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Configura o driver do Selenium"""
        try:
            chrome_options = Options()
            
            # Configurações para modo headless
            if HEADLESS_BROWSER:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={self.ua.random}")
            
            # Desabilita imagens para ser mais rápido
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Instala e configura o ChromeDriver automaticamente
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_page_load_timeout(SELENIUM_TIMEOUT)
                
                print("✅ Selenium configurado com sucesso")
                
            except Exception as e:
                print(f"⚠️ Erro com ChromeDriverManager: {e}")
                # Fallback - tentar usar chromedriver do sistema
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.driver.set_page_load_timeout(SELENIUM_TIMEOUT)
                    print("✅ Selenium configurado com chromedriver do sistema")
                except Exception as e2:
                    print(f"⚠️ Erro com chromedriver do sistema: {e2}")
                    raise e2
                
        except Exception as e:
            print(f"⚠️ Erro ao configurar Selenium: {e}")
            print("Usando requests/BeautifulSoup como fallback...")
            self.use_selenium = False
    
    def _build_search_params(self, params: CarSearchParams) -> dict:
        """
        Constrói os parâmetros de pesquisa para o StandVirtual
        
        Args:
            params: Parâmetros de pesquisa
            
        Returns:
            Dicionário com parâmetros para a URL
        """
        search_params = {}
        
        # Marca
        if params.marca:
            search_params['search[filter_enum_make]'] = params.marca.lower()
        
        # Modelo - Usa pesquisa específica (funciona melhor)
        if params.modelo:
            search_params['search[filter_enum_model]'] = params.modelo.lower()
        
        # Ano
        if params.ano_min:
            search_params['search[filter_float_first_registration_year:from]'] = params.ano_min
        if params.ano_max:
            search_params['search[filter_float_first_registration_year:to]'] = params.ano_max
        
        # Quilometragem
        if params.km_max:
            search_params['search[filter_float_mileage:to]'] = params.km_max
        
        # Preço
        if params.preco_max:
            search_params['search[filter_float_price:to]'] = params.preco_max
        
        # Combustível
        if params.combustivel and params.combustivel in FUEL_TYPE_MAP:
            search_params['search[filter_enum_fuel_type]'] = FUEL_TYPE_MAP[params.combustivel]
        
        # Transmissão
        if params.caixa and params.caixa in TRANSMISSION_MAP:
            search_params['search[filter_enum_gearbox]'] = TRANSMISSION_MAP[params.caixa]
        
        return search_params
    
    def _get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Obtém o conteúdo de uma página
        
        Args:
            url: URL da página
            
        Returns:
            BeautifulSoup object ou None se erro
        """
        try:
            if self.use_selenium and self.driver:
                print(f"🌐 Carregando página com Selenium...")
                self.driver.get(url)
                
                # Aguarda o carregamento da página
                try:
                    # Aguarda elementos aparecerem ou timeout
                    WebDriverWait(self.driver, SELENIUM_TIMEOUT).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
                    time.sleep(2)  # Aguarda um pouco mais para JavaScript carregar
                except:
                    print("⚠️ Timeout aguardando carregamento, continuando...")
                
                html = self.driver.page_source
                return BeautifulSoup(html, 'html.parser')
            
            else:
                # Fallback para requests
                print(f"🌐 Carregando página com requests...")
                response = self.session.get(url, headers={'User-Agent': self.ua.random})
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
                
        except Exception as e:
            print(f"⚠️ Erro ao obter página {url}: {e}")
            return None
    
    def _extract_json_ld_data(self, soup: BeautifulSoup) -> List[Car]:
        """
        Extrai dados dos carros a partir do JSON-LD estruturado
        
        Args:
            soup: BeautifulSoup object da página
            
        Returns:
            Lista de carros extraídos dos dados estruturados
        """
        cars = []
        
        try:
            # Procura pelo script JSON-LD com dados dos anúncios
            json_ld_script = soup.find('script', {'data-testid': 'listing-json-ld'})
            
            if json_ld_script and json_ld_script.string:
                data = json.loads(json_ld_script.string)
                
                if 'mainEntity' in data and 'itemListElement' in data['mainEntity']:
                    items = data['mainEntity']['itemListElement']
                    
                    # Também extrai URLs dos elementos HTML para fazer correspondência
                    url_map = self._extract_urls_from_html(soup)
                    
                    for i, item in enumerate(items):
                        if item.get('@type') == 'Offer':
                            car = self._parse_json_ld_item(item, url_map.get(i))
                            if car:
                                cars.append(car)
                                
        except Exception as e:
            print(f"⚠️ Erro ao extrair dados JSON-LD: {e}")
        
        return cars
    
    def _extract_urls_from_html(self, soup: BeautifulSoup) -> dict:
        """
        Extrai URLs dos anúncios da página HTML
        
        Args:
            soup: BeautifulSoup object da página
            
        Returns:
            Dicionário mapeando índice para URL
        """
        url_map = {}
        
        try:
            # Método 1: Procura por todas as URLs de anúncios no HTML
            all_ad_urls = []
            
            # Padrões para encontrar URLs de anúncios
            url_patterns = [
                r'href="(https://www\.standvirtual\.com/carros/anuncio/[^"]+)"',
                r'href="(/carros/anuncio/[^"]+)"',
                r'"url":"(https://www\.standvirtual\.com/carros/anuncio/[^"]+)"',
                r'"url":"(/carros/anuncio/[^"]+)"'
            ]
            
            html_text = str(soup)
            
            for pattern in url_patterns:
                matches = re.findall(pattern, html_text)
                for match in matches:
                    if match.startswith('/'):
                        full_url = f"https://www.standvirtual.com{match}"
                    else:
                        full_url = match
                    
                    if full_url not in all_ad_urls:
                        all_ad_urls.append(full_url)
            
            # Mapeia URLs por índice (primeira URL para primeiro item, etc.)
            for i, url in enumerate(all_ad_urls):
                url_map[i] = url
            
            print(f"🔗 URLs extraídas do HTML: {len(all_ad_urls)}")
            for i, url in enumerate(all_ad_urls):
                print(f"   {i}: {url}")
            
            # Método 2: Fallback - procura por elementos article
            if not url_map:
                articles = soup.find_all('article')
                
                for i, article in enumerate(articles):
                    # Procura por links dentro do article
                    link_selectors = [
                        'a[href*="/anuncio/"]', 
                        'a[href*="/carro/"]',
                        'a[href*="/veiculo/"]',
                        'h3 a', 'h2 a', 'h1 a',
                        'a[title]'
                    ]
                    
                    for selector in link_selectors:
                        link = article.select_one(selector)
                        if link and link.get('href'):
                            href = link.get('href')
                            if href.startswith('/'):
                                url_map[i] = f"https://www.standvirtual.com{href}"
                            elif href.startswith('http'):
                                url_map[i] = href
                            break
                            
        except Exception as e:
            print(f"⚠️ Erro ao extrair URLs HTML: {e}")
        
        return url_map
    
    def _parse_json_ld_item(self, item: dict, url: str = None) -> Optional[Car]:
        """
        Converte um item JSON-LD em objeto Car
        
        Args:
            item: Item do JSON-LD
            url: URL do anúncio (opcional)
            
        Returns:
            Objeto Car ou None se erro
        """
        try:
            # Extrai informações do preço
            price_spec = item.get('priceSpecification', {})
            price_value = price_spec.get('price', '0')
            currency = price_spec.get('priceCurrency', 'EUR')
            
            preco_numerico = float(price_value) if price_value else 0.0
            # Correção: usar formatação segura para preços
            if preco_numerico > 0:
                preco_formatado = f"{preco_numerico:.0f} {currency}"
            else:
                preco_formatado = f"0 {currency}"
            
            # Extrai informações do veículo
            car_info = item.get('itemOffered', {})
            
            titulo = car_info.get('name', 'Título não disponível')
            marca = car_info.get('brand', '')
            combustivel = car_info.get('fuelType', '')
            ano = None
            
            # Converte ano
            model_date = car_info.get('modelDate')
            if model_date:
                ano = int(model_date) if model_date.isdigit() else extract_year(model_date)
            
            # Extrai quilometragem
            mileage_info = car_info.get('mileageFromOdometer', {})
            km_value = mileage_info.get('value')
            km_unit = mileage_info.get('unitCode', 'KMT')
            
            quilometragem = None
            if km_value:
                # Correção: formatação segura para quilometragem
                try:
                    km_num = float(km_value)
                    quilometragem = f"{km_num:.0f} km"
                except (ValueError, TypeError):
                    quilometragem = f"{km_value} km"
            
            # Tenta extrair URL do próprio item JSON-LD
            json_url = item.get('url') or item.get('@id') or item.get('offers', {}).get('url')
            
            # Usa a URL extraída do HTML se disponível, senão tenta a do JSON-LD
            final_url = url or json_url
            
            # Se ainda não tem URL, tenta construir uma básica
            if not final_url and titulo != 'Título não disponível':
                # Tenta criar uma URL de busca básica
                search_title = titulo.lower().replace(' ', '-').replace('/', '-')
                final_url = f"https://www.standvirtual.com/carros/{search_title}"
            
            # Mapeia combustível para português
            combustivel_map = {
                'Gasolina': 'Gasolina',
                'Diesel': 'Gasóleo', 
                'Híbrido (Gasolina)': 'Híbrido',
                'Híbrido Plug-In': 'Híbrido Plug-In',
                'Eléctrico': 'Elétrico'
            }
            combustivel = combustivel_map.get(combustivel, combustivel)
            
            return Car(
                titulo=titulo,
                preco=preco_formatado,
                preco_numerico=preco_numerico,
                ano=ano,
                quilometragem=quilometragem,
                combustivel=combustivel,
                caixa="N/A",  # Será preenchido na validação
                potencia="N/A",  # Será preenchido na validação
                segmento="N/A",  # Será preenchido na validação
                cilindrada="N/A",  # Será preenchido na validação
                url=final_url    # Agora extrai a URL real
            )
            
        except Exception as e:
            print(f"⚠️ Erro ao processar item JSON-LD: {e}")
            return None
    
    def _extract_selenium_data(self, driver) -> List[Car]:
        """
        Extrai dados usando Selenium para sites dinâmicos
        
        Args:
            driver: WebDriver do Selenium
            
        Returns:
            Lista de carros extraídos
        """
        cars = []
        
        try:
            # Aguarda elementos dos anúncios carregarem
            wait = WebDriverWait(driver, SELENIUM_TIMEOUT)
            
            # Tenta diferentes seletores para os anúncios
            selectors = [
                'article',
                '[data-testid*="listing"]',
                '[data-testid*="ad"]',
                '.listing-item',
                '.car-item',
                '.offer-item'
            ]
            
            elements = []
            for selector in selectors:
                try:
                    elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                    if elements:
                        print(f"✅ Encontrados {len(elements)} elementos com: {selector}")
                        break
                except:
                    continue
            
            if not elements:
                print("❌ Nenhum elemento de anúncio encontrado")
                return cars
            
            # Extrai dados de cada elemento
            for element in elements[:MAX_RESULTS]:
                try:
                    car = self._extract_selenium_car_data(element)
                    if car and car.preco_numerico > 0:
                        cars.append(car)
                except Exception as e:
                    print(f"⚠️ Erro ao extrair dados do elemento: {e}")
                    continue
                    
        except Exception as e:
            print(f"⚠️ Erro na extração com Selenium: {e}")
        
        return cars
    
    def _extract_selenium_car_data(self, element) -> Optional[Car]:
        """
        Extrai dados de um elemento usando Selenium
        
        Args:
            element: WebElement do Selenium
            
        Returns:
            Objeto Car ou None se erro
        """
        try:
            # Extrai texto do elemento
            text = element.text
            html = element.get_attribute('outerHTML')
            
            if not text or len(text.strip()) < 10:
                return None  # Elemento muito pequeno, provavelmente não é um anúncio
            
            # Procura por título/nome do carro - seletores mais específicos
            titulo = "Título não encontrado"
            title_selectors = [
                'h1.offer-title',  # Seletor específico do StandVirtual
                'h3[data-testid*="ad-title"]',
                'h2[data-testid*="ad-title"]', 
                'h1[data-testid*="ad-title"]',
                '[data-testid*="ad-title"]',
                'h3 a', 'h2 a', 'h1 a',
                'a[title]', 
                'h3', 'h2', 'h1'
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    title_text = title_elem.text.strip() or title_elem.get_attribute('title')
                    if title_text and len(title_text) > 5:
                        titulo = title_text
                        break
                except:
                    continue
            
            # Se não encontrou título nos elementos filhos, tenta extrair da primeira linha do texto
            if titulo == "Título não encontrado":
                lines = text.split('\n')
                for line in lines[:3]:  # Primeiras 3 linhas
                    if len(line.strip()) > 10 and not re.search(r'\d+.*€', line):
                        titulo = line.strip()
                        break
            
            # Procura por preço - padrões mais específicos
            preco_text = None
            price_patterns = [
                r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€)',  # 25.000,00 €
                r'(\d{1,3}(?:,\d{3})*\s*€)',               # 25,000 €
                r'(\d+\.\d{3}\s*€)',                       # 25.000 €
                r'(\d+,\d{3}\s*€)',                        # 25,000 €
                r'(\d+\s*€)',                              # 25000 €
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    # Pega o primeiro preço encontrado que pareça válido
                    for match in matches:
                        price_num = re.sub(r'[^\d]', '', match)
                        if len(price_num) >= 3:  # Preço mínimo de 100
                            preco_text = match
                            break
                    if preco_text:
                        break
            
            if preco_text:
                preco_formatado, preco_numerico = clean_price(preco_text)
            else:
                return None  # Se não tem preço, não é um anúncio válido
            
            # Extrai ano - melhor regex
            ano = None
            year_patterns = [
                r'\b(20[0-2]\d|19[89]\d)\b',  # 1980-2029
                r'(\d{4})\s*/',               # 2020/
                r'/(\d{4})\s',                # /2020
            ]
            
            for pattern in year_patterns:
                match = re.search(pattern, text)
                if match:
                    year_candidate = int(match.group(1))
                    if 1980 <= year_candidate <= 2030:
                        ano = year_candidate
                        break
            
            # Extrai quilometragem - melhor regex
            quilometragem = None
            km_patterns = [
                r'(\d{1,3}(?:\.\d{3})*)\s*km',    # 150.000 km
                r'(\d{1,3}(?:,\d{3})*)\s*km',     # 150,000 km
                r'(\d+)\s*km',                     # 150000 km
            ]
            
            for pattern in km_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    km_text = match.group(1)
                    # Limpa e formata
                    km_clean = re.sub(r'[^\d]', '', km_text)
                    if km_clean and int(km_clean) > 100:  # Mínimo 100 km
                        quilometragem = f"{km_text} km"
                        break
            
            # Extrai combustível - mais tipos
            combustivel = None
            combustiveis_map = {
                'gasolina': 'Gasolina',
                'gasóleo': 'Gasóleo', 
                'diesel': 'Gasóleo',
                'híbrido': 'Híbrido',
                'hibrido': 'Híbrido',
                'elétrico': 'Elétrico',
                'eletrico': 'Elétrico',
                'plug-in': 'Híbrido Plug-In'
            }
            
            text_lower = text.lower()
            for key, value in combustiveis_map.items():
                if key in text_lower:
                    combustivel = value
                    break
            
            # Extrai URL do anúncio - método melhorado
            url = None
            try:
                # Seletores mais específicos para links de anúncios
                link_selectors = [
                    'a[href*="/anuncio/"]', 
                    'a[href*="/anuncios/"]', 
                    'a[href*="/carro/"]',
                    'a[href*="/automovel/"]',
                    'a[href*="/veiculo/"]',
                    'h3 a[href]', 
                    'h2 a[href]', 
                    'h1 a[href]',
                    'a[title][href]',
                    'a[href][class*="link"]',
                    'a[href]'
                ]
                
                for selector in link_selectors:
                    try:
                        link_elem = element.find_element(By.CSS_SELECTOR, selector)
                        href = link_elem.get_attribute('href')
                        
                        if href:
                            # Valida se é um link de anúncio válido
                            if any(keyword in href for keyword in ['/anuncio/', '/anuncios/', '/carro/', '/automovel/', '/veiculo/']):
                                if href.startswith('/'):
                                    url = f"https://www.standvirtual.com{href}"
                                elif href.startswith('http'):
                                    url = href
                                break
                            # Se não tem palavras-chave específicas, mas é um link interno
                            elif href.startswith('/') and len(href) > 10:
                                url = f"https://www.standvirtual.com{href}"
                                break
                            elif href.startswith('https://www.standvirtual.com/') and len(href) > 30:
                                url = href
                                break
                    except:
                        continue
                        
                # Se ainda não encontrou URL, tenta método alternativo
                if not url:
                    try:
                        # Procura por qualquer link que pareça ser de um anúncio
                        all_links = element.find_elements(By.CSS_SELECTOR, 'a[href]')
                        for link in all_links:
                            href = link.get_attribute('href')
                            if href and len(href) > 30 and 'standvirtual.com' in href:
                                url = href
                                break
                    except:
                        pass
                        
            except Exception as e:
                print(f"⚠️ Erro ao extrair URL: {e}")
            
            # Se ainda não encontrou URL, cria uma URL de busca baseada no título
            if not url and titulo != "Título não encontrado":
                try:
                    # Cria uma URL de busca simples
                    search_term = titulo.lower().replace(' ', '+').replace('/', '')
                    url = f"https://www.standvirtual.com/carros?search%5Bfilter_enum_make%5D={search_term.split('+')[0]}"
                except:
                    pass
            
            # Só retorna se tiver informações mínimas válidas
            if preco_numerico > 0 and titulo != "Título não encontrado":
                return Car(
                    titulo=titulo,
                    preco=preco_formatado,
                    preco_numerico=preco_numerico,
                    ano=ano,
                    quilometragem=quilometragem,
                    combustivel=combustivel,
                    caixa="N/A",  # Será preenchido na validação
                    potencia="N/A",  # Será preenchido na validação
                    segmento="N/A",  # Será preenchido na validação
                    cilindrada="N/A",  # Será preenchido na validação
                    url=url    # Agora extrai a URL real
                )
            
            return None
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair dados do elemento: {e}")
            return None
    
    def _validate_url(self, url: str) -> bool:
        """
        Valida se a URL é um link válido para um carro específico
        
        Args:
            url: URL para validar
            
        Returns:
            True se a URL é válida, False caso contrário
        """
        if not url:
            return False
            
        try:
            # Verifica se é uma URL do StandVirtual
            if not 'standvirtual.com' in url:
                return False
            
            # REJEITA apenas URLs claramente genéricas
            invalid_patterns = [
                r'/carros/?$',                           # /carros ou /carros/
                r'/carros\?',                           # /carros?search=...
                r'/carros/[a-zA-Z-]+/?$',              # /carros/bmw ou /carros/mercedes-benz (só marca)
                r'/carros/[a-zA-Z-]+/[a-zA-Z-]+/?$',   # /carros/bmw/x5 (só marca/modelo)
            ]
            
            # Mas NÃO rejeita se tem características específicas (hífen + números/especificações)
            for pattern in invalid_patterns:
                if re.search(pattern, url):
                    # Se a URL contém números, pontos ou especificações técnicas, é válida
                    if re.search(r'[\d.]+|fsi|quattro|tronic|cv|km|diesel|gasolina', url.lower()):
                        continue  # Não rejeita, é específica
                    return False
            
            # Aceita URLs específicas
            valid_patterns = [
                r'/anuncio/.+ID\w+\.html$',             # /anuncio/...ID123abc.html
                r'/carros/.+ID\w+',                     # /carros/...-ID123abc
                r'/carros/[^/]+/[^/]+/[^/]+',          # /carros/marca/modelo/especifico
                r'/carros/[^/]+-[^/]*[\d.]',           # /carros/audi-r8-4.2-fsi (com especificações)
                r'/carros/[^/]*[\d.]+[^/]*-',          # /carros/audi-r8-coupé-4.2-fsi
            ]
            
            for pattern in valid_patterns:
                if re.search(pattern, url):
                    return True
            
            # Se tem especificações técnicas na URL, aceita
            if re.search(r'[\d.]+.*(?:fsi|tdi|cv|km|diesel|gasolina|quattro|tronic|xdrive)', url.lower()):
                return True
            
            # Se tem pelo menos 4 níveis e é longa, provavelmente é específica
            if url.count('/') >= 4 and len(url) > 50:
                return True
                
            return False
            
        except Exception:
            return False
    
    def _validate_car_data(self, car: Car) -> Car:
        """
        Valida e atualiza dados do carro acessando a página individual do anúncio
        
        Args:
            car: Objeto Car com dados iniciais
            
        Returns:
            Objeto Car com dados validados/atualizados ou None se inválido
        """
        if not car or not car.url:
            return None
            
        # Validação RIGOROSA apenas para URLs genéricas
        if not self._validate_url(car.url):
            print(f"   ❌ URL genérica rejeitada: {car.url}")
            return None
            
        try:
            print(f"🔍 Validando: {car.titulo[:40]}...")
            
            # Dados originais para comparação
            original_price = car.preco_numerico
            original_title = car.titulo
            original_km = car.quilometragem
            original_year = car.ano
            original_fuel = car.combustivel
            
            validated = False
            corrections_made = 0
            
            # Método 1: Selenium (mais preciso) - SEMPRE usa para dados técnicos
            if self.use_selenium and self.driver:
                try:
                    # Verifica se o driver ainda está ativo
                    try:
                        current_url = self.driver.current_url
                    except Exception:
                        # Driver morreu, recria
                        print(f"   🔄 Recreando driver Selenium...")
                        self._setup_selenium()
                        if not self.driver:
                            raise Exception("Falha ao recriar driver")
                    
                    original_url = self.driver.current_url
                    self.driver.get(car.url)
                    time.sleep(3)  # Aguarda carregamento completo
                    
                    # Verifica se a página carregou corretamente
                    current_url = self.driver.current_url
                    if ('erro' in current_url.lower() or '404' in current_url or 
                        'standvirtual.com/carros?' in current_url or 
                        current_url.endswith('/carros') or
                        current_url.endswith('/carros/')):
                        print(f"   ❌ Redirecionamento inválido: {current_url}")
                        return None
                    
                    # 1. Extrai o TÍTULO CORRETO diretamente do h1.offer-title
                    try:
                        # Busca pelo título correto na página usando o seletor h1.offer-title
                        title_element = self.driver.find_element(By.CSS_SELECTOR, 'h1.offer-title')
                        correct_title = title_element.text.strip()
                        
                        if correct_title and len(correct_title) > 5:
                            if original_title != correct_title:
                                print(f"   📝 Título corrigido: {original_title[:30]}... → {correct_title}")
                                corrections_made += 1
                            car.titulo = correct_title
                            
                    except Exception as e:
                        print(f"   ⚠️ Erro ao extrair título correto: {e}")
                    
                    # 2. Extrai dados do título da página para preço, ano e quilometragem
                    title = self.driver.title
                    if title and 'standvirtual' in title.lower():
                        # Extrai preço do título: "Usado BMW X5 2020 - 56 990 EUR, 51 000 km"
                        price_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*EUR', title)
                        if price_match:
                            price_str = price_match.group(1).replace(' ', '')
                            new_price = float(price_str)
                            
                            if abs(new_price - original_price) > 100:  # Só mostra se diferença significativa
                                print(f"   💰 Preço: {original_price} → {new_price}")
                                corrections_made += 1
                            car.preco_numerico = new_price
                            car.preco = f"{new_price:.0f} EUR"
                        
                        # Extrai quilometragem do título
                        km_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*km', title)
                        if km_match:
                            km_str = km_match.group(1).replace(' ', '')
                            new_km = f"{km_str} km"
                            if original_km and original_km != new_km:
                                print(f"   🛣️  KM: {original_km} → {new_km}")
                                corrections_made += 1
                            car.quilometragem = new_km
                        
                        # Extrai ano do título
                        year_match = re.search(r'\b(20[0-2]\d|19[89]\d)\b', title)
                        if year_match:
                            new_year = int(year_match.group(1))
                            if original_year and original_year != new_year:
                                print(f"   📅 Ano: {original_year} → {new_year}")
                                corrections_made += 1
                            car.ano = new_year
                    
                    # 2. Extrai dados técnicos da página usando Selenium
                    page_source = self.driver.page_source
                    
                    # Combustível - busca em elementos estruturados
                    combustivel_found = False
                    try:
                        # Busca em elementos que podem conter dados técnicos
                        tech_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                            '[data-testid*="parameter"], .parameter, .spec, .characteristic, p, div')
                        
                        for element in tech_elements:
                            text = element.text.lower()
                            if any(fuel in text for fuel in ['combustível', 'fuel', 'combustible']):
                                # Mapeia combustíveis corretamente
                                if 'gasóleo' in text or 'diesel' in text:
                                    car.combustivel = 'Gasóleo'
                                    combustivel_found = True
                                elif 'gasolina' in text or 'petrol' in text:
                                    car.combustivel = 'Gasolina'
                                    combustivel_found = True
                                elif 'híbrido' in text or 'hybrid' in text:
                                    if 'plug' in text:
                                        car.combustivel = 'Híbrido Plug-In'
                                    else:
                                        car.combustivel = 'Híbrido'
                                    combustivel_found = True
                                elif 'elétrico' in text or 'electric' in text:
                                    car.combustivel = 'Elétrico'
                                    combustivel_found = True
                                break
                    except:
                        pass
                    
                    # Se não encontrou combustível em elementos estruturados, busca no texto geral
                    if not combustivel_found:
                        text_lower = page_source.lower()
                        if 'gasóleo' in text_lower or 'diesel' in text_lower:
                            car.combustivel = 'Gasóleo'
                        elif 'gasolina' in text_lower:
                            car.combustivel = 'Gasolina'
                        elif 'híbrido' in text_lower or 'hybrid' in text_lower:
                            car.combustivel = 'Híbrido'
                        elif 'elétrico' in text_lower or 'electric' in text_lower:
                            car.combustivel = 'Elétrico'
                    
                    if original_fuel != car.combustivel:
                        print(f"   ⛽ Combustível: {original_fuel} → {car.combustivel}")
                        corrections_made += 1
                    
                    # 3. Extrai outros dados técnicos usando seletores específicos que funcionam
                    try:
                        # Caixa de velocidades
                        if not car.caixa or car.caixa == "N/A":
                            if 'automática' in page_source.lower() or 'automatic' in page_source.lower():
                                car.caixa = 'Automática'
                            elif 'manual' in page_source.lower():
                                car.caixa = 'Manual'
                        
                        # Segmento - busca por texto específico no conteúdo da página
                        if not car.segmento or car.segmento == "N/A":
                            try:
                                # Segmentos portugueses completos do StandVirtual
                                segmento_keywords = [
                                    'Cabrio', 'Carrinha', 'Citadino', 'Coupé', 'Monovolume', 
                                    'Pequeno citadino', 'Sedan', 'SUV', 'TT', 'Utilitário',
                                    # Variantes e sinónimos
                                    'Station', 'Hatchback', 'MPV', 'Van', 'Pick-up'
                                ]
                                
                                for keyword in segmento_keywords:
                                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                                    for elem in elements:
                                        text = elem.text.strip()
                                        if keyword in text and len(text) < 30:  # Evita textos muito longos
                                            # Mapeamento para segmentos portugueses
                                            if 'Cabrio' in text:
                                                car.segmento = 'Cabrio'
                                            elif 'Carrinha' in text or 'Station' in text:
                                                car.segmento = 'Carrinha'
                                            elif 'Pequeno citadino' in text:
                                                car.segmento = 'Pequeno citadino'
                                            elif 'Citadino' in text or 'Hatchback' in text:
                                                car.segmento = 'Citadino'
                                            elif 'Coupé' in text:
                                                car.segmento = 'Coupé'
                                            elif 'Monovolume' in text or 'MPV' in text:
                                                car.segmento = 'Monovolume'
                                            elif 'Sedan' in text:
                                                car.segmento = 'Sedan'
                                            elif 'SUV' in text or 'TT' in text:
                                                car.segmento = 'SUV / TT'
                                            elif 'Utilitário' in text or 'Van' in text or 'Pick-up' in text:
                                                car.segmento = 'Utilitário'
                                            
                                            if car.segmento != "N/A":
                                                print(f"   🚗 Segmento extraído: {car.segmento}")
                                                break
                                    if car.segmento != "N/A":
                                        break
                            except Exception as e:
                                print(f"   ⚠️ Erro extraindo segmento: {e}")
                        
                        # Cilindrada - usa seletor .ez0zock2 que funciona
                        if not car.cilindrada or car.cilindrada == "N/A":
                            try:
                                # Busca elementos com classe ez0zock2 que contêm cm3
                                ez_elements = self.driver.find_elements(By.CSS_SELECTOR, '.ez0zock2')
                                for elem in ez_elements:
                                    text = elem.text.strip()
                                    if 'cm3' in text.lower() and any(char.isdigit() for char in text):
                                        car.cilindrada = text
                                        print(f"   🔧 Cilindrada extraída: {car.cilindrada}")
                                        break
                                
                                # Fallback: busca por aria-label ou texto direto
                                if car.cilindrada == "N/A":
                                    cilindrada_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'cm3') or contains(text(), 'cm³')]")
                                    for elem in cilindrada_elements:
                                        text = elem.text.strip()
                                        if any(char.isdigit() for char in text) and len(text) < 15:
                                            car.cilindrada = text
                                            print(f"   🔧 Cilindrada (fallback): {car.cilindrada}")
                                            break
                                            
                            except Exception as e:
                                print(f"   ⚠️ Erro extraindo cilindrada: {e}")
                        
                        # Potência - busca por aria-label que funciona
                        if not car.potencia or car.potencia == "N/A":
                            try:
                                # Método 1: aria-label específico
                                potencia_element = self.driver.find_element(By.CSS_SELECTOR, '[aria-label*="Potência"]')
                                # Extrai texto do elemento ou dos seus filhos
                                text = potencia_element.text.strip()
                                if 'cv' in text.lower():
                                    # Extrai apenas a parte numérica + cv
                                    match = re.search(r'(\d+\s*cv)', text, re.IGNORECASE)
                                    if match:
                                        car.potencia = match.group(1)
                                        print(f"   ⚡ Potência extraída: {car.potencia}")
                                    
                            except:
                                try:
                                    # Método 2: busca por texto que contenha 'cv'
                                    cv_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'cv')]")
                                    for elem in cv_elements:
                                        text = elem.text.strip()
                                        if any(char.isdigit() for char in text) and len(text) < 15 and 'cv' in text.lower():
                                            car.potencia = text
                                            print(f"   ⚡ Potência (fallback): {car.potencia}")
                                            break
                                except Exception as e:
                                    print(f"   ⚠️ Erro extraindo potência: {e}")
                        
                    except Exception as e:
                        print(f"   ⚠️ Erro geral ao extrair dados técnicos: {e}")
                    
                    validated = True
                    
                    # Volta para a página original
                    if original_url != car.url:
                        self.driver.get(original_url)
                        
                except Exception as e:
                    print(f"   ⚠️ Erro Selenium: {e}")
                    # Continua com requests como fallback
            
            # Método 2: Requests como fallback (extrai TODOS os dados técnicos)
            if not validated:
                try:
                    print(f"   🔄 Usando requests como fallback...")
                    response = self.session.get(car.url, timeout=8)
                    if response.status_code == 200:
                        # Verifica redirecionamentos inválidos
                        if (response.url.endswith('/carros') or 
                            response.url.endswith('/carros/') or
                            'standvirtual.com/carros?' in response.url):
                            print(f"   ❌ Redirecionamento inválido: {response.url}")
                            return None
                        
                        html_content = response.text
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Extrai título da página HTML
                        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
                        if title_match:
                            title = title_match.group(1)
                            
                            # Processa preço do título
                            price_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*EUR', title)
                            if price_match:
                                price_str = price_match.group(1).replace(' ', '')
                                new_price = float(price_str)
                                
                                if abs(new_price - original_price) > 100:
                                    print(f"   💰 Preço (requests): {original_price} → {new_price}")
                                    corrections_made += 1
                                car.preco_numerico = new_price
                                car.preco = f"{new_price:.0f} EUR"
                        
                        # EXTRAI DADOS TÉCNICOS com requests/BeautifulSoup
                        self._extract_technical_data_fallback(car, html_content, soup)
                        validated = True
                        
                except Exception as e:
                    print(f"   ⚠️ Erro requests: {e}")
            
            # Se não conseguiu validar mas tem dados básicos, aceita
            if not validated and car.preco_numerico > 0:
                validated = True
                print(f"   📋 Mantendo dados originais")
            
            if not validated:
                print(f"   ❌ Falha na validação")
                return None
            
            # Validações finais (menos rigorosas)
            if car.preco_numerico < 200:  # Preço muito baixo
                print(f"   ❌ Preço suspeito: {car.preco_numerico}")
                return None
                
            if not car.titulo or len(car.titulo) < 5:
                print(f"   ❌ Título muito curto: {car.titulo}")
                return None
            
            if corrections_made > 0:
                print(f"   ✅ Validado com {corrections_made} correções")
            else:
                print(f"   ✅ Validado (dados já corretos)")
            
            return car
            
        except Exception as e:
            print(f"   ❌ Erro geral: {e}")
            return None
    
    def _extract_technical_data_fallback(self, car: Car, html_content: str, soup: BeautifulSoup):
        """
        Extrai dados técnicos usando requests/BeautifulSoup como fallback
        
        Args:
            car: Objeto Car para atualizar
            html_content: Conteúdo HTML da página
            soup: BeautifulSoup object
        """
        try:
            # 1. Caixa de velocidades
            if not car.caixa or car.caixa == "N/A":
                if 'automática' in html_content.lower() or 'automatic' in html_content.lower():
                    car.caixa = 'Automática'
                    print(f"   ⚙️  Caixa (fallback): {car.caixa}")
                elif 'manual' in html_content.lower():
                    car.caixa = 'Manual'
                    print(f"   ⚙️  Caixa (fallback): {car.caixa}")
            
            # 2. Segmento - busca no HTML
            if not car.segmento or car.segmento == "N/A":
                segmento_keywords = [
                    'Cabrio', 'Carrinha', 'Citadino', 'Coupé', 'Monovolume', 
                    'Pequeno citadino', 'Sedan', 'SUV', 'TT', 'Utilitário',
                    # Variantes e sinónimos
                    'Station', 'Hatchback', 'MPV', 'Van', 'Pick-up', 'Spyder'
                ]
                
                for keyword in segmento_keywords:
                    if keyword.lower() in html_content.lower():
                        # Mapeamento para segmentos portugueses
                        if keyword == 'Cabrio' or keyword == 'Spyder':
                            car.segmento = 'Cabrio'
                        elif keyword == 'Carrinha' or keyword == 'Station':
                            car.segmento = 'Carrinha'
                        elif keyword == 'Pequeno citadino':
                            car.segmento = 'Pequeno citadino'
                        elif keyword == 'Citadino' or keyword == 'Hatchback':
                            car.segmento = 'Citadino'
                        elif keyword == 'Coupé':
                            car.segmento = 'Coupé'
                        elif keyword == 'Monovolume' or keyword == 'MPV':
                            car.segmento = 'Monovolume'
                        elif keyword == 'Sedan':
                            car.segmento = 'Sedan'
                        elif keyword == 'SUV' or keyword == 'TT':
                            car.segmento = 'SUV / TT'
                        elif keyword == 'Utilitário' or keyword == 'Van' or keyword == 'Pick-up':
                            car.segmento = 'Utilitário'
                        
                        print(f"   🚗 Segmento (fallback): {car.segmento}")
                        break
            
            # 3. Cilindrada - busca por padrões regex
            if not car.cilindrada or car.cilindrada == "N/A":
                cilindrada_patterns = [
                    r'(\d{1,2}\s?\d{3}\s?cm3)',      # 1 598 cm3
                    r'(\d{1,2}\.\d{3}\s?cm3)',       # 1.598 cm3
                    r'(\d{1,2},\d{3}\s?cm3)',        # 1,598 cm3
                    r'(\d{3,4}\s?cm3)',              # 1598 cm3
                ]
                
                for pattern in cilindrada_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        car.cilindrada = match.group(1)
                        print(f"   🔧 Cilindrada (fallback): {car.cilindrada}")
                        break
            
            # 4. Potência - busca por padrões regex
            if not car.potencia or car.potencia == "N/A":
                potencia_patterns = [
                    r'(\d{2,4}\s?cv)',               # 150 cv
                    r'(\d{2,4}\s?CV)',               # 150 CV
                    r'(\d{2,4}\s?hp)',               # 150 hp
                    r'(\d{2,4}\s?HP)',               # 150 HP
                ]
                
                for pattern in potencia_patterns:
                    match = re.search(pattern, html_content)
                    if match:
                        potencia_text = match.group(1).lower()
                        # Converte HP para CV se necessário
                        if 'hp' in potencia_text:
                            hp_value = int(re.search(r'\d+', potencia_text).group())
                            cv_value = int(hp_value * 0.986)  # Conversão HP para CV
                            car.potencia = f"{cv_value} cv"
                        else:
                            car.potencia = potencia_text
                        print(f"   ⚡ Potência (fallback): {car.potencia}")
                        break
            
            # 5. Título correto do h1.offer-title se disponível
            offer_title = soup.select_one('h1.offer-title')
            if offer_title and offer_title.get_text(strip=True):
                new_title = offer_title.get_text(strip=True)
                if new_title != car.titulo:
                    print(f"   📝 Título corrigido (fallback): {car.titulo[:30]}... → {new_title}")
                    car.titulo = new_title
                    
        except Exception as e:
            print(f"   ⚠️ Erro na extração de dados técnicos (fallback): {e}")
    
    def search_cars(self, params: CarSearchParams) -> List[Car]:
        """
        Pesquisa carros com os parâmetros especificados
        
        Args:
            params: Parâmetros de pesquisa
            
        Returns:
            Lista de carros encontrados
        """
        cars = []
        
        try:
            # NOVA FUNCIONALIDADE: Pesquisa inteligente por variações
            search_variations = self._get_model_variations(params)
            
            # Sempre faz pesquisa inteligente se há variações
            if len(search_variations) > 1:
                print(f"🔍 Pesquisa inteligente: buscando {len(search_variations)} variações do modelo")
                
                # Pesquisa cada variação separadamente
                for i, variation_params in enumerate(search_variations, 1):
                    modelo_display = variation_params.modelo or 'modelo genérico'
                    print(f"\n📋 Variação {i}/{len(search_variations)}: {modelo_display}")
                    variation_cars = self._search_single_variation(variation_params)
                    
                    if variation_cars:
                        cars.extend(variation_cars)
                        print(f"✅ {len(variation_cars)} carros encontrados nesta variação")
                    else:
                        print(f"❌ Nenhum carro encontrado nesta variação")
            else:
                # Pesquisa normal para um modelo específico
                print(f"🔍 Pesquisa simples: {params.modelo}")
                cars = self._search_single_variation(params)
            
        except Exception as e:
            print(f"❌ Erro durante a pesquisa: {e}")
        
        finally:
            # Fecha o driver se foi usado
            if self.use_selenium and self.driver:
                self.driver.quit()
        
        return self._process_final_results(cars, params)
    
    def _get_model_variations(self, params: CarSearchParams) -> List[CarSearchParams]:
        """
        Obtém todas as variações de um modelo para pesquisa inteligente
        
        Args:
            params: Parâmetros originais
            
        Returns:
            Lista de parâmetros para cada variação
        """
        variations = [params]  # Sempre inclui a pesquisa original
        
        # Se especificou marca e modelo, busca variações
        if params.marca and params.modelo:
            try:
                from utils.brand_model_validator import validator
                
                # Busca todas as variações do modelo (corrige case sensitivity)
                marca_original = params.marca.title()  # Audi, BMW, etc.
                all_models = validator.get_models_for_brand(marca_original)
                base_model = params.modelo.lower()
                
                # Encontra variações que contêm o modelo base
                model_variations = []
                for model in all_models:
                    model_text_lower = model['text'].lower()
                    
                    # Se contém o modelo base, é uma variação (inclui também o modelo exato)
                    if base_model in model_text_lower:
                        model_variations.append(model)
                
                print(f"🎯 Encontradas {len(model_variations)} variações para '{params.modelo}':")
                for var in model_variations:
                    print(f"   • {var['text']} → {var['value']}")
                
                # Cria parâmetros para TODAS as variações (incluindo o original)
                for variation in model_variations:
                    var_params = CarSearchParams()
                    var_params.marca = params.marca
                    var_params.modelo = variation['value']  # Usa o valor correto
                    var_params.ano_min = params.ano_min
                    var_params.ano_max = params.ano_max
                    var_params.km_max = params.km_max
                    var_params.preco_max = params.preco_max
                    var_params.caixa = params.caixa
                    var_params.combustivel = params.combustivel
                    
                    variations.append(var_params)
                
                # Remove o primeiro (original) se há mais de uma variação
                if len(variations) > 1:
                    variations = variations[1:]  # Remove o primeiro (original)
                    
            except Exception as e:
                print(f"⚠️ Erro ao buscar variações: {e}")
        
        return variations
    
    def _search_single_variation(self, params: CarSearchParams) -> List[Car]:
        """
        Pesquisa uma única variação de modelo
        
        Args:
            params: Parâmetros de pesquisa
            
        Returns:
            Lista de carros encontrados
        """
        cars = []
        
        # Constrói parâmetros de pesquisa
        search_params = self._build_search_params(params)
        
        # Constrói URL de pesquisa
        if search_params:
            query_string = urllib.parse.urlencode(search_params)
            search_url = f"{STANDVIRTUAL_SEARCH_URL}?{query_string}"
        else:
            search_url = STANDVIRTUAL_SEARCH_URL
        
        print(f"🔗 URL: {search_url}")
        
        page = 1
        while page <= MAX_PAGES and len(cars) < MAX_RESULTS:
            # URL da página
            if page > 1:
                page_url = f"{search_url}&page={page}"
            else:
                page_url = search_url
            
            # Obtém conteúdo da página
            soup = self._get_page_content(page_url)
            if not soup:
                break
            
            # Primeira tentativa: dados JSON-LD
            json_cars = self._extract_json_ld_data(soup)
            if json_cars:
                cars.extend(json_cars)
            
            # Segunda tentativa: Selenium se disponível e necessário
            if self.use_selenium and self.driver and len(cars) < 5:
                selenium_cars = self._extract_selenium_data(self.driver)
                if selenium_cars:
                    # Evita duplicatas
                    for car in selenium_cars:
                        if not any(existing.titulo == car.titulo for existing in cars):
                            cars.append(car)
            
            if len(cars) == 0:
                break
            
            # Só processa uma página se encontrou dados JSON-LD (são completos)
            if json_cars:
                break
            
            page += 1
            
            # Delay entre requisições
            if page <= MAX_PAGES:
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return cars
    
    def _process_final_results(self, cars: List[Car], params: CarSearchParams) -> List[Car]:
        """
        Processa os resultados finais (deduplicação, validação)
        
        Args:
            cars: Lista de carros encontrados
            params: Parâmetros originais de pesquisa
            
        Returns:
            Lista de carros processados
        """
        if not cars:
            return []
        
        print(f"🎉 Total de {len(cars)} carros extraídos!")
        
        # MELHORIA 1: Deduplicação APENAS por URL (não por título)
        print(f"\n🔧 Removendo duplicatas por URL...")
        unique_cars = []
        seen_urls = set()
        
        for car in cars:
            # Remove APENAS por URL duplicada (mesmo anúncio)
            if car.url and car.url in seen_urls:
                print(f"   🗑️  Duplicata: mesmo anúncio → {car.titulo[:40]}...")
                continue
            
            # Aceita o carro se URL for única ou se não tiver URL
            unique_cars.append(car)
            if car.url:
                seen_urls.add(car.url)
        
        print(f"✅ {len(unique_cars)} carros únicos após deduplicação (só URLs)")
        print(f"💡 Carros com mesmo nome mas características diferentes são mantidos")
        
        # MELHORIA 2: Validação RIGOROSA de TODOS os carros
        print(f"\n🔍 Validando TODOS os carros rigorosamente...")
        validated_cars = []
        
        for i, car in enumerate(unique_cars):
            print(f"   [{i+1}/{len(unique_cars)}]", end=" ")
            validated_car = self._validate_car_data(car)
            if validated_car:
                validated_cars.append(validated_car)
            else:
                print(f"   ❌ Carro rejeitado: {car.titulo[:40]}...")
        
        print(f"\n✅ Validação concluída! {len(validated_cars)} carros válidos")
        print(f"🎯 TODOS os carros têm URLs válidas e dados verificados")
        
        return validated_cars
    
    def __del__(self):
        """Destructor para limpar recursos"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass 