# backend/app/core/image/line_extractor.py
"""
Line Extraction Module for Floor Plan Digitization.

This module uses OpenCV to detect, standardize, and reconstruct architectural lines
from hand-drawn images. It enforces strict angular constraints (0, 45, 90 degrees)
and uses geometric intersection logic to create a connected wall graph.
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import math
import logging

logger = logging.getLogger(__name__)

class LineExtractor:
    """
    Advanced line extraction pipeline for architectural floor plans.
    
    This class implements a multi-stage algorithm to convert raw edge detections 
    into a structured network of walls:
    1. Standardization: Snaps lines to strict architectural angles (0°, 45°, 90°).
    2. Merging: Combines collinear segments to reduce noise.
    3. Topology: Extends lines to find intersections and rebuilds the wall network.
    """

    def __init__(self):
        self.adaptive_block_size = 11
        self.adaptive_c = 2
        self.hough_threshold = 40
        self.min_line_length = 20
        self.max_line_gap = 25
        self.merge_distance = 15.0
        self.angle_tolerance = 10
        self.extension_margin = 50.0    # Pixels to extend lines for intersection finding
        self.min_segment_length = 10.0  # Minimum length for a final wall segment

    def _detect_lines(self, binary_img: np.ndarray) -> List[Tuple[float, float, float, float]]:
        """Detects raw line segments using the Probabilistic Hough Transform."""
        lines = cv2.HoughLinesP(
            binary_img, rho=1, theta=np.pi / 180,
            threshold=self.hough_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap
        )
        if lines is None: return []
        
        result = []
        for line in lines:
            coords = line[0] if isinstance(line[0], (list, tuple, np.ndarray)) else line
            try:
                x1, y1, x2, y2 = float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])
                result.append((x1, y1, x2, y2))
            except: continue
        return result

    def _standardize_angles(self, lines: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float, float, float]]:
        """
        Projects detected lines to the nearest valid architectural angle.
        
        Hand-drawn lines often have slight deviations. This method ensures all 
        walls align with 0°, 45°, 90°, or 135° to facilitate room detection later.
        """
        standardized = []
        tol = math.radians(self.angle_tolerance)
        
        for x1, y1, x2, y2 in lines:
            dx = x2 - x1
            dy = y2 - y1
            angle = math.atan2(dy, dx)
            
            # Normalize the angle between 0 and pi
            norm_angle = angle % math.pi
            
            # Determine target angle based on tolerance
            target_angle = 0
            if abs(norm_angle - math.pi/2) < tol or abs(norm_angle - math.pi/2) > (math.pi - tol):
                target_angle = math.pi/2 # Vertical
            elif abs(norm_angle - math.pi/4) < tol or abs(norm_angle - 3*math.pi/4) < tol:
                target_angle = math.pi/4 if abs(norm_angle - math.pi/4) < tol else 3*math.pi/4 # Diagonal
            else:
                target_angle = 0 # Horizontal

            # Reconstruct line around its centroid
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            length = math.hypot(dx, dy)
            
            new_x1 = cx - (length/2) * math.cos(target_angle)
            new_y1 = cy - (length/2) * math.sin(target_angle)
            new_x2 = cx + (length/2) * math.cos(target_angle)
            new_y2 = cy + (length/2) * math.sin(target_angle)
            
            standardized.append((new_x1, new_y1, new_x2, new_y2))
            
        return standardized

    def _merge_collinear_lines(self, lines: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float, float, float]]:
        if not lines: return []
        merged = []
        used = [False] * len(lines)
        
        for i in range(len(lines)):
            if used[i]: continue
            curr = list(lines[i])
            used[i] = True
            
            for j in range(i+1, len(lines)):
                if used[j]: continue
                if self._are_similar(curr, lines[j]):
                    curr = self._extend_line(curr, lines[j])
                    used[j] = True
            merged.append(tuple(curr))
        return merged

    def _extend_and_rebuild(self, lines: List[Tuple[float, float, float, float]]) -> List[Tuple[int, int, int, int]]:
        """
        الگوریتم ساده‌سازی شده:
        1. امتداد خطوط
        2. یافتن تقاطع‌ها و ذخیره در دیکشنری
        3. شکستن خطوط فقط بین نقاط تقاطع (حذف خودکار بخش‌های اضافی ابتدا و انتها)
        """
        if not lines:
            return []

        # 1. امتداد خطوط (Extension)
        extended_lines = []
        for l in lines:
            x1, y1, x2, y2 = l
            dx = x2 - x1
            dy = y2 - y1
            length = math.hypot(dx, dy)
            if length < 1e-6: continue
            
            ux, uy = dx/length, dy/length
            # امتداد به میزان margin از دو طرف
            ex1 = x1 - ux * self.extension_margin
            ey1 = y1 - uy * self.extension_margin
            ex2 = x2 + ux * self.extension_margin
            ey2 = y2 + uy * self.extension_margin
            
            extended_lines.append((ex1, ey1, ex2, ey2))

        # 2. یافتن تقاطع‌ها و ذخیره در دیکشنری {index: [points]}
        n = len(extended_lines)
        # استفاده از دیکشنری برای نگهداری نقاط تقاطع هر خط
        intersections_map: Dict[int, List[Tuple[float, float]]] = {i: [] for i in range(n)}
        
        for i in range(n):
            for j in range(i + 1, n):
                inter = self._solve_line_intersection(extended_lines[i], extended_lines[j])
                if inter is None: continue
                
                ix, iy = inter
                
                # بررسی اینکه آیا نقطه تقاطع واقعاً روی پاره‌خط امتداد یافته قرار دارد؟
                # با توجه به امتداد زیاد، تقریباً همه تقاطع‌های ریاضی معتبر خواهند بود
                # مگر اینکه خطوط موازی باشند (که قبلاً چک شده) یا خیلی دور باشند.
                if self._is_point_on_segment(ix, iy, extended_lines[i]) and \
                   self._is_point_on_segment(ix, iy, extended_lines[j]):
                    intersections_map[i].append((ix, iy))
                    intersections_map[j].append((ix, iy))

        # 3. شکستن خطوط و تولید خروجی نهایی
        final_segments = []
        
        for i in range(n):
            points = intersections_map[i]
            
            # اگر خطی کمتر از 2 نقطه تقاطع داشته باشد، یعنی به جایی وصل نشده است
            # (یا فقط یک نقطه دارد که نمی‌توان پاره‌خط ساخت). این خطوط حذف می‌شوند.
            if len(points) < 2:
                continue

            # مرتب‌سازی نقاط بر اساس فاصله از ابتدای خط امتداد یافته
            # این کار تضمین می‌کند که نقاط به ترتیب روی خط قرار می‌گیرند
            ex1, ey1, _, _ = extended_lines[i]
            points.sort(key=lambda p: math.hypot(p[0] - ex1, p[1] - ey1))
            
            # حذف نقاط تکراری (با تلورانس بسیار کم برای جلوگیری از خطای اعشاری)
            unique_points = [points[0]]
            for p in points[1:]:
                last = unique_points[-1]
                if math.hypot(p[0]-last[0], p[1]-last[1]) > 0.5:
                    unique_points.append(p)
            
            # ایجاد پاره‌خط‌ها بین نقاط متوالی
            # نکته مهم: ما فقط بین نقاط تقاطع خط می‌کشیم.
            # این کار به طور خودکار "تکه اول و آخر" که خارج از شبکه دیوارها هستند را حذف می‌کند.
            for k in range(len(unique_points) - 1):
                p1 = unique_points[k]
                p2 = unique_points[k+1]
                
                # گرد کردن نهایی به اعداد صحیح
                ix1, iy1 = int(round(p1[0])), int(round(p1[1]))
                ix2, iy2 = int(round(p2[0])), int(round(p2[1]))
                
                seg_len = math.hypot(ix2-ix1, iy2-iy1)
                
                # فیلتر خطوط خیلی کوتاه (نویز)
                if seg_len >= self.min_segment_length:
                    final_segments.append((ix1, iy1, ix2, iy2))

        return final_segments

    @staticmethod
    def _solve_line_intersection(l1, l2) -> Optional[Tuple[float, float]]:
        """
        Calculates the exact intersection point of two infinite lines.
        
        Uses the parametric line equation. Returns None if lines are parallel.
        """
        x1, y1, x2, y2 = l1
        x3, y3, x4, y4 = l2
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None 
            
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        
        return (ix, iy)

    @staticmethod
    def _is_point_on_segment(px: float, py: float, seg: Tuple[float, float, float, float]) -> bool:
        x1, y1, x2, y2 = seg
        dx, dy = x2 - x1, y2 - y1
        len_sq = dx*dx + dy*dy
        if len_sq == 0: return False
        
        t = ((px - x1) * dx + (py - y1) * dy) / len_sq
        # اجازه می‌دهیم کمی خارج از بازه باشد (به خاطر خطای اعشاری و امتداد)
        return -0.01 <= t <= 1.01

    def _are_similar(self, l1, l2) -> bool:
        a1 = math.atan2(l1[3]-l1[1], l1[2]-l1[0])
        a2 = math.atan2(l2[3]-l2[1], l2[2]-l2[0])
        diff = min(abs(a1-a2), math.pi - abs(a1-a2))
        if diff > math.radians(5): return False
        dist = self._point_to_line_distance(l2[0], l2[1], l1[0], l1[1], l1[2], l1[3])
        return dist < self.merge_distance

    @staticmethod
    def _point_to_line_distance(px, py, x1, y1, x2, y2) -> float:
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0: return math.hypot(px - x1, py - y1)
        return abs(dy * px - dx * py + x2 * y1 - y2 * x1) / math.hypot(dx, dy)

    @staticmethod
    def _extend_line(line1, line2) -> list:
        """
        Creates a new line segment that encompasses two collinear lines.
        
        Returns the coordinates of the two furthest endpoints.
        """
        points = [
            (line1[0], line1[1]), (line1[2], line1[3]),
            (line2[0], line2[1]), (line2[2], line2[3])
        ]
        max_dist = 0
        best_pair = (points[0], points[1])
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                d = math.hypot(points[i][0] - points[j][0], points[i][1] - points[j][1])
                if d > max_dist:
                    max_dist = d
                    best_pair = (points[i], points[j])
        return [best_pair[0][0], best_pair[0][1], best_pair[1][0], best_pair[1][1]]

    def process_line(self, image_path: str, brightness: float = 1.0, contrast: float = 1.0) -> List[Tuple[int, int, int, int]]:
        """
        Main entry point for processing an image file.
        
        Args:
            image_path: Path to the input image.
            brightness: Brightness adjustment factor.
            contrast: Contrast adjustment factor.
            
        Returns:
            List of standardized wall segments as (x1, y1, x2, y2) tuples.
        """
        # Note: Importing here to avoid circular dependency if ImageProcessor 
        # depends on LineExtractor in other contexts.
        from backend.app.core.image.preprocessor import ImageProcessor
        _ip = ImageProcessor()
        binary_img = _ip.process_image(image_path, brightness, contrast)

        raw_lines = self._detect_lines(binary_img)

        if not raw_lines:
            return []
        # VISUAL DEBUG STEP
        # return raw_lines

        # 1. Standardize angles to architectural norms (0, 45, 90, 135)
        standardized_lines = self._standardize_angles(raw_lines)
        # VISUAL DEBUG STEP
        # return standardized_lines
        
        # 2. Merge collinear lines to reduce fragmentation
        merged_lines = self._merge_collinear_lines(standardized_lines)
        # VISUAL DEBUG STEP
        # return merged_lines
        
        # 3. Extend lines, find intersections, and rebuild the wall graph
        final_segments = self._extend_and_rebuild(merged_lines)
        
        return final_segments
