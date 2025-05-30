import chromadb
from chromadb.config import Settings # Importar Settings
import os
import shutil # Para borrar la carpeta si es necesario después del reset

# --- CONFIGURACIÓN ---
# Ruta a la carpeta de tu base de datos ChromaDB persistente
CHROMA_DB_PATH = "./my_chroma_db" 

def borrar_toda_la_base_de_datos(db_path):
    """
    Borra todas las colecciones y datos de la instancia de ChromaDB especificada.
    También ofrece la opción de eliminar la carpeta de la base de datos.
    """
    print("--- ¡ADVERTENCIA! ---")
    print(f"Estás a punto de borrar TODAS LAS COLECCIONES Y DATOS de la base de datos ChromaDB ubicada en: '{db_path}'.")
    print("Esta acción es IRREVERSIBLE.")
    
    confirmacion_texto = input(f"¿Estás seguro de que quieres continuar? (s/N): ")
    
    if confirmacion_texto.lower() != 's':
        print("Operación de borrado cancelada por el usuario.")
        return

    if not os.path.exists(db_path):
        print(f"La carpeta de la base de datos '{db_path}' no existe. No hay nada que borrar.")
        return

    try:
        print(f"\nConectando a la base de datos ChromaDB en: {db_path}...")
        # Modificación: Inicializar el cliente con la configuración para permitir el reseteo
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(allow_reset=True) # Habilitar la función reset
        )
        print("Cliente de ChromaDB (persistente) inicializado con la opción de reseteo habilitada.")
        
        print("Reseteando la base de datos (eliminando todas las colecciones y datos)...")
        client.reset() # ¡Esta es la operación que borra todo!
        print("¡Base de datos reseteada exitosamente! Todas las colecciones han sido eliminadas.")

        confirmacion_carpeta = input(f"La base de datos ha sido reseteada. ¿Deseas también eliminar la carpeta física '{db_path}' del sistema de archivos? (s/N): ")
        if confirmacion_carpeta.lower() == 's':
            try:
                # Para estar seguros, cerramos explícitamente la conexión o nos aseguramos de que no haya bloqueos.
                # En la práctica, después de reset(), el cliente podría haber liberado los recursos.
                # Si `client.stop()` o similar estuviera disponible y fuera necesario, se usaría aquí.
                # Por ahora, asumimos que reset() es suficiente para la mayoría de los casos locales antes de rmtree.
                shutil.rmtree(db_path) # Elimina la carpeta y todo su contenido
                print(f"La carpeta '{db_path}' ha sido eliminada del sistema de archivos.")
            except Exception as e_rm:
                print(f"Error al intentar eliminar la carpeta '{db_path}': {e_rm}")
                print("Es posible que necesites cerrarla en otros programas o eliminarla manualmente.")
        else:
            print(f"La carpeta '{db_path}' no ha sido eliminada. Contendrá una base de datos vacía o reinicializada.")

    except chromadb.errors.InvalidDimensionException as e_dim:
        print(f"Error de dimensión inválida al conectar o resetear: {e_dim}")
        print("Esto podría indicar un problema con los archivos de la base de datos existente si no se creó con la misma configuración de embedding.")
    except Exception as e:
        print(f"Ocurrió un error durante el proceso de borrado: {e}")

if __name__ == "__main__":
    borrar_toda_la_base_de_datos(CHROMA_DB_PATH)
