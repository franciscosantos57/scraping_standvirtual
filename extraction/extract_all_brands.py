#!/usr/bin/env python3
"""
Extração de modelos para TODAS as marcas (adiciona novos modelos se não existirem)
"""

import json
import time
import re
from datetime import datetime
from typing import List, Set, Dict
from models.car import CarSearchParams
from scraper.standvirtual_scraper import StandVirtualScraper


class AllBrandsModelExtractor:
    """Extrator de modelos para todas as marcas"""
    
    def __init__(self, database_path: str = "data/json/standvirtual_master_database.json"):
        self.database_path = database_path
        self.database = self._load_database()
        self.scraper = StandVirtualScraper()
        
    def _load_database(self) -> dict:
        """Carrega a base de dados atual"""
        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Base de dados não encontrada: {self.database_path}")
            return None
    
    def _save_database(self):
        """Salva a base de dados atualizada"""
        # Atualiza metadados
        total_models = sum(len(brand_data.get('models', [])) for brand_data in self.database['brands'].values())
        total_brands = len(self.database['brands'])
        incomplete_brands = sum(1 for brand_data in self.database['brands'].values() 
                              if len(brand_data.get('models', [])) == 1 and 
                              brand_data['models'][0]['text'] == 'Outros modelos')
        completion_rate = round(((total_brands - incomplete_brands) / total_brands) * 100, 1)
        
        self.database['metadata'].update({
            'last_update': datetime.now().isoformat(),
            'total_brands': total_brands,
            'total_models': total_models,
            'incomplete_brands': incomplete_brands,
            'completion_rate': completion_rate,
            'correction_method': 'all_brands_extraction'
        })
        
        with open(self.database_path, 'w', encoding='utf-8') as f:
            json.dump(self.database, f, indent=2, ensure_ascii=False)
    
    def _extract_model_from_title(self, title: str, brand_name: str) -> str:
        """
        Extrai o modelo do título do anúncio
        
        Args:
            title: Título do anúncio
            brand_name: Nome da marca
            
        Returns:
            Nome do modelo extraído ou None
        """
        if not title or not brand_name:
            return None
            
        # Remove a marca do início do título
        title_clean = title.strip()
        brand_variations = [
            brand_name,
            brand_name.upper(),
            brand_name.lower(),
            brand_name.title()
        ]
        
        for brand_var in brand_variations:
            if title_clean.startswith(brand_var):
                title_clean = title_clean[len(brand_var):].strip()
                break
        
        # Remove prefixos comuns
        prefixes_to_remove = ['Usado', 'usado', 'USADO', '-', '—', '–']
        for prefix in prefixes_to_remove:
            if title_clean.startswith(prefix):
                title_clean = title_clean[len(prefix):].strip()
        
        # Padrões para encontrar o modelo
        patterns = [
            # Mercedes: "Classe A 180" → "Classe A"
            r'^(Classe [A-Z])\s',
            # BMW: "Serie 3 320d" → "Serie 3"  
            r'^(Serie \d+)\s',
            # Audi: "A4 Avant 2.0" → "A4 Avant"
            r'^([A-Z]\d+(?:\s+(?:Avant|Sportback|Allroad|Cabrio))?)\s',
            # Modelos com hífen: "T-Cross 1.0" → "T-Cross"
            r'^([A-Z]+-[A-Z]+)\s',
            # Modelos simples: "Golf GTI" → "Golf"
            r'^([A-Za-z]+)\s',
            # Modelos com números: "X5 M" → "X5"
            r'^([A-Z]+\d*)\s'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title_clean)
            if match:
                model = match.group(1).strip()
                # Valida se o modelo não é muito genérico
                if len(model) >= 2 and not model.lower() in ['de', 'do', 'da', 'com', 'auto', 'car']:
                    return model
        
        # Fallback: pega a primeira palavra se for válida
        first_word = title_clean.split()[0] if title_clean.split() else None
        if first_word and len(first_word) >= 2 and first_word.isalnum():
            return first_word
            
        return None
    
    def _normalize_model_name(self, model: str) -> str:
        """Normaliza o nome do modelo para comparação"""
        if not model:
            return ""
        return model.lower().strip().replace('-', '').replace(' ', '')
    
    def _model_exists(self, brand_name: str, model: str) -> bool:
        """Verifica se o modelo já existe na base de dados"""
        if brand_name not in self.database['brands']:
            return False
            
        existing_models = self.database['brands'][brand_name].get('models', [])
        model_normalized = self._normalize_model_name(model)
        
        for existing in existing_models:
            if self._normalize_model_name(existing['text']) == model_normalized:
                return True
        return False
    
    def extract_models_for_brand(self, brand_name: str) -> List[str]:
        """
        Extrai modelos para uma marca específica analisando anúncios
        
        Args:
            brand_name: Nome da marca
            
        Returns:
            Lista de novos modelos encontrados (que não existem na base de dados)
        """
        print(f"\n🔍 Analisando anúncios da marca: {brand_name}")
        
        # Configura parâmetros para buscar TODOS os anúncios da marca
        params = CarSearchParams()
        params.marca = brand_name.lower()
        
        try:
            # Usa o scraper para obter anúncios
            cars = self.scraper._search_single_variation(params)
            
            if not cars:
                print(f"   ❌ Nenhum anúncio encontrado para {brand_name}")
                return []
            
            print(f"   📋 {len(cars)} anúncios encontrados")
            
            # Extrai modelos únicos dos títulos
            models_found = set()
            new_models = set()
            
            for car in cars:
                model = self._extract_model_from_title(car.titulo, brand_name)
                if model:
                    models_found.add(model)
                    # Verifica se é um modelo novo
                    if not self._model_exists(brand_name, model):
                        new_models.add(model)
                        print(f"   ✅ Novo modelo: {model}")
            
            if models_found:
                existing_count = len(models_found) - len(new_models)
                print(f"   📊 Modelos extraídos: {len(models_found)} total ({existing_count} já existem, {len(new_models)} novos)")
            
            return list(new_models)
            
        except Exception as e:
            print(f"   ❌ Erro ao processar {brand_name}: {e}")
            return []
    
    def add_models_to_database(self, brand_name: str, new_models: List[str]):
        """
        Adiciona novos modelos à base de dados (mantém os existentes)
        
        Args:
            brand_name: Nome da marca
            new_models: Lista de novos modelos
        """
        if not new_models or brand_name not in self.database['brands']:
            return
        
        brand_data = self.database['brands'][brand_name]
        
        # Obtém modelos existentes (remove "Outros modelos" se for o único)
        existing_models = brand_data.get('models', [])
        if len(existing_models) == 1 and existing_models[0]['text'] == 'Outros modelos':
            models = []  # Remove "Outros modelos"
            print(f"   🔄 Substituindo 'Outros modelos' por modelos específicos")
        else:
            models = existing_models.copy()  # Mantém modelos existentes
        
        # Adiciona novos modelos
        for model in new_models:
            model_value = model.lower().replace(' ', '-').replace('ç', 'c').replace('ã', 'a')
            models.append({
                'text': model,
                'value': model_value
            })
        
        # Ordena modelos alfabeticamente
        models.sort(key=lambda x: x['text'])
        
        # Atualiza base de dados
        brand_data['models'] = models
        brand_data['model_count'] = len(models)
        brand_data['total_models'] = len(models)
        
        print(f"   💾 {len(new_models)} novos modelos adicionados à {brand_name} (total: {len(models)})")
    
    def extract_all_brands(self, max_brands: int = None, start_from: str = None):
        """
        Extrai modelos para todas as marcas da base de dados
        
        Args:
            max_brands: Máximo de marcas a processar (None = todas)
            start_from: Marca para começar (útil para continuar de onde parou)
        """
        if not self.database:
            print("❌ Base de dados não carregada")
            return
        
        all_brands = list(self.database['brands'].keys())
        
        # Se especificou onde começar, filtra a partir dessa marca
        if start_from:
            try:
                start_index = all_brands.index(start_from)
                all_brands = all_brands[start_index:]
                print(f"🔄 Continuando a partir da marca: {start_from}")
            except ValueError:
                print(f"⚠️ Marca '{start_from}' não encontrada, começando do início")
        
        print(f"🌟 EXTRAÇÃO PARA TODAS AS MARCAS")
        print(f"📋 {len(all_brands)} marcas para processar")
        
        if max_brands:
            all_brands = all_brands[:max_brands]
            print(f"📋 Limitado a {max_brands} marcas por teste")
        
        total_new_models = 0
        brands_updated = 0
        brands_processed = 0
        
        for i, brand_name in enumerate(all_brands, 1):
            print(f"\n[{i}/{len(all_brands)}] 🔄 Processando: {brand_name}")
            brands_processed += 1
            
            try:
                # Extrai modelos
                new_models = self.extract_models_for_brand(brand_name)
                
                if new_models:
                    # Adiciona novos modelos à base de dados
                    self.add_models_to_database(brand_name, new_models)
                    total_new_models += len(new_models)
                    brands_updated += 1
                else:
                    print(f"   ⚠️ Nenhum modelo novo encontrado para {brand_name}")
                
                # Salva periodicamente (a cada 10 marcas)
                if brands_processed % 10 == 0:
                    print(f"   💾 Salvamento periódico...")
                    self._save_database()
                
                # Delay entre marcas
                if i < len(all_brands):
                    print(f"   ⏳ Aguardando 2 segundos...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   ❌ Erro ao processar {brand_name}: {e}")
                continue
        
        # Salva a base de dados final
        print(f"\n💾 Salvando base de dados final...")
        self._save_database()
        
        print(f"\n🎉 EXTRAÇÃO COMPLETA!")
        print(f"📊 Resumo:")
        print(f"   • Marcas processadas: {brands_processed}")
        print(f"   • Marcas atualizadas: {brands_updated}")
        print(f"   • Novos modelos adicionados: {total_new_models}")
        
        # Mostra estatísticas finais
        self._show_final_stats()
    
    def _show_final_stats(self):
        """Mostra estatísticas finais da base de dados"""
        metadata = self.database['metadata']
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        print(f"   🏷️  Marcas: {metadata['total_brands']}")
        print(f"   🚗 Modelos: {metadata['total_models']}")
        print(f"   ❌ Marcas incompletas: {metadata['incomplete_brands']}")
        print(f"   ✅ Taxa de completude: {metadata['completion_rate']}%")


def main():
    """Função principal"""
    print("🌟 EXTRAÇÃO PARA TODAS AS MARCAS")
    print("=" * 60)
    print("Este script processa TODAS as marcas e adiciona novos modelos")
    
    extractor = AllBrandsModelExtractor()
    
    if not extractor.database:
        return
    
    total_brands = len(extractor.database['brands'])
    print(f"\n📋 Total de marcas na base de dados: {total_brands}")
    
    # Pergunta configurações
    try:
        print("\n⚙️ CONFIGURAÇÕES:")
        
        # Quantas marcas processar
        choice = input("🔢 Quantas marcas processar? (Enter = todas, número = limite): ").strip()
        max_brands = int(choice) if choice and choice.isdigit() else None
        
        # De onde começar
        start_from = None
        if not max_brands or max_brands >= total_brands:
            choice = input("🔄 Começar de uma marca específica? (Enter = início, nome da marca): ").strip()
            if choice:
                start_from = choice
        
        # Confirmação
        if max_brands:
            print(f"\n📋 Processando máximo {max_brands} marcas")
        else:
            print(f"\n📋 Processando TODAS as {total_brands} marcas")
        
        if start_from:
            print(f"🔄 Começando a partir de: {start_from}")
        
        confirm = input("\n✅ Confirma e inicia extração? (s/n): ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("❌ Operação cancelada")
            return
        
        # Inicia extração
        extractor.extract_all_brands(max_brands, start_from)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo utilizador.")
        print("💾 Base de dados salva até ao ponto atual")
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
    finally:
        # Fecha o scraper
        if hasattr(extractor, 'scraper') and extractor.scraper:
            if hasattr(extractor.scraper, 'driver') and extractor.scraper.driver:
                extractor.scraper.driver.quit()


if __name__ == "__main__":
    main() 