import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extracts text from an image or PDF file using Tesseract OCR.
    Assumes Bulgarian language ('bul') is installed.
    """
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            # Convert PDF to images
            images = convert_from_bytes(file_content)
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image, lang='bul')
                text += f"--- Page {i+1} ---\n{page_text}\n"
        else:
            # Assume image
            image = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(image, lang='bul')
            
        return text.strip()
    except Exception as e:
        logger.error(f"OCR Error processing {filename}: {e}")
        return f"Error during OCR: {str(e)}"