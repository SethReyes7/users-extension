import requests
import logging
import sys
import os
import re # Para sanitizar nombres de archivo
import time # Para el polling
import json # Para parsear respuestas de API
from dotenv import load_dotenv
import urllib3 # Para parse_url
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup 

# --- BEGIN LOGGING CONFIGURATION (File and Console) ---
LOG_FILENAME = 'confluence_script_direct_pdf_debug.log'
logging.getLogger().setLevel(logging.DEBUG)

# Configuración del FileHandler
fh = logging.FileHandler(LOG_FILENAME, mode='w', encoding='utf-8')
fh.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
fh.setFormatter(file_formatter)
logging.getLogger().addHandler(fh)

# Configuración del StreamHandler (consola)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO) # Mostrar INFO y superior en consola
console_formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
ch.setFormatter(console_formatter)
logging.getLogger().addHandler(ch)
# --- END LOGGING CONFIGURATION ---

logging.info(f"Los logs de depuración se están escribiendo en: {LOG_FILENAME}")
logging.info("La consola mostrará mensajes de nivel INFO y superiores.")

if hasattr(urllib3, 'disable_warnings') and hasattr(urllib3.exceptions, 'InsecureRequestWarning'):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.info("Advertencia InsecureRequestWarning para urllib3 deshabilitada.")

# Constantes de configuración
DEFAULT_REQUEST_LIMIT = 25
DEFAULT_REQUEST_TIMEOUT = 180 
POLLING_INTERVAL_SECONDS = 10 
MAX_POLLING_ATTEMPTS = 30 

def sanitize_filename(filename):
    if not isinstance(filename, str):
        filename = str(filename)
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    filename = filename.strip('_. ')
    if not filename:
        filename = "pagina_sin_titulo"
    return filename

def get_atl_token(session, page_view_url):
    try:
        logging.info(f"Intentando obtener atl_token desde: {page_view_url}")
        headers = {'Referer': page_view_url} 
        response = session.get(page_view_url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        token_tag = soup.find('meta', attrs={'name': 'atlassian-token'})
        if token_tag and token_tag.get('content'):
            token = token_tag.get('content')
            logging.info(f"atl_token encontrado: {token}")
            return token
        else:
            logging.error(f"No se pudo encontrar la meta etiqueta 'atlassian-token' en {page_view_url}")
            logging.debug(f"Contenido de la página donde se buscó el token (primeros 1000 chars): {response.text[:1000]}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al solicitar la página para obtener atl_token ({page_view_url}): {e}")
        return None
    except Exception as e:
        logging.error(f"Error inesperado al parsear atl_token desde {page_view_url}: {e}")
        return None

def download_page_as_pdf(session, page_id, page_title, base_url, output_dir):
    page_view_url = f"{base_url.rstrip('/')}/pages/viewpage.action?pageId={page_id}" 
    atl_token = get_atl_token(session, page_view_url)

    if not atl_token:
        logging.error(f"No se pudo obtener atl_token para la página ID {page_id}. Saltando descarga de PDF.")
        return False

    initial_export_url = f"{base_url.rstrip('/')}/spaces/flyingpdf/pdfpageexport.action"
    initial_params = {'pageId': page_id, 'atl_token': atl_token, 'unmatched-route': 'true'}
    initial_headers = {'Referer': page_view_url, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'}
    
    logging.info(f"Iniciando exportación a PDF para '{page_title}' (ID: {page_id}) desde {initial_export_url} con params: {initial_params}")
    
    try:
        response_initial = session.get(initial_export_url, params=initial_params, headers=initial_headers, timeout=DEFAULT_REQUEST_TIMEOUT, verify=False)
        response_initial.raise_for_status()
        logging.info(f"Respuesta inicial de exportación: Status {response_initial.status_code}, URL: {response_initial.url}")

        soup_progress_page = BeautifulSoup(response_initial.content, 'html.parser')
        task_id_tag = soup_progress_page.find('meta', attrs={'name': 'ajs-taskId'})
        
        if not task_id_tag or not task_id_tag.get('content'):
            logging.error(f"No se pudo encontrar 'ajs-taskId' en la página de progreso para '{page_title}'.")
            logging.debug(f"Contenido de la página de progreso (primeros 2000 chars): {response_initial.text[:2000]}")
            return False
        
        task_id = task_id_tag.get('content')
        logging.info(f"Task ID extraído: {task_id} para '{page_title}'")

        progress_url_template = f"{base_url.rstrip('/')}/services/api/v1/task/{task_id}/progress"
        
        for attempt in range(MAX_POLLING_ATTEMPTS):
            logging.info(f"Polling attempt {attempt + 1}/{MAX_POLLING_ATTEMPTS} para task ID {task_id} ('{page_title}')")
            try:
                response_progress = session.get(progress_url_template, headers={'Accept': 'application/json', 'Referer': response_initial.url}, timeout=DEFAULT_REQUEST_TIMEOUT, verify=False)
                response_progress.raise_for_status()
                progress_data = response_progress.json()
                logging.debug(f"Respuesta del progreso para task ID {task_id}: {progress_data}")

                current_progress = progress_data.get("progress", 0)
                current_state = progress_data.get("state", "UNKNOWN")
                
                print(f"    Progreso para '{page_title}': {current_progress}% - Estado: {current_state}")

                if current_state == "FAILED":
                    logging.error(f"La tarea de exportación a PDF {task_id} falló para '{page_title}'. Mensaje: {progress_data.get('message', 'No message')}")
                    return False
                
                if current_progress == 100 and current_state != "RUNNING": 
                    logging.info(f"La tarea de exportación {task_id} completada para '{page_title}'. Obteniendo enlace de descarga final.")
                    
                    intermediate_link_api_url_path = progress_data.get("result")
                    if not intermediate_link_api_url_path:
                        logging.error(f"El resultado de la tarea de progreso no contiene URL para task ID {task_id} ('{page_title}'). Data: {progress_data}")
                        return False
                    
                    if intermediate_link_api_url_path.startswith('http'):
                        intermediate_link_api_url = intermediate_link_api_url_path
                    else:
                        parsed_main_url = urllib3.util.parse_url(base_url)
                        scheme_host_port = f"{parsed_main_url.scheme}://{parsed_main_url.host}"
                        if parsed_main_url.port:
                            scheme_host_port += f":{parsed_main_url.port}"
                        if not intermediate_link_api_url_path.startswith('/'):
                           intermediate_link_api_url_path = '/' + intermediate_link_api_url_path
                        intermediate_link_api_url = f"{scheme_host_port}{intermediate_link_api_url_path}"

                    logging.info(f"Obteniendo URL final de descarga desde: {intermediate_link_api_url}")
                    response_final_url = session.get(intermediate_link_api_url, headers={'Accept': 'text/plain, */*', 'Referer': progress_url_template}, timeout=DEFAULT_REQUEST_TIMEOUT, verify=False)
                    response_final_url.raise_for_status()
                    
                    actual_pdf_download_url = response_final_url.text.strip() 
                    if not actual_pdf_download_url or not actual_pdf_download_url.startswith('http'):
                        logging.error(f"No se obtuvo una URL de descarga final válida desde {intermediate_link_api_url}. Respuesta: {actual_pdf_download_url}")
                        return False
                        
                    logging.info(f"URL final de descarga de PDF para '{page_title}': {actual_pdf_download_url}")

                    # Usar requests.get() para la descarga desde S3 para evitar enviar cabeceras de sesión.
                    response_pdf = requests.get(
                        actual_pdf_download_url, 
                        timeout=DEFAULT_REQUEST_TIMEOUT * 2, 
                        verify=False, 
                        stream=True
                    )
                    response_pdf.raise_for_status()

                    content_type_pdf = response_pdf.headers.get('Content-Type', '').lower()
                    if 'application/pdf' not in content_type_pdf and 'application/octet-stream' not in content_type_pdf:
                        logging.error(f"El contenido final descargado para '{page_title}' no parece ser un PDF. Content-Type: '{content_type_pdf}'. URL: {actual_pdf_download_url}")
                        return False

                    sanitized_title = sanitize_filename(page_title)
                    pdf_filename = os.path.join(output_dir, f"{sanitized_title}.pdf")
                    with open(pdf_filename, 'wb') as f:
                        for chunk in response_pdf.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logging.info(f"PDF descargado exitosamente: {pdf_filename}")
                    print(f"    PDF guardado en: {pdf_filename}")
                    return True
                
                time.sleep(POLLING_INTERVAL_SECONDS)

            except requests.exceptions.RequestException as e_poll:
                logging.error(f"Error durante el polling para task ID {task_id} ('{page_title}'): {e_poll}")
                if hasattr(e_poll, 'response') and e_poll.response is not None and e_poll.response.status_code == 404:
                    logging.error(f"La URL de progreso {progress_url_template} devolvió 404. La tarea {task_id} puede haber expirado o ser inválida.")
                    return False 
                time.sleep(POLLING_INTERVAL_SECONDS) 
            except json.JSONDecodeError as e_json:
                logging.error(f"Error al decodificar JSON de progreso para task ID {task_id} ('{page_title}'): {e_json}. Respuesta: {response_progress.text[:200]}")
                return False
        
        logging.error(f"Se excedió el máximo de intentos de polling para la tarea {task_id} ('{page_title}').")
        return False

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Error HTTP al iniciar/descargar PDF para '{page_title}' (ID: {page_id}): {http_err}")
        if http_err.response is not None:
            logging.error(f"Headers de la respuesta del error: {http_err.response.headers}")
            try:
                error_content_decoded = http_err.response.content.decode(errors='ignore')
                logging.error(f"Contenido de la respuesta del error HTTP: {error_content_decoded[:2000]}")
            except Exception:
                logging.error(f"Contenido de la respuesta del error HTTP (bytes, primeros 512): {http_err.response.content[:512]}")
    except Exception as e:
        logging.error(f"Un error inesperado ocurrió al descargar/guardar PDF para '{page_title}' (ID: {page_id}): {e}", exc_info=True)
    
    print(f"    Error al descargar PDF para: {page_title}")
    return False

def get_page_details_by_id(session, page_id, base_url):
    api_url = f"{base_url.rstrip('/')}/rest/api/content/{page_id}"
    headers = {'Accept': 'application/json'}
    logging.info(f"Obteniendo detalles para la página ID: {page_id} desde {api_url}")
    try:
        response = session.get(api_url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()
        data = response.json()
        return {'id': data.get('id'), 'title': data.get('title', 'N/A')}
    except Exception as e:
        logging.error(f"[get_page_details_by_id] Error para la página {page_id}: {e}", exc_info=True)
    return None

def get_all_pages_in_space(session, base_url, space_key):
    pages_data = []
    api_base_for_space = f"{base_url.rstrip('/')}/rest/api/space/{space_key}/content/page"
    current_api_url = api_base_for_space
    current_api_params = {'start': 0, 'limit': DEFAULT_REQUEST_LIMIT, 'expand': 'title'}
    headers = {'Accept': 'application/json'}
    logging.info(f"Obteniendo todas las páginas en el espacio '{space_key}': {current_api_url} con límite={DEFAULT_REQUEST_LIMIT}")
    is_first_request = True
    while current_api_url:
        params_for_request = current_api_params if is_first_request and current_api_url == api_base_for_space else None
        logging.info(f"Obtención de todas las páginas del espacio: Solicitando desde {current_api_url} con params {params_for_request if params_for_request else '(params en URL next)'}")
        is_first_request = False
        try:
            response = session.get(current_api_url, params=params_for_request, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            data = response.json()
            current_pages_results = data.get('results', [])
            if not current_pages_results: break
            for page_item in current_pages_results:
                pages_data.append({'id': page_item.get('id'), 'title': page_item.get('title', 'N/A')})
            
            next_url_from_api = data.get('_links', {}).get('next')
            if next_url_from_api:
                if next_url_from_api.startswith(base_url): 
                    current_api_url = next_url_from_api
                elif next_url_from_api.startswith('/wiki/'): 
                    parsed_main_url = urllib3.util.parse_url(base_url)
                    domain_root = f"{parsed_main_url.scheme}://{parsed_main_url.host}"
                    if parsed_main_url.port:
                         domain_root += f":{parsed_main_url.port}"
                    current_api_url = f"{domain_root}{next_url_from_api}"
                elif next_url_from_api.startswith('/rest/api/'): 
                     current_api_url = f"{base_url.rstrip('/')}{next_url_from_api}"
                elif next_url_from_api.startswith('http'): 
                    current_api_url = next_url_from_api
                else: 
                    logging.warning(f"Formato de URL 'next' no reconocido completamente: {next_url_from_api}, intentando unir con base_url.")
                    current_api_url = f"{base_url.rstrip('/')}{next_url_from_api if next_url_from_api.startswith('/') else '/' + next_url_from_api}"
                current_api_params = None 
            else: break
        except Exception as e:
            logging.error(f"[get_all_pages_in_space] Error: {e}", exc_info=True)
            return []
    return pages_data

def get_direct_children(session, parent_page_id, base_url, space_key_for_logging="N/A"):
    children_data = []
    api_base_for_children = f"{base_url.rstrip('/')}/rest/api/content/{parent_page_id}/child/page"
    current_api_url = api_base_for_children
    current_api_params = {'start': 0, 'limit': DEFAULT_REQUEST_LIMIT, 'expand': 'title'}
    headers = {'Accept': 'application/json'}
    logging.info(f"Obteniendo hijos directos para la página ID: {parent_page_id}")
    is_first_request = True
    while current_api_url:
        params_for_request = current_api_params if is_first_request and current_api_url == api_base_for_children else None
        logging.info(f"Hijos directos: Solicitando para padre {parent_page_id} desde {current_api_url} con params {params_for_request if params_for_request else '(params en URL next)'}")
        is_first_request = False
        try:
            response = session.get( current_api_url, params=params_for_request, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            data = response.json()
            current_children_results = data.get('results', [])
            if not current_children_results: break
            for child_item in current_children_results:
                children_data.append({'id': child_item.get('id'), 'title': child_item.get('title', 'N/A')})
            
            next_url_from_api = data.get('_links', {}).get('next')
            if next_url_from_api:
                if next_url_from_api.startswith(base_url):
                    current_api_url = next_url_from_api
                elif next_url_from_api.startswith('/wiki/'):
                    parsed_main_url = urllib3.util.parse_url(base_url)
                    domain_root = f"{parsed_main_url.scheme}://{parsed_main_url.host}"
                    if parsed_main_url.port:
                         domain_root += f":{parsed_main_url.port}"
                    current_api_url = f"{domain_root}{next_url_from_api}"
                elif next_url_from_api.startswith('/rest/api/'):
                     current_api_url = f"{base_url.rstrip('/')}{next_url_from_api}"
                elif next_url_from_api.startswith('http'):
                    current_api_url = next_url_from_api
                else:
                    logging.warning(f"Formato de URL 'next' no reconocido completamente: {next_url_from_api}, intentando unir con base_url.")
                    current_api_url = f"{base_url.rstrip('/')}{next_url_from_api if next_url_from_api.startswith('/') else '/' + next_url_from_api}"
                current_api_params = None
            else: break
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 404: # type: ignore
                logging.info(f"No se encontraron hijos (404) para el padre {parent_page_id}.")
                break 
            else: logging.error(f"[Direct Children] Error HTTP para padre {parent_page_id}: {http_err}", exc_info=True)
            return []
        except Exception as e:
            logging.error(f"[Direct Children] Error para padre {parent_page_id}: {e}", exc_info=True)
            return []
    return children_data

def display_direct_children_recursively(session, page_id, page_title, indent_level, base_url, space_key, 
                                        visited_ids_for_recursion_control, all_displayed_pages_summary):
    indent = "  " * indent_level
    print(f"{indent}- {page_title} (ID: {page_id})")
    if page_id not in all_displayed_pages_summary:
        all_displayed_pages_summary[page_id] = page_title 
    
    if page_id in visited_ids_for_recursion_control:
        logging.warning(f"Los hijos de la página ID {page_id} ('{page_title}') ya fueron procesados. Saltando.")
        return
    visited_ids_for_recursion_control.add(page_id)
    
    direct_children = get_direct_children(session, page_id, base_url, space_key_for_logging=space_key)
    for child in direct_children:
        display_direct_children_recursively(
            session, child['id'], child['title'], indent_level + 1, 
            base_url, space_key, 
            visited_ids_for_recursion_control, all_displayed_pages_summary
        )

def main():
    print("Listador de Páginas de Confluence - Exportación Recursiva a PDF (Descarga Directa)")
    print("---------------------------------------------------------------------------------")
    
    default_output_directory = "confluence_exported_pdfs_directos"
    output_directory_prompt = input(f"Introduce el nombre para el directorio de salida de los PDFs (default: {default_output_directory}): ").strip()
    output_directory = output_directory_prompt if output_directory_prompt else default_output_directory
    
    if not os.path.exists(output_directory):
        try:
            os.makedirs(output_directory)
            print(f"Directorio de salida creado: {output_directory}")
        except OSError as e:
            print(f"Error al crear el directorio de salida '{output_directory}': {e}")
            return
    print(f"Los PDFs se guardarán en el directorio: {output_directory}")

    load_dotenv()
    confluence_url_env = os.getenv("CONFLUENCE_URL")
    email_or_username = os.getenv("CONFLUENCE_USER")
    api_token_or_password = os.getenv("CONFLUENCE_TOKEN_OR_PASS") 
    space_key_env = os.getenv("CONFLUENCE_SPACE_KEY")
    parent_page_id_env = os.getenv("CONFLUENCE_PARENT_PAGE_ID")

    if not all([confluence_url_env, email_or_username, api_token_or_password, space_key_env]):
        print("Error: Faltan variables de entorno requeridas (CONFLUENCE_URL, CONFLUENCE_USER, CONFLUENCE_TOKEN_OR_PASS, CONFLUENCE_SPACE_KEY).")
        print("Asegúrate de que tu archivo .env está configurado correctamente.")
        return
    
    cleaned_confluence_url = confluence_url_env.strip()
    if cleaned_confluence_url.endswith('/'):
        cleaned_confluence_url = cleaned_confluence_url[:-1]

    if ".atlassian.net" in cleaned_confluence_url and not cleaned_confluence_url.endswith("/wiki"):
        cleaned_confluence_url = f"{cleaned_confluence_url}/wiki"
    
    logging.info(f"URL base de Confluence procesada para API/Exportación: {cleaned_confluence_url}")

    space_key = space_key_env.upper()
    
    session = requests.Session()
    session.auth = HTTPBasicAuth(email_or_username, api_token_or_password)
    
    all_displayed_pages_details = {} 
    processed_page_ids_for_recursion_control = set() 
    listing_context_message = ""
    root_pages_for_hierarchy = []

    if parent_page_id_env and parent_page_id_env.strip() != "":
        print(f"\nConfiguración cargada. ID de Página Padre Objetivo: {parent_page_id_env}")
        root_page_details = get_page_details_by_id(session, parent_page_id_env, cleaned_confluence_url)
        if not root_page_details:
            print(f"No se pudieron obtener los detalles para el ID de página padre inicial '{parent_page_id_env}'. Saliendo.")
            return
        root_pages_for_hierarchy = [root_page_details]
        listing_context_message = f"\n--- Listado Jerárquico de Páginas (Comenzando desde '{root_page_details['title']}' - ID: {root_page_details['id']}) ---"
    else:
        print("\nCONFLUENCE_PARENT_PAGE_ID no establecido. Procesando todas las páginas de nivel superior en el espacio.")
        top_level_pages = get_all_pages_in_space(session, cleaned_confluence_url, space_key)
        if not top_level_pages:
            print(f"No se encontraron páginas de nivel superior en el espacio '{space_key}'.")
            return
        root_pages_for_hierarchy = top_level_pages
        listing_context_message = f"\n--- Listado Jerárquico de Páginas (Todas las páginas en el Espacio: {space_key}) ---"
    
    print(listing_context_message)

    for page_summary in root_pages_for_hierarchy:
        display_direct_children_recursively(
            session, page_summary['id'], page_summary['title'], 0, 
            cleaned_confluence_url, space_key, 
            processed_page_ids_for_recursion_control, all_displayed_pages_details
        )
    
    print("\n--- Descarga de PDF Directa desde Confluence ---")
    if not all_displayed_pages_details:
        print("No se identificaron páginas para la descarga de PDF.")
    else:
        print(f"Descargando PDFs desde {len(all_displayed_pages_details)} páginas únicas identificadas...")
        
        successful_downloads = 0
        failed_downloads = 0

        for i, (page_id, page_title) in enumerate(all_displayed_pages_details.items()):
            print(f"  Procesando PDF para: {page_title} (ID: {page_id}) ({i+1}/{len(all_displayed_pages_details)})")
            
            if download_page_as_pdf(session, page_id, page_title, cleaned_confluence_url, output_directory):
                successful_downloads += 1
            else:
                failed_downloads += 1
        
        print(f"\nDescarga de PDFs completada.")
        print(f"  Descargas exitosas: {successful_downloads}")
        print(f"  Descargas fallidas: {failed_downloads}")
        if failed_downloads > 0:
            print(f"  Revisa el archivo de log '{LOG_FILENAME}' para detalles sobre las fallas.")

    print("\n--- Resumen de Todas las Páginas Mostradas (también procesadas para PDF) ---")
    if all_displayed_pages_details:
        print(f"Total de páginas únicas procesadas: {len(all_displayed_pages_details)}")
        for i, (page_id, page_title) in enumerate(all_displayed_pages_details.items()):
            print(f"  {i+1}. Título: {page_title} (ID: {page_id})")
    else:
        print("No se mostraron/procesaron páginas.")
    print("\n--- Fin del Script ---")

if __name__ == "__main__":
    main()
