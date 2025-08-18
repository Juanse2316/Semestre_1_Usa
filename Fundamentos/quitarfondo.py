#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
from pathlib import Path
from typing import Union, Iterable

import fitz  # PyMuPDF
from PIL import Image

def white_to_alpha(img: Image.Image, tol: int = 15) -> Image.Image:
    """Vuelve transparente todo píxel cercano a blanco."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    lim = 255 - tol
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r >= lim and g >= lim and b >= lim:
                pixels[x, y] = (r, g, b, 0)
    return img

def pdf_to_transparent_pngs(
    pdf_path: Union[str, Path],
    out_dir: Union[str, Path],
    dpi: int = 300,
    tol_white: int = 15,
    zoom: float = None
) -> Iterable[Path]:
    """
    Convierte un PDF a PNGs RGBA con fondo blanco → transparente.
    - Salida en 'out_dir' (sin subcarpetas).
    - Si el PDF tiene 1 página: <stem>.png
      Si tiene varias: <stem>-p001.png, <stem>-p002.png, ...
    """
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    scale = (dpi / 72.0) if zoom is None else zoom
    mat = fitz.Matrix(scale, scale)

    outputs = []
    multi = len(doc) > 1
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat, alpha=True)  # RGBA
        img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
        img = white_to_alpha(img, tol=tol_white)

        out_name = f"{pdf_path.stem}.png" if not multi else f"{pdf_path.stem}-p{i+1:03d}.png"
        out_path = out_dir / out_name
        img.save(out_path)
        outputs.append(out_path)

    doc.close()
    return outputs

def process_many(
    input_path: Union[str, Path],
    out_root: Union[str, Path] = "salida",
    pattern: str = "*.pdf",
    dpi: int = 300,
    tol_white: int = 15
):
    """
    Procesa un archivo PDF o todos los PDFs de una carpeta.
    Guarda TODO directamente en 'out_root' (sin subcarpetas).
    """
    input_path = Path(input_path)
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        pdf_to_transparent_pngs(input_path, out_root, dpi=dpi, tol_white=tol_white)
    else:
        for pdf_file in sorted(input_path.glob(pattern)):
            pdf_to_transparent_pngs(pdf_file, out_root, dpi=dpi, tol_white=tol_white)

if __name__ == "__main__":
    # RUTAS EJEMPLO (Windows):
    process_many(
        input_path=r"F:\Universidad_USA\assets\imagenes_con_fondo",
        out_root=r"F:\Universidad_USA\assets\Talleres_fundamentos",
        pattern="*.pdf",
        dpi=300,
        tol_white=15
    )
