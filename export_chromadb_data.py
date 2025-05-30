import chromadb
import os

# --- CONFIGURACIÓN ---
# Ruta a la carpeta de tu base de datos ChromaDB persistente
CHROMA_DB_PATH = "./my_chroma_db" 
# Nombre de la colección de la cual quieres exportar los documentos
COLLECTION_NAME = "shared" # Asegúrate que este sea el nombre de tu colección
# Nombre del archivo de texto de salida
OUTPUT_TEXT_FILE = "shared.txt"

def exportar_coleccion_a_texto(db_path, collection_name, output_file):
    """
    Exporta los documentos de una colección de ChromaDB a un archivo de texto.
    """
    print(f"Intentando conectar a la base de datos ChromaDB en: {db_path}")
    try:
        client = chromadb.PersistentClient(path=db_path)
        print("Cliente de ChromaDB (persistente) inicializado.")
    except Exception as e:
        print(f"Error al inicializar el cliente persistente: {e}")
        print("Asegúrate de que la ruta a la base de datos sea correcta y que tengas permisos.")
        return

    try:
        print(f"Intentando obtener la colección: '{collection_name}'...")
        # No es necesario especificar la función de embedding al obtener una colección existente
        collection = client.get_collection(name=collection_name)
        print(f"Colección '{collection_name}' obtenida. Número de documentos: {collection.count()}")
    except Exception as e:
        print(f"Error al obtener la colección '{collection_name}': {e}")
        print("Verifica que el nombre de la colección sea correcto y que exista.")
        return

    if collection.count() == 0:
        print(f"La colección '{collection_name}' está vacía. No hay nada que exportar.")
        # Crear un archivo vacío o con un mensaje
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"La colección '{collection_name}' no contiene documentos.\n")
        print(f"Archivo de salida '{output_file}' creado (vacío).")
        return

    print(f"\nExtrayendo documentos de la colección '{collection_name}'...")
    try:
        # Obtenemos IDs, documentos y metadatos. Los embeddings no suelen ser necesarios para este propósito.
        data = collection.get(
            include=['documents', 'metadatas']
        )
    except Exception as e:
        print(f"Error al extraer datos de la colección: {e}")
        return

    print(f"Formateando y escribiendo {len(data['ids'])} documentos en '{output_file}'...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for i in range(len(data['ids'])):
            doc_id = data['ids'][i]
            document_text = data['documents'][i] if data.get('documents') and data['documents'][i] else "Contenido no disponible"
            metadata = data['metadatas'][i] if data.get('metadatas') and data['metadatas'][i] else {}
            
            source_file_info = ""
            if metadata.get('source_file'):
                source_file_info = f"Fuente Original: {metadata.get('source_file')}"
                if metadata.get('file_type'):
                    source_file_info += f" (Tipo: {metadata.get('file_type')})"
            
            f.write(f"--- Inicio Documento (ID: {doc_id}) ---\n")
            if source_file_info:
                f.write(f"{source_file_info}\n")
            f.write("Contenido:\n")
            f.write(document_text)
            f.write("\n--- Fin Documento ---\n\n") # Doble salto de línea para separar bien los documentos

    print(f"\n¡Exportación completada! {len(data['ids'])} documentos guardados en '{output_file}'.")

if __name__ == "__main__":
    # Crea la carpeta de base de datos si no existe (solo para evitar error si se corre sin datos)
    # En un escenario real, la base de datos ya debería existir y estar poblada.
    if not os.path.exists(CHROMA_DB_PATH):
        print(f"Advertencia: La carpeta de la base de datos '{CHROMA_DB_PATH}' no existe.")
        print("Este script espera una base de datos ChromaDB ya existente y poblada.")
        # Podrías crearla aquí si es parte de un flujo, pero para un script de exportación puro,
        # es mejor asumir que ya existe.
        # os.makedirs(CHROMA_DB_PATH) 
        # print(f"Carpeta '{CHROMA_DB_PATH}' creada, pero probablemente esté vacía.")

    exportar_coleccion_a_texto(CHROMA_DB_PATH, COLLECTION_NAME, OUTPUT_TEXT_FILE)