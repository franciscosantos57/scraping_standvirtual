# Script de Mapeamento Mobile.de ↔ StandVirtual com AI

Este script faz o mapeamento inteligente entre as bases de dados do mobile.de (Alemanha) e StandVirtual (Portugal), usando **Inteligência Artificial** para identificar correspondências considerando diferenças regionais.

## 🚀 Funcionalidades

- **🤖 Mapeamento Inteligente com AI**: Usa AI para entender diferenças alemão-português
- **📍 Seleção de Marca de Início**: Escolha de onde começar (início, marca específica, ou continuar)
- **💾 Save/Resume Avançado**: Continue exatamente de onde saiu
- **🔄 Desfazer Alterações**: Remova todos os mapeamentos feitos pelo script
- **⚡ Estratégia Otimizada**: Correspondência exata → Similaridade avançada → AI
- **🚨 Controle de Saída**: 'q' para sair sem aplicar alterações da marca atual

## 🧠 Como a AI Funciona

### Diferenças Regionais Consideradas
- **Mobile.de (Alemanha)**: Nomenclaturas alemãs/europeias
- **StandVirtual (Portugal)**: Nomenclaturas portuguesas/locais
- **Variações**: Acentuação, hífens, espaços, sufixos regionais

### Exemplos Reais
```
🇩🇪 Mobile.de → 🇵🇹 StandVirtual

SIMILARIDADE AVANÇADA:
"Coupé" ≈ "Coupe" (acentos removidos)
"Scouty" ≈ "Scouty R" (substring match)
"Serie 1" ≈ "Série 1" (normalização)
"A-Class" ≈ "A Class" (hífen vs espaço)

AI INTELIGENTE:
"320d" → "Série 3" submodelo "320d" (estrutura)
"Golf GTI" → "Golf" submodelo "GTI" (hierarquia)
```

## ⚙️ Configuração

### 1. API Key da OpenAI ✅ Já Configurada!
Sua API key já está no arquivo `config_mapping.env`.

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

## 🎯 Como Usar

```bash
python3 scripts/map_mobile_de_to_standvirtual.py
```

### Menu de Início
Quando executar, terá estas opções:

```
📋 SELEÇÃO DE MARCA DE INÍCIO
==================================================
Opções:
1. Começar do início
2. Escolher marca específica
3. Continuar de onde parei (se houver progresso)
4. Remover todos os mapeamentos existentes

Escolha uma opção (1-4):
```

## 🔄 Fluxo de Execução

### Para Cada Marca:
1. **Correspondência Exata** - Busca nomes idênticos
2. **≈ Similaridade Avançada** - Remove acentos, detecta substrings, normaliza
3. **🤖 AI Regional** - Analisa diferenças complexas alemão-português
4. **Mostra Alterações** para a marca
5. **Confirma ou Sai**:
   - `Enter` = aplicar e continuar
   - `q` = sair **sem aplicar** esta marca

### Sistema de Progresso:
- **Salva automaticamente** após cada marca confirmada
- **Lembra onde saiu** se usar 'q'
- **Resume exatamente** de onde parou

## 📊 Saída Visual

```
🔍 Processando marca 25/131: BMW
--------------------------------------------------
✅ Marca encontrada no Mobile.de!
   Modelos mapeados: 8
   Submodelos mapeados: 22
   ≈ Similaridade: 15
   🤖 Sugestões AI: 7
   Detalhes:
   ✓ Modelo mapeado (exato): Serie 1
   ≈ Modelo mapeado (similaridade 1.00): Coupe -> Coupé
   ≈ Submodelo mapeado (similaridade 1.00): X3 -> Scouty -> Scouty R
   🤖 Submodelo mapeado (AI): Série 1 -> 120 -> 120d
   🤖 Submodelo mapeado (AI): Série 3 -> 320d -> 320d
   
Pressione Enter para continuar ou 'q' para sair (sem aplicar alterações desta marca):
```

## 🎛️ Opções Avançadas

### Escolher Marca Específica
```
📝 Digite o nome da marca (total: 131 marcas)
Primeiras 10 marcas: ['Abarth', 'AC', 'Acura', ...]

Nome da marca: BMW
✓ Encontrada: BMW (posição 25)
```

### Desfazer Todos os Mapeamentos
```
🗑️ Removendo todos os mapeamentos existentes...
✅ Removidos 2547 mapeamentos!
💾 Base de dados limpa salva em: data/mapped_sv_md_database.json
```

## 📁 Arquivos Gerados

- **`data/mapped_sv_md_database.json`** - Base final com mapeamentos
- **`data/mapping_progress.json`** - Progresso atual (auto-removido ao concluir)

## 🎨 Estrutura do Mapeamento

Quando há correspondência, adiciona o campo `text_md`:

```json
{
  "text": "120d",           // Nome português
  "value": "120d",
  "text_md": "120"         // Nome alemão correspondente
}
```

## ⚠️ Controle de Qualidade

### Estratégia Otimizada
1. **Exato primeiro** - Match perfeito de nomes
2. **Similaridade avançada** - Remove acentos, detecta substrings, normaliza
3. **AI seletiva** - Só para casos complexos sem correspondência
4. **Contexto regional** - Considera mercado alemão vs português

### Saída Segura
- `q` = sair **SEM aplicar** alterações da marca atual
- Progresso salva apenas marcas **confirmadas**
- Pode **reverter tudo** com opção 4

## 🛟 Troubleshooting

### AI Não Funciona
```bash
# Verificar API key
python -c "import openai, os; from dotenv import load_dotenv; load_dotenv('config_mapping.env'); print('OK' if os.getenv('OPENAI_API_KEY') else 'Erro')"
```

### Progresso Corrompido
- Use opção 1 (começar do início) para ignorar progresso anterior

### Performance
- **Com AI**: ~3-5 segundos por marca
- **Total estimado**: 15-30 minutos para todas as marcas

## 📈 Resultados Esperados

- **Correspondências exatas**: ~30-40% dos modelos
- **Similaridade avançada**: ~35-45% dos modelos restantes  
- **Mapeamentos AI**: ~15-20% dos casos complexos
- **Sem correspondência**: ~10-15% (normais, mercados diferentes)

### Similaridade Avançada resolve:
- ✅ Acentuação: "Coupé" ≈ "Coupe"
- ✅ Substrings: "Scouty" ≈ "Scouty R"
- ✅ Normalização: hífen, espaços, maiúsculas
- ✅ Sufixos técnicos: "320d" ≈ "320"

### AI é especialmente útil para:
- Diferentes estruturas hierárquicas
- Mapeamento modelo → submodelo
- Contexto regional específico
- Nomes completamente diferentes entre mercados 