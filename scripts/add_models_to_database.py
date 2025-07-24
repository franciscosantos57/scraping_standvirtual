#!/usr/bin/env python3
"""
Modo batch automático para adicionar modelos a todas as marcas, aceitando o formato 'Nome (número)'.
"""
import json
import os
import re

def load_database():
    """Carrega a base de dados"""
    db_file = "data/json/new_master_database.json"
    if os.path.exists(db_file):
        with open(db_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"❌ Arquivo {db_file} não encontrado!")
        return None

def save_database(data):
    """Salva a base de dados"""
    db_file = "data/json/new_master_database.json"
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Base de dados salva em {db_file}")

def generate_model_value(model_name):
    """
    Gera o value para um modelo baseado no seu nome
    Converte para lowercase, remove espaços e caracteres especiais
    """
    value = re.sub(r'[^\w\s]', '', model_name.lower())
    value = re.sub(r'\s+', '-', value)
    value = re.sub(r'-+', '-', value)
    value = value.strip('-')
    return value

def add_models_to_brand(data, brand_name, models_text):
    models_list = []
    lines = models_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and '(' in line and ')' in line:
            text = line.split('(')[0].strip()
            value = generate_model_value(text)
            models_list.append({"text": text, "value": value})
    data['brands'][brand_name]['models'] = models_list
    data['brands'][brand_name]['model_count'] = len(models_list)
    total_models = sum(len(brand['models']) for brand in data['brands'].values())
    data['metadata']['total_models'] = total_models
    data['metadata']['completion_rate'] = round((total_models / (len(data['brands']) * 10)) * 100, 1)
    print(f"✅ {brand_name}: {len(models_list)} modelos adicionados.")
    save_database(data)

def show_status(data):
    """Mostra o status atual da base de dados"""
    print("\n📊 STATUS ATUAL DA BASE DE DADOS:")
    print("=" * 60)
    brands_with_models = 0
    total_models = 0
    for brand_name, brand_data in data['brands'].items():
        model_count = len(brand_data['models'])
        total_models += model_count
        if model_count > 0:
            brands_with_models += 1
            status = f"✅ {model_count} modelos"
        else:
            status = "❌ Sem modelos"
        print(f"{brand_name:<25} {status}")
    print("=" * 60)
    print(f"📈 Marcas com modelos: {brands_with_models}/{len(data['brands'])}")
    print(f"📈 Total de modelos: {total_models}")
    print(f"📈 Taxa de completude: {data['metadata']['completion_rate']}%")

def main():
    print("🚀 MODO BATCH AUTOMÁTICO PARA ADICIONAR MODELOS")
    print("Cole os modelos no formato: Nome (número)")
    print("Digite 'fim' para terminar cada marca, ou 'sair' para parar.")
    print("Exemplo:")
    print("100/4 (0)\n3000 (0)\nSprite (0)\nSprite Mk I (1)\nSprite Mk II (0)\nSprite Mk III (0)\nSprite Mk IV (0)")
    print("-")
    data = load_database()
    if not data:
        return
    brands = list(data['brands'].keys())
    # Escolher marca inicial
    print("\nMarcas disponíveis:")
    for i, brand in enumerate(brands, 1):
        print(f"{i:2d}. {brand}")
    while True:
        try:
            start_idx = int(input("\nDigite o número da marca para começar: ")) - 1
            if 0 <= start_idx < len(brands):
                break
            else:
                print("❌ Número inválido!")
        except ValueError:
            print("❌ Entrada inválida!")
    # Loop automático pelas marcas
    for idx in range(start_idx, len(brands)):
        brand_name = brands[idx]
        print(f"\n🔧 {idx+1}/{len(brands)} - Adicione modelos para: {brand_name}")
        print("Cole os modelos (um por linha). Digite 'fim' para avançar, 'sair' para terminar.")
        models_lines = []
        while True:
            line = input()
            if line.strip().lower() == 'fim':
                break
            if line.strip().lower() == 'sair':
                print("👋 Saindo...")
                show_status(data)
                return
            models_lines.append(line)
        models_text = '\n'.join(models_lines)
        add_models_to_brand(data, brand_name, models_text)
    print("\n✅ Todas as marcas processadas!")
    show_status(data)

if __name__ == "__main__":
    main() 