import open3d as o3d
import numpy as np
import os
from pathlib import Path


def get_eye_position(lookat: np.ndarray, distance: float, az_deg: float, el_deg: float) -> np.ndarray:
    """Convert MATLAB-style view angles to a camera eye position."""
    az = np.radians(az_deg)
    el = np.radians(el_deg)

    x = distance * np.cos(el) * np.cos(az)
    y = distance * np.cos(el) * np.sin(az)
    z = distance * np.sin(el)

    return lookat + np.array([x, y, z])


def visualize_obj_modern(obj_path: str, az: float = 45.0, el: float = 30.0):
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"File not found: {obj_path}")

    print("Loading the mesh and materials...")

    model = o3d.io.read_triangle_model(obj_path)

    if len(model.meshes) == 0:
        raise ValueError("The OBJ contains no valid faces. Export it with triangulated faces.")

    bbox = o3d.geometry.AxisAlignedBoundingBox()
    for mesh_info in model.meshes:
        mesh_info.mesh.compute_vertex_normals()
        bbox += mesh_info.mesh.get_axis_aligned_bounding_box()

    lookat = bbox.get_center()
    max_extent = np.max(bbox.get_extent())
    distance = max_extent * 1.5
    eye = get_eye_position(lookat, distance, az, el)
    up = [0.0, 1.0, 0.0]

    def save_high_res_screenshot(vis):
        print("Rendering a 3600 x 2700 image...")
        try:
            view_matrix = vis.scene.camera.get_view_matrix()
            c2w = np.linalg.inv(view_matrix)
            current_eye = c2w[0:3, 3]
            current_forward = -c2w[0:3, 2]
            current_up = c2w[0:3, 1]
            current_lookat = current_eye + current_forward

            try:
                fov = vis.scene.camera.get_field_of_view()
            except:
                fov = 60.0

            width, height = 1200 * 3, 900 * 3
            render = o3d.visualization.rendering.OffscreenRenderer(width, height)

            render.scene.set_background(np.array([1.0, 1.0, 1.0, 1.0]))
            render.scene.scene.enable_sun_light(False)
            render.scene.scene.enable_indirect_light(True)
            render.scene.scene.set_indirect_light_intensity(45000.0)

            # render.scene.scene.add_directional_light(
            #     "front_light",
            # )

            render.scene.add_model("model", model)
            render.setup_camera(fov, current_lookat, current_eye, current_up)

            img = render.render_to_image()
            img_np = np.asarray(img).copy()

            mask = (img_np[:, :, 0] > 240) & (img_np[:, :, 1] > 240) & (img_np[:, :, 2] > 240)
            if img_np.shape[2] == 4:
                img_np[mask, :3] = [255, 255, 255]
                img_np[mask, 3] = 255
            else:
                img_np[mask] = [255, 255, 255]

            final_img = o3d.geometry.Image(img_np)
            base_name = os.path.splitext(os.path.basename(obj_path))[0]
            out_file = f"{base_name}_az{az}_el{el}_PaperReady.png"
            o3d.io.write_image(out_file, final_img)
            print(f"High-resolution image saved to: {out_file}\n")

        except Exception as e:
            print(f"Save failed: {e}")

    print("=====================================================")
    print(f" Viewer started at camera view view({az}, {el})")
    print(" Instructions:")
    print("    - The interactive view uses the configured materials and colors.")
    print("    - Use Custom Actions -> Save Paper-Ready High-Res to export an image.")
    print("    - The export uses a 3600 x 2700 canvas with a white background.")
    print("=====================================================")

    o3d.visualization.draw(
        geometry=model,
        title="Scientific OBJ Viewer (Paper Ready)",
        width=1200,
        height=900,
        bg_color=[1.0, 1.0, 1.0, 1.0],
        eye=eye,
        lookat=lookat,
        up=up,
        show_ui=True,
        actions=[("Save Paper-Ready High-Res", save_high_res_screenshot)]
    )


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    OBJ_FILE_PATH = repo_root / "data" / "scene_models" / "scene1.obj"

    # scene1
    visualize_obj_modern(
        obj_path=OBJ_FILE_PATH,
        az=75.0,
        el=25.0
    )

    # # scene2
    # visualize_obj_modern(
    #     obj_path=OBJ_FILE_PATH,
    # )

    # # scene3
    # visualize_obj_modern(
    #     obj_path=OBJ_FILE_PATH,
    # )
