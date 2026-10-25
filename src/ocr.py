import io

LANGS = "eng+urd+hin"   # install these Tesseract language packs


def _ocr(img, langs):
    import pytesseract
    try:
        return pytesseract.image_to_string(img, lang=langs).strip()
    except pytesseract.TesseractError:      # language pack missing -> English only
        return pytesseract.image_to_string(img, lang="eng").strip()


def ocr_image(data: bytes, langs: str = LANGS) -> str:
    from PIL import Image
    return _ocr(Image.open(io.BytesIO(data)), langs)


def ocr_pdf(data: bytes, langs: str = LANGS, max_pages: int = 30) -> str:
    import fitz
    from PIL import Image
    out = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in list(doc)[:max_pages]:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            out.append(_ocr(img, langs))
    return "\n".join(out).strip()
