# main.py - MVP com LangChain + Groq
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI(title="Dataset Analyzer API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LangChain + Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY não encontrada")

# Inicializar LLM com LangChain
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.7
)

# ===== SCHEMAS =====
class DatasetRequest(BaseModel):
    """Request do N8N com dados do CSV"""
    nome_arquivo: str
    dados_completos: list

class AnalyzeResponse(BaseModel):
    """Resposta da análise"""
    nome_arquivo: str
    resumo_dados: dict
    insights: str

# ===== LANGCHAIN: PROMPT TEMPLATE =====
analysis_prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um analista de dados experiente. Seja claro, objetivo e prático."),
    ("user", """Analise este dataset e forneça insights acionáveis:

DATASET: {filename}
Total de linhas: {total_linhas}
Total de colunas: {total_colunas}
Colunas: {colunas}
Valores faltantes: {valores_faltantes}
Linhas duplicadas: {linhas_duplicadas}

PREVIEW DOS DADOS:
{preview}

ESTATÍSTICAS (se disponíveis):
{estatisticas}

FORNEÇA:
1. **3 Insights Principais** sobre os dados
2. **2 Recomendações de Ações** práticas
3. **Pontos de Atenção** (se houver problemas detectados)

Seja direto e acionável.""")
])

# Chain: Prompt → LLM → Output Parser
analysis_chain = analysis_prompt | llm | StrOutputParser()

# ===== FUNÇÃO PRINCIPAL =====
def analyze_dataset(df: pd.DataFrame, filename: str) -> dict:
    """
    Analisa dataset e gera insights usando LangChain + Groq

    1. Calcula estatísticas básicas
    2. Usa LangChain chain para gerar insights
    3. Retorna análise completa
    """

    # 1. ESTATÍSTICAS BÁSICAS
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

    resumo = {
        "total_linhas": len(df),
        "total_colunas": len(df.columns),
        "colunas": df.columns.tolist(),
        "colunas_numericas": len(numeric_cols),
        "valores_faltantes": int(df.isnull().sum().sum()),
        "linhas_duplicadas": int(df.duplicated().sum())
    }

    # Estatísticas numéricas (apenas 3 primeiras colunas)
    estatisticas_str = "Nenhuma coluna numérica"
    if numeric_cols:
        stats = {}
        for col in numeric_cols[:3]:
            stats[col] = {
                "media": round(float(df[col].mean()), 2),
                "minimo": round(float(df[col].min()), 2),
                "maximo": round(float(df[col].max()), 2)
            }
        resumo["estatisticas"] = stats
        estatisticas_str = str(stats)

    # Preview dos dados (5 primeiras linhas)
    preview = df.head(5).to_dict(orient='records')

    # 2. GERAR INSIGHTS COM LANGCHAIN
    insights = analysis_chain.invoke({
        "filename": filename,
        "total_linhas": resumo['total_linhas'],
        "total_colunas": resumo['total_colunas'],
        "colunas": ', '.join(resumo['colunas']),
        "valores_faltantes": resumo['valores_faltantes'],
        "linhas_duplicadas": resumo['linhas_duplicadas'],
        "preview": str(preview[:3]),
        "estatisticas": estatisticas_str
    })

    return {
        "resumo_dados": resumo,
        "insights": insights
    }

# ===== LIMPEZA DE DADOS =====
def clean_data(dados_completos: list) -> list:
    """
    Limpa dados recebidos do N8N removendo campos inválidos

    - Remove campos 'undefined'
    - Remove valores que são listas
    - Converte tudo para tipos simples (str, int, float)
    """
    cleaned = []
    for row in dados_completos:
        clean_row = {}
        for key, value in row.items():
            # Ignorar campos 'undefined' ou None
            if key == "undefined" or key is None:
                continue

            # Ignorar valores que são listas ou dicts
            if isinstance(value, (list, dict)):
                continue

            # Manter apenas valores simples
            clean_row[key] = value

        if clean_row:  # Só adicionar se tiver algum dado
            cleaned.append(clean_row)

    return cleaned

# ===== ENDPOINTS =====
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: DatasetRequest):
    """
    Endpoint principal: recebe dados do N8N e retorna análise

    Flow:
    1. N8N envia CSV como JSON
    2. Limpa dados (remove campos inválidos)
    3. Converte para DataFrame
    4. Gera estatísticas + insights via LangChain
    5. Retorna análise completa
    """
    try:
        # Limpar dados antes de processar
        dados_limpos = clean_data(request.dados_completos)

        if not dados_limpos:
            raise HTTPException(status_code=400, detail="Dataset vazio após limpeza")

        # Converter lista de dicts para DataFrame
        df = pd.DataFrame(dados_limpos)

        if df.empty:
            raise HTTPException(status_code=400, detail="DataFrame vazio")

        # Analisar usando LangChain
        result = analyze_dataset(df, request.nome_arquivo)

        return AnalyzeResponse(
            nome_arquivo=request.nome_arquivo,
            resumo_dados=result["resumo_dados"],
            insights=result["insights"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

@app.get("/")
def health():
    """Health check"""
    return {
        "status": "online",
        "service": "Dataset Analyzer API",
        "version": "2.0-langchain",
        "framework": "LangChain + Groq"
    }

@app.get("/info")
def info():
    """Informações da API"""
    return {
        "endpoints": {
            "/": "Health check",
            "/api/analyze": "Analisar dataset (POST)",
            "/docs": "Documentação interativa",
            "/info": "Informações da API"
        },
        "tecnologias": {
            "framework": "FastAPI",
            "llm": "gpt-oss-120b (OpenAI via Groq)",
            "orchestration": "LangChain",
            "data": "Pandas"
        }
    }
