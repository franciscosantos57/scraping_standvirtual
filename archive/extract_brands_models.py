#!/usr/bin/env python3
"""
Script para extrair todas as marcas e modelos disponíveis no StandVirtual.com
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
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


def extract_brands_and_models():
    """Extrai todas as marcas e modelos do StandVirtual"""
    
    driver = setup_driver()
    if not driver:
        return None
    
    brands_models = {}
    
    try:
        print("🌐 Carregando página de pesquisa avançada...")
        url = "https://www.standvirtual.com/carros?search%5Badvanced_search_expanded%5D=true"
        driver.get(url)
        
        # Aguarda a página carregar
        wait = WebDriverWait(driver, 20)
        time.sleep(5)  # Aguarda JavaScript carregar
        
        print("🔍 Procurando por dropdowns de marca...")
        
        # Diferentes seletores possíveis para o dropdown de marca
        marca_selectors = [
            'select[name*="make"]',
            'select[name*="marca"]', 
            'select[id*="make"]',
            'select[id*="marca"]',
            '[data-testid*="make"]',
            '[data-testid*="marca"]',
            'select:first-of-type'
        ]
        
        marca_element = None
        for selector in marca_selectors:
            try:
                marca_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                print(f"✅ Dropdown de marca encontrado: {selector}")
                break
            except TimeoutException:
                continue
        
        if not marca_element:
            print("❌ Dropdown de marca não encontrado")
            
            # Tenta encontrar qualquer elemento que possa ser um dropdown
            print("🔍 Procurando por elementos alternativos...")
            
            # Procura por elementos que podem ser dropdowns customizados
            possible_elements = driver.find_elements(By.CSS_SELECTOR, 
                '[role="combobox"], [role="listbox"], .dropdown, .select, input[placeholder*="marca"], input[placeholder*="Marca"]')
            
            print(f"Elementos possíveis encontrados: {len(possible_elements)}")
            
            for i, elem in enumerate(possible_elements):
                try:
                    tag = elem.tag_name
                    classes = elem.get_attribute('class')
                    placeholder = elem.get_attribute('placeholder')
                    role = elem.get_attribute('role')
                    print(f"  {i+1}. {tag} - classes: {classes} - placeholder: {placeholder} - role: {role}")
                except:
                    pass
            
            # Se não encontrou dropdown tradicional, tenta método alternativo
            print("🔄 Tentando método alternativo...")
            return extract_from_api_calls(driver)
        
        # Se encontrou dropdown de marca
        if marca_element.tag_name.lower() == 'select':
            select_marca = Select(marca_element)
            marcas = []
            
            print("📋 Extraindo marcas...")
            for option in select_marca.options:
                value = option.get_attribute('value')
                text = option.text.strip()
                if value and text and value != '' and text != 'Todas as marcas':
                    marcas.append({'value': value, 'text': text})
            
            print(f"✅ {len(marcas)} marcas encontradas")
            
            # Para cada marca, extrai os modelos
            for i, marca in enumerate(marcas):
                print(f"🔍 [{i+1}/{len(marcas)}] Extraindo modelos para {marca['text']}...")
                
                try:
                    # Seleciona a marca
                    select_marca.select_by_value(marca['value'])
                    time.sleep(2)  # Aguarda carregar modelos
                    
                    # Procura dropdown de modelo
                    modelo_selectors = [
                        'select[name*="model"]',
                        'select[name*="modelo"]',
                        'select[id*="model"]', 
                        'select[id*="modelo"]'
                    ]
                    
                    modelo_element = None
                    for selector in modelo_selectors:
                        try:
                            modelo_element = driver.find_element(By.CSS_SELECTOR, selector)
                            break
                        except NoSuchElementException:
                            continue
                    
                    if modelo_element:
                        select_modelo = Select(modelo_element)
                        modelos = []
                        
                        for option in select_modelo.options:
                            value = option.get_attribute('value')
                            text = option.text.strip()
                            if value and text and value != '' and text != 'Todos os modelos':
                                modelos.append({'value': value, 'text': text})
                        
                        brands_models[marca['text']] = {
                            'brand_value': marca['value'],
                            'models': modelos
                        }
                        
                        print(f"   ✅ {len(modelos)} modelos encontrados")
                    else:
                        print(f"   ⚠️ Dropdown de modelo não encontrado para {marca['text']}")
                        brands_models[marca['text']] = {
                            'brand_value': marca['value'],
                            'models': []
                        }
                
                except Exception as e:
                    print(f"   ❌ Erro ao processar {marca['text']}: {e}")
                    continue
                
                # Limita para não sobrecarregar (remover depois de testar)
                if i >= 5:  # Testa apenas primeiras 5 marcas
                    print("🔄 Limitando a 5 marcas para teste...")
                    break
        
        return brands_models
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return None
        
    finally:
        driver.quit()


def extract_from_api_calls(driver):
    """
    Método alternativo: intercepta chamadas de API ou extrai dados do HTML/JavaScript
    """
    print("🔍 Tentando extrair dados de chamadas de API...")
    
    try:
        # Procura por dados no JavaScript da página
        scripts = driver.find_elements(By.TAG_NAME, 'script')
        
        for script in scripts:
            try:
                content = script.get_attribute('innerHTML')
                if content and ('make' in content.lower() or 'marca' in content.lower()):
                    # Procura por estruturas que parecem conter marcas
                    import re
                    
                    # Padrões para encontrar dados de marcas
                    patterns = [
                        r'"makes":\s*\[(.*?)\]',
                        r'"marcas":\s*\[(.*?)\]',
                        r'"brands":\s*\[(.*?)\]'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.DOTALL)
                        if matches:
                            print(f"✅ Dados encontrados com padrão: {pattern}")
                            # Tenta parsear os dados
                            try:
                                # Extrai nomes das marcas
                                brand_names = re.findall(r'"([^"]*(?:BMW|Mercedes|Audi|Volkswagen|Toyota|Ford|Opel|Renault|Peugeot|Citroën)[^"]*)"', matches[0])
                                if brand_names:
                                    print(f"Marcas encontradas: {brand_names[:10]}")
                                    return {"method": "javascript", "brands": brand_names}
                            except:
                                pass
            except:
                continue
    
    except Exception as e:
        print(f"❌ Erro no método alternativo: {e}")
    
    return None


def main():
    """Função principal"""
    print("🚀 Iniciando extração de marcas e modelos do StandVirtual...")
    print("="*60)
    
    result = extract_brands_and_models()
    
    if result:
        print(f"\n✅ Extração concluída!")
        print(f"📊 Marcas processadas: {len(result)}")
        
        # Salva os dados em JSON
        filename = "standvirtual_brands_models.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Dados salvos em: {filename}")
        
        # Mostra resumo
        print(f"\n📋 Resumo:")
        for brand, data in list(result.items())[:10]:  # Primeiras 10
            model_count = len(data.get('models', []))
            print(f"  {brand}: {model_count} modelos")
        
        if len(result) > 10:
            print(f"  ... e mais {len(result) - 10} marcas")
    else:
        print("\n❌ Falha na extração")
        print("💡 Possíveis soluções:")
        print("  1. Site pode usar dropdowns dinâmicos/customizados")
        print("  2. Pode ser necessário aguardar mais tempo para carregar")
        print("  3. Seletores podem ter mudado")


if __name__ == "__main__":
    main() 