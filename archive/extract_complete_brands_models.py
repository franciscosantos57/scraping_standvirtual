#!/usr/bin/env python3
"""
Script completo para extrair todas as marcas e seus modelos do StandVirtual.com
"""

import time
import json
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
from urllib.parse import quote


def setup_session():
    """Configura sessão HTTP"""
    session = requests.Session()
    ua = UserAgent()
    session.headers.update({
        'User-Agent': ua.chrome,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session


def get_all_brands():
    """Obtém lista de marcas conhecidas (base para extrair modelos)"""
    return [
        'Audi', 'BMW', 'Mercedes-Benz', 'Volkswagen', 'Toyota', 'Ford',
        'Opel', 'Renault', 'Peugeot', 'Citroën', 'Nissan', 'Honda',
        'Hyundai', 'Kia', 'Mazda', 'Subaru', 'Volvo', 'Jaguar',
        'Land Rover', 'Porsche', 'Ferrari', 'Lamborghini', 'Bentley',
        'Rolls-Royce', 'Maserati', 'Alfa Romeo', 'Fiat', 'SEAT',
        'Skoda', 'Mini', 'Smart', 'Dacia', 'Lada', 'Mitsubishi',
        'Suzuki', 'Lexus', 'Infiniti', 'Acura', 'Cadillac', 'Chevrolet',
        'Dodge', 'Jeep', 'Lincoln', 'Tesla', 'Genesis', 'DS'
    ]


def extract_models_for_brand(session, brand):
    """
    Extrai modelos para uma marca específica
    """
    print(f"🔍 Extraindo modelos para {brand}...")
    
    try:
        # URL para pesquisar carros da marca
        brand_encoded = quote(brand.lower())
        url = f"https://www.standvirtual.com/carros/{brand_encoded}"
        
        response = session.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"   ❌ Erro HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Método 1: Procura por links de modelos na página
        models = set()
        
        # Padrões de URLs que contêm modelos
        model_links = soup.find_all('a', href=re.compile(f'/carros/{brand_encoded}/[^/]+/?$'))
        
        for link in model_links:
            href = link.get('href', '')
            # Extrai o nome do modelo da URL
            match = re.search(f'/carros/{brand_encoded}/([^/?]+)', href)
            if match:
                model_name = match.group(1).replace('-', ' ').title()
                if len(model_name) > 1 and model_name not in ['Desde', 'Ate', 'Novo', 'Usado']:
                    models.add(model_name)
        
        # Método 2: Procura por texto que menciona modelos
        page_text = soup.get_text()
        
        # Padrões comuns de modelos por marca
        brand_model_patterns = {
            'BMW': [r'Serie?\s*(\d+)', r'X(\d+)', r'Z(\d+)', r'i(\d+)', r'M(\d+)'],
            'Mercedes-Benz': [r'Classe?\s*([A-Z])', r'CL[A-Z]', r'GL[A-Z]', r'ML[A-Z]', r'SL[A-Z]'],
            'Audi': [r'A(\d+)', r'Q(\d+)', r'TT', r'R8', r'RS(\d+)', r'S(\d+)'],
            'Volkswagen': [r'Golf', r'Passat', r'Polo', r'Tiguan', r'Touran', r'Sharan'],
            'Toyota': [r'Corolla', r'Camry', r'Prius', r'RAV4', r'Yaris', r'Avensis'],
            'Ford': [r'Focus', r'Fiesta', r'Mondeo', r'Kuga', r'Galaxy', r'S-Max'],
        }
        
        if brand in brand_model_patterns:
            for pattern in brand_model_patterns[brand]:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, str):
                        model_name = match.strip()
                    else:
                        model_name = f"{pattern.split('(')[0]}{match}"
                    
                    if len(model_name) > 1:
                        models.add(model_name)
        
        # Método 3: Procura por elementos que podem conter nomes de modelos
        model_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'a'], 
                                     string=re.compile(f'{brand}', re.IGNORECASE))
        
        for element in model_elements:
            text = element.get_text().strip()
            # Remove a marca do texto para ficar só com o modelo
            model_text = re.sub(f'{brand}\\s*', '', text, flags=re.IGNORECASE).strip()
            
            if len(model_text) > 1 and len(model_text) < 50:
                # Remove caracteres especiais e números desnecessários
                clean_model = re.sub(r'[^\w\s-]', '', model_text).strip()
                if clean_model and not clean_model.isdigit():
                    models.add(clean_model)
        
        # Converte para lista e limpa
        models_list = []
        for model in models:
            clean_model = model.strip().title()
            if (len(clean_model) > 1 and 
                not clean_model.isdigit() and 
                clean_model not in ['Carros', 'Venda', 'Usado', 'Novo', 'Portugal']):
                models_list.append(clean_model)
        
        models_list = sorted(list(set(models_list)))
        print(f"   ✅ {len(models_list)} modelos encontrados: {models_list[:5]}...")
        
        return models_list
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return []


def extract_models_from_search_api(session, brand):
    """
    Tenta extrair modelos usando a API de pesquisa do StandVirtual
    """
    try:
        # Faz uma pesquisa pela marca para ver se retorna dados estruturados
        search_url = "https://www.standvirtual.com/carros"
        params = {
            'search[filter_enum_make]': brand.lower()
        }
        
        response = session.get(search_url, params=params, timeout=10)
        
        if response.status_code == 200:
            # Procura por dados JSON na resposta
            json_pattern = r'<script[^>]*data-testid="listing-json-ld"[^>]*>(.*?)</script>'
            match = re.search(json_pattern, response.text, re.DOTALL)
            
            if match:
                try:
                    json_data = json.loads(match.group(1))
                    
                    if 'mainEntity' in json_data and 'itemListElement' in json_data['mainEntity']:
                        models = set()
                        items = json_data['mainEntity']['itemListElement']
                        
                        for item in items:
                            car_info = item.get('itemOffered', {})
                            car_name = car_info.get('name', '')
                            
                            if car_name and brand.lower() in car_name.lower():
                                # Extrai o modelo do nome do carro
                                # Ex: "BMW Serie 3" -> "Serie 3"
                                model_match = re.search(f'{brand}\\s+(.+?)(?:\\s+\\d|$)', car_name, re.IGNORECASE)
                                if model_match:
                                    model = model_match.group(1).strip()
                                    if len(model) > 1:
                                        models.add(model)
                        
                        return list(models)
                        
                except json.JSONDecodeError:
                    pass
        
        return []
        
    except Exception as e:
        print(f"   ⚠️ Erro na API: {e}")
        return []


def main():
    """Função principal"""
    print("🚀 Iniciando extração completa de marcas e modelos...")
    print("="*60)
    
    session = setup_session()
    brands = get_all_brands()
    
    print(f"📋 Processando {len(brands)} marcas...")
    
    brands_models = {}
    
    for i, brand in enumerate(brands, 1):
        print(f"\n[{i}/{len(brands)}] Processando {brand}...")
        
        # Método 1: Extração da página da marca
        models = extract_models_for_brand(session, brand)
        
        # Método 2: Se não encontrou modelos, tenta API de pesquisa
        if not models:
            print(f"   🔄 Tentando método alternativo...")
            models = extract_models_from_search_api(session, brand)
        
        # Se ainda não encontrou, usa modelos conhecidos básicos
        if not models:
            print(f"   ⚠️ Usando modelos genéricos...")
            models = ['Outros']  # Placeholder
        
        brands_models[brand] = {
            'brand_value': brand.lower().replace(' ', '-').replace('/', '-'),
            'models': [{'value': model.lower().replace(' ', '-'), 'text': model} for model in models]
        }
        
        # Delay para não sobrecarregar o servidor
        time.sleep(1)
        
        # Para teste, limita a primeiras 10 marcas
        if i >= 10:
            print(f"\n🔄 Limitando a {i} marcas para teste...")
            break
    
    # Salva os dados
    filename = "standvirtual_complete_brands_models.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(brands_models, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Extração concluída!")
    print(f"💾 Dados salvos em: {filename}")
    
    # Mostra resumo
    print(f"\n📊 Resumo:")
    total_models = 0
    for brand, data in brands_models.items():
        model_count = len(data['models'])
        total_models += model_count
        print(f"  {brand}: {model_count} modelos")
    
    print(f"\n📈 Total: {len(brands_models)} marcas, {total_models} modelos")
    
    # Mostra exemplo de estrutura
    print(f"\n📋 Exemplo de estrutura:")
    example_brand = list(brands_models.keys())[0]
    example_data = brands_models[example_brand]
    print(json.dumps({example_brand: example_data}, indent=2, ensure_ascii=False)[:300] + "...")


if __name__ == "__main__":
    main() 