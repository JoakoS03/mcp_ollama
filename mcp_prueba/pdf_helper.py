import base64
import requests
from pdf2image import convert_from_path
import tempfile
import os
import shutil
from ollama import Client
import cv2
import numpy as np

OLLAMA_URL = os.environ.get("OLLAMA_URL")
MODEL = os.environ.get("OLLAMA_MODEL")
PDF_DIR = os.environ.get("PDF_DIR", "./res")
RES_DIR = os.environ.get("RES_DIR", "./res")


def pdf_to_images(pdf_path, dpi=400):
    tmpdir = tempfile.mkdtemp(prefix="pdf_images_")

    pages = convert_from_path(
        pdf_path,
        dpi=dpi,
        fmt="png",
        output_folder=tmpdir
    )

    image_paths = []

    for i, page in enumerate(pages):
        img = np.array(page)

        # --- Grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # --- Suavizado leve
        gray = cv2.medianBlur(gray, 3)

        # --- Binarización adaptativa
        th = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            2
        )

        # --- Morfología ligera (une letras)
        kernel = np.ones((2, 2), np.uint8)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)

        # --- Deskew (solo si hace falta)
        coords = np.column_stack(np.where(th < 255))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            if abs(angle) > 2:
                h, w = th.shape
                M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
                th = cv2.warpAffine(
                    th,
                    M,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )

        # Crop con padding
        coords = np.where(th < 255)
        if coords[0].size > 0:
            y_min, y_max = coords[0].min(), coords[0].max()
            x_min, x_max = coords[1].min(), coords[1].max()

            pad = 10
            y_min = max(0, y_min - pad)
            x_min = max(0, x_min - pad)
            y_max = min(th.shape[0], y_max + pad)
            x_max = min(th.shape[1], x_max + pad)

            th = th[y_min:y_max + 1, x_min:x_max + 1]

        # Resize por altura (mejor lectura VL)
        max_height = 2200
        h, w = th.shape
        if h > max_height:
            scale = max_height / h
            th = cv2.resize(
                th,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_AREA
            )

        # Guardar PNG sin compresión
        img_path = os.path.join(tmpdir, f"page_{i + 1}.png")
        cv2.imwrite(
            img_path,
            th,
            [cv2.IMWRITE_PNG_COMPRESSION, 0]
        )

        image_paths.append(img_path)

    return image_paths, tmpdir


def ocr_images(image_paths, client):
    texts = []

    for img in image_paths:
        resp = client.chat(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": (
                    "Extraé TODO el texto TIPIADO del documento. "
                    "Respetá el orden de lectura y los saltos de línea. "
                    "Ignorá sellos, firmas y marcas gráficas. "
                    "No inventes ni agregues texto."
                ),
                "images": [img]
            }]
        )
        texts.append(resp.message.content)

    return "\n\n".join(texts)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def initialize_and_process(pdf_path: str) -> str:
    if not pdf_path:
        raise FileNotFoundError("No se encontró ningún PDF.")

    pdf_name = os.path.basename(pdf_path)
    pdf_stem = os.path.splitext(pdf_name)[0]
    out_folder = ensure_dir(os.path.join(RES_DIR, pdf_stem))

    image_paths, tmpdir = pdf_to_images(pdf_path)

    client = Client(host=OLLAMA_URL)

    try:
        # Guardar imágenes procesadas
        for img in image_paths:
            shutil.copy(img, os.path.join(out_folder, os.path.basename(img)))

        # OCR
        text = ocr_images(image_paths, client)
        try:
            text = text.replace("GDEBA- ", "GDEBA-")
        except:
            pass
        try:
            text = text.replace("ACTA-", "EX-", 1)
        except:
            pass
        # Guardar texto
        text_file = os.path.join(out_folder, f"{pdf_stem}_extracted.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Procesado correctamente")
        print(f"Salida: {out_folder}")
        print(f"Texto: {text_file}")

        return text
    except requests.exceptions.RequestException as e:
        print(f"Error en la petición a Ollama ({OLLAMA_URL}): {e}")
      
    except Exception as e:
        print(f"Error inesperado: {e}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
