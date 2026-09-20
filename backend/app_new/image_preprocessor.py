import cv2
import numpy as np

class ImagePreprocessor:
    """
    مسئولیت: خواندن تصویر، اصلاح نور و کنتراست، و تولید تصویر باینری.
    """
    def __init__(self, adaptive_block_size=11, adaptive_c=2):
        self.adaptive_block_size = adaptive_block_size
        self.adaptive_c = adaptive_c

    def load_and_adjust(self, image_path: str, brightness: float = 1.0, contrast: float = 1.0) -> np.ndarray:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
        return self._adjust_brightness_contrast(img, brightness, contrast)

    def preprocess_to_binary(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            self.adaptive_block_size, 
            self.adaptive_c
        )
        # عملیات مورفولوژی برای بستن شکاف‌های کوچک
        kernel = np.ones((3,3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        return binary

    @staticmethod
    def _adjust_brightness_contrast(img: np.ndarray, brightness: float, contrast: float) -> np.ndarray:
        alpha = contrast
        beta = (brightness - 1.0) * 127
        return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)