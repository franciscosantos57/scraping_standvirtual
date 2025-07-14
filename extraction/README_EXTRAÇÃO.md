# 🚗 Sistema de Extração de Modelos - StandVirtual

Sistema completo para extrair e atualizar modelos de carros na base de dados do StandVirtual.

## 📁 **Arquivos Criados**

### 1. **`extract_incomplete_brands.py`** - Marcas Incompletas
- **Finalidade**: Processa APENAS marcas que têm "Outros modelos"
- **Ação**: Substitui "Outros modelos" por modelos específicos encontrados
- **Uso**: Para correção rápida de marcas incompletas

### 2. **`extract_all_brands.py`** - Todas as Marcas  
- **Finalidade**: Processa TODAS as marcas da base de dados
- **Ação**: Adiciona novos modelos sem remover os existentes
- **Uso**: Para expansão completa da base de dados

### 3. **`database_stats.py`** - Estatísticas
- **Finalidade**: Ver estatísticas e explorar a base de dados
- **Funcionalidades**: 
  - Estatísticas gerais
  - Lista de marcas incompletas
  - Top marcas com mais modelos
  - Detalhes de marca específica
  - Busca de modelos

## 🎯 **Como Usar**

### ⚡ **Extração Rápida (Marcas Incompletas)**
```bash
python3 extract_incomplete_brands.py
```
- Mostra quantas marcas têm "Outros modelos"
- Permite escolher quantas processar
- **Recomendado**: Começar com 3-5 marcas para testar

### 🌟 **Extração Completa (Todas as Marcas)**
```bash
python3 extract_all_brands.py
```
- Processa todas as 131 marcas
- Permite continuar de onde parou
- Salva automaticamente a cada 10 marcas
- **Tempo estimado**: 4-6 horas para todas as marcas

### 📊 **Ver Estatísticas**
```bash
python3 database_stats.py
```
- Menu interativo com várias opções
- Ver progresso da base de dados
- Explorar marcas e modelos

## 📋 **Estado Atual da Base de Dados**

**Última verificação:**
- **Marcas**: 131
- **Modelos**: 622 (+8 desde a última execução)
- **Taxa de completude**: 71.8%
- **Marcas incompletas**: 37

## 🔧 **Funcionalidades dos Scripts**

### **Script de Marcas Incompletas** (`extract_incomplete_brands.py`)
✅ **Vantagens:**
- Foco nas marcas que precisam de correção
- Execução rápida (5-15 min para todas)
- Substitui "Outros modelos" por modelos reais

❌ **Limitações:**
- Só processa marcas com "Outros modelos"
- Não adiciona modelos a marcas já completas

### **Script Completo** (`extract_all_brands.py`)
✅ **Vantagens:**
- Processa TODAS as marcas
- Adiciona novos modelos às marcas existentes
- Mantém modelos já existentes
- Salvamento periódico para segurança
- Pode continuar de onde parou

❌ **Limitações:**
- Execução mais longa (horas para todas)
- Pode encontrar duplicatas (que são filtradas)

## 🛠️ **Estratégia Recomendada**

### **Fase 1: Correção de Incompletas** 
```bash
# 1. Ver quantas marcas incompletas existem
python3 database_stats.py
# Escolher opção 2 (marcas incompletas)

# 2. Corrigir marcas incompletas
python3 extract_incomplete_brands.py
# Começar com 5 marcas para testar
```

### **Fase 2: Expansão Completa**
```bash
# 3. Executar extração completa
python3 extract_all_brands.py
# Processar todas as marcas ou começar de uma específica
```

### **Fase 3: Monitoramento**
```bash
# 4. Verificar resultados
python3 database_stats.py
# Ver estatísticas atualizadas
```

## ⚙️ **Configurações Avançadas**

### **Limitação de Processamento**
- **Marcas incompletas**: Escolher quantas processar
- **Todas as marcas**: Definir limite ou processar todas

### **Continuação de Processo**
- **Script completo** permite continuar de uma marca específica
- Útil se o processo for interrompido

### **Salvamento**
- **Incompletas**: Salva no final
- **Completas**: Salva a cada 10 marcas + final

## 📊 **Exemplo de Execução**

```bash
$ python3 extract_incomplete_brands.py

🎯 EXTRAÇÃO PARA MARCAS INCOMPLETAS
================================================================
Este script processa APENAS marcas que têm 'Outros modelos'

📋 Encontradas 37 marcas incompletas

🔢 Quantas marcas processar? (Enter = todas, número = limite): 5

[1/5] 🔄 Processando: Acura
🔍 Analisando anúncios da marca: Acura
   ❌ Nenhum anúncio encontrado para Acura
   ⚠️ Nenhum modelo encontrado para Acura - mantém 'Outros modelos'

[2/5] 🔄 Processando: Alpina
🔍 Analisando anúncios da marca: Alpina
   📋 2 anúncios encontrados
   ✅ Modelo encontrado: B7
   💾 1 modelos adicionados à Alpina (substituiu 'Outros modelos')

...
```

## 🚨 **Importante**

1. **Backup**: A base de dados é salva automaticamente, mas mantenha backups
2. **Paciência**: O processo completo pode demorar várias horas
3. **Interrupção**: Use Ctrl+C para parar - o progresso é salvo
4. **Testes**: Comece sempre com poucas marcas para testar
5. **Monitoramento**: Use `database_stats.py` para acompanhar o progresso

## 💡 **Dicas**

- **Para testar**: Use 3-5 marcas primeiro
- **Para produção**: Execute durante a noite ou fim de semana  
- **Se travar**: Restart e continue de onde parou
- **Para monitorar**: Use o script de estatísticas regularmente 