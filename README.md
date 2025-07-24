# 🚗 StandVirtual Scraper

Sistema de scraping otimizado para extrair intervalos de preços de carros do **StandVirtual.com**.

Sistema pronto para produção que retorna JSON completo com dados detalhados dos anúncios.

## 📋 Características

- **Ultra-rápido**: 3-6x mais rápido que versões anteriores
- **JSON otimizado**: Retorna apenas dados básicos extraídos (título, preço, ano, quilometragem, combustível, URL, imagem)
- **Logs detalhados**: Informações técnicas gravadas em ficheiro
- **Sem outliers**: Remove preços extremos para estatísticas realistas
- **Zero interação**: Totalmente automatizado via linha de comando
- **Produção ready**: Ideal para APIs e automação

## ⚡ Instalação Rápida

```bash
# 1. Clonar repositório
git clone <url-do-repositorio>
cd scraping_standvirtual

# 2. Instalar dependências
pip3 install -r requirements.txt

# 3. Testar instalação
python3 main.py --help
```

## 🎯 Uso Básico

### Exemplos Simples
```bash
# Qualquer carro até 20.000€
python3 main.py --preco_max 20000

# BMW X5 até 50.000€
python3 main.py --marca bmw --modelo x5 --preco_max 50000

# Carros de 2020-2024 até 30.000€
python3 main.py --ano_min 2020 --ano_max 2024 --preco_max 30000
```

### Output JSON
```json
{
  "preco_intervalo": {
    "min": 15000,
    "max": 45000
  },
  "media_aproximada": 28500,
  "viaturas_consideradas": 12,
  "anuncios_usados_para_calculo": [
    {
      "titulo": "BMW X5 3.0d xDrive",
      "preco": "35.000 €",
      "preco_numerico": 35000,
      "ano": 2020,
      "quilometragem": "85.000 km",
      "combustivel": "Gasóleo",
      "url": "https://standvirtual.com/anuncio/...",
      "imagem": "https://standvirtual.com/image/..."
    }
  ]
}
```

## 🔧 Argumentos Disponíveis

| Parâmetro | Tipo | Exemplo | Descrição |
|-----------|------|---------|-----------|
| `--marca` | texto | `bmw`, `audi`, `toyota` | Marca do carro |
| `--modelo` | texto | `x5`, `a4`, `golf` | Modelo específico |
| `--ano_min` | número | `2018`, `2020` | Ano mínimo de fabrico |
| `--ano_max` | número | `2024`, `2023` | Ano máximo de fabrico |
| `--km_max` | número | `50000`, `100000` | Quilometragem máxima |
| `--preco_max` | número | `25000`, `40000` | Preço máximo em euros |
| `--caixa` | escolha | `manual`, `automatica` | Tipo de caixa |
| `--combustivel` | escolha | `gasolina`, `gasoleo`, `hibrido`, `eletrico` | Combustível |

## 💡 Exemplos Avançados

### Pesquisas Específicas
```bash
# BMW Serie 5 automática de 2022-2024
python3 main.py --marca "BMW" --modelo "Serie 5" --ano_min 2022 --ano_max 2024 --caixa automatica

# Híbridos até 35.000€ com máximo 80.000km
python3 main.py --combustivel hibrido --preco_max 35000 --km_max 80000

# Mercedes Classe C manual até 40.000€
python3 main.py --marca "Mercedes-Benz" --modelo "Classe C" --caixa manual --preco_max 40000
```

### ⚠️ Importante: Modelos com Espaços
Modelos com espaços **devem** usar aspas:

```bash
# ✅ CORRETO
python3 main.py --marca "BMW" --modelo "Serie 5"
python3 main.py --marca "Mercedes-Benz" --modelo "Classe C"

# ❌ ERRO
python3 main.py --marca BMW --modelo Serie 5
```

## 📊 Sistema de Logs

Todas as informações detalhadas são gravadas em `logs/scraping.log`:

- Total de carros encontrados
- Análise de outliers 
- Tempo de extração
- Velocidade (carros/segundo)
- Erros e debugging

### Exemplo de Log
```
2024-01-15 14:30:15 - INFO - NOVA SESSÃO DE SCRAPING INICIADA
2024-01-15 14:30:18 - INFO - Encontrados 35 carros
2024-01-15 14:30:19 - INFO - Outliers removidos: 3
2024-01-15 14:30:19 - INFO - Intervalo final: 15000€ - 45000€
```

## 🔌 Integração em Código

### Python
```python
import subprocess
import json

def get_car_prices(marca=None, modelo=None, preco_max=None):
    cmd = ['python3', 'main.py']
    
    if marca:
        cmd.extend(['--marca', marca])
    if modelo:
        cmd.extend(['--modelo', modelo])
    if preco_max:
        cmd.extend(['--preco_max', str(preco_max)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise Exception(f"Erro: {result.stderr}")

# Exemplo de uso
try:
    data = get_car_prices('bmw', 'x3', 40000)
    interval = data['preco_intervalo']
    print(f"BMW X3: {interval['min']:,.0f}€ - {interval['max']:,.0f}€")
    print(f"Média: {data['media_aproximada']:,.0f}€")
    print(f"Carros considerados: {data['viaturas_consideradas']}")
except Exception as e:
    print(f"Erro: {e}")
```

### API REST (Flask)
```python
from flask import Flask, jsonify, request
import subprocess
import json

app = Flask(__name__)

@app.route('/api/car-prices', methods=['GET'])
def get_car_prices():
    marca = request.args.get('marca')
    modelo = request.args.get('modelo')
    preco_max = request.args.get('preco_max')
    
    cmd = ['python3', 'main.py']
    if marca: cmd.extend(['--marca', marca])
    if modelo: cmd.extend(['--modelo', modelo])
    if preco_max: cmd.extend(['--preco_max', preco_max])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return jsonify(json.loads(result.stdout))
    else:
        return jsonify({"error": result.stderr}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### cURL
```bash
# Via API REST
curl "http://localhost:5000/api/car-prices?marca=bmw&modelo=x5&preco_max=50000"
```

## 🐳 Docker

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Exemplo: pesquisa carros até 30.000€
CMD ["python3", "main.py", "--preco_max", "30000"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  scraper:
    build: .
    volumes:
      - ./logs:/app/logs
    environment:
      - MARCA=bmw
      - MODELO=x5
      - PRECO_MAX=50000
    command: python3 main.py --marca ${MARCA} --modelo ${MODELO} --preco_max ${PRECO_MAX}
```

## 🛠️ Estrutura do Projeto

```
scraping_standvirtual/
├── main.py                 # 🚀 Programa principal
├── requirements.txt        # 📦 Dependências
├── logs/                   # 📝 Logs automáticos
│   └── scraping.log
├── models/                 # 🏗️ Estruturas de dados
│   └── car.py
├── scraper/               # 🕷️ Motor de scraping
│   └── standvirtual_scraper.py
├── utils/                 # 🛠️ Utilitários
│   ├── helpers.py         # Funções auxiliares
│   ├── logging_config.py  # Configuração de logs
│   └── brand_model_validator.py
└── data/                  # 📊 Base de dados de marcas/modelos
    └── json/
```

## 📈 Performance

| Métrica | Valor Típico |
|---------|--------------|
| **Velocidade** | 3-8 carros/segundo |
| **Tempo médio** | 5-15 segundos |
| **Carros por pesquisa** | 15-50 |
| **Taxa de sucesso** | >95% |

## ❓ Troubleshooting

### Erro: "command not found"
```bash
# Use python3 em vez de python
python3 main.py --help
```

### Erro: "unrecognized arguments"
```bash
# Use aspas para modelos com espaços
python3 main.py --modelo "Serie 5"  # ✅ Correto
python3 main.py --modelo Serie 5    # ❌ Erro
```

### Erro: JSON inválido
```bash
# Verifique logs para mais detalhes
tail -20 logs/scraping.log
```

### Nenhum resultado encontrado
```json
{
  "min": null,
  "max": null
}
```
**Solução**: Tente critérios menos restritivos (aumentar preço máximo, remover ano mínimo, etc.)

### Performance lenta
- **Chrome não instalado**: Instale Google Chrome
- **Rede lenta**: Execute em rede mais rápida
- **Muitos critérios**: Simplifique a pesquisa

## 🔄 Casos de Uso Comuns

### 1. Monitorização de Preços
```bash
# Script para executar de hora em hora
#!/bin/bash
echo "$(date): $(python3 main.py --marca bmw --modelo x5 --preco_max 50000)" >> preco_historico.log
```

### 2. Comparação de Segmentos
```bash
# Carros pequenos vs SUVs
python3 main.py --modelo golf --preco_max 25000
python3 main.py --modelo x5 --preco_max 50000
```

### 3. Análise por Combustível
```bash
# Comparar gasolina vs híbrido
python3 main.py --combustivel gasolina --preco_max 30000
python3 main.py --combustivel hibrido --preco_max 30000
```

## 🎯 Output em Diferentes Cenários

### Pesquisa com Resultados
```json
{
  "preco_intervalo": {
    "min": 15000,
    "max": 45000
  },
  "media_aproximada": 28500,
  "viaturas_consideradas": 12,
  "anuncios_usados_para_calculo": [...]
}
```

### Pesquisa sem Resultados
```json
{
  "preco_intervalo": {
    "min": null,
    "max": null
  },
  "media_aproximada": null,
  "viaturas_consideradas": 0,
  "anuncios_usados_para_calculo": []
}
```

### Pesquisa com Erro
```json
{
  "preco_intervalo": {
    "min": null,
    "max": null
  },
  "media_aproximada": null,
  "viaturas_consideradas": 0,
  "anuncios_usados_para_calculo": []
}
```
*(Detalhes do erro em `logs/scraping.log`)*

## 📞 Suporte

Para problemas ou dúvidas:

1. **Verifique logs**: `logs/scraping.log`
2. **Teste comando simples**: `python3 main.py --preco_max 20000`
3. **Valide argumentos**: Use aspas para modelos com espaços
4. **Verifique dependências**: `pip3 install -r requirements.txt`

---

**Sistema StandVirtual Scraper - Pronto para Produção! 🚀** 