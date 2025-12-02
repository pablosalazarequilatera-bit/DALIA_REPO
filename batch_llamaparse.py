"""
batch_llamaparse.py
-------------------
Template para hacer parsing en lote de documentos usando LlamaParse (Llama Cloud)
y guardar el resultado en una carpeta de salida.

Uso desde terminal:

    python batch_llamaparse.py \
        --input_dir ./data/raw_docs \
        --output_dir ./data/parsed_docs \
        --format json

Formatos soportados (en este template): json, md
"""

import os
import argparse
from pathlib import Path
from typing import List

from llama_parse import LlamaParse  # SDK oficial
try:
    from dotenv import load_dotenv  # opcional, para .env (pip install python-dotenv)
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False

# ================
# Configuración
# ================

# Carga variables de entorno desde .env si existe
if _HAS_DOTENV:
    load_dotenv()

LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

if not LLAMA_CLOUD_API_KEY:
    raise ValueError(
        "No se encontró LLAMA_CLOUD_API_KEY en variables de entorno. "
        "Defínela antes de ejecutar el script, por ejemplo:\n"
        "  export LLAMA_CLOUD_API_KEY='TU_API_KEY_AQUI'"
    )

# Inicializa el parser
# Puedes ajustar parámetros como:
#   result_type="markdown" / "json"
#   max_pages, language, etc.
parser = LlamaParse(
    api_key=LLAMA_CLOUD_API_KEY,
    result_type="json",  # por defecto, luego convertimos si queremos texto
    num_workers=4,       # paralelismo
    verbose=True,
)


# ================
# Funciones
# ================

def list_documents(input_dir: Path, exts: List[str]) -> List[Path]:
    """Lista documentos en la carpeta con extensiones permitidas."""
    docs = []
    for ext in exts:
        docs.extend(input_dir.rglob(f"*{ext}"))
    return docs


def parse_document(doc_path: Path, output_dir: Path, output_format: str = "json") -> None:
    """
    Parsea un documento individual con LlamaParse y guarda el resultado.

    output_format:
        - "json": guarda el resultado estructurado
        - "md": guarda el contenido en texto/markdown
    """
    print(f"\n=== Procesando: {doc_path.name} ===")

    # Ejecutar parsing
    # parser.load_data devuelve una lista de "Document" (LlamaIndex)
    documents = parser.load_data(str(doc_path))

    # Aseguramos carpeta de salida
    output_dir.mkdir(parents=True, exist_ok=True)

    # Nombre base del archivo
    base_name = doc_path.stem

    if output_format == "json":
        # Guardar cada Document como json aparte o todos en uno
        import json

        json_out_path = output_dir / f"{base_name}.json"

        # Convertimos la lista de Documents a una estructura serializable
        json_payload = []
        for d in documents:
            json_payload.append(
                {
                    "id": getattr(d, "doc_id", None),
                    "metadata": getattr(d, "metadata", {}),
                    "text": d.text,
                }
            )

        with open(json_out_path, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, ensure_ascii=False, indent=2)

        print(f"Guardado JSON en: {json_out_path}")

    elif output_format == "md":
        # Concatenar texto de todos los Documents y guardar como markdown
        md_out_path = output_dir / f"{base_name}.md"
        all_text = "\n\n".join(d.text for d in documents)

        with open(md_out_path, "w", encoding="utf-8") as f:
            f.write(all_text)

        print(f"Guardado Markdown en: {md_out_path}")

    else:
        raise ValueError("output_format debe ser 'json' o 'md'")


def batch_parse(
    input_dir: str,
    output_dir: str,
    output_format: str = "json",
    exts: List[str] = None,
) -> None:
    """
    Pipeline en lote:
    - Lee todos los docs en input_dir (con exts)
    - Parsea cada uno con LlamaParse
    - Guarda outputs en output_dir
    """
    if exts is None:
        # Ajusta según lo que uses
        exts = [".pdf", ".docx", ".pptx", ".txt"]

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"La carpeta de entrada no existe: {input_dir}")

    docs = list_documents(input_dir, exts)

    if not docs:
        print(f"No se encontraron documentos en {input_dir} con extensiones {exts}")
        return

    print(f"Encontrados {len(docs)} documentos para parsear.")

    for doc_path in docs:
        try:
            parse_document(doc_path, output_dir, output_format=output_format)
        except Exception as e:
            print(f"Error procesando {doc_path.name}: {e}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch parsing de documentos con LlamaParse.")
    parser.add_argument("--input_dir", "-i", required=True, help="Carpeta de documentos originales")
    parser.add_argument("--output_dir", "-o", required=True, help="Carpeta donde se guardan los parseos")
    parser.add_argument(
        "--format",
        "-f",
        default="json",
        choices=["json", "md"],
        help="Formato de salida (json o md). Por defecto 'json'.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    batch_parse(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        output_format=args.format,
    )
