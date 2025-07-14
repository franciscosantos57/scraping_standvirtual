"""
Validador de marcas e modelos para o StandVirtual Scraper
"""

import json
import os
from typing import List, Dict, Optional


class BrandModelValidator:
    """Validador de marcas e modelos baseado nos dados extraídos do StandVirtual"""
    
    def __init__(self, data_file: str = "data/json/standvirtual_master_database.json"):
        """
        Inicializa o validador
        
        Args:
            data_file: Caminho para o arquivo JSON com dados de marcas e modelos
        """
        self.data_file = data_file
        self.brands_data = {}
        self._load_data()
    
    def _load_data(self):
        """Carrega os dados de marcas e modelos"""
        try:
            # Tenta carregar do arquivo
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Se tem estrutura de metadados, extrai só as marcas
                if 'brands' in data:
                    self.brands_data = data['brands']
                    print(f"✅ Base de dados mestre carregada: {len(self.brands_data)} marcas")
                else:
                    # Formato antigo
                    self.brands_data = data
                    print(f"✅ Dados de marcas carregados: {len(self.brands_data)} marcas")
            else:
                print(f"⚠️ Arquivo {self.data_file} não encontrado, usando dados básicos")
                self._load_basic_data()
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar dados: {e}, usando dados básicos")
            self._load_basic_data()
    
    def _load_basic_data(self):
        """Carrega dados básicos de marcas se o arquivo não existir"""
        basic_brands = {
            'Audi': ['A1', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'Q2', 'Q3', 'Q5', 'Q7', 'Q8', 'TT', 'R8'],
            'BMW': ['Serie 1', 'Serie 2', 'Serie 3', 'Serie 4', 'Serie 5', 'Serie 6', 'Serie 7', 'Serie 8', 'X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'X7', 'Z4'],
            'Mercedes-Benz': ['Classe A', 'Classe B', 'Classe C', 'Classe E', 'Classe S', 'CLA', 'CLS', 'GLA', 'GLB', 'GLC', 'GLE', 'GLS'],
            'Volkswagen': ['Polo', 'Golf', 'Jetta', 'Passat', 'Tiguan', 'Touran', 'Sharan', 'Touareg'],
            'Toyota': ['Yaris', 'Corolla', 'Camry', 'Prius', 'Auris', 'Avensis', 'RAV4'],
            'Ford': ['Fiesta', 'Focus', 'Mondeo', 'Mustang', 'Kuga', 'EcoSport'],
            'Opel': ['Corsa', 'Astra', 'Insignia', 'Mokka', 'Crossland', 'Grandland'],
            'Renault': ['Clio', 'Megane', 'Scenic', 'Captur', 'Kadjar', 'Koleos'],
            'Peugeot': ['108', '208', '308', '508', '2008', '3008', '5008'],
            'Citroën': ['C1', 'C3', 'C4', 'C5', 'C3 Aircross', 'C5 Aircross']
        }
        
        self.brands_data = {}
        for brand, models in basic_brands.items():
            self.brands_data[brand] = {
                'brand_value': brand.lower().replace(' ', '-'),
                'models': [
                    {'value': model.lower().replace(' ', '-'), 'text': model}
                    for model in models
                ]
            }
    
    def get_all_brands(self) -> List[str]:
        """
        Retorna lista de todas as marcas disponíveis
        
        Returns:
            Lista de nomes de marcas
        """
        return list(self.brands_data.keys())
    
    def get_models_for_brand(self, brand: str) -> List[Dict[str, str]]:
        """
        Retorna lista de modelos para uma marca específica
        
        Args:
            brand: Nome da marca
            
        Returns:
            Lista de dicionários com 'value' e 'text' dos modelos
        """
        if brand in self.brands_data:
            return self.brands_data[brand]['models']
        return []
    
    def is_valid_brand(self, brand: str) -> bool:
        """
        Verifica se uma marca é válida
        
        Args:
            brand: Nome da marca
            
        Returns:
            True se a marca é válida
        """
        return brand in self.brands_data
    
    def is_valid_model(self, brand: str, model: str) -> bool:
        """
        Verifica se um modelo é válido para uma marca
        
        Args:
            brand: Nome da marca
            model: Nome do modelo
            
        Returns:
            True se o modelo é válido para a marca
        """
        if not self.is_valid_brand(brand):
            return False
        
        models = self.get_models_for_brand(brand)
        model_names = [m['text'].lower() for m in models]
        
        return model.lower() in model_names
    
    def suggest_brands(self, partial_brand: str) -> List[str]:
        """
        Sugere marcas baseadas em texto parcial
        
        Args:
            partial_brand: Texto parcial da marca
            
        Returns:
            Lista de marcas que correspondem
        """
        partial_lower = partial_brand.lower()
        suggestions = []
        
        for brand in self.brands_data.keys():
            if partial_lower in brand.lower():
                suggestions.append(brand)
        
        return suggestions
    
    def suggest_models(self, brand: str, partial_model: str) -> List[Dict[str, str]]:
        """
        Sugere modelos baseados em texto parcial
        
        Args:
            brand: Nome da marca
            partial_model: Texto parcial do modelo
            
        Returns:
            Lista de modelos que correspondem
        """
        if not self.is_valid_brand(brand):
            return []
        
        partial_lower = partial_model.lower()
        models = self.get_models_for_brand(brand)
        suggestions = []
        
        for model in models:
            if partial_lower in model['text'].lower():
                suggestions.append(model)
        
        return suggestions
    
    def get_brand_value(self, brand: str) -> Optional[str]:
        """
        Retorna o valor da marca para usar em URLs/parâmetros
        
        Args:
            brand: Nome da marca
            
        Returns:
            Valor da marca ou None se inválida
        """
        if brand in self.brands_data:
            return self.brands_data[brand]['brand_value']
        return None
    
    def get_model_value(self, brand: str, model: str) -> Optional[str]:
        """
        Retorna o valor do modelo para usar em URLs/parâmetros
        
        Args:
            brand: Nome da marca
            model: Nome do modelo
            
        Returns:
            Valor do modelo ou None se inválido
        """
        models = self.get_models_for_brand(brand)
        
        for m in models:
            if m['text'].lower() == model.lower():
                return m['value']
        
        return None
    
    def validate_search_params(self, brand: str = None, model: str = None) -> Dict[str, str]:
        """
        Valida e corrige parâmetros de pesquisa
        
        Args:
            brand: Nome da marca
            model: Nome do modelo
            
        Returns:
            Dicionário com parâmetros validados e sugestões
        """
        result = {
            'valid': True,
            'brand': brand,
            'model': model,
            'brand_value': None,
            'model_value': None,
            'suggestions': {},
            'errors': []
        }
        
        # Valida marca
        if brand:
            if self.is_valid_brand(brand):
                result['brand_value'] = self.get_brand_value(brand)
            else:
                result['valid'] = False
                result['errors'].append(f"Marca '{brand}' não encontrada")
                
                # Sugere marcas similares
                suggestions = self.suggest_brands(brand)
                if suggestions:
                    result['suggestions']['brands'] = suggestions[:5]
        
        # Valida modelo
        if model and brand and self.is_valid_brand(brand):
            if self.is_valid_model(brand, model):
                result['model_value'] = self.get_model_value(brand, model)
            else:
                result['valid'] = False
                result['errors'].append(f"Modelo '{model}' não encontrado para {brand}")
                
                # Sugere modelos similares
                suggestions = self.suggest_models(brand, model)
                if suggestions:
                    result['suggestions']['models'] = [m['text'] for m in suggestions[:5]]
        
        return result
    
    def get_stats(self) -> Dict[str, int]:
        """
        Retorna estatísticas dos dados carregados
        
        Returns:
            Dicionário com estatísticas
        """
        total_models = sum(len(data['models']) for data in self.brands_data.values())
        
        return {
            'total_brands': len(self.brands_data),
            'total_models': total_models,
            'avg_models_per_brand': round(total_models / len(self.brands_data), 1) if self.brands_data else 0
        }


# Instância global para uso fácil
validator = BrandModelValidator() 