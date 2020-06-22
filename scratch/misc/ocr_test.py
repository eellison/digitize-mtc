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

def ocr(image, response_region):
    """
    This function will handle the core OCR processing of images.
    """
    cutout = get_region_of_image(image, response_region)
    text = pytesseract.image_to_string(cutout, config="-c tessedit_char_whitelist=0123456789")
    return text

def get_region_of_image(image, response_region):
    w, h, x, y = (response_region.w, response_region.h, response_region.x, response_region.y)
    cutout = image[y : y+h, x : x+w]
    print(cutout)
    cv2.imwrite(str(response_region.name) + "_pic" + ".jpg", cutout)
    return cutout
