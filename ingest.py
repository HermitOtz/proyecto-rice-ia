import os
import time
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

def prepare_knowledge_base():
    print("🚀 Iniciando proceso de ingesta...")
    
    if not os.path.exists('./kb'):
        print("❌ Error: No se encuentra la carpeta 'kb'")
        return

    # 1. Cargar
    print("📖 Leyendo archivos PDF en /kb...")
    loader = DirectoryLoader('./kb', glob="./*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    print(f"✅ Se cargaron {len(documents)} páginas.")

    # 2. Dividir
    print("✂️ Dividiendo texto en fragmentos (chunks)...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(documents)
    print(f"✅ Texto dividido en {len(splits)} fragmentos.")

    # 3. Guardar con reintentos y pausas
    print("🧠 Generando embeddings por lotes (esto evitará el error de cuota)...")
    
    # Creamos la base de datos vacía primero
    vectorstore = Chroma(
        embedding_function=GoogleGenerativeAIEmbeddings(model="models/text-embedding-004"),
        persist_directory="./chroma_db"
    )

    # Añadimos los documentos en grupos de 50
    batch_size = 50
    for i in range(0, len(splits), batch_size):
        batch = splits[i:i + batch_size]
        print(f"📦 Procesando lote {i//batch_size + 1} de {len(splits)//batch_size + 1}...")
        
        try:
            vectorstore.add_documents(batch)
            # Pausa de 10 segundos entre lotes para no saturar la API
            time.sleep(10) 
        except Exception as e:
            print(f"⚠️ Error en lote, esperando 30s para reintentar... {e}")
            time.sleep(30)
            vectorstore.add_documents(batch)

    print("✨ ¡ÉXITO! Base de datos 'chroma_db' creada correctamente.")

if __name__ == "__main__":
    prepare_knowledge_base()