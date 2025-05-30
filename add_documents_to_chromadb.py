import chromadb
from chromadb.utils import embedding_functions
import os # Necesario para listar archivos y construir rutas
import pdfplumber # Para leer archivos PDF

# --- 0. Configuración de la Carpeta de Documentos ---
# Nombre de la subcarpeta donde guardarás tus archivos de texto y PDF
DOCUMENTS_FOLDER = "shared"

# Asegúrate de que la carpeta exista, si no, créala para que el usuario sepa dónde poner los archivos
if not os.path.exists(DOCUMENTS_FOLDER):
    os.makedirs(DOCUMENTS_FOLDER)
    print(f"Carpeta '{DOCUMENTS_FOLDER}' creada. Por favor, añade tus archivos de texto (.txt) o PDF (.pdf) allí.")

# --- 1. Configurar el Cliente de ChromaDB (Persistente Localmente) ---
try:
    client = chromadb.PersistentClient(path="./my_chroma_db")
    print("Cliente de ChromaDB (persistente) inicializado.")
except Exception as e:
    print(f"Error al inicializar el cliente persistente: {e}")
    print("Intentando con un cliente efímero (en memoria)...")
    client = chromadb.EphemeralClient()
    print("Cliente de ChromaDB (efímero) inicializado.")

# --- 2. Seleccionar una Función de Embedding ---
try:
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    print(f"Función de embedding '{sentence_transformer_ef.model_name}' cargada.")
except Exception as e:
    print(f"Error al cargar la función de embedding: {e}")
    print("Asegúrate de tener 'sentence-transformers' instalado y conexión a internet la primera vez.")
    exit()

# --- 3. Crear o Cargar una Colección ---
collection_name = "shared" # Nuevo nombre para incluir PDFs
try:
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=sentence_transformer_ef
    )
    print(f"Colección '{collection_name}' obtenida/creada.")
except Exception as e:
    print(f"Error al obtener o crear la colección '{collection_name}': {e}")
    exit()

# --- 4. Leer Archivos y Añadir Documentos a la Colección ---
documentos_para_anadir = []
ids_para_anadir = []
metadatos_para_anadir = [] # Opcional: para guardar el tipo de archivo

# Obtener IDs ya en la colección para evitar duplicados
archivos_procesados_previamente = set()
if collection.count() > 0: # Solo intentar obtener IDs si la colección no está vacía
    try:
        # Obtenemos solo los IDs, ya que es lo único que necesitamos para la comparación.
        # Pedir 'documents' o 'metadatas' podría ser costoso si la colección es muy grande.
        existing_items_ids = collection.get(include=[])['ids'] 
        if existing_items_ids:
             archivos_procesados_previamente = set(existing_items_ids)
    except Exception as e:
        print(f"Advertencia: No se pudieron obtener los IDs existentes de la colección: {e}")


print(f"\nBuscando archivos en la carpeta '{DOCUMENTS_FOLDER}'...")
archivos_encontrados = 0
archivos_nuevos_anadidos = 0

for nombre_archivo in os.listdir(DOCUMENTS_FOLDER):
    ruta_archivo = os.path.join(DOCUMENTS_FOLDER, nombre_archivo)
    id_documento = f"file::{ruta_archivo}" # Usar la ruta del archivo como ID único

    if id_documento in archivos_procesados_previamente:
        print(f"  - Archivo '{nombre_archivo}' ya procesado anteriormente (ID: {id_documento}). Saltando.")
        continue

    contenido_extraido = ""
    tipo_archivo = "desconocido"

    if nombre_archivo.lower().endswith(".txt"):
        archivos_encontrados += 1
        tipo_archivo = "txt"
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                contenido_extraido = f.read()
            print(f"  - Archivo TXT '{nombre_archivo}' leído.")
        except Exception as e:
            print(f"  - Error al leer el archivo TXT '{nombre_archivo}': {e}")
            continue

    elif nombre_archivo.lower().endswith(".pdf"):
        archivos_encontrados += 1
        tipo_archivo = "pdf"
        try:
            texto_pdf = []
            with pdfplumber.open(ruta_archivo) as pdf:
                for pagina in pdf.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina: # Asegurarse de que se extrajo texto
                        texto_pdf.append(texto_pagina)
            contenido_extraido = "\n".join(texto_pdf) # Unir el texto de todas las páginas
            print(f"  - Archivo PDF '{nombre_archivo}' leído.")
        except Exception as e:
            print(f"  - Error al leer el archivo PDF '{nombre_archivo}': {e}")
            continue
    else:
        # Opcional: podrías añadir manejo para otros tipos de archivo aquí
        # print(f"  - Archivo '{nombre_archivo}' no es .txt ni .pdf. Saltando.")
        continue # Saltar archivos no soportados

    if contenido_extraido and contenido_extraido.strip(): # Solo añadir si se extrajo contenido
        documentos_para_anadir.append(contenido_extraido)
        ids_para_anadir.append(id_documento)
        metadatos_para_anadir.append({"source_file": nombre_archivo, "file_type": tipo_archivo}) # Añadir metadatos
        print(f"    Preparado para añadir (ID: {id_documento}).")
    elif tipo_archivo != "desconocido": # Si fue un tipo soportado pero no se extrajo contenido
        print(f"  - Archivo '{nombre_archivo}' de tipo '{tipo_archivo}' no contenía texto extraíble o estaba vacío. Saltando.")


if not archivos_encontrados:
    print(f"No se encontraron archivos .txt o .pdf en la carpeta '{DOCUMENTS_FOLDER}'.")

if documentos_para_anadir:
    try:
        print(f"\nAñadiendo {len(documentos_para_anadir)} nuevos documentos a la colección '{collection_name}'...")
        collection.add(
            documents=documentos_para_anadir,
            ids=ids_para_anadir,
            metadatas=metadatos_para_anadir # Añadir los metadatos
        )
        archivos_nuevos_anadidos = len(documentos_para_anadir)
        print(f"{archivos_nuevos_anadidos} nuevos documentos añadidos exitosamente.")
    except Exception as e:
        print(f"Error al añadir documentos desde archivos: {e}")
else:
    if archivos_encontrados > 0:
        print("\nNo hay nuevos documentos de archivos para añadir a la colección.")

print(f"Total de documentos en la colección '{collection_name}' ahora: {collection.count()}")

# --- SECCIÓN DE BÚSQUEDA ELIMINADA ---

# --- Opcional: Listar todas las colecciones ---
try:
    print("\nColecciones en la base de datos:")
    collections_list = client.list_collections()
    if not collections_list:
        print("  No hay colecciones en la base de datos.")
    for coll_obj in collections_list:
        print(f"  - Nombre: {coll_obj.name}, ID: {coll_obj.id}, Documentos: {coll_obj.count()}")
except Exception as e:
    print(f"Error al listar colecciones: {e}")

print("\n¡Proceso de carga de documentos completado!")
