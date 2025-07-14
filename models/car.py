"""
Modelos de dados para carros e parâmetros de pesquisa
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CarSearchParams:
    """Parâmetros para pesquisa de carros"""
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano_min: Optional[int] = None
    ano_max: Optional[int] = None
    km_max: Optional[int] = None
    preco_max: Optional[int] = None
    caixa: Optional[str] = None  # 'manual', 'automatica'
    combustivel: Optional[str] = None  # 'gasolina', 'gasoleo', 'hibrido', 'eletrico'
    
    def to_dict(self):
        """Converte os parâmetros para dicionário, removendo valores None"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Car:
    """Representação de um carro encontrado"""
    titulo: str
    preco: str
    preco_numerico: float
    ano: Optional[int] = None
    quilometragem: Optional[str] = None
    combustivel: Optional[str] = None
    caixa: Optional[str] = None
    potencia: Optional[str] = None
    segmento: Optional[str] = None
    cilindrada: Optional[str] = None
    url: Optional[str] = None
    imagem: Optional[str] = None
    
    def __str__(self):
        return f"{self.titulo} - {self.preco}"
    
    def to_dict(self):
        """Converte o carro para dicionário - apenas um preço para CSV"""
        return {
            'Título': self.titulo,
            'Preço': self.preco,  # Apenas um preço no CSV
            'Ano': self.ano,
            'Quilometragem': self.quilometragem,
            'Combustível': self.combustivel,
            'Caixa': self.caixa,
            'Segmento': self.segmento,
            'Cilindrada': self.cilindrada,
            'Potência': self.potencia,
            'URL': self.url
        } 