# image_processor.py
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import math

class ImageProcessor:
    """
    Handles initial image preprocessing for floor plan detection.
    
    Workflow:
    1. Adjusts brightness and contrast based on user input.
    2. Converts to grayscale and applies Gaussian blur to reduce noise.
    3. Uses Adaptive Thresholding to create a clean binary image for line detection.
    4. Applies morphological closing to fill small gaps in lines.
    """

    def __init__(self):
        # Preprocessing parameters
        self.adaptive_block_size = 11
        self.adaptive_c = 2

    def _adjust_brightness_contrast(self, img: np.ndarray, brightness: float, contrast: float) -> np.ndarray:
        """
        Adjusts image brightness and contrast.
        
        Args:
            img: Input BGR image.
            brightness: Brightness factor (1.0 is neutral).
            contrast: Contrast factor (1.0 is neutral).
            
        Returns:
            Adjusted image.
        """
        alpha = contrast
        beta = (brightness - 1.0) * 127
        return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        """
        Converts image to binary format suitable for Hough Line Transform.
        
        Args:
            img: Input BGR image.
            
        Returns:
            Binary image (black background, white lines).
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive thresholding handles varying lighting conditions better than global thresholding
        binary = cv2.adaptiveThreshold(
            blurred, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            self.adaptive_block_size, 
            self.adaptive_c
        )

        # Morphological closing to connect broken line segments
        kernel = np.ones((3,3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

        return binary

    def process_image(self, image_path: str, brightness: float = 1.0, contrast: float = 1.0) -> np.ndarray:
        """
        Main entry point for image processing.
        
        Args:
            image_path: Path to the input image file.
            brightness: Brightness adjustment factor.
            contrast: Contrast adjustment factor.
            
        Returns:
            Processed binary image.
            
        Raises:
            ValueError: If the image cannot be read.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")

        adjusted_img = self._adjust_brightness_contrast(img, brightness, contrast)
        binary = self._preprocess(adjusted_img)
        return binary
