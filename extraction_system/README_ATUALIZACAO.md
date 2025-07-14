# 🔄 Sistema de Atualização da Base de Dados StandVirtual

## 📋 Descrição
Este sistema permite atualizar automaticamente a base de dados de marcas e modelos do StandVirtual.com.

## 📁 Arquivos Incluídos
- `extract_simple_solution.py` - **Solução rápida** (recomendada)
- `run_complete_extraction.py` - Extração completa (mais lenta)
- `demo_extraction.py` - Monitoramento e estatísticas
- `extract_complete_standvirtual_database.py` - Extração inicial completa
- `fix_missing_models.py` - Correção de modelos em falta

## 🚀 Como Atualizar a Base de Dados

### ⚡ Método Rápido (Recomendado)
```bash
# Executa correção rápida das marcas incompletas
python3 extract_simple_solution.py
```
- ⏱️ **Tempo**: 5-15 minutos
- 🎯 **Resultado**: Corrige marcas com "outros modelos"
- ✅ **Recomendado para**: Atualizações regulares

### 🔧 Método Completo
```bash
# Executa extração completa (mais lenta)
python3 run_complete_extraction.py
```
- ⏱️ **Tempo**: 30-60 minutos
- 🎯 **Resultado**: Reconstrói toda a base de dados
- ✅ **Recomendado para**: Primeira vez ou problemas graves

### 📊 Verificar Estatísticas
```bash
# Ver estatísticas atuais
python3 demo_extraction.py stats

# Ver marcas incompletas
python3 demo_extraction.py incomplete

# Ver detalhes de uma marca específica
python3 demo_extraction.py brand:"BMW"
```

## 📈 Resultados Esperados
- **Antes**: 561 modelos, 64.1% completude, 47 marcas incompletas
- **Depois**: 614+ modelos, 70%+ completude, 35-40 marcas incompletas

## 🎯 Arquivo Final
O arquivo atualizado fica em: `../data/json/standvirtual_master_database.json`

## 🔄 Frequência Recomendada
- **Mensal**: `extract_simple_solution.py` (correção rápida)
- **Trimestral**: `run_complete_extraction.py` (extração completa)

## ⚠️ Requisitos
- Python 3.7+
- Chrome browser instalado
- Conexão com internet
- Dependências: `pip install -r ../requirements.txt`

## 📞 Suporte
Em caso de erro, verificar:
1. Chrome está instalado
2. Conexão com internet está estável
3. Site StandVirtual.com está acessível 