# backend/app/core/sh3d_exporter.py
import xml.etree.ElementTree as ET
from typing import List, Tuple
import uuid
import zipfile
import io

class SH3DExporter:
    """
    Converts detected wall coordinates into a Sweet Home 3D (.sh3d) file.
    
    The .sh3d format is essentially a ZIP archive containing a single 'Home.xml' file.
    This exporter handles:
    1. XML structure generation compliant with SH3D v7.0+.
    2. Automatic wall connection detection (wallAtStart/wallAtEnd).
    3. ZIP packaging in memory for direct HTTP response.
    """

    WALL_HEIGHT = 250  # cm
    WALL_THICKNESS = 10  # cm

    def __init__(self):
        self.root = ET.Element("home")
        self.root.set("version", "5.2")
        
        # Create basic structure
        self.properties = ET.SubElement(self.root, "properties")
        self.walls_element = ET.SubElement(self.root, "walls")
        
    # def add_wall(self, wall: Wall):
    #     """Add a wall element to the XML structure."""
    #     wall_elem = ET.SubElement(self.walls_element, "wall")
    #     wall_elem.set("xStart", str(wall.x_start))
    #     wall_elem.set("yStart", str(wall.y_start))
    #     wall_elem.set("xEnd", str(wall.x_end))
    #     wall_elem.set("yEnd", str(wall.y_end))
    #     wall_elem.set("height", str(wall.height))
    #     wall_elem.set("thickness", str(wall.thickness))
        
    # def lines_to_walls(self, lines: List[Tuple[int, int, int, int]], scale: float = 1.0) -> List[Wall]:
    #     """Convert detected line segments to Wall objects with scaling."""
    #     walls = []
    #     for line in lines:
    #         # Invert Y axis because image coordinates (0,0 is top-left) 
    #         # differ from Sweet Home 3D (0,0 is bottom-left usually, but we can adjust)
    #         # For now, we just scale.
    #         walls.append(Wall(
    #             x_start=line.x1 * scale,
    #             y_start=line.y1 * scale,
    #             x_end=line.x2 * scale,
    #             y_end=line.y2 * scale,
    #             height=WALL_HEIGHT,
    #             thickness=WALL_THICKNESS
    #         ))
    #     return walls

    # def export_to_string(self) -> str:
    #     """Return the XML as a string."""
    #     return ET.tostring(self.root, encoding='unicode', xml_declaration=True)
    
    # def export_to_file(self, filename: str):
    #     """Save the XML to a file."""
    #     tree = ET.ElementTree(self.root)
    #     ET.indent(tree, space="  ")
    #     tree.write(filename, encoding='unicode', xml_declaration=True)

    def export_to_sh3d(self, lines: List[Tuple[int, int, int, int]], output_path: str) -> None:
        """
        Generates a .sh3d file from a list of wall segments.
        
        Args:
            lines: List of (x1, y1, x2, y2) tuples. Coordinates are treated as centimeters.
            output_path: Base path for the output (a .xml file is created temporarily during processing).
            
        Returns:
            bytes: The binary content of the .sh3d ZIP file.
        """

        root = ET.Element("home", {
            "version": "7000",
            "name": "map.sh3d",
            "camera":"topCamera",
            "wallHeight":"243.84"            
        })

        # --- Add UI Properties ---
        ui_properties = [
            ("com.eteks.sweethome3d.SweetHome3D.CatalogPaneDividerLocation", "364"),
            ("com.eteks.sweethome3d.SweetHome3D.ColumnWidths", "129,59,59,59,49"),
            ("com.eteks.sweethome3d.SweetHome3D.FrameHeight", "825"),
            ("com.eteks.sweethome3d.SweetHome3D.FrameWidth", "1121"),
            ("com.eteks.sweethome3d.SweetHome3D.FrameX", "320"),
            ("com.eteks.sweethome3d.SweetHome3D.FrameY", "187"),
            ("com.eteks.sweethome3d.SweetHome3D.PlanPaneDividerLocation", "729"),
            ("com.eteks.sweethome3d.SweetHome3D.PlanViewportX", "0"),
            ("com.eteks.sweethome3d.SweetHome3D.PlanViewportY", "0"),
            ("com.eteks.sweethome3d.SweetHome3D.ScreenHeight", "1032"),
            ("com.eteks.sweethome3d.SweetHome3D.ScreenWidth", "1920"),
        ]

        for name, value in ui_properties:
            ET.SubElement(root, "property", {"name": name, "value": value})

        # --- Add Furniture Visible Properties ---
        furniture_props = ["NAME", "WIDTH", "DEPTH", "HEIGHT", "VISIBLE"]
        for prop_name in furniture_props:
            ET.SubElement(root, "furnitureVisibleProperty", {"name": prop_name})

        # --- Add Environment ---
        ET.SubElement(root, "environment", {
            "groundColor": "00A8A8A8",
            "skyColor": "00CCE4FC",
            "lightColor": "00D0D0D0",
            "ceillingLightColor": "00D0D0D0", # Note: Keeping original typo 'ceilling' if required by SweetHome3D
            "photoWidth": "400",
            "photoHeight": "300",
            "photoAspectRatio": "VIEW_3D_RATIO",
            "photoQuality": "0",
            "videoWidth": "320",
            "videoAspectRatio": "RATIO_4_3",
            "videoQuality": "0",
            "videoFrameRate": "25"
        })

        # --- Add Compass ---
        ET.SubElement(root, "compass", {
            "x": "-100.0",
            "y": "50.0",
            "diameter": "100.0",
            "northDirection": "0.0",
            "longitude": "0.8975259",
            "latitude": "0.62259287",
            "timeZone": "Asia/Tehran"
        })

        # --- Add Observer Camera ---
        ET.SubElement(root, "observerCamera", {
            "attribute": "observerCamera",
            "lens": "PINHOLE",
            "x": "50.0",
            "y": "50.0",
            "z": "170.0",
            "yaw": "5.4977875",
            "pitch": "0.19634955",
            "fieldOfView": "1.0995575",
            "time": "1787659200000"
        })

        # --- Add Top Camera ---
        ET.SubElement(root, "camera", {
            "attribute": "topCamera",
            "lens": "PINHOLE",
            "x": "302.1099",
            "y": "1557.7703",
            "z": "1121.92",
            "yaw": "3.1415927",
            "pitch": "0.7853982",
            "fieldOfView": "1.0995575",
            "time": "1787659200000"
        })

        # --- PASS 1: Assign IDs and store data ---
        processed_lines = []
        for line in lines:
            x1, y1, x2, y2 = line
            # Ensure they are treated as integers if they aren't already
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            line_id = str(uuid.uuid4())
            processed_lines.append({
                "id": line_id,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "wall_at_start": None,
                "wall_at_end": None
            })

        # --- PASS 2: Find connections (Exact Match) ---
        # Note: We use exact integer matching because lines were already 
        # snapped and standardized in the LineExtractor phase.
        for i, current in enumerate(processed_lines):
            start_point = (current["x1"], current["y1"])
            end_point = (current["x2"], current["y2"])

            for j, other in enumerate(processed_lines):
                if i == j:
                    continue
                
                other_start = (other["x1"], other["y1"])
                other_end = (other["x2"], other["y2"])

                # Check if current START matches other's START or END
                if start_point == other_start or start_point == other_end:
                    current["wall_at_start"] = other["id"]

                # Check if current END matches other's START or END
                if end_point == other_start or end_point == other_end:
                    current["wall_at_end"] = other["id"]

        # --- PASS 3: Create XML Elements ---
        for line_data in processed_lines:
            attrs = {
                "id": line_data["id"],
                "xStart": str(line_data["x1"]),
                "yStart": str(line_data["y1"]),
                "xEnd": str(line_data["x2"]),
                "yEnd": str(line_data["y2"]),
                "height": str(self.WALL_HEIGHT),
                "thickness": str(self.WALL_THICKNESS)
            }

            if line_data["wall_at_start"]:
                attrs["wallAtStart"] = line_data["wall_at_start"]
            
            if line_data["wall_at_end"]:
                attrs["wallAtEnd"] = line_data["wall_at_end"]

            ET.SubElement(root, "wall", attrs)                

        # Write XML to file with proper formatting
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(output_path + ".xml", encoding="utf-8", xml_declaration=True)
        xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True)

        # 7. Create a ZIP file in memory with .sh3d extension
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Sweet Home 3D expects the main file to be named 'home.xml' inside the zip
            zip_file.writestr('Home.xml', xml_str)
        
        # Reset buffer position to the beginning
        zip_buffer.seek(0)
        
        return zip_buffer.getvalue()
