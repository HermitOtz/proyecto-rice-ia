# Sistema RAG Multi-Agente - Consulta de Reglamento (RICE)

Este proyecto implementa un sistema de IA capaz de responder preguntas sobre el Reglamento Interno de Convivencia Escolar (RICE) utilizando una arquitectura RAG.

## Características Técnicas
- **LLM**: Gemini 2.0 flash.
- **Framework**: FastAPI + LangGraph para orquestación de agentes.
- **Base de Datos**: ChromaDB con persistencia local.
- **Ingesta**: Procesamiento por lotes (batch_size=50) para optimización de cuota de API.

## Cómo ejecutar
1. Clonar el repositorio.
2. Configurar el archivo `.env` con la API Key de Google.
3. Ejecutar mediante Docker:
   ```bash
   docker build -t proyecto-rice-ia .
   docker run -p 8000:8000 proyecto-rice-ia
