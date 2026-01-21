import base64
import requests
from pdf2image import convert_from_path
import tempfile
import os
import shutil
import sys
from ollama import Client

OLLAMA_URL = os.environ.get("OLLAMA_URL")
MODEL = os.environ.get("OLLAMA_MODEL")
PDF_DIR = os.environ.get("PDF_DIR", "./res")
RES_DIR = os.environ.get("RES_DIR", "./res")

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def pdf_to_images(pdf_path, dpi=300):
    tmpdir = tempfile.mkdtemp(prefix="pdf_images_")
    pages = convert_from_path(pdf_path, dpi=dpi, output_folder=tmpdir)
    image_paths = []
    for i, page in enumerate(pages):
        img_path = os.path.join(tmpdir, f"page_{i+1}.png")
        page.save(img_path, "PNG")
        image_paths.append(img_path)
    return image_paths, tmpdir

def ocr_images(image_paths, client, timeout=300):
    resp = client.chat(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[{
            "role": "user",
            "content": "Extraé TODO el texto del documento. Mantené el orden de lectura y respetá saltos de línea.",
            "images": image_paths
        }]
    )
    
    message_content = resp.message.content 
    return message_content


def find_first_pdf(dir_path):
    if not os.path.isdir(dir_path):
        return None
    for entry in os.listdir(dir_path):
        if entry.lower().endswith(".pdf"):
            return os.path.join(dir_path, entry)
    return None

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

def initialize_and_process(pdf_path : str) -> str:
    #pdf_path = os.path.join(PDF_DIR, pdf_name)
    if not pdf_path:
        print(f"No se encontró ningún .pdf en '{PDF_DIR}'. Pon el archivo (ej. documento.pdf) dentro de esa carpeta.")
        

    pdf_name = os.path.basename(pdf_path)
    pdf_stem = os.path.splitext(pdf_name)[0]
    out_folder = ensure_dir(os.path.join(RES_DIR, pdf_stem))

    image_paths, tmpdir = pdf_to_images(pdf_path)

    #Setup llm Ollama
    client = Client(host=OLLAMA_URL)

    try:
        # Copiamos las imágenes al folder de salida para que queden persistentes en ./res
        saved_image_paths = []
        for img in image_paths:
            dest = os.path.join(out_folder, os.path.basename(img))
            shutil.copy(img, dest)
            saved_image_paths.append(dest)

        # Llamada OCR (usando las imágenes en memoria/temporal)
        text = ocr_images(image_paths, client)
        # Guardamos el texto en res
        text_file = os.path.join(out_folder, f"{pdf_stem}_extracted.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            # Si ocr_images devolvió dict/string, lo guardamos tal cual
            if isinstance(text, (dict, list)):
                f.write(str(text))
            else:
                f.write(text)

        print(f"Procesado. Archivos en: {out_folder}")
        print(f"Texto guardado en: {text_file}")
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error en la petición a Ollama ({OLLAMA_URL}): {e}")
      
    except Exception as e:
        print(f"Error inesperado: {e}")
      
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass