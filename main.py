# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import Optional, TypedDict
import uuid
from groq import Groq
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI(title="Dataset Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente Groq usando variável de ambiente
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY não encontrada nas variáveis de ambiente")

client = Groq(api_key=GROQ_API_KEY)

# ===== SCHEMAS =====
class N8NDatasetRequest(BaseModel):
    nome_arquivo: str
    total_de_linhas: int
    dados_completos: list
    user_email: Optional[str] = None

class AnalyzeResponse(BaseModel):
    dataset_id: str
    route: str
    summary: dict
    insights: list
    agent_recommendation: str

class AnalysisState(TypedDict):
    df: pd.DataFrame
    route: str
    analysis: dict
    insights: list
    recommendation: str

# ===== AGENTES =====
def decisor_agent(state: AnalysisState) -> AnalysisState:
    """Decide: ML ou EDA"""
    df = state["df"]

    response = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": "Responda APENAS: ML ou EDA"},
            {"role": "user", "content": f"""Dataset:
- Linhas: {len(df)}
- Colunas: {df.shape[1]}
- Numéricas: {len(df.select_dtypes(include=[np.number]).columns)}

ML se >500 linhas E >50% numéricas, senão EDA.
Responda: ML ou EDA"""}
        ],
        temperature=0
    )
    
    route = "ml" if "ML" in response.choices[0].message.content.upper() else "eda"
    state["route"] = route
    return state

def eda_agent(state: AnalysisState) -> AnalysisState:
    """Análise Exploratória"""
    df = state["df"]
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    state["analysis"] = {
        "linhas": len(df),
        "colunas": df.shape[1],
        "numericas": len(numeric_cols),
        "faltantes": int(df.isnull().sum().sum()),
        "duplicados": int(df.duplicated().sum()),
        "stats": df[numeric_cols].describe().to_dict() if len(numeric_cols) > 0 else {}
    }
    return state

def ml_agent(state: AnalysisState) -> AnalysisState:
    """Machine Learning"""
    df = state["df"]
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        state["analysis"] = {"erro": "Sem colunas numéricas"}
        return state
    
    X = df[numeric_cols].fillna(0)
    
    # Outliers
    iso = IsolationForest(contamination=0.1, random_state=42)
    outliers = iso.fit_predict(X)
    n_outliers = int((outliers == -1).sum())
    
    # Clustering
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    n_clusters = min(4, max(2, len(df) // 25))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    state["analysis"] = {
        "outliers": n_outliers,
        "outlier_percent": round(n_outliers / len(df) * 100, 2),
        "clusters": n_clusters,
        "distribuicao": {f"C{i}": int((clusters == i).sum()) for i in range(n_clusters)}
    }
    return state

def insights_agent(state: AnalysisState) -> AnalysisState:
    """Gera Insights"""
    df = state["df"]

    response = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": "Analista de dados. Seja objetivo."},
            {"role": "user", "content": f"""Análise: {state['route'].upper()}
Resultados: {state['analysis']}
Preview: {df.head(3).to_dict()}

Gere:
INSIGHTS:
- insight 1
- insight 2

RECOMENDAÇÃO:
texto"""}
        ],
        temperature=0.7
    )
    
    content = response.choices[0].message.content
    parts = content.split("RECOMENDAÇÃO:")
    insights_text = parts[0].replace("INSIGHTS:", "").strip()
    recommendation = parts[1].strip() if len(parts) > 1 else "Análise concluída"
    
    insights = [line.strip("- ").strip() for line in insights_text.split("\n") if line.strip().startswith("-")]
    
    state["insights"] = insights if insights else ["Dataset processado"]
    state["recommendation"] = recommendation
    return state

# ===== ORQUESTRADOR =====
def run_analysis(df: pd.DataFrame) -> AnalysisState:
    """Orquestra agentes manualmente"""
    state: AnalysisState = {
        "df": df,
        "route": "",
        "analysis": {},
        "insights": [],
        "recommendation": ""
    }
    
    # 1. Decisor
    state = decisor_agent(state)
    
    # 2. ML ou EDA
    if state["route"] == "ml":
        state = ml_agent(state)
    else:
        state = eda_agent(state)
    
    # 3. Insights
    state = insights_agent(state)
    
    return state

# ===== ENDPOINT =====
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_dataset(request: N8NDatasetRequest):
    try:
        df = pd.DataFrame(request.dados_completos)
        result = run_analysis(df)
        
        return AnalyzeResponse(
            dataset_id=str(uuid.uuid4()),
            route=result["route"],
            summary=result["analysis"],
            insights=result["insights"],
            agent_recommendation=result["recommendation"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health():
    return {"status": "online"}

# pip install fastapi uvicorn pandas scikit-learn groq
# uvicorn main:app --reload