#!/usr/bin/env python3
"""
Script para debug de extração de dados técnicos específicos
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def debug_technical_data():
    """Debug específico para dados técnicos"""
    
    # URL específica do exemplo (BMW X5 híbrido)
    test_url = "https://www.standvirtual.com/carros/anuncio/bmw-x5-ver-45-e-xdrive-xline-ID8PNQmI.html"
    
    print(f"🔍 Investigando dados técnicos: {test_url}")
    print("="*80)
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(test_url)
        
        # Aguarda carregamento
        time.sleep(5)
        
        print(f"📄 Título da página: {driver.title}")
        print()
        
        # 1. Testa seletores específicos que encontrei no HTML
        print("🔧 TESTE 1: Seletores data-testid específicos")
        print("-" * 50)
        
        test_selectors = [
            ('engine_capacity', 'Cilindrada'),
            ('engine_power', 'Potência'), 
            ('body_type', 'Segmento'),
            ('fuel_type', 'Combustível'),
            ('gearbox', 'Caixa')
        ]
        
        for testid, nome in test_selectors:
            try:
                # Tenta o seletor completo
                element = driver.find_element(By.CSS_SELECTOR, f'[data-testid="{testid}"] p:last-child')
                valor = element.text.strip()
                print(f"   ✅ {nome} ({testid}): {valor}")
            except Exception as e:
                print(f"   ❌ {nome} ({testid}): Não encontrado - {e}")
        
        # 2. Procura por qualquer elemento que tenha data-testid
        print(f"\n🔍 TESTE 2: Todos os data-testid encontrados")
        print("-" * 50)
        
        try:
            all_testid_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid]')
            testids = set()
            
            for elem in all_testid_elements:
                testid = elem.get_attribute('data-testid')
                if testid and 'engine' in testid.lower() or 'power' in testid.lower() or 'capacity' in testid.lower():
                    testids.add(testid)
                    try:
                        text = elem.text.strip()
                        if text and len(text) < 100:  # Evita textos muito longos
                            print(f"   🎯 {testid}: {text}")
                    except:
                        pass
            
            print(f"   📊 Total de data-testid encontrados: {len(all_testid_elements)}")
            print(f"   🎯 Data-testid relevantes: {len(testids)}")
            
        except Exception as e:
            print(f"   ❌ Erro ao buscar data-testid: {e}")
        
        # 3. Procura por texto que contenha as palavras-chave
        print(f"\n📝 TESTE 3: Busca por texto com palavras-chave")
        print("-" * 50)
        
        keywords = ['cm3', 'cm³', 'cv', 'Cilindrada', 'Potência', 'SUV', 'Sedan']
        
        for keyword in keywords:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                print(f"   🔎 '{keyword}': {len(elements)} elementos encontrados")
                
                for i, elem in enumerate(elements[:3]):  # Primeiros 3
                    try:
                        text = elem.text.strip()
                        if text and len(text) < 50:
                            print(f"      {i+1}. {text}")
                    except:
                        pass
                        
            except Exception as e:
                print(f"   ❌ Erro buscando '{keyword}': {e}")
        
        # 4. Inspeciona a estrutura ao redor de "Especificações técnicas"
        print(f"\n🔧 TESTE 4: Estrutura de especificações técnicas")
        print("-" * 50)
        
        try:
            # Procura elemento que contenha "Especificações técnicas"
            spec_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Especificações técnicas')]")
            
            for i, spec_elem in enumerate(spec_elements):
                print(f"   📋 Especificação {i+1}:")
                try:
                    # Pega o elemento pai
                    parent = spec_elem.find_element(By.XPATH, "./..")
                    # Pega elementos filhos/irmãos que podem conter dados
                    siblings = parent.find_elements(By.XPATH, ".//*")
                    
                    for sibling in siblings[:20]:  # Primeiros 20
                        text = sibling.text.strip()
                        if text and any(word in text for word in ['cm3', 'cm³', 'cv', 'SUV', 'Sedan']):
                            print(f"      📊 {text}")
                            
                except Exception as e:
                    print(f"      ❌ Erro: {e}")
        
        except Exception as e:
            print(f"   ❌ Erro ao buscar especificações: {e}")
        
        # 5. Testa seletores alternativos baseados na estrutura do HTML
        print(f"\n🎯 TESTE 5: Seletores alternativos")
        print("-" * 50)
        
        alternative_selectors = [
            ('.eur4qwl9', 'Classe eur4qwl9'),
            ('[class*="eur4qwl"]', 'Classes que contêm eur4qwl'),
            ('.ez0zock2', 'Classe ez0zock2'),
            ('[aria-label*="Cilindrada"]', 'Aria-label Cilindrada'),
            ('[aria-label*="Potência"]', 'Aria-label Potência'),
        ]
        
        for selector, desc in alternative_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"   🔍 {desc}: {len(elements)} elementos")
                
                for i, elem in enumerate(elements[:5]):
                    try:
                        text = elem.text.strip()
                        if text and len(text) < 30 and any(char.isdigit() for char in text):
                            print(f"      {i+1}. {text}")
                    except:
                        pass
                        
            except Exception as e:
                print(f"   ❌ {desc}: {e}")
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
    
    print("\n" + "="*80)
    print("🎯 CONCLUSÃO: Use os seletores que funcionaram para corrigir o código!")


if __name__ == "__main__":
    debug_technical_data() 