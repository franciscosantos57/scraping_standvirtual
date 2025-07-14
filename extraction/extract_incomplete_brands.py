#!/usr/bin/env python3
"""
Extração de modelos APENAS para marcas incompletas (com "Outros modelos")
"""

import json
import time
import re
from datetime import datetime
from typing import List, Set, Dict
from models.car import CarSearchParams
from scraper.standvirtual_scraper import StandVirtualScraper


class IncompleteModelExtractor:
    """Extrator de modelos para marcas incompletas"""
    
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
            'correction_method': 'incomplete_brands_extraction'
        })
        
        with open(self.database_path, 'w', encoding='utf-8') as f:
            json.dump(self.database, f, indent=2, ensure_ascii=False)
    
    def get_incomplete_brands(self) -> List[str]:
        """
        Obtém lista de marcas que têm apenas "Outros modelos"
        
        Returns:
            Lista de nomes de marcas incompletas
        """
        incomplete_brands = []
        
        for brand_name, brand_data in self.database['brands'].items():
            models = brand_data.get('models', [])
            # Verifica se tem apenas um modelo e é "Outros modelos"
            if len(models) == 1 and models[0]['text'] == 'Outros modelos':
                incomplete_brands.append(brand_name)
        
        return incomplete_brands
    
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
    
    def extract_models_for_brand(self, brand_name: str) -> List[str]:
        """
        Extrai modelos para uma marca específica analisando anúncios
        
        Args:
            brand_name: Nome da marca
            
        Returns:
            Lista de novos modelos encontrados
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
            
            for car in cars:
                model = self._extract_model_from_title(car.titulo, brand_name)
                if model:
                    models_found.add(model)
                    print(f"   ✅ Modelo encontrado: {model}")
            
            return list(models_found)
            
        except Exception as e:
            print(f"   ❌ Erro ao processar {brand_name}: {e}")
            return []
    
    def add_models_to_database(self, brand_name: str, new_models: List[str]):
        """
        Substitui "Outros modelos" pelos modelos encontrados
        
        Args:
            brand_name: Nome da marca
            new_models: Lista de novos modelos
        """
        if not new_models or brand_name not in self.database['brands']:
            return
        
        brand_data = self.database['brands'][brand_name]
        
        # Cria lista de modelos formatados
        models = []
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
        
        print(f"   💾 {len(new_models)} modelos adicionados à {brand_name} (substituiu 'Outros modelos')")
    
    def extract_incomplete_brands(self, max_brands: int = None):
        """
        Extrai modelos para todas as marcas incompletas
        
        Args:
            max_brands: Máximo de marcas a processar (None = todas)
        """
        if not self.database:
            print("❌ Base de dados não carregada")
            return
        
        incomplete_brands = self.get_incomplete_brands()
        
        print(f"🎯 EXTRAÇÃO PARA MARCAS INCOMPLETAS")
        print(f"📋 {len(incomplete_brands)} marcas com 'Outros modelos':")
        print(f"   {', '.join(incomplete_brands)}")
        
        if max_brands:
            incomplete_brands = incomplete_brands[:max_brands]
            print(f"📋 Limitado a {max_brands} marcas por teste")
        
        if not incomplete_brands:
            print("✅ Todas as marcas já têm modelos específicos!")
            return
        
        total_new_models = 0
        brands_updated = 0
        
        for i, brand_name in enumerate(incomplete_brands, 1):
            print(f"\n[{i}/{len(incomplete_brands)}] 🔄 Processando: {brand_name}")
            
            try:
                # Extrai modelos
                new_models = self.extract_models_for_brand(brand_name)
                
                if new_models:
                    # Substitui "Outros modelos" pelos novos modelos
                    self.add_models_to_database(brand_name, new_models)
                    total_new_models += len(new_models)
                    brands_updated += 1
                else:
                    print(f"   ⚠️ Nenhum modelo encontrado para {brand_name} - mantém 'Outros modelos'")
                
                # Delay entre marcas
                if i < len(incomplete_brands):
                    print(f"   ⏳ Aguardando 2 segundos...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   ❌ Erro ao processar {brand_name}: {e}")
                continue
        
        # Salva a base de dados atualizada
        if total_new_models > 0:
            print(f"\n💾 Salvando base de dados...")
            self._save_database()
            print(f"✅ Base de dados atualizada!")
            print(f"📊 Resumo: {brands_updated} marcas atualizadas, {total_new_models} novos modelos")
        else:
            print(f"\n⚠️ Nenhuma marca foi atualizada")
        
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
    print("🎯 EXTRAÇÃO PARA MARCAS INCOMPLETAS")
    print("=" * 60)
    print("Este script processa APENAS marcas que têm 'Outros modelos'")
    
    extractor = IncompleteModelExtractor()
    
    if not extractor.database:
        return
    
    # Mostra marcas incompletas
    incomplete_brands = extractor.get_incomplete_brands()
    print(f"\n📋 Encontradas {len(incomplete_brands)} marcas incompletas")
    
    if not incomplete_brands:
        print("✅ Todas as marcas já têm modelos específicos!")
        return
    
    # Pergunta quantas marcas processar
    try:
        choice = input("\n🔢 Quantas marcas processar? (Enter = todas, número = limite): ").strip()
        max_brands = int(choice) if choice and choice.isdigit() else None
        
        if max_brands:
            print(f"📋 Processando máximo {max_brands} marcas")
        else:
            print(f"📋 Processando TODAS as {len(incomplete_brands)} marcas incompletas")
        
        # Inicia extração
        extractor.extract_incomplete_brands(max_brands)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo utilizador.")
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
    finally:
        # Fecha o scraper
        if hasattr(extractor, 'scraper') and extractor.scraper:
            if hasattr(extractor.scraper, 'driver') and extractor.scraper.driver:
                extractor.scraper.driver.quit()


if __name__ == "__main__":
    main() 