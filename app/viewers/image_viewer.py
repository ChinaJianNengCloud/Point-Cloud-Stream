import sys
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel,
                               QPushButton, QHBoxLayout, QMessageBox, QSizePolicy)
from PySide6.QtGui import QPixmap, QResizeEvent, QMouseEvent
from PySide6.QtCore import Qt, Signal, QTimer
import numpy as np 
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
class ResizableImageLabel(QLabel):
    """Custom QLabel that automatically resizes the image to fit the widget while maintaining aspect ratio."""
    
    clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)  # Prevent the label from becoming too small
        self.original_pixmap = None
        self.setScaledContents(False)  # We'll handle scaling manually
        self.frame_data = None

    def set_frame(self, frame: dict):
        """手动设置当前帧数据，用于点击时返回完整 frame"""
        self.frame_data = frame

    def setPixmap(self, pixmap):
        self.original_pixmap = pixmap
        if self.original_pixmap:
            self.update_scaled_pixmap()

    def resizeEvent(self, event):
        if self.original_pixmap:
            self.update_scaled_pixmap()
        super().resizeEvent(event)

    def update_scaled_pixmap(self):
        scaled_pixmap = self.original_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        super().setPixmap(scaled_pixmap)
    #根据scale重新计算图片的xy
    def mousePressEvent(self, event: QMouseEvent):
        if not self.original_pixmap:
            return

        # color_img = self.frame_data.get('color', None)
        # if color_img is not None:
        #     color_np = np.asarray(color_img)
        #     raw_h, raw_w = color_np.shape[:2]
        #     print(f"[Open3D 原始 color 图尺寸] width: {raw_w}, height: {raw_h}")

        # 假的?
        pixmap_width = self.original_pixmap.width()
        pixmap_height = self.original_pixmap.height()
        print(f"[QPixmap 尺寸] width: {pixmap_width}, height: {pixmap_height}")

        # 控件内部大小
        widget_width = self.width()
        widget_height = self.height()
        print(f"[控件尺寸] widget width: {widget_width}, height: {widget_height}")

        scaled_pixmap = self.original_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        display_width = scaled_pixmap.width()
        display_height = scaled_pixmap.height()
        print(f"[缩放后显示尺寸] scaled width: {display_width}, height: {display_height}")

        offset_x = (widget_width - display_width) // 2
        offset_y = (widget_height - display_height) // 2
        print(f"[偏移量] offset_x: {offset_x}, offset_y: {offset_y}")
        click_x = event.position().x()
        click_y = event.position().y()
        print(f"[dangqianzuob: {click_x }, height: {click_y }")
        if not (offset_x <= click_x <= offset_x + display_width and
                offset_y <= click_y <= offset_y + display_height):
            return
        pic_x = click_x - offset_x
        pic_y = click_y - offset_y  
        # 计算点击点在图像中的相对比例
        relative_x = (click_x - offset_x) / display_width
        relative_y = (click_y - offset_y) / display_height

        click_data = {
            'type': 'image_click',
            'version': 1.0,
            'source': 'color_view' if 'color' in (self.frame_data or {}) else 'depth_view',
            'relative_x': relative_x,
            'relative_y': relative_y,
            'frame_data': self.frame_data,  # 原始帧数据
            'display_width': display_width,
            'display_height': display_height,
            'true_pic_hight' : 720,
            'true_pic_width' : 1280,
        }
        print(f"[点击比例] relative_x: {relative_x:.3f}, relative_y: {relative_y:.3f}")

        # 发出点击信号
        self.clicked.emit(click_data)







class ImageConfirmationDialog(QDialog):
    def __init__(self, image_path, notice_text, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Confirm Action")

        self.image_path = image_path
        self.notice_text = notice_text
        self.original_pixmap = QPixmap(self.image_path) # Store original for aspect ratio

        if self.original_pixmap.isNull():
            QMessageBox.critical(self, "Error", f"Could not load image: {self.image_path}")
            self.reject()
            return

        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)

        # Image Label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.update_pixmap()  # Initial pixmap setup
        main_layout.addWidget(self.image_label)

        # Notice Text Label
        self.notice_label = QLabel(self.notice_text)
        self.notice_label.setWordWrap(True)
        self.notice_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.notice_label)

        # Button Layout (Confirm and Cancel)
        button_layout = QHBoxLayout()

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        # Set Dialog Properties
        self.setLayout(main_layout)
        self.setMinimumWidth(300)

    def resizeEvent(self, event):
        # Override the resize event to update the pixmap when the dialog is resized
        self.update_pixmap()
        super().resizeEvent(event)

    def update_pixmap(self):
        # Get the current size of the label
        label_size = self.image_label.size()

        # Calculate the scaled size while preserving aspect ratio
        original_size = self.original_pixmap.size()
        scaled_size = original_size.scaled(label_size, Qt.AspectRatioMode.KeepAspectRatio)

        # Create a scaled pixmap
        scaled_pixmap = self.original_pixmap.scaled(scaled_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # Set the pixmap on the label
        self.image_label.setPixmap(scaled_pixmap)


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     dialog = ImageConfirmationDialog("image.jpg", "Are you sure you want to proceed?")
#     dialog.exec()
#     sys.exit(app.exec())