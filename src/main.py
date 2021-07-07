########################################################################################
# pdf_ocr (according to Extracting Text from Scanned PDF using Pytesseract & Open CV)
########################################################################################
# Matthias Mueller, 07.07.2021
# matthias.mueller@swissmedic.ch
########################################################################################
# Resources used:
# https://towardsdatascience.com/extracting-text-from-scanned-pdf-using-pytesseract-open-cv-cd670ee38052
# install tesseract for windows: https://computer.meinwissen.info/python-texterkennung-bild-zu-text-mit-pytesseract-in-windows/#Tesseract_unter_Windows_installieren
# install poppler https://stackoverflow.com/questions/18381713/how-to-install-poppler-on-windows, http://blog.alivate.com.au/poppler-windows/

# imports
from ocr_reading import PdfToText
import matplotlib.pyplot as plt

pdf_to_text = PdfToText()
pdf_to_text.cropping = True
a = pdf_to_text.crop_images()
plt.figure(figsize=(10, 10))
plt.imshow(a)
plt.show()
print(pdf_to_text.get_text())

