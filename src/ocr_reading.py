"""This module is so fancy because it does ocr reading.

Matthias Mueller, 07.07.2021
matthias.mueller@swissmedic.ch
"""
from pathlib import Path

from pdf2image import convert_from_path
import cv2
import pytesseract
import matplotlib.pyplot as plt


# TODO: Save coordinates of each letter to draw black out boxes in the png when NER is done (pdf backtrafo)
class PdfToText:
    """Saves the pdf as an image, searches for ROIs (text), crops it and returns text. The cropping is not mandatory"""

    def __init__(self, pdf_path: Path, cropping: bool = True, original_images: list = None):
        # TODO: to work only with one image for testing purposes
        self.im = None
        self.marked_images = []
        self.cropped_images = []
        self.rect = []
        self.coordinates = []

        if original_images is None:
            original_images = []
        self._original_images = original_images
        self._pdf_path = pdf_path
        self._cropping = cropping

    def image_per_page(self):
        """Extracts each page of the pdf to an image"""
        pages = convert_from_path(self._pdf_path, 350, poppler_path=Path('C:/Program Files/poppler-0.68.0/bin'))

        for i, page in enumerate(pages):
            image_name = "Page_" + str(i) + ".png"
            #TODO: directly convert to png for original_images
            page.save(image_name, "PNG")
            self._original_images.append(cv2.imread(image_name))

    def image_editing(self):
        """Edit image to make the text extraction easier"""
        self.image_per_page() # could also assign variable self.im here...
        # TODO: loop over original images. Be aware, these are arrays (RGB channels) stored in a list
        # if pages > 1:
        #     im = self.original_images[0]
        # for testing purposes only use one image from the list (for more, make a for loop)
        self.im = self._original_images[0]

        # TODO: maybe RGB to grey instead of BGR (make greyscale picture when scanned in color)
        gray = cv2.cvtColor(self.im, cv2.COLOR_BGR2GRAY)
        # gaussian smoothing if required. Higher numbers result in stronger smoothing
        blur = cv2.GaussianBlur(gray, (1, 1), 0)
        # automatic adaptive thresholding (not uniform): here based on block size (11 nearest neighbours).
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 30)

        return thresh

    def find_ROI(self):
        thresh = self.image_editing()
        # Dilate to combine adjacent text contours (make lines thicker as opposed to erosion)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10)) # adapt parameters if required
        dilate = cv2.dilate(thresh, kernel, iterations=5)
        # Find contours and assign text areas in a list. cv2.CHAIN_APPROX_SIMPLE stores only four points for each
        # rectangle
        cont = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        # cont[1] is the hierarchy (relationship: i.e. parents, childs as outer and inner cont)

        for x in cont:
            area = cv2.contourArea(x)
            x, y, w, h = cv2.boundingRect(x)
            # image is approx. 4100 x 2500 pixels (width x height)
            if w >= 20 and h >= 50 and area > 200: # make sure that the rectangles are not too small. Adapt if required
                start_point = (x, y) # top left
                end_point = (2700, y + h) # bottom right
                self.rect = cv2.rectangle(self.im, start_point, end_point, color=(255, 0, 255), thickness=3)
                self.coordinates.append([start_point, end_point])

            # plt.figure(figsize=(10, 10))
            # plt.imshow(self.rect)
            # plt.show()

        return self.coordinates

    def crop_images(self):
        """Crop image to ROI"""
        self.find_ROI() # should the coord being defined here

        xmin = []
        xmax = []
        ymin = []
        ymax = []
        for i in self.coordinates:
            xleft = i[0][0]
            xright = i[1][0]
            xmin.append(xleft)
            xmax.append(xright)

            yupper= i[0][1]
            ylower = i[1][1]
            ymin.append(yupper)
            ymax.append(ylower)

        # self.cropped_images[y0:y1, x0:x1]
        self.cropped_images = self.im[min(ymin):max(ymax), min(xmin):max(xmax)]

        # # show the cropped image
        # plt.figure(figsize=(10,10))
        # plt.imshow(self.cropped_images)
        # plt.show()

        return self.cropped_images

    def get_text(self) -> str:
        """Get text from image using OCR with pytesseract either with cropped images or with native ones"""
        pytesseract.pytesseract.tesseract_cmd = r'C:\Tesseract\tesseract.exe'
        if self._cropping:
            self.crop_images()
            # B/W conversion for better contrast for OCR
            ret, thresh_new = cv2.threshold(self.cropped_images, 120, 255, cv2.THRESH_BINARY)
        else:
            self.image_editing()
            ret, thresh_new = cv2.threshold(self.im, 120, 255, cv2.THRESH_BINARY)

        # convert image to string
        text = str(pytesseract.image_to_string(thresh_new, config='--psm 6'))
        return text

