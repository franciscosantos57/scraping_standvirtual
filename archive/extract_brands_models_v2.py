#!/usr/bin/env python3
"""
Script melhorado para extrair marcas e modelos do StandVirtual.com
Lida com dropdowns customizados e elementos dinâmicos
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def setup_driver():
    """Configura o driver do Selenium"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"❌ Erro ao configurar driver: {e}")
        return None


def extract_from_page_source(driver):
    """
    Extrai dados diretamente do código fonte da página
    """
    print("🔍 Extraindo dados do código fonte da página...")
    
    try:
        page_source = driver.page_source
        
        # Padrões para encontrar dados de marcas e modelos
        patterns = {
            'graphql_data': r'__APOLLO_STATE__":\s*({.*?})(?=,"__APOLLO_CLIENT_CACHE__")',
            'window_data': r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            'filter_data': r'"filterOptions":\s*({.*?})',
            'make_data': r'"make":\s*\[(.*?)\]',
            'model_data': r'"model":\s*\[(.*?)\]'
        }
        
        extracted_data = {}
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, page_source, re.DOTALL)
            if matches:
                print(f"✅ Dados encontrados: {pattern_name}")
                extracted_data[pattern_name] = matches[0]
        
        if extracted_data:
            return parse_extracted_data(extracted_data)
        
        # Se não encontrou dados estruturados, procura por listas simples
        print("🔍 Procurando por listas de marcas simples...")
        
        # Procura por nomes de marcas conhecidas
        known_brands = [
            'BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Toyota', 'Ford', 
            'Opel', 'Renault', 'Peugeot', 'Citroën', 'Nissan', 'Honda',
            'Hyundai', 'Kia', 'Mazda', 'Subaru', 'Volvo', 'Jaguar',
            'Land Rover', 'Porsche', 'Ferrari', 'Lamborghini', 'Bentley',
            'Rolls-Royce', 'Maserati', 'Alfa Romeo', 'Fiat', 'SEAT',
            'Skoda', 'Mini', 'Smart', 'Dacia', 'Lada'
        ]
        
        found_brands = []
        for brand in known_brands:
            # Procura por padrões que incluem a marca
            brand_patterns = [
                f'"{brand}"',
                f"'{brand}'",
                f'value="{brand.lower()}"',
                f"value='{brand.lower()}'"
            ]
            
            for brand_pattern in brand_patterns:
                if brand_pattern in page_source:
                    found_brands.append(brand)
                    break
        
        if found_brands:
            print(f"✅ {len(found_brands)} marcas encontradas por busca simples")
            return {"method": "simple_search", "brands": found_brands}
        
        return None
        
    except Exception as e:
        print(f"❌ Erro ao extrair do código fonte: {e}")
        return None


def parse_extracted_data(data):
    """
    Processa os dados extraídos para encontrar marcas e modelos
    """
    print("🔧 Processando dados extraídos...")
    
    brands_models = {}
    
    try:
        # Tenta parsear dados GraphQL/Apollo
        if 'graphql_data' in data:
            try:
                import json
                apollo_data = json.loads(data['graphql_data'])
                
                # Procura por dados de filtros
                for key, value in apollo_data.items():
                    if isinstance(value, dict) and ('make' in str(value).lower() or 'brand' in str(value).lower()):
                        print(f"🎯 Dados de marca encontrados em: {key}")
                        # Processa os dados encontrados
                        # (implementação específica dependeria da estrutura exata)
                        
            except json.JSONDecodeError:
                pass
        
        # Método alternativo: regex para encontrar estruturas de dados
        all_data = ' '.join(data.values())
        
        # Procura por arrays que contenham marcas
        brand_arrays = re.findall(r'\[((?:"[^"]*(?:BMW|Mercedes|Audi|Volkswagen)[^"]*"[^]]*)+)\]', all_data, re.IGNORECASE)
        
        if brand_arrays:
            print(f"✅ Arrays de marcas encontrados: {len(brand_arrays)}")
            
            for array in brand_arrays:
                # Extrai nomes das marcas
                brand_names = re.findall(r'"([^"]*(?:BMW|Mercedes|Audi|Toyota|Ford|Opel|Renault|Peugeot|Volkswagen|Citroën|Nissan|Honda)[^"]*)"', array, re.IGNORECASE)
                
                if brand_names:
                    print(f"Marcas encontradas: {brand_names[:10]}")
                    
                    # Para cada marca, tenta encontrar modelos associados
                    for brand in brand_names:
                        brands_models[brand] = {
                            'brand_value': brand.lower().replace(' ', '-'),
                            'models': []  # Modelos serão extraídos separadamente
                        }
                    
                    return brands_models
        
        return None
        
    except Exception as e:
        print(f"❌ Erro ao processar dados: {e}")
        return None


def extract_with_interaction(driver):
    """
    Tenta interagir com elementos da página para extrair dados
    """
    print("🔍 Tentando interação com elementos da página...")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Procura por elementos que podem ser dropdowns customizados
        possible_selectors = [
            '[data-testid*="make"]',
            '[data-testid*="marca"]',
            '[placeholder*="Marca"]',
            '[placeholder*="marca"]',
            'input[type="text"]',
            '[role="combobox"]',
            '.dropdown',
            '.select'
        ]
        
        for selector in possible_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"Elementos encontrados para {selector}: {len(elements)}")
                
                for i, element in enumerate(elements):
                    try:
                        # Tenta clicar no elemento para ver se abre opções
                        print(f"  Testando elemento {i+1}...")
                        
                        # Scroll até o elemento
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)
                        
                        # Clica no elemento
                        ActionChains(driver).move_to_element(element).click().perform()
                        time.sleep(2)
                        
                        # Procura por opções que apareceram
                        option_selectors = [
                            '[role="option"]',
                            '.dropdown-item',
                            '.option',
                            'li[data-value]',
                            '[data-testid*="option"]'
                        ]
                        
                        for opt_selector in option_selectors:
                            options = driver.find_elements(By.CSS_SELECTOR, opt_selector)
                            if options:
                                print(f"    ✅ {len(options)} opções encontradas!")
                                
                                brands = []
                                for option in options[:20]:  # Limita a 20 primeiras
                                    text = option.text.strip()
                                    if text and len(text) > 2:
                                        brands.append(text)
                                
                                if brands:
                                    print(f"    Marcas: {brands[:10]}")
                                    return {"method": "interaction", "brands": brands}
                        
                        # Clica fora para fechar
                        driver.find_element(By.TAG_NAME, 'body').click()
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"    ❌ Erro no elemento {i+1}: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Erro com seletor {selector}: {e}")
                continue
        
        return None
        
    except Exception as e:
        print(f"❌ Erro na interação: {e}")
        return None


def main():
    """Função principal"""
    print("🚀 Iniciando extração avançada de marcas e modelos...")
    print("="*60)
    
    driver = setup_driver()
    if not driver:
        return
    
    try:
        print("🌐 Carregando página...")
        url = "https://www.standvirtual.com/carros?search%5Badvanced_search_expanded%5D=true"
        driver.get(url)
        
        # Aguarda carregamento
        time.sleep(8)
        
        print("📄 Página carregada, iniciando extração...")
        
        # Método 1: Extração do código fonte
        result = extract_from_page_source(driver)
        
        if not result:
            # Método 2: Interação com elementos
            result = extract_with_interaction(driver)
        
        if result:
            print(f"\n✅ Extração bem-sucedida!")
            print(f"📊 Método usado: {result.get('method', 'desconhecido')}")
            
            brands = result.get('brands', [])
            print(f"📋 {len(brands)} marcas encontradas:")
            
            # Organiza os dados
            brands_models = {}
            for brand in brands:
                brands_models[brand] = {
                    'brand_value': brand.lower().replace(' ', '-').replace('/', '-'),
                    'models': []  # Por agora, apenas marcas
                }
            
            # Salva os dados
            filename = "standvirtual_brands_models.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(brands_models, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Dados salvos em: {filename}")
            
            # Mostra resumo
            print(f"\n📋 Marcas encontradas:")
            for i, brand in enumerate(sorted(brands), 1):
                print(f"  {i:2d}. {brand}")
                if i >= 20:
                    print(f"  ... e mais {len(brands) - 20} marcas")
                    break
                    
        else:
            print("\n❌ Nenhum dado extraído")
            print("💡 O site pode estar usando proteções anti-bot ou estrutura muito dinâmica")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    main() 