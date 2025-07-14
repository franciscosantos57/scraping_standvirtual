#!/usr/bin/env python3
"""
Solução simples: corrige o database atual usando dados dos anúncios reais
"""

import json
import re
import requests
from typing import Dict, List, Set
from collections import defaultdict
import time
from datetime import datetime

def load_current_database() -> Dict:
    """Carrega o database atual"""
    with open('../data/json/standvirtual_master_database.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_incomplete_brands(database: Dict) -> List[str]:
    """Identifica marcas que só têm 'outros modelos'"""
    incomplete = []
    
    for brand_name, brand_info in database.get('brands', {}).items():
        models = brand_info.get('models', [])
        if (len(models) == 1 and 
            any(model.get('text') == 'Outros modelos' for model in models)):
            incomplete.append(brand_name)
    
    return incomplete

def extract_models_from_real_ads(brand: str, max_pages: int = 10) -> Set[str]:
    """
    Extrai modelos reais de uma marca analisando anúncios
    """
    models = set()
    
    # Converte marca para formato URL
    brand_slug = brand.lower().replace(' ', '-').replace('ë', 'e')
    brand_slug = brand_slug.replace('ç', 'c').replace('ã', 'a')
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    print(f"   🔍 Analisando anúncios de {brand}...")
    
    for page in range(1, max_pages + 1):
        try:
            # URL de pesquisa por marca
            url = f"https://www.standvirtual.com/carros?search%5Bfilter_enum_make%5D={brand_slug}&page={page}"
            
            response = session.get(url, timeout=10)
            if response.status_code != 200:
                continue
            
            html = response.text
            
            # Extrai títulos dos anúncios (método mais confiável)
            brand_escaped = re.escape(brand)
            title_patterns = [
                brand_escaped + r'\s+([A-Za-z0-9\-\s]+?)(?:\s+\d|\s+[0-9.,]+\s*[€$]|\s+ver\s|\s+\(|\s*$)',
                r'"title":"[^"]*' + brand_escaped + r'\s+([^"]+?)\s+[0-9]',
                r'"displayValue":"' + brand_escaped + r'[^"]*","label":"make"[^}]*"displayValue":"([^"]+)","label":"model"'
            ]
            
            page_models = set()
            
            for pattern in title_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    
                    model = clean_model_name(match, brand)
                    if model and is_valid_model(model):
                        page_models.add(model)
            
            models.update(page_models)
            
            if page_models:
                print(f"      📄 Página {page}: {len(page_models)} modelos")
            
            # Para se não há mais anúncios
            if len(page_models) == 0 and page > 3:
                break
                
            time.sleep(0.5)  # Delay menor
            
        except Exception as e:
            print(f"      ⚠️ Erro na página {page}: {e}")
            continue
    
    return models

def clean_model_name(model: str, brand: str) -> str:
    """Limpa e formata nome do modelo"""
    if not model:
        return ""
    
    model = model.strip()
    
    # Remove a marca do início se estiver presente
    brand_escaped = re.escape(brand)
    model = re.sub(brand_escaped + r'\s+', '', model, flags=re.IGNORECASE)
    
    # Remove prefixos comuns
    model = re.sub(r'^(ver\s+|modelo\s+|new\s+)', '', model, flags=re.IGNORECASE)
    
    # Remove sufixos comuns
    model = re.sub(r'\s+(usado|novo|seminovo|impecavel|garantia).*$', '', model, flags=re.IGNORECASE)
    
    # Remove anos e preços
    model = re.sub(r'\s+\d{4}.*$', '', model)
    model = re.sub(r'\s+[0-9.,]+\s*(€|euros?).*$', '', model, flags=re.IGNORECASE)
    
    # Limpa caracteres especiais
    model = re.sub(r'[^\w\s\-]', '', model)
    model = re.sub(r'\s+', ' ', model).strip()
    
    # Capitaliza corretamente
    words = []
    for word in model.split():
        if word.upper() in ['BMW', 'AMG', 'GTI', 'TDI', 'TSI', 'FSI', 'SUV']:
            words.append(word.upper())
        elif len(word) <= 3 and word.isalnum():
            words.append(word.upper())
        else:
            words.append(word.capitalize())
    
    return ' '.join(words)

def is_valid_model(model: str) -> bool:
    """Valida se é um modelo válido"""
    if not model or len(model) < 1:
        return False
    
    # Rejeita palavras inválidas
    invalid_words = [
        'outros', 'modelos', 'carros', 'veiculos', 'automoveis', 'usado', 'novo',
        'seminovo', 'impecavel', 'garantia', 'vendido', 'reservado', 'stand',
        'standvirtual', 'anuncio', 'venda', 'comprar', 'financiamento', 'crédito'
    ]
    
    model_lower = model.lower()
    for invalid in invalid_words:
        if invalid in model_lower:
            return False
    
    # Deve ter pelo menos uma letra
    if not re.search(r'[a-zA-Z]', model):
        return False
    
    # Não deve ser só números
    if model.replace(' ', '').replace('-', '').isdigit():
        return False
    
    return True

def fix_incomplete_brands(database: Dict) -> Dict:
    """Corrige marcas incompletas"""
    
    incomplete_brands = get_incomplete_brands(database)
    print(f"🔧 Corrigindo {len(incomplete_brands)} marcas incompletas...")
    
    for i, brand in enumerate(incomplete_brands, 1):
        print(f"\n[{i}/{len(incomplete_brands)}] 🚗 {brand}")
        
        # Extrai modelos reais
        models = extract_models_from_real_ads(brand, max_pages=5)
        
        if models:
            # Remove "Outros modelos"
            models.discard("Outros modelos")
            
            # Cria lista de modelos formatada
            models_list = []
            for model in sorted(models):
                models_list.append({
                    'text': model,
                    'value': model.lower().replace(' ', '-')
                })
            
            # Atualiza no database
            database['brands'][brand]['models'] = models_list
            database['brands'][brand]['total_models'] = len(models_list)
            
            print(f"   ✅ {len(models)} modelos encontrados: {', '.join(sorted(models)[:5])}{'...' if len(models) > 5 else ''}")
        else:
            print(f"   ❌ Nenhum modelo específico encontrado, mantendo 'Outros modelos'")
    
    return database

def update_metadata(database: Dict) -> Dict:
    """Atualiza metadados do database"""
    
    total_brands = len(database.get('brands', {}))
    total_models = sum(brand.get('total_models', 0) for brand in database.get('brands', {}).values())
    
    incomplete_count = len([
        brand for brand, info in database.get('brands', {}).items()
        if (info.get('total_models', 0) == 1 and 
            any(model.get('text') == 'Outros modelos' for model in info.get('models', [])))
    ])
    
    completion_rate = ((total_brands - incomplete_count) / total_brands) * 100 if total_brands > 0 else 0
    
    database['metadata'].update({
        'last_update': datetime.now().isoformat(),
        'version': '3.0',
        'total_brands': total_brands,
        'total_models': total_models,
        'incomplete_brands': incomplete_count,
        'completion_rate': round(completion_rate, 1),
        'correction_method': 'real_ads_analysis'
    })
    
    return database

def save_database(database: Dict, filename: str = None) -> str:
    """Salva database atualizado"""
    if not filename:
        filename = '../data/json/standvirtual_master_database.json'
    
    # Backup do original
    backup_filename = filename.replace('.json', '_backup.json')
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    # Salva versão atualizada
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    return filename

def main():
    """Função principal"""
    print("🚀 CORREÇÃO SIMPLES DO DATABASE STANDVIRTUAL")
    print("=" * 60)
    
    # Carrega database atual
    print("📂 Carregando database atual...")
    database = load_current_database()
    
    # Estatísticas iniciais
    incomplete_brands = get_incomplete_brands(database)
    total_brands = len(database.get('brands', {}))
    
    print(f"📊 Estatísticas atuais:")
    print(f"   Total de marcas: {total_brands}")
    print(f"   Marcas incompletas: {len(incomplete_brands)}")
    print(f"   Taxa de completude: {((total_brands - len(incomplete_brands)) / total_brands * 100):.1f}%")
    
    # Mostra algumas marcas incompletas
    print(f"\n🔍 Marcas a corrigir:")
    for brand in incomplete_brands[:10]:
        print(f"   • {brand}")
    if len(incomplete_brands) > 10:
        print(f"   ... e mais {len(incomplete_brands) - 10}")
    
    # Confirma execução
    print(f"\n⚠️  Este processo irá analisar anúncios reais para extrair modelos específicos.")
    print(f"   Tempo estimado: {len(incomplete_brands) * 2} minutos")
    
    # Executa correção
    print(f"\n🔧 Iniciando correção...")
    corrected_database = fix_incomplete_brands(database)
    
    # Atualiza metadados
    corrected_database = update_metadata(corrected_database)
    
    # Salva resultado
    filename = save_database(corrected_database)
    
    # Estatísticas finais
    new_incomplete = get_incomplete_brands(corrected_database)
    metadata = corrected_database.get('metadata', {})
    
    print(f"\n✅ CORREÇÃO CONCLUÍDA!")
    print(f"📊 Resultados:")
    print(f"   Total de marcas: {metadata.get('total_brands', 0)}")
    print(f"   Total de modelos: {metadata.get('total_models', 0)}")
    print(f"   Marcas incompletas: {len(new_incomplete)} (era {len(incomplete_brands)})")
    print(f"   Taxa de completude: {metadata.get('completion_rate', 0):.1f}%")
    print(f"   Melhoria: +{len(incomplete_brands) - len(new_incomplete)} marcas corrigidas")
    print(f"💾 Database atualizado: {filename}")

if __name__ == "__main__":
    main() 