# Go see the IPython notebook primarily

import io
import logging
import zlib

from collections import defaultdict
from importlib import reload

from pikepdf import Pdf, PdfImage, Name
from PIL import Image, ImageDraw

TARGETS = list(range(32, 63)) + [64, 65] + [67] + list(range(69, 84)) + list(range(86, 91))  # Starting at 1, not 0.
NUM_PAGES = 94
DEFAULT_LEFT = 1440
DEFAULT_RIGHT = 1640

OVERRIDES = defaultdict(dict)
for i in list(range(1,39)):
    OVERRIDES[i]["left"] = 1520
OVERRIDES[42]["left"] = 1520

reload(logging)

logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s', level=logging.DEBUG, datefmt='%I:%M:%S')

LOG = logging.getLogger(__name__)
LOG.setLevel("DEBUG")

def get_pdf_image(page, page_number):
    raw_image = page.images[f"/Im{page_number+1}"]
    pdf_image = PdfImage(raw_image)
    return pdf_image

def remove_noise(pil_image):
    LOG.debug("Removing noise")
    pil_image = pil_image.convert("L")  # Grayscale.
    pil_image = pil_image.convert('1', dither=Image.NONE)
    return pil_image

def remove_black_center(pil_image, page_number):
    draw = ImageDraw.Draw(pil_image)
    left = OVERRIDES[page_number].get("left", DEFAULT_LEFT)
    right = OVERRIDES[page_number].get("right", DEFAULT_RIGHT)
    LOG.debug(f"Removing black center from {left} to {right}")
    draw.rectangle(((left, 0), (right, 10000)), fill="white")
    pil_image.save("/tmp/fix.jpg", format="jpeg")
    pil_image = Image.open("/tmp/fix.jpg")
    return pil_image

def fix_page(page, page_number, fix_noise=False, fix_black_center=False):
    # The first page is 1, not 0. 
    pdf_image = get_pdf_image(page, page_number)

    pil_image = pdf_image.as_pil_image()

    if fix_noise:
        pil_image = remove_noise(pil_image)
    if fix_black_center:
        pil_image = remove_black_center(pil_image, page_number)
    
    pdf_image.obj.write(zlib.compress(pil_image.tobytes()), filter=Name("/FlateDecode"))
    pdf_image.obj.ColorSpace = Name("/DeviceGray")
    LOG.debug(f"Fixed page {page_number}")


pdf = Pdf.open("input.pdf")
for page_number in range(0, NUM_PAGES):
    page = pdf.pages[page_number]
    # fix_black_center = page_number + 1 in TARGETS
    fix_page(page, page_number, fix_noise=True, fix_black_center=True)
pdf.save("fixed.pdf")
LOG.info("Done!")
