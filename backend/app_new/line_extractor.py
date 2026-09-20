import cv2
import numpy as np
from typing import List, Tuple

class LineExtractor:
    """
    مسئولیت: تبدیل تصویر باینری به لیستی از خطوط خام با استفاده از HoughLinesP.
    """
    def __init__(self, hough_threshold=40, min_line_length=20, max_line_gap=25):
        self.hough_threshold = hough_threshold
        self.min_line_length = min_line_length
        self.max_line_gap = max_line_gap

    def detect_lines(self, binary_img: np.ndarray) -> List[Tuple[float, float, float, float]]:
        lines = cv2.HoughLinesP(
            binary_img, rho=1, theta=np.pi / 180,
            threshold=self.hough_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap
        )
        if lines is None: 
            return []
        
        result = []
        for line in lines:
            coords = line[0] if isinstance(line[0], (list, tuple, np.ndarray)) else line
            try:
                x1, y1, x2, y2 = float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])
                result.append((x1, y1, x2, y2))
            except: 
                continue
        return result