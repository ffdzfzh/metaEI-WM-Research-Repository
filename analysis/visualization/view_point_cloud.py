import open3d as o3d
from pathlib import Path


def view_point_cloud(file_path):
    print(f"Reading point cloud: {file_path}")

    pcd = o3d.io.read_point_cloud(file_path)

    if pcd.is_empty():
        print("Unable to read the point cloud or the file is empty.")
        return

    print(f"Loaded {len(pcd.points)} points.")
    print("Press H for viewer shortcuts or Q to quit.")

    o3d.visualization.draw_geometries([pcd], window_name="PLY Point Cloud Viewer")


if __name__ == "__main__":

    repo_root = Path(__file__).resolve().parents[2]
    PLY_FILE_PATH = repo_root / "data" / "scene_models" / "scene3_show.ply"
    view_point_cloud(PLY_FILE_PATH)
