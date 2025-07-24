#!/usr/bin/env python3
"""
Script para mapear dados do mobile.de para o StandVirtual

Faz o mapeamento marca por marca, adicionando campo text_md 
quando há correspondências entre os modelos/submodelos.
Usa AI (OpenAI) para mapeamento inteligente e save/resume de progresso.
"""

import json
import re
import os
from pathlib import Path
from difflib import SequenceMatcher
from dotenv import load_dotenv
import openai
from datetime import datetime


# Configurações globais
load_dotenv('config_mapping.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AI_MAPPING_ENABLED = os.getenv('AI_MAPPING_ENABLED', 'true').lower() == 'true'
AI_SIMILARITY_THRESHOLD = float(os.getenv('AI_SIMILARITY_THRESHOLD', '0.7'))
PROGRESS_SAVE_FILE = os.getenv('PROGRESS_SAVE_FILE', 'data/mapping_progress.json')

# Configurar OpenAI
if OPENAI_API_KEY and OPENAI_API_KEY != 'your_openai_api_key_here':
    openai.api_key = OPENAI_API_KEY
    AI_AVAILABLE = True
else:
    AI_AVAILABLE = False
    print("⚠️ OpenAI API key não configurada. Mapeamento AI desabilitado.")


def similarity(a, b):
    """Calcula similaridade entre duas strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def save_progress(standvirtual_data, processed_brands, current_brand_index, exit_brand=None):
    """Salva o progresso atual"""
    progress_data = {
        'timestamp': datetime.now().isoformat(),
        'processed_brands': processed_brands,
        'current_brand_index': current_brand_index,
        'exit_brand': exit_brand,  # Marca onde o usuário saiu
        'total_brands': len(standvirtual_data['brands'])
    }
    
    os.makedirs(os.path.dirname(PROGRESS_SAVE_FILE), exist_ok=True)
    with open(PROGRESS_SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)


def remove_all_mappings(standvirtual_data):
    """Remove todos os mapeamentos text_md da base de dados"""
    removed_count = 0
    
    for brand_data in standvirtual_data['brands'].values():
        for model in brand_data['models']:
            if 'text_md' in model:
                del model['text_md']
                removed_count += 1
            
            if 'submodels' in model:
                for submodel in model['submodels']:
                    if 'text_md' in submodel:
                        del submodel['text_md']
                        removed_count += 1
    
    return removed_count


def select_starting_brand(brands_list):
    """Permite ao usuário selecionar a marca de início"""
    print("\n📋 SELEÇÃO DE MARCA DE INÍCIO")
    print("="*50)
    print("Opções:")
    print("1. Começar do início")
    print("2. Escolher marca específica")
    print("3. Continuar de onde parei (se houver progresso)")
    print("4. Remover todos os mapeamentos existentes")
    
    while True:
        choice = input("\nEscolha uma opção (1-4): ").strip()
        
        if choice == "1":
            return 0, False  # Começar do início
            
        elif choice == "2":
            print(f"\n📝 Digite o nome da marca (total: {len(brands_list)} marcas)")
            print("Primeiras 10 marcas:", [brands_list[i][0] for i in range(min(10, len(brands_list)))])
            
            while True:
                brand_name = input("\nNome da marca: ").strip()
                for i, (name, _) in enumerate(brands_list):
                    if name.lower() == brand_name.lower():
                        print(f"✓ Encontrada: {name} (posição {i+1})")
                        return i, False
                print(f"❌ Marca '{brand_name}' não encontrada. Tente novamente.")
                
        elif choice == "3":
            return None, True  # Indicar para usar progresso existente
            
        elif choice == "4":
            return None, "remove_mappings"
            
        else:
            print("❌ Opção inválida. Escolha 1, 2, 3 ou 4.")


def load_progress():
    """Carrega o progresso salvo"""
    if os.path.exists(PROGRESS_SAVE_FILE):
        with open(PROGRESS_SAVE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def ai_mapping_suggestion(mobile_de_model, standvirtual_models, brand_name):
    """
    Usa OpenAI para sugerir mapeamento entre modelos, considerando diferenças regionais
    """
    if not AI_AVAILABLE or not AI_MAPPING_ENABLED:
        return None, 0
    
    try:
        # Preparar dados para a AI
        sv_models_text = []
        for model in standvirtual_models:
            model_info = f"Modelo: {model['text']}"
            if 'submodels' in model:
                submodels = [sm['text'] for sm in model['submodels']]
                model_info += f" (Submodelos: {', '.join(submodels)})"
            sv_models_text.append(model_info)
        
        prompt = f"""
Você é um especialista em mapeamento de dados de carros entre mercados alemão (mobile.de) e português (StandVirtual).

CONTEXTO CRÍTICO:
- Mobile.de (Alemanha): Nomenclaturas alemãs/europeias
- StandVirtual (Portugal): Nomenclaturas portuguesas/locais
- IMPORTANTE: Considere variações mínimas como IGUAIS

VARIAÇÕES CONSIDERADAS IGUAIS:
- Acentos: "Coupé" = "Coupe" 
- Sufixos: "Scouty" = "Scouty R" (R é apenas versão específica)
- Hífens/Espaços: "A-Class" = "A Class" = "AClass"
- Maiúsculas: "GTI" = "gti"

Marca: {brand_name}
Modelo Mobile.de (Alemanha): "{mobile_de_model}"

Modelos disponíveis no StandVirtual (Portugal):
{chr(10).join(sv_models_text)}

TAREFA:
Determine se o modelo alemão "{mobile_de_model}" corresponde a algum modelo/submodelo português.
SEJA TOLERANTE com pequenas diferenças!

REGRAS DE RESPOSTA:
1. SUBMODELO: "SUBMODEL:modelo_principal:submodelo"
2. MODELO: "MODEL:nome_do_modelo"  
3. SEM CORRESPONDÊNCIA: "NO_MATCH"

EXEMPLOS IMPORTANTES:
- "Coupe" (alemão) → "Coupé" (português) → "MODEL:Coupé"
- "Scouty" (alemão) → "Scouty R" (português) → "MODEL:Scouty R"
- "120" (alemão) → "Série 1" submodelo "120d" → "SUBMODEL:Série 1:120d"
- "Serie 1" (alemão) → "Série 1" (português) → "MODEL:Série 1"

Resposta (apenas o resultado):"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        if result.startswith("SUBMODEL:"):
            parts = result.split(":")
            if len(parts) == 3:
                return {"type": "submodel", "model": parts[1], "submodel": parts[2]}, 0.9
        elif result.startswith("MODEL:"):
            model_name = result.split(":", 1)[1]
            return {"type": "model", "model": model_name}, 0.9
        
        return None, 0
        
    except Exception as e:
        print(f"   ⚠️ Erro na AI: {e}")
        return None, 0


def normalize_text(text):
    """Normaliza texto para comparação (mais agressivo para similaridade)"""
    import unicodedata
    
    # Converter para lowercase
    text = text.lower()
    
    # Remover acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Remover caracteres especiais e espaços extras
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def advanced_similarity(a, b):
    """Calcula similaridade avançada considerando variações comuns"""
    # Normalizar ambos os textos
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)
    
    # Similaridade básica
    basic_sim = similarity(a_norm, b_norm)
    
    # Verificar se um é substring do outro (para casos como "Scouty" vs "Scouty R")
    if a_norm in b_norm or b_norm in a_norm:
        substring_bonus = 0.2
    else:
        substring_bonus = 0
    
    # Verificar diferenças apenas em acentos (como "Coupé" vs "Coupe")
    if a_norm == b_norm:
        accent_bonus = 0.3
    else:
        accent_bonus = 0
    
    # Verificar match exato (prioridade máxima)
    if a == b:
        exact_bonus = 0.5
    else:
        exact_bonus = 0
    
    # Combinar todas as similaridades
    final_score = min(1.0, basic_sim + substring_bonus + accent_bonus + exact_bonus)
    
    return final_score


def get_mapping_score(text_md, text_sv):
    """
    Calcula um score de qualidade para um mapeamento existente
    Retorna: (score, tipo)
    """
    if text_md == text_sv:
        return 1.5, "exato"  # Prioridade máxima para matches exatos
        
    sim_score = advanced_similarity(text_md, text_sv)
    if sim_score >= 0.7:
        return sim_score, "similaridade"
        
    return 0.5, "ai"  # Score base para mapeamentos da AI


def find_best_match(target_text, candidates, threshold=0.7):
    """Encontra a melhor correspondência para um texto entre candidatos usando similaridade avançada"""
    best_match = None
    best_score = 0
    
    for candidate in candidates:
        score = advanced_similarity(target_text, candidate)
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate
    
    return best_match, best_score


def load_databases():
    """Carrega as duas bases de dados"""
    sv_path = "data/json/standvirtual_database.json"
    md_path = "data/json/mobile_de_database.json"
    
    with open(sv_path, 'r', encoding='utf-8') as f:
        standvirtual_data = json.load(f)
    
    with open(md_path, 'r', encoding='utf-8') as f:
        mobile_de_data = json.load(f)
    
    return standvirtual_data, mobile_de_data


def map_brand_models(sv_brand_data, md_brand_data, brand_name):
    """
    Mapeia modelos de uma marca específica usando correspondência exata, similaridade avançada e AI
    Retorna as alterações feitas
    """
    changes = {
        'brand': brand_name,
        'models_mapped': 0,
        'submodels_mapped': 0,
        'similarity_matches': 0,
        'ai_suggestions': 0,
        'details': []
    }
    
    # Lista de modelos do mobile.de para esta marca
    md_models = {model['text']: model for model in md_brand_data['models']}
    md_model_texts = list(md_models.keys())
    
    # Para cada modelo do mobile.de, tentar mapear
    for md_model_text in md_model_texts:
        md_model = md_models[md_model_text]
        mapped = False
        
        # 1. Tentar correspondência exata com modelos SV
        for sv_model in sv_brand_data['models']:
            if sv_model['text'] == md_model_text:
                # Se já existe mapeamento, comparar scores
                if 'text_md' in sv_model:
                    existing_score, existing_type = get_mapping_score(sv_model['text_md'], sv_model['text'])
                    new_score, _ = get_mapping_score(md_model['text'], sv_model['text'])
                    
                    if new_score > existing_score:
                        old_mapping = sv_model['text_md']
                        sv_model['text_md'] = md_model['text']
                        changes['models_mapped'] += 1
                        changes['details'].append(f"✓ Modelo remapeado (melhor match): {md_model_text} (substituiu {old_mapping})")
                else:
                    sv_model['text_md'] = md_model['text']
                    changes['models_mapped'] += 1
                    changes['details'].append(f"✓ Modelo mapeado (exato): {md_model_text}")
                mapped = True
                break
        
        if mapped:
            continue
            
        # 2. Tentar correspondência exata com submodelos SV
        for sv_model in sv_brand_data['models']:
            if 'submodels' in sv_model:
                for sv_submodel in sv_model['submodels']:
                    if sv_submodel['text'] == md_model_text:
                        # Se já existe mapeamento, comparar scores
                        if 'text_md' in sv_submodel:
                            existing_score, existing_type = get_mapping_score(sv_submodel['text_md'], sv_submodel['text'])
                            new_score, _ = get_mapping_score(md_model['text'], sv_submodel['text'])
                            
                            if new_score > existing_score:
                                old_mapping = sv_submodel['text_md']
                                sv_submodel['text_md'] = md_model['text']
                                changes['submodels_mapped'] += 1
                                changes['details'].append(f"  ✓ Submodelo remapeado (melhor match): {sv_model['text']} -> {md_model_text} (substituiu {old_mapping})")
                        else:
                            sv_submodel['text_md'] = md_model['text']
                            changes['submodels_mapped'] += 1
                            changes['details'].append(f"  ✓ Submodelo mapeado (exato): {sv_model['text']} -> {md_model_text}")
                        mapped = True
                        break
                if mapped:
                    break
        
        if mapped:
            continue
            
        # 3. Tentar similaridade avançada com modelos SV
        sv_model_texts = [model['text'] for model in sv_brand_data['models']]
        best_match, score = find_best_match(md_model_text, sv_model_texts, threshold=0.7)
        
        if best_match:
            for sv_model in sv_brand_data['models']:
                if sv_model['text'] == best_match:
                    # Se já existe mapeamento, comparar scores
                    if 'text_md' in sv_model:
                        existing_score, existing_type = get_mapping_score(sv_model['text_md'], sv_model['text'])
                        new_score, _ = get_mapping_score(md_model['text'], sv_model['text'])
                        
                        if new_score > existing_score:
                            old_mapping = sv_model['text_md']
                            sv_model['text_md'] = md_model['text']
                            changes['models_mapped'] += 1
                            changes['similarity_matches'] += 1
                            changes['details'].append(f"≈ Modelo remapeado (similaridade {score:.2f}): {md_model_text} -> {best_match} (substituiu {old_mapping})")
                    else:
                        sv_model['text_md'] = md_model['text']
                        changes['models_mapped'] += 1
                        changes['similarity_matches'] += 1
                        changes['details'].append(f"≈ Modelo mapeado (similaridade {score:.2f}): {md_model_text} -> {best_match}")
                    mapped = True
                    break
        
        if mapped:
            continue
            
        # 4. Tentar similaridade avançada com submodelos SV
        all_submodels = []
        for sv_model in sv_brand_data['models']:
            if 'submodels' in sv_model:
                for sv_submodel in sv_model['submodels']:
                    all_submodels.append((sv_model, sv_submodel))
        
        if all_submodels:
            submodel_texts = [sm[1]['text'] for sm in all_submodels]
            best_match, score = find_best_match(md_model_text, submodel_texts, threshold=0.7)
            
            if best_match:
                for sv_model, sv_submodel in all_submodels:
                    if sv_submodel['text'] == best_match:
                        # Se já existe mapeamento, comparar scores
                        if 'text_md' in sv_submodel:
                            existing_score, existing_type = get_mapping_score(sv_submodel['text_md'], sv_submodel['text'])
                            new_score, _ = get_mapping_score(md_model['text'], sv_submodel['text'])
                            
                            if new_score > existing_score:
                                old_mapping = sv_submodel['text_md']
                                sv_submodel['text_md'] = md_model['text']
                                changes['submodels_mapped'] += 1
                                changes['similarity_matches'] += 1
                                changes['details'].append(f"  ≈ Submodelo remapeado (similaridade {score:.2f}): {sv_model['text']} -> {md_model_text} -> {best_match} (substituiu {old_mapping})")
                        else:
                            sv_submodel['text_md'] = md_model['text']
                            changes['submodels_mapped'] += 1
                            changes['similarity_matches'] += 1
                            changes['details'].append(f"  ≈ Submodelo mapeado (similaridade {score:.2f}): {sv_model['text']} -> {md_model_text} -> {best_match}")
                        mapped = True
                        break
        
        if mapped:
            continue
            
        # 5. Usar AI para identificar correspondências complexas (alemão vs português)
        if AI_AVAILABLE and AI_MAPPING_ENABLED:
            print(f"    🤖 Consultando AI para: {md_model_text}")
            ai_suggestion, confidence = ai_mapping_suggestion(md_model_text, sv_brand_data['models'], brand_name)
            
            if ai_suggestion and confidence >= AI_SIMILARITY_THRESHOLD:
                if ai_suggestion['type'] == 'model':
                    # Mapear para modelo principal
                    for sv_model in sv_brand_data['models']:
                        if sv_model['text'] == ai_suggestion['model']:
                            # Se já existe mapeamento, comparar scores
                            if 'text_md' in sv_model:
                                existing_score, existing_type = get_mapping_score(sv_model['text_md'], sv_model['text'])
                                new_score, _ = get_mapping_score(md_model['text'], sv_model['text'])
                                
                                if new_score > existing_score:
                                    old_mapping = sv_model['text_md']
                                    sv_model['text_md'] = md_model['text']
                                    changes['models_mapped'] += 1
                                    changes['ai_suggestions'] += 1
                                    changes['details'].append(f"🤖 Modelo remapeado (AI): {md_model_text} -> {ai_suggestion['model']} (substituiu {old_mapping})")
                            else:
                                sv_model['text_md'] = md_model['text']
                                changes['models_mapped'] += 1
                                changes['ai_suggestions'] += 1
                                changes['details'].append(f"🤖 Modelo mapeado (AI): {md_model_text} -> {ai_suggestion['model']}")
                            mapped = True
                            break
                            
                elif ai_suggestion['type'] == 'submodel':
                    # Mapear para submodelo
                    for sv_model in sv_brand_data['models']:
                        if sv_model['text'] == ai_suggestion['model'] and 'submodels' in sv_model:
                            for sv_submodel in sv_model['submodels']:
                                if sv_submodel['text'] == ai_suggestion['submodel']:
                                    # Se já existe mapeamento, comparar scores
                                    if 'text_md' in sv_submodel:
                                        existing_score, existing_type = get_mapping_score(sv_submodel['text_md'], sv_submodel['text'])
                                        new_score, _ = get_mapping_score(md_model['text'], sv_submodel['text'])
                                        
                                        if new_score > existing_score:
                                            old_mapping = sv_submodel['text_md']
                                            sv_submodel['text_md'] = md_model['text']
                                            changes['submodels_mapped'] += 1
                                            changes['ai_suggestions'] += 1
                                            changes['details'].append(f"  🤖 Submodelo remapeado (AI): {sv_model['text']} -> {md_model_text} -> {ai_suggestion['submodel']} (substituiu {old_mapping})")
                                    else:
                                        sv_submodel['text_md'] = md_model['text']
                                        changes['submodels_mapped'] += 1
                                        changes['ai_suggestions'] += 1
                                        changes['details'].append(f"  🤖 Submodelo mapeado (AI): {sv_model['text']} -> {md_model_text} -> {ai_suggestion['submodel']}")
                                    mapped = True
                                    break
                            if mapped:
                                break
        
        if not mapped:
            changes['details'].append(f"  ❌ Sem correspondência: {md_model_text}")
    
    return changes


def process_brand_mapping(standvirtual_data, mobile_de_data):
    """Processa o mapeamento marca por marca com save/resume e seleção de início"""
    
    # Criar mapeamento de marcas do mobile.de por nome
    md_brands_by_name = {}
    for md_brand_name, md_brand_data in mobile_de_data['brands'].items():
        md_brands_by_name[md_brand_name] = md_brand_data
    
    brands_list = list(standvirtual_data['brands'].items())
    
    # Seleção de ponto de início
    start_index, use_progress = select_starting_brand(brands_list)
    
    # Tratar opções especiais
    if use_progress == "remove_mappings":
        print("\n🗑️ Removendo todos os mapeamentos existentes...")
        removed_count = remove_all_mappings(standvirtual_data)
        print(f"✅ Removidos {removed_count} mapeamentos!")
        
        # Salvar e sair
        output_file = save_updated_database(standvirtual_data)
        print(f"💾 Base de dados limpa salva em: {output_file}")
        
        # Limpar progresso
        if os.path.exists(PROGRESS_SAVE_FILE):
            os.remove(PROGRESS_SAVE_FILE)
        
        return [], 0, 0, 0, 0
    
    processed_brands = []
    
    # Se usar progresso existente
    if use_progress:
        progress = load_progress()
        if progress:
            if 'exit_brand' in progress and progress['exit_brand']:
                # Encontrar índice da marca onde saiu
                for i, (name, _) in enumerate(brands_list):
                    if name == progress['exit_brand']:
                        start_index = i
                        break
                print(f"🔄 Continuando da marca onde saiu: {progress['exit_brand']} (posição {start_index + 1})")
            else:
                start_index = progress['current_brand_index']
                print(f"🔄 Continuando da marca {start_index + 1}...")
            
            processed_brands = progress.get('processed_brands', [])
        else:
            print("❌ Nenhum progresso encontrado. Começando do início.")
            start_index = 0
    
    all_changes = []
    total_models_mapped = 0
    total_submodels_mapped = 0
    total_similarity_matches = 0
    total_ai_suggestions = 0
    
    print("="*60)
    print("INICIANDO MAPEAMENTO MOBILE.DE -> STANDVIRTUAL")
    if AI_AVAILABLE:
        print("🤖 AI MAPEAMENTO HABILITADO (Considerando diferenças alemão-português)")
    print("="*60)
    
    for i in range(start_index, len(brands_list)):
        sv_brand_name, sv_brand_data = brands_list[i]
        current_position = i + 1
        
        print(f"\n🔍 Processando marca {current_position}/{len(brands_list)}: {sv_brand_name}")
        print("-" * 50)
        
        # Verificar se a marca existe no mobile.de
        if sv_brand_name in md_brands_by_name:
            md_brand_data = md_brands_by_name[sv_brand_name]
            
            # Fazer mapeamento dos modelos
            changes = map_brand_models(sv_brand_data, md_brand_data, sv_brand_name)
            all_changes.append(changes)
            
            total_models_mapped += changes['models_mapped']
            total_submodels_mapped += changes['submodels_mapped']
            total_similarity_matches += changes.get('similarity_matches', 0)
            total_ai_suggestions += changes.get('ai_suggestions', 0)
            
            # Mostrar alterações para esta marca
            if changes['models_mapped'] > 0 or changes['submodels_mapped'] > 0:
                print(f"✅ Marca encontrada no Mobile.de!")
                print(f"   Modelos mapeados: {changes['models_mapped']}")
                print(f"   Submodelos mapeados: {changes['submodels_mapped']}")
                if changes.get('similarity_matches', 0) > 0:
                    print(f"   ≈ Similaridade: {changes['similarity_matches']}")
                if changes.get('ai_suggestions', 0) > 0:
                    print(f"   🤖 Sugestões AI: {changes['ai_suggestions']}")
                print("   Detalhes:")
                for detail in changes['details']:
                    print(f"   {detail}")
            else:
                print(f"⚠️ Marca encontrada mas sem correspondências de modelos")
        else:
            print(f"❌ Marca não encontrada no Mobile.de")
            all_changes.append({
                'brand': sv_brand_name,
                'models_mapped': 0,
                'submodels_mapped': 0,
                'similarity_matches': 0,
                'ai_suggestions': 0,
                'details': ['Marca não existe no Mobile.de']
            })
        
        # Pausa para o usuário ver as alterações
        if i < len(brands_list) - 1:  # Não perguntar na última marca
            user_input = input("\nPressione Enter para continuar ou 'q' para sair (sem aplicar alterações desta marca): ")
            if user_input.lower() == 'q':
                # Salvar progresso indicando onde saiu, mas sem incluir a marca atual
                processed_brands.append(sv_brand_name)  # Não incluir esta marca
                save_progress(standvirtual_data, processed_brands, i, exit_brand=sv_brand_name)
                print(f"\n💾 Progresso salvo! Saiu na marca: {sv_brand_name}")
                print("Execute novamente e escolha 'continuar de onde parei' para retomar.")
                
                # Remover alterações desta marca (reverter)
                remove_brand_mappings(sv_brand_data)
                print(f"🔄 Alterações da marca {sv_brand_name} foram revertidas.")
                
                break
        
        # Salvar progresso após confirmar a marca
        processed_brands.append(sv_brand_name)
        save_progress(standvirtual_data, processed_brands, i + 1)
    
    return all_changes, total_models_mapped, total_submodels_mapped, total_similarity_matches, total_ai_suggestions


def remove_brand_mappings(brand_data):
    """Remove mapeamentos text_md de uma marca específica"""
    for model in brand_data['models']:
        if 'text_md' in model:
            del model['text_md']
        
        if 'submodels' in model:
            for submodel in model['submodels']:
                if 'text_md' in submodel:
                    del submodel['text_md']


def save_updated_database(standvirtual_data):
    """Salva a base de dados atualizada"""
    output_path = "data/json/mapped_sv_md_database.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(standvirtual_data, f, ensure_ascii=False, indent=2)
    
    return output_path


def main():
    """Função principal"""
    try:
        # Carregar bases de dados
        print("Carregando bases de dados...")
        standvirtual_data, mobile_de_data = load_databases()
        
        print(f"StandVirtual: {len(standvirtual_data['brands'])} marcas")
        print(f"Mobile.de: {len(mobile_de_data['brands'])} marcas")
        
        # Processar mapeamento marca por marca
        all_changes, total_models, total_submodels, total_similarity, total_ai = process_brand_mapping(standvirtual_data, mobile_de_data)
        
        # Salvar base de dados atualizada
        output_file = save_updated_database(standvirtual_data)
        
        # Limpar arquivo de progresso após conclusão
        if os.path.exists(PROGRESS_SAVE_FILE):
            os.remove(PROGRESS_SAVE_FILE)
        
        # Mostrar resumo final
        print("\n" + "="*60)
        print("RESUMO FINAL DO MAPEAMENTO")
        print("="*60)
        print(f"Total de marcas processadas: {len(all_changes)}")
        print(f"Total de modelos mapeados: {total_models}")
        print(f"Total de submodelos mapeados: {total_submodels}")
        if total_similarity > 0:
            print(f"≈ Total por similaridade: {total_similarity}")
        if total_ai > 0:
            print(f"🤖 Total de sugestões AI: {total_ai}")
        print(f"Arquivo salvo: {output_file}")
        print("="*60)
        
    except Exception as e:
        print(f"Erro durante o mapeamento: {e}")
        raise


if __name__ == "__main__":
    main() 