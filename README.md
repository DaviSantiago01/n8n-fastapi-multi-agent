# 📊 Dataset Analyzer API - Multi-Agent System

Plataforma de análise de dados self-service com IA usando sistema multi-agentes para processamento inteligente de datasets.

## 🎯 Objetivo

Sistema que recebe datasets via N8N e realiza análise automatizada usando múltiplos agentes especializados:
- **Agente Decisor**: Escolhe entre análise ML ou EDA
- **Agente ML**: Detecção de outliers e clustering
- **Agente EDA**: Análise exploratória estatística
- **Agente Insights**: Geração de recomendações via IA

## 🏗️ Arquitetura

```
Lovable (Frontend)
  ↓ webhook
N8N (Orquestrador)
  ↓ HTTP POST
FastAPI (Railway) - Multi-Agentes
  ↓
Supabase (Dados + Vector Store)
```

## 🚀 Stack Técnica

**Backend (FastAPI):**
- Multi-agentes com orquestração manual
- Groq API (LLM - llama-3.3-70b-versatile)
- Scikit-learn (outliers com Isolation Forest, clustering com KMeans)
- Pandas (análise de dados)

**Orquestração:**
- N8N recebe CSV via Gmail/Telegram
- Valida arquivo
- Converte para JSON
- Envia para FastAPI
- Retorna análise completa

**Deploy:**
- FastAPI: Railway (Docker)
- N8N: Railway ou cloud
- Supabase: Vector store para RAG

## 📦 Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd n8n_flask_supabase
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env e adicione sua GROQ_API_KEY
```

5. Execute o servidor:
```bash
uvicorn main:app --reload
```

## 🔐 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` com base no `.env.example`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

**IMPORTANTE**: Nunca commit o arquivo `.env` no repositório!

## 📡 Endpoints

### `POST /api/analyze`

Recebe dataset do N8N e retorna análise completa.

**Request Body:**
```json
{
  "nome_arquivo": "vendas.csv",
  "total_de_linhas": 1000,
  "dados_completos": [
    {"col1": "value1", "col2": 123},
    ...
  ],
  "user_email": "user@example.com"
}
```

**Response:**
```json
{
  "dataset_id": "uuid",
  "route": "ml",
  "summary": {
    "outliers": 45,
    "outlier_percent": 4.5,
    "clusters": 3,
    "distribuicao": {"C0": 400, "C1": 350, "C2": 250}
  },
  "insights": [
    "Dataset possui 4.5% de outliers detectados",
    "Identificados 3 grupos distintos nos dados"
  ],
  "agent_recommendation": "Recomenda-se investigar o cluster C2..."
}
```

### `GET /`

Health check endpoint.

## 🤖 Sistema de Agentes

### 1. Agente Decisor
- Analisa características do dataset
- Decide entre rota ML ou EDA
- Critério: >500 linhas E >50% colunas numéricas → ML

### 2. Agente ML
- **Outliers**: Isolation Forest (contamination=0.1)
- **Clustering**: KMeans (2-4 clusters adaptativos)
- **Pré-processamento**: StandardScaler

### 3. Agente EDA
- Estatísticas descritivas
- Contagem de valores faltantes
- Detecção de duplicados
- Análise de tipos de dados

### 4. Agente Insights
- Usa Groq API (LLM)
- Gera insights contextualizados
- Fornece recomendações acionáveis

## 🔄 Fluxo de Dados

1. Usuário envia CSV por email/Telegram
2. N8N captura e converte para JSON
3. FastAPI recebe JSON do N8N
4. **Decisor** escolhe ML ou EDA
5. **Agente específico** processa (sklearn)
6. **Insights** gera recomendações (Groq)
7. Retorna análise + insights

## 🛠️ Desenvolvimento

### Requisitos
- Python 3.9+
- FastAPI
- Groq API Key
- N8N (opcional para testes completos)

### Estrutura do Projeto
```
.
├── main.py              # API FastAPI com sistema multi-agentes
├── requirements.txt     # Dependências Python
├── vendas_dataset.csv   # Dataset de exemplo
├── .env                 # Variáveis de ambiente (não versionado)
├── .env.example         # Template de variáveis de ambiente
├── .gitignore           # Arquivos ignorados pelo Git
└── README.md            # Esta documentação
```

## 🔒 Segurança

- ✅ API keys em variáveis de ambiente
- ✅ CORS configurado
- ✅ Validação de entrada com Pydantic
- ✅ Error handling apropriado
- ⚠️ CORS permite todas as origens (ajustar para produção)

## 📝 Próximos Passos

- [ ] Deploy no Railway
- [ ] Integração completa com N8N
- [ ] Supabase Vector Store para RAG
- [ ] Rate limiting
- [ ] Autenticação JWT
- [ ] Logs estruturados
- [ ] Testes unitários

## 📄 Licença

MIT

## 👤 Autor

Desenvolvido com FastAPI e Multi-Agent System Architecture
