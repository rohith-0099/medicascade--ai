import os

os.environ["TF_USE_LEGACY_KERAS"] = "1"

import tensorflow as tf
from tensorflow.keras.models import load_model    
import cv2
import imutils
import numpy as np
import os

class MLTumorDetector:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.input_shape = (240, 240)
        
    def load(self):
        if not self.model:
            print(f"Loading ML Model from {self.model_path}")
            self.model = load_model(self.model_path)
            
    def crop_brain_contour(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        thresh = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.erode(thresh, None, iterations=2)
        thresh = cv2.dilate(thresh, None, iterations=2)

        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        
        if not cnts:
            return image
            
        c = max(cnts, key=cv2.contourArea)

        extLeft = tuple(c[c[:, :, 0].argmin()][0])
        extRight = tuple(c[c[:, :, 0].argmax()][0])
        extTop = tuple(c[c[:, :, 1].argmin()][0])
        extBot = tuple(c[c[:, :, 1].argmax()][0])
        
        new_image = image[extTop[1]:extBot[1], extLeft[0]:extRight[0]]            
        return new_image

    def predict(self, image_path):
        self.load()
        
        image = cv2.imread(image_path)
        if image is None:
            return 0.0
            
        cropped = self.crop_brain_contour(image)
        resized = cv2.resize(cropped, self.input_shape)
        normalize = resized / 255.0
        
        input_data = np.expand_dims(normalize, axis=0)
        
        prediction = self.model.predict(input_data)
        return float(prediction[0][0])

detector = MLTumorDetector(os.path.join(os.path.dirname(__file__), '../models/brain_tumor_model.h5'))
