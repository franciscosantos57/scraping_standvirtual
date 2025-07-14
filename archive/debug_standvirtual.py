#!/usr/bin/env python3
"""
Script de debug para investigar a estrutura HTML do StandVirtual.com
"""

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re


def debug_standvirtual():
    """Investiga a estrutura HTML do StandVirtual"""
    
    # Headers para simular um browser real
    ua = UserAgent()
    headers = {
        'User-Agent': ua.chrome,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # URL para testar
    url = 'https://www.standvirtual.com/carros'
    
    print(f"🔍 Investigando: {url}")
    print('='*60)
    
    try:
        # Fazer requisição
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📦 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"📏 Content Length: {len(response.content)} bytes")
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Salvar HTML para análise
        with open('standvirtual_debug.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        print(f"💾 HTML salvo em: standvirtual_debug.html")
        
        # Verificar se há elementos que parecem ser anúncios de carros
        print(f"\n🔍 Procurando por elementos de anúncios...")
        
        # Possíveis seletores para anúncios
        selectors_to_test = [
            '[data-testid="listing-ad"]',
            '.listing-item',
            '.ad-item', 
            '.offer-item',
            'article',
            '[data-testid*="ad"]',
            '[data-testid*="listing"]',
            '.offer',
            '.advert'
        ]
        
        found_elements = []
        
        for selector in selectors_to_test:
            elements = soup.select(selector)
            if elements:
                found_elements.append((selector, len(elements)))
                print(f"✅ {selector}: {len(elements)} elementos encontrados")
        
        if not found_elements:
            print("❌ Nenhum elemento de anúncio encontrado com os seletores testados")
            
            # Vamos ver as primeiras divs
            print(f"\n📝 Primeiros 20 elementos div encontrados:")
            divs = soup.find_all('div', limit=20)
            for i, div in enumerate(divs):
                classes = div.get('class', [])
                id_attr = div.get('id', '')
                print(f"  {i+1}. classes: {classes[:3]} - id: {id_attr}")
        
        # Verificar se há conteúdo JavaScript
        scripts = soup.find_all('script')
        print(f"\n📜 Scripts encontrados: {len(scripts)}")
        
        # Procurar por indicadores de SPA/JS
        js_content = ' '.join([script.get_text() for script in scripts])
        if 'React' in js_content or 'Vue' in js_content or 'Angular' in js_content:
            print("⚠️  Página parece usar framework JS - Selenium pode ser necessário")
            
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    debug_standvirtual() 