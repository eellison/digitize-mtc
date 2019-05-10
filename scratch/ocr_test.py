from PIL import Image
import pytesseract

def ocr_core(filename):
    """
    This function will handle the core OCR processing of images.
    """
    text = pytesseract.image_to_string(Image.open(filename), config="-c tessedit_char_whitelist=0123456789")  # We'll use Pillow's Image class to open the image and pytesseract to detect the string in the image
    return text
#c tessedit_char_whitelist=0123456789 --psm 6
print(ocr_core('filled_form_1.png'))
