import open3d as o3d
import numpy as np
import re
import copy
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List

RECT_NORMAL_MARGIN = 0.1
WALL_COLOR = np.array([0.75, 0.75, 0.75])
FLOOR_COLOR = np.array([0.85, 0.85, 0.85])


@dataclass
class ParsedObject:
    category: str
    center: np.ndarray
    extent: np.ndarray
    rotation_z: float
    raw_id: str


BBOX_CATEGORIES = [
    "sofa", "chair", "stairway", "plateform", "dining_chair", "bar_chair", "stool", "bed",
    "pillow", "wardrobe", "nightstand", "tv_cabinet", "wine_cabinet", "bathroom_cabinet",
    "shoe_cabinet", "entrance_cabinet", "decorative_cabinet", "washing_cabinet", "wall_cabinet",
    "sideboard", "cupboard", "coffee_table", "dining_table", "side_table", "dressing_table",
    "desk", "integrated_stove", "gas_stove", "range_hood", "micro-wave_oven", "sink", "stove",
    "refrigerator", "hand_sink", "shower", "shower_room", "toilet", "tub", "illumination",
    "chandelier", "floor-standing_lamp", "wall_decoration", "painting", "curtain", "carpet",
    "plants", "potted_bonsai", "tv", "computer", "air_conditioner", "washing_machine",
    "clothes_rack", "mirror", "bookcase", "cushion", "bar", "screen", "combination_sofa",
    "dining_table_combination", "leisure_table_and_chair_combination", "multifunctional_combination_bed"
]


def get_color_mapping() -> Dict[str, np.ndarray]:
    np.random.seed(42)
    color_map = {}
    for cat in BBOX_CATEGORIES:
        color_map[cat] = np.random.uniform(0.2, 0.9, 3)

    color_map['door'] = np.array([0.55, 0.27, 0.07])
    color_map['window'] = np.array([0.53, 0.81, 0.92])
    color_map['wall'] = WALL_COLOR
    return color_map


def parse_txt_to_objects(txt_path: str) -> List[ParsedObject]:
    objects = []
    walls_dict = {}
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    pattern = re.compile(r"([^=]+)=([A-Za-z]+)\((.*)\)")

    # Pass 1: Wall
    for line in lines:
        line = line.strip()
        if not line: continue
        match = pattern.match(line)
        if not match: continue
        obj_id, obj_type, args_str = match.groups()
        args = [x.strip() for x in args_str.split(',')]
        if obj_type == "Wall":
            ax, ay, az = float(args[0]), float(args[1]), float(args[2])
            bx, by, bz = float(args[3]), float(args[4]), float(args[5])
            h = float(args[6])
            dx, dy = bx - ax, by - ay
            length = np.sqrt(dx ** 2 + dy ** 2)
            angle = np.arctan2(dy, dx)
            cx, cy, cz = (ax + bx) / 2, (ay + by) / 2, az + h / 2
            extent = np.array([length, RECT_NORMAL_MARGIN * 2, h])
            obj = ParsedObject("wall", np.array([cx, cy, cz]), extent, angle, obj_id)
            walls_dict[obj_id] = obj
            objects.append(obj)

    # Pass 2: Others
    for line in lines:
        line = line.strip()
        if not line: continue
        match = pattern.match(line)
        if not match: continue
        obj_id, obj_type, args_str = match.groups()
        args = [x.strip() for x in args_str.split(',')]
        if obj_type == "Wall":
            continue
        elif obj_type in ["Door", "Window"]:
            parent_id = args[0]
            px, py, pz = float(args[1]), float(args[2]), float(args[3])
            w, h = float(args[4]), float(args[5])
            if parent_id in walls_dict:
                angle = walls_dict[parent_id].rotation_z
                extent = np.array([w, RECT_NORMAL_MARGIN * 2, h])
                cat = "door" if obj_type == "Door" else "window"
                objects.append(ParsedObject(cat, np.array([px, py, pz]), extent, angle, obj_id))
        elif obj_type == "Bbox":
            cat_name = args[0]
            px, py, pz = float(args[1]), float(args[2]), float(args[3])
            angle = float(args[4])
            sx, sy, sz = float(args[5]), float(args[6]), float(args[7])
            objects.append(ParsedObject(cat_name, np.array([px, py, pz]), np.array([sx, sy, sz]), angle, obj_id))
    return objects


def get_rotation_matrix_z(angle_z: float) -> np.ndarray:
    cos_a, sin_a = np.cos(angle_z), np.sin(angle_z)
    return np.array([[cos_a, -sin_a, 0], [sin_a, cos_a, 0], [0, 0, 1]])


def process_point_cloud(ply_path: str, txt_path: str, floor_z_threshold: float = 0.0) -> o3d.geometry.PointCloud:
    pcd = o3d.io.read_point_cloud(ply_path)
    if pcd.is_empty():
        raise ValueError("Unable to read the point cloud; check the file path.")

    points = np.asarray(pcd.points)
    colors = np.ones_like(points) * WALL_COLOR

    floor_indices = np.where(points[:, 2] < floor_z_threshold)[0]
    colors[floor_indices] = FLOOR_COLOR

    objects = parse_txt_to_objects(txt_path)
    color_map = get_color_mapping()
    pcd_points_vec = o3d.utility.Vector3dVector(points)

    bboxes = [obj for obj in objects if obj.category not in ["wall", "door", "window"]]
    walls = [obj for obj in objects if obj.category == "wall"]
    doors_windows = [obj for obj in objects if obj.category in ["door", "window"]]

    def apply_colors(obj_list: List[ParsedObject]):
        for obj in obj_list:
            if obj.category not in color_map: continue
            R = get_rotation_matrix_z(obj.rotation_z)
            obb = o3d.geometry.OrientedBoundingBox(obj.center, R, obj.extent)
            indices = obb.get_point_indices_within_bounding_box(pcd_points_vec)
            colors[indices] = color_map[obj.category]

    apply_colors(bboxes)
    apply_colors(walls)
    apply_colors(doors_windows)

    pcd_colored = copy.deepcopy(pcd)
    pcd_colored.colors = o3d.utility.Vector3dVector(colors)
    return pcd_colored


def get_front_from_view(azimuth_deg: float, elevation_deg: float) -> list:
    """Convert MATLAB-style view angles to an Open3D front vector."""
    az = np.radians(azimuth_deg)
    el = np.radians(elevation_deg)

    x = np.cos(el) * np.cos(az)
    y = np.cos(el) * np.sin(az)
    z = np.sin(el)
    return [x, y, z]


def visualize_comparison_scientific(ply_path: str, txt_path: str, floor_z: float = 0.0, az: float = 45.0,
                                    el: float = 30.0):
    pcd_orig = o3d.io.read_point_cloud(ply_path)
    pcd_colored = process_point_cloud(ply_path, txt_path, floor_z_threshold=floor_z)

    window_width, window_height = 1200, 900
    target_width, target_height = 3600, 2700

    vis1 = o3d.visualization.VisualizerWithKeyCallback()
    vis1.create_window(window_name="Original Point Cloud (Press 'S' to Save)",
                       width=window_width, height=window_height, left=0, top=0)
    vis1.add_geometry(pcd_orig)

    vis2 = o3d.visualization.VisualizerWithKeyCallback()
    vis2.create_window(window_name="Segmented & Colored (Press 'S' to Save)",
                       width=window_width, height=window_height, left=window_width, top=0)
    vis2.add_geometry(pcd_colored)

    def save_image_high_res(vis, filename):

        print(f"Capturing a high-resolution image...")

        vis.poll_events()
        vis.update_renderer()

        image = vis.capture_screen_float_buffer(do_render=True)

        img_np = (np.asarray(image) * 255).astype(np.uint8)

        try:
            from PIL import Image
            img = Image.fromarray(img_np)
            if img.size != (target_width, target_height):
                img = img.resize((target_width, target_height), Image.LANCZOS)
            img.save(filename, quality=100)
            print(f"High-resolution image saved: {filename} (resolution: {target_width}x{target_height})")
        except ImportError:
            vis.capture_screen_image(filename)
            print(f"Pillow is unavailable; saved at the native window resolution: {filename}")

    def save_image_vis1(vis):
        save_image_high_res(vis, "original_high_res.png")
        return False

    def save_image_vis2(vis):
        save_image_high_res(vis, "colored_high_res.png")
        return False

    vis1.register_key_callback(83, save_image_vis1)
    vis2.register_key_callback(83, save_image_vis2)

    front_vector = get_front_from_view(az, el)

    for vis, pcd in [(vis1, pcd_orig), (vis2, pcd_colored)]:
        opt = vis.get_render_option()
        opt.background_color = np.asarray([1.0, 1.0, 1.0])
        opt.point_size = 2.0
        opt.light_on = False

        ctr = vis.get_view_control()
        ctr.set_lookat(pcd.get_axis_aligned_bounding_box().get_center())
        ctr.set_front(front_vector)
        ctr.set_up([0.0, 0.0, 1.0])
        ctr.set_zoom(0.7)

    while True:
        if not vis1.poll_events() or not vis2.poll_events():
            break
        vis1.update_renderer()
        vis2.update_renderer()

    vis1.destroy_window()
    vis2.destroy_window()


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    PLY_FILE_PATH = repo_root / "data" / "scene_models" / "scene3_show.ply"
    TXT_FILE_PATH = repo_root / "data" / "scene_models" / "scene3.txt"

    FLOOR_Z_VALUE = 0

    # # scene1
    # visualize_comparison_scientific(
    #     PLY_FILE_PATH,
    #     TXT_FILE_PATH,
    #     floor_z=FLOOR_Z_VALUE,
    # )

    # # scene2
    # visualize_comparison_scientific(
    #     PLY_FILE_PATH,
    #     TXT_FILE_PATH,
    #     floor_z=FLOOR_Z_VALUE,
    # )

    # scene3
    visualize_comparison_scientific(
        PLY_FILE_PATH,
        TXT_FILE_PATH,
        floor_z=FLOOR_Z_VALUE,
        az=-45,
        el=30.0
    )
