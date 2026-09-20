import math
from typing import List, Tuple, Optional
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, snap
import numpy as np

class WallReconstructor:
    """
    مسئولیت: استانداردسازی زوایا، ادغام خطوط هم‌راستا، امتداد دادن و شکستن خطوط در نقاط تقاطع.
    تمام عملیات هندسی با استفاده از کتابخانه Shapely انجام می‌شود.
    """
    def __init__(self, angle_tolerance=10, merge_distance=15.0, extension_margin=50.0, min_segment_length=10.0):
        self.angle_tolerance = math.radians(angle_tolerance)
        self.merge_distance = merge_distance
        self.extension_margin = extension_margin
        self.min_segment_length = min_segment_length

    def process_lines(self, raw_lines: List[Tuple[float, float, float, float]]) -> List[Tuple[int, int, int, int]]:
        if not raw_lines:
            return []

        # 1. تبدیل به اشیاء Shapely و استانداردسازی زوایا
        standardized_lines = self._standardize_angles_shapely(raw_lines)
        
        # 2. ادغام خطوط هم‌راستا (Collinear)
        merged_lines = self._merge_collinear_shapely(standardized_lines)
        
        # 3. امتداد دادن، یافتن تقاطع‌ها و شکستن خطوط
        final_segments = self._extend_intersect_and_split(merged_lines)
        
        return final_segments

    def _standardize_angles_shapely(self, lines: List[Tuple[float, float, float, float]]) -> List[LineString]:
        standardized = []
        for x1, y1, x2, y2 in lines:
            dx = x2 - x1
            dy = y2 - y1
            angle = math.atan2(dy, dx)
            norm_angle = angle % math.pi
            
            # تعیین زاویه هدف (0, 45, 90, 135)
            target_angle = 0
            if abs(norm_angle - math.pi/2) < self.angle_tolerance or abs(norm_angle - math.pi/2) > (math.pi - self.angle_tolerance):
                target_angle = math.pi/2
            elif abs(norm_angle - math.pi/4) < self.angle_tolerance or abs(norm_angle - 3*math.pi/4) < self.angle_tolerance:
                target_angle = math.pi/4 if abs(norm_angle - math.pi/4) < self.angle_tolerance else 3*math.pi/4
            
            # بازسازی خط حول مرکز ثقل
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            length = math.hypot(dx, dy)
            
            new_x1 = cx - (length/2) * math.cos(target_angle)
            new_y1 = cy - (length/2) * math.sin(target_angle)
            new_x2 = cx + (length/2) * math.cos(target_angle)
            new_y2 = cy + (length/2) * math.sin(target_angle)
            
            standardized.append(LineString([(new_x1, new_y1), (new_x2, new_y2)]))
            
        return standardized

    def _merge_collinear_shapely(self, lines: List[LineString]) -> List[LineString]:
        if not lines: 
            return []
        
        merged = []
        used = [False] * len(lines)
        
        for i in range(len(lines)):
            if used[i]: 
                continue
            curr_line = lines[i]
            used[i] = True
            
            for j in range(i+1, len(lines)):
                if used[j]: 
                    continue
                
                # بررسی هم‌راستا بودن و نزدیکی
                if self._are_collinear_and_close(curr_line, lines[j]):
                    # ادغام با ایجاد یک LineString از تمام نقاط و سپس گرفتن convex hull یا ساده‌ترین مسیر
                    # روش ساده‌تر: ترکیب نقاط انتها و ساخت خط جدید بین دورترین نقاط
                    all_points = list(curr_line.coords) + list(lines[j].coords)
                    # پیدا کردن دو نقطه‌ای که بیشترین فاصله را دارند
                    best_pair = self._get_farthest_points(all_points)
                    curr_line = LineString([best_pair[0], best_pair[1]])
                    used[j] = True
                    
            merged.append(curr_line)
        return merged

    def _are_collinear_and_close(self, l1: LineString, l2: LineString) -> bool:
        # بررسی موازی بودن (زاویه مشابه)
        a1 = math.atan2(l1.coords[1][1] - l1.coords[0][1], l1.coords[1][0] - l1.coords[0][0])
        a2 = math.atan2(l2.coords[1][1] - l2.coords[0][1], l2.coords[1][0] - l2.coords[0][0])
        diff = min(abs(a1-a2), math.pi - abs(a1-a2))
        
        if diff > math.radians(5): # تلورانس سخت‌گیرانه‌تر برای ادغام
            return False
            
        # بررسی فاصله (یکی از نقاط خط دوم باید به خط اول نزدیک باشد)
        dist = l1.distance(Point(l2.coords[0]))
        return dist < self.merge_distance

    @staticmethod
    def _get_farthest_points(points: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        max_dist = 0
        best_pair = (points[0], points[1])
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                d = math.hypot(points[i][0] - points[j][0], points[i][1] - points[j][1])
                if d > max_dist:
                    max_dist = d
                    best_pair = (points[i], points[j])
        return best_pair

    def _extend_intersect_and_split(self, lines: List[LineString]) -> List[Tuple[int, int, int, int]]:
        if not lines:
            return []

        # 1. امتداد خطوط (Extension)
        extended_lines = []
        for line in lines:
            coords = list(line.coords)
            p1 = Point(coords[0])
            p2 = Point(coords[1])
            
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            length = math.hypot(dx, dy)
            
            if length < 1e-6: 
                continue
            
            ux, uy = dx/length, dy/length
            
            # محاسبه نقاط جدید با امتداد
            ex1 = p1.x - ux * self.extension_margin
            ey1 = p1.y - uy * self.extension_margin
            ex2 = p2.x + ux * self.extension_margin
            ey2 = p2.y + uy * self.extension_margin
            
            extended_lines.append(LineString([(ex1, ey1), (ex2, ey2)]))

        # 2. یافتن تمام تقاطع‌ها و شکستن خطوط (Splitting)
        # استفاده از unary_union برای یافتن تمام نقاط تقاطع به صورت خودکار
        # وقتی خطوط یکدیگر را قطع می‌کنند، union آن‌ها را در نقاط تقاطع می‌شکند
        
        # ابتدا همه خطوط را با هم متحد می‌کنیم. این کار باعث شکستن خطوط در نقاط تقاطع می‌شود
        # اما توجه داشته باشید که خطوط امتداد یافته ممکن است خیلی طولانی باشند و تقاطع‌های کاذب ایجاد کنند
        # بنابراین بهتر است از روش دستی‌تر اما دقیق‌تر استفاده کنیم یا از snap برای دقت بیشتر
        
        multi_line = unary_union(extended_lines)
        
        final_segments = []
        
        # اگر خروجی MultiLineString بود، آن را پیمایش می‌کنیم
        if multi_line.geom_type == 'LineString':
            segments_to_check = [multi_line]
        elif multi_line.geom_type == 'MultiLineString':
            segments_to_check = list(multi_line.geoms)
        else:
            return []

        for segment in segments_to_check:
            # بررسی طول حداقل
            if segment.length >= self.min_segment_length:
                coords = list(segment.coords)
                # گرد کردن به اعداد صحیح برای خروجی نهایی
                x1, y1 = int(round(coords[0][0])), int(round(coords[0][1]))
                x2, y2 = int(round(coords[1][0])), int(round(coords[1][1]))
                
                # اطمینان از اینکه خط صفر طول ندارد
                if x1 != x2 or y1 != y2:
                    final_segments.append((x1, y1, x2, y2))
                    
        return final_segments