# Matthias Mueller, 07.07.2021
# matthias.mueller@swissmedic.ch
from pdf2image import convert_from_path
import cv2
import pytesseract
import matplotlib.pyplot as plt

# TODO: Generally proceed line by line and save coordinates.
class PdfToText:
    """Saves the pdf as an image, searches for ROIs (text), crops it and returns text. The cropping is not mandatory"""
    def __init__(self):
        self.original_images = []
        # TODO: to work only with one image for testing purposes
        self.im = None
        self.marked_images = []
        self.cropped_images = []
        self.rect = []
        # define relative path of pdf and its name for testing purposes (will be used in a UI with a browsing function)
        self.rel_path = r".\src\data"
        self.pdf = r"\ScanTest.pdf"
        self.pdf_path = self.rel_path + self.pdf
        self.pages = 0
        self.coordinates = []
        self.cropping = False

    def image_per_page(self) -> list:
        """Extracts each page of the pdf to an image"""
        self.pages = convert_from_path(self.pdf_path, 350, poppler_path=r'C:\Program Files\poppler-0.68.0\bin')
        i = 1

        for page in self.pages:
            image_name = "Page_" + str(i) + ".png"
            page.save(image_name, "PNG")
            self.original_images.append(cv2.imread(image_name))
            i += 1
        return self.original_images

    def image_editing(self):
        """Edit image to make the text extraction easier"""
        self.image_per_page() # could also assign variable self.im here...
        # TODO: loop over original images. Be aware, these are arrays (RGB channels) stored in a list
        # if self.pages > 1:
        #     im = self.original_images[0]
        # for testing purposes only use one image from the list (for more, make a for loop)
        self.im = self.original_images[0]

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
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        dilate = cv2.dilate(thresh, kernel, iterations=4)
        # Find contours and assign text areas in a list. cv2.CHAIN_APPROX_SIMPLE stores only four points for each
        # rectangle
        cont1 = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cont = cont1[0] if len(cont1) > 1 else cont1[1]

        for c in cont:
            area = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)

            if y >= 600 and x <= 1000 and area > 10000:
                self.rect = cv2.rectangle(self.im, (x, y), (2200, y + h), color=(255, 0, 255), thickness=3)
                self.coordinates.append([(x, y), (2200, y + h)])

            elif y >= 2400 and x <= 2000:
                self.rect = cv2.rectangle(self.im, (x, y), (2200, y + h), color=(255, 0, 255), thickness=3)
                self.coordinates.append([(x, y), (2200, y + h)])

        return self.rect, self.coordinates

    def crop_images(self):
        """Crop image to ROI"""
        self.find_ROI() # should the coord being defined here
        c = self.coordinates[1] # for cropping
        self.cropped_images = self.im[c[0][1]:c[1][1], c[0][0]:c[1][0]]

        # show the cropped image
        plt.figure(figsize=(10,10))
        plt.imshow(self.cropped_images)
        plt.show()

        return self.cropped_images

    def get_text(self) -> str:
        """Get text from image using OCR with pytesseract either with cropped images or with native ones"""
        pytesseract.pytesseract.tesseract_cmd = r'C:\Tesseract\tesseract.exe'
        if self.cropping:
            self.crop_images()
            # B/W conversion for better contrast for OCR
            ret, thresh_new = cv2.threshold(self.cropped_images, 120, 255, cv2.THRESH_BINARY)
        else:
            self.image_editing()
            ret, thresh_new = cv2.threshold(self.im, 120, 255, cv2.THRESH_BINARY)

        # convert image to string
        text = str(pytesseract.image_to_string(thresh_new, config='--psm 6'))
        return text
