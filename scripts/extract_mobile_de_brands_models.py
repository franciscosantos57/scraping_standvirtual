#!/usr/bin/env python3
"""
Script para extrair marcas e modelos de carros do mobile.de

Este script:
1. Extrai todas as marcas de carros da API do mobile.de
2. Para cada marca, extrai todos os modelos disponíveis
3. Salva os dados em formato JSON

Uso: python extract_mobile_de_brands_models.py
"""

import requests
import xml.etree.ElementTree as ET
import json
import time
import logging
from pathlib import Path
from urllib.parse import quote


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MobileDeBrandModelExtractor:
    """Extrator de marcas e modelos do mobile.de"""
    
    BASE_URL = "https://services.mobile.de/refdata/classes/Car/makes"
    
    def __init__(self, delay_between_requests=0.5):
        """
        Inicializa o extrator
        
        Args:
            delay_between_requests (float): Delay entre requisições em segundos
        """
        self.delay = delay_between_requests
        self.session = requests.Session()
        # Headers para simular um navegador
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def _make_request(self, url):
        """
        Faz uma requisição HTTP com tratamento de erros
        
        Args:
            url (str): URL para fazer a requisição
            
        Returns:
            requests.Response: Resposta da requisição
        """
        try:
            logger.info(f"Fazendo requisição para: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}")
            raise
            
    def _parse_xml_items(self, xml_content):
        """
        Parse do XML para extrair items
        
        Args:
            xml_content (str): Conteúdo XML
            
        Returns:
            list: Lista de dicionários com key e description
        """
        try:
            # Parse do XML
            root = ET.fromstring(xml_content)
            
            # Namespace do XML
            namespaces = {
                'reference': 'http://services.mobile.de/schema/reference',
                'resource': 'http://services.mobile.de/schema/resource'
            }
            
            items = []
            # Buscar todos os items
            for item in root.findall('.//reference:item', namespaces):
                key = item.get('key')
                
                # Buscar a descrição
                desc_element = item.find('.//resource:local-description', namespaces)
                description = desc_element.text if desc_element is not None else key
                
                # Pular o item "ANDERE" (Other)
                if key and key != 'ANDERE':
                    items.append({
                        'key': key,
                        'name': description
                    })
                    
            return items
            
        except ET.ParseError as e:
            logger.error(f"Erro ao fazer parse do XML: {e}")
            raise
            
    def extract_brands(self):
        """
        Extrai todas as marcas de carros
        
        Returns:
            list: Lista de dicionários com informações das marcas
        """
        logger.info("Extraindo marcas de carros...")
        
        response = self._make_request(self.BASE_URL)
        brands = self._parse_xml_items(response.text)
        
        logger.info(f"Encontradas {len(brands)} marcas")
        return brands
        
    def extract_models_for_brand(self, brand_key):
        """
        Extrai todos os modelos para uma marca específica
        
        Args:
            brand_key (str): Chave da marca (ex: 'AUDI')
            
        Returns:
            list: Lista de dicionários com informações dos modelos
        """
        # URL encode da marca para lidar com espaços e caracteres especiais
        encoded_brand = quote(brand_key)
        url = f"{self.BASE_URL}/{encoded_brand}/models"
        
        try:
            response = self._make_request(url)
            models = self._parse_xml_items(response.text)
            
            logger.info(f"Encontrados {len(models)} modelos para {brand_key}")
            return models
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Erro ao extrair modelos para {brand_key}: {e}")
            return []
            
    def extract_all_data(self):
        """
        Extrai todas as marcas e seus respectivos modelos
        
        Returns:
            dict: Dicionário com todas as marcas e modelos
        """
        logger.info("Iniciando extração completa de marcas e modelos...")
        
        # Extrair marcas
        brands = self.extract_brands()
        
        # Estrutura final dos dados
        data = {
            'metadata': {
                'source': 'mobile.de',
                'total_brands': len(brands),
                'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'brands': {}
        }
        
        # Para cada marca, extrair os modelos
        for i, brand in enumerate(brands, 1):
            brand_key = brand['key']
            brand_name = brand['name']
            
            logger.info(f"Processando marca {i}/{len(brands)}: {brand_name}")
            
            # Extrair modelos
            models = self.extract_models_for_brand(brand_key)
            
            # Adicionar aos dados
            data['brands'][brand_key] = {
                'name': brand_name,
                'key': brand_key,
                'models': models,
                'total_models': len(models)
            }
            
            # Delay entre requisições para não sobrecarregar o servidor
            if i < len(brands):  # Não fazer delay na última iteração
                time.sleep(self.delay)
                
        # Atualizar estatísticas
        total_models = sum(len(brand_data['models']) for brand_data in data['brands'].values())
        data['metadata']['total_models'] = total_models
        
        logger.info(f"Extração completa! {len(brands)} marcas, {total_models} modelos")
        
        return data
        
    def save_to_json(self, data, filepath):
        """
        Salva os dados em um arquivo JSON
        
        Args:
            data (dict): Dados para salvar
            filepath (str): Caminho do arquivo de destino
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Dados salvos em: {filepath}")


def main():
    """Função principal"""
    try:
        # Criar extrator
        extractor = MobileDeBrandModelExtractor(delay_between_requests=0.5)
        
        # Extrair todos os dados
        data = extractor.extract_all_data()
        
        # Salvar em JSON
        output_file = "data/json/mobile_de_brands_models.json"
        extractor.save_to_json(data, output_file)
        
        # Mostrar estatísticas
        print("\n" + "="*50)
        print("EXTRAÇÃO COMPLETA!")
        print("="*50)
        print(f"Total de marcas: {data['metadata']['total_brands']}")
        print(f"Total de modelos: {data['metadata']['total_models']}")
        print(f"Arquivo salvo: {output_file}")
        print("="*50)
        
        # Mostrar algumas marcas como exemplo
        print("\nExemplos de marcas extraídas:")
        for i, (brand_key, brand_data) in enumerate(list(data['brands'].items())[:5]):
            print(f"  {brand_data['name']}: {brand_data['total_models']} modelos")
            
        if len(data['brands']) > 5:
            print(f"  ... e mais {len(data['brands']) - 5} marcas")
            
    except Exception as e:
        logger.error(f"Erro durante a extração: {e}")
        raise


if __name__ == "__main__":
    main() 