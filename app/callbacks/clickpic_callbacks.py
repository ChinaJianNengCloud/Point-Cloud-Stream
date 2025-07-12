from PySide6.QtCore import QTimer, Qt
from typing import TYPE_CHECKING

from app.utils.logger import setup_logger
import open3d as o3d
import numpy as np
import vtk
import cv2
from PySide6.QtGui import QImage, QPixmap


logger = setup_logger(__name__)

if TYPE_CHECKING:
    from app.entry import PCDStreamer

def project_pixel_to_3d(u, v, depth_np, intrinsic, extrinsic, depth_scale):
    z = depth_np[v, u] / depth_scale
    if z <= 0:
        return None
    fx, fy = intrinsic[0][0], intrinsic[1][1]
    cx, cy = intrinsic[0][2], intrinsic[1][2]
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy
    point_cam = np.array([x, y, z, 1.0])
    point_world = extrinsic @ point_cam
    return point_world[:3]

def on_test_color_clicked(main_window: "PCDStreamer", click_data: dict):
    relative_x = click_data.get('relative_x', 0.0)
    relative_y = click_data.get('relative_y', 0.0)
    frame = click_data.get('frame_data', {})
    pic_width = click_data.get('true_pic_width', 1)
    pic_height = click_data.get('true_pic_hight', 1)

    u = int(relative_x * pic_width)
    v = int(relative_y * pic_height)
    logger.info(f"[点击像素] u={u}, v={v}")

    pcd: o3d.geometry.PointCloud = frame.get('pcd')
    pixel_to_index: dict = frame.get('pixel_to_index', {})
    points = np.asarray(pcd.points) if pcd else []

    point3d = None
    idx = pixel_to_index.get((u, v), -1)

    if idx != -1 and 0 <= idx < len(points):
        point3d = points[idx]
        logger.info(f"[点云命中] index={idx}, point={point3d}")
    else:
        logger.info(f"[点云未命中] fallback to depth-based 3D reconstruction")

        depth_np = frame.get('depth_np')
        intrinsic = np.array(frame.get('intrinsic'))
        extrinsic = np.array(frame.get('extrinsic'))
        depth_scale = frame.get('depth_scale', 1000.0)

        point3d = project_pixel_to_3d(u, v, depth_np, intrinsic, extrinsic, depth_scale)

        if point3d is None:
            logger.warning("点击位置无有效深度")
            return

        logger.info(f"[还原3D点] {point3d}")

    if main_window:
        main_window.mark_point_on_test_depth(relative_x, relative_y)
        main_window.add_point_to_vtk_from_relative(point3d, frame)
