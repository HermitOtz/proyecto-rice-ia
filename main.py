import os
import time
from typing import TypedDict, List
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Configuración de credenciales y modelos
load_dotenv()

# En main.py
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    temperature=0,
    model_kwargs={"api_version": "v1"}
)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 2. Definición del Estado compartido (Memoria del flujo)
class AgentState(TypedDict):
    question: str
    context: str
    answer: str
    next_step: str
    agent_used: str

# --- AGENTE 1: ROUTER ---
def router_agent(state: AgentState):
    print("--- EJECUTANDO ROUTER ---")
    time.sleep(2) # <--- Agrega esta pausa de 2 segundos
    prompt = f"¿La siguiente pregunta trata sobre reglamentos escolares, normas o el RICE? Responde 'RAG' si es así, o 'DIRECTO' si es un saludo o tema general. Pregunta: {state['question']}"
    response = llm.invoke(prompt).content.strip().upper()
    decision = "rag" if "RAG" in response else "directo"
    return {"next_step": decision}

# --- AGENTE 2: RAG ---
def rag_agent(state: AgentState):
    print("--- EJECUTANDO RAG (Buscando en PDF) ---")
    docs = retriever.invoke(state["question"])
    context = "\n\n".join([doc.page_content for doc in docs])
    return {"context": context, "agent_used": "rag_agent"}

# --- AGENTE 3: ANSWER ---
def answer_agent(state: AgentState):
    print("--- EJECUTANDO ANSWER ---")
    context = state.get("context", "Sin contexto adicional.")
    prompt = f"Usa este contexto: {context}\n\nResponde a la pregunta: {state['question']}"
    response = llm.invoke(prompt).content
    agent = state.get("agent_used", "answer_directo")
    return {"answer": response, "agent_used": agent}

# 3. Orquestación con LangGraph
def decide_path(state):
    return "rag_node" if state["next_step"] == "rag" else "answer_node"

workflow = StateGraph(AgentState)

workflow.add_node("router_node", router_agent)
workflow.add_node("rag_node", rag_agent)
workflow.add_node("answer_node", answer_agent)

workflow.set_entry_point("router_node")
workflow.add_conditional_edges("router_node", decide_path)
workflow.add_edge("rag_node", "answer_node")
workflow.add_edge("answer_node", END)

app_graph = workflow.compile()

# 4. API REST con FastAPI
app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    # Definimos el estado inicial completo para que LangGraph no falle
    inputs = {
        "question": request.question,
        "context": "",
        "answer": "",
        "next_step": "",
        "agent_used": ""
    }
    
    print(f"🚀 Procesando pregunta: {request.question}")
    
    try:
        # Ejecutamos el grafo
        result = app_graph.invoke(inputs)
        
        return {
            "answer": result["answer"],
            "agent_used": result["agent_used"]
        }
    except Exception as e:
        print(f"❌ Error en el grafo: {e}")
        return {"error": str(e), "detail": "Revisa la consola del servidor"}