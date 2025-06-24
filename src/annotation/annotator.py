import sys
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QListWidget, QPushButton, QHBoxLayout,
                             QFileDialog, QListWidgetItem, QMessageBox,
                             QAbstractItemView, QFrame, QStyle, QAction)
from PyQt5.QtGui import (QPixmap, QPainter, QPen, QColor, QFont,
                         QKeySequence)
from PyQt5.QtCore import (Qt, QPoint, QRect, QSize, QPointF)

DARK_STYLESHEET = """
QWidget { background-color: #2b2b2b; color: #f0f0f0; font-size: 14px; }
QMainWindow { border: 1px solid #1e1e1e; }
QPushButton { background-color: #3c3f41; border: 1px solid #4a4d4f; padding: 8px; border-radius: 4px; }
QPushButton:hover { background-color: #4a4d4f; }
QPushButton:pressed { background-color: #525557; }
QListWidget { background-color: #3c3f41; border: 1px solid #4a4d4f; border-radius: 4px; padding: 5px; }
QListWidget::item { padding: 8px; }
QListWidget::item:selected { background-color: #528bff; color: #ffffff; }
QListWidget::item:hover { background-color: #4a4d4f; }
QLabel { color: #f0f0f0; }
QFrame { border: none; }
"""

class ZoomPanLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._pixmap = QPixmap()
        self.scale = 1.0
        self.offset = QPointF(0, 0)
        self.pan_last_pos = QPoint()
        self.is_panning = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.drawing = False
        self.setMouseTracking(True)

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.reset_zoom()
        self.update()

    def pixmap(self):
        return self._pixmap

    def reset_zoom(self):
        if self._pixmap.isNull(): return
        self.scale = min(self.width() / self._pixmap.width(), self.height() / self._pixmap.height())
        pixmap_width_scaled = self._pixmap.width() * self.scale
        pixmap_height_scaled = self._pixmap.height() * self.scale
        x_offset = (self.width() - pixmap_width_scaled) / 2
        y_offset = (self.height() - pixmap_height_scaled) / 2
        self.offset = QPointF(x_offset, y_offset)
        self.update()

    def screen_to_image_coords(self, screen_pos):
        return (screen_pos - self.offset) / self.scale

    def image_to_screen_coords(self, image_pos):
        return image_pos * self.scale + self.offset

    def wheelEvent(self, event):
        zoom_factor = 1.15
        old_scale = self.scale
        if event.angleDelta().y() > 0: self.scale *= zoom_factor
        else: self.scale /= zoom_factor
        mouse_pos = event.pos()
        self.offset = mouse_pos - self.scale * (mouse_pos - self.offset) / old_scale
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.is_panning = True
            self.pan_last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton and self.parent_window.is_create_mode_enabled():
            self.start_point = self.screen_to_image_coords(event.pos()).toPoint()
            self.end_point = self.start_point
            self.drawing = True
        elif event.button() == Qt.RightButton:
            self.reset_zoom()

    def mouseMoveEvent(self, event):
        if self.is_panning:
            delta = event.pos() - self.pan_last_pos
            self.offset += delta
            self.pan_last_pos = event.pos()
            self.update()
        elif self.drawing:
            self.end_point = self.screen_to_image_coords(event.pos()).toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
        elif event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.parent_window.add_new_box(QRect(self.start_point, self.end_point).normalized())
            self.update()

    def paintEvent(self, event):
        if self._pixmap.isNull(): return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        target_rect = QRect(self.offset.toPoint(), (self._pixmap.size() * self.scale))
        painter.drawPixmap(target_rect, self._pixmap)
        pen_rect = QPen(QColor(82, 139, 255), 2, Qt.SolidLine)
        pen_rect.setCosmetic(True)
        painter.setPen(pen_rect)
        for box in self.parent_window.boxes:
            box_rect_img = box['rect']
            top_left_screen = self.image_to_screen_coords(QPointF(box_rect_img.topLeft()))
            bottom_right_screen = self.image_to_screen_coords(QPointF(box_rect_img.bottomRight()))
            screen_rect = QRect(top_left_screen.toPoint(), bottom_right_screen.toPoint())
            painter.drawRect(screen_rect)
            painter.setFont(QFont('Arial', 12, QFont.Bold))
            painter.drawText(screen_rect.topLeft() - QPoint(0, 5), box['label'])
        if self.drawing:
            top_left_screen = self.image_to_screen_coords(QPointF(self.start_point))
            bottom_right_screen = self.image_to_screen_coords(QPointF(self.end_point))
            painter.drawRect(QRect(top_left_screen.toPoint(), bottom_right_screen.toPoint()))

    def resizeEvent(self, event): self.reset_zoom()

class AnnotationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dark Annotator")
        self.setGeometry(100, 100, 1400, 900)
        self.image_dir = None
        self.label_dir = None
        self.image_files = []
        self.current_image_index = -1
        self.classes = []
        self.boxes = []
        self.create_mode = False
        self.setup_ui()
        self.setup_actions()
        self.load_classes()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        image_frame = QFrame()
        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(0,0,0,0)
        self.image_label = ZoomPanLabel(self)
        image_layout.addWidget(self.image_label)
        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.main_layout.addWidget(image_frame, 4)
        self.main_layout.addWidget(self.controls_widget, 1)
        self.load_button = QPushButton(self.style().standardIcon(QStyle.SP_DirOpenIcon), "")
        self.prev_button = QPushButton(self.style().standardIcon(QStyle.SP_ArrowLeft), "")
        self.next_button = QPushButton(self.style().standardIcon(QStyle.SP_ArrowRight), "")
        button_layout = QHBoxLayout()
        for btn in [self.load_button, self.prev_button, self.next_button]:
            btn.setIconSize(QSize(32, 32))
            button_layout.addWidget(btn)
        self.controls_layout.addLayout(button_layout)
        self.class_list_widget = QListWidget()
        self.box_list_widget = QListWidget()
        self.controls_layout.addWidget(QLabel("Classes:"))
        self.controls_layout.addWidget(self.class_list_widget)
        self.controls_layout.addWidget(QLabel("Annotations:"))
        self.controls_layout.addWidget(self.box_list_widget)

    def setup_actions(self):
        self.load_button.setToolTip("Load Image Directory (O)")
        self.load_button.clicked.connect(self.load_directory)
        self.next_button.setToolTip("Next Image (D)")
        self.next_button.clicked.connect(self.next_image)
        self.prev_button.setToolTip("Previous Image (A)")
        self.prev_button.clicked.connect(self.prev_image)
        self.actions_list = [
            QAction(self, text="Next Image", shortcut="D", triggered=self.next_image),
            QAction(self, text="Previous Image", shortcut="A", triggered=self.prev_image),
            QAction(self, text="Load Directory", shortcut="O", triggered=self.load_directory),
            QAction(self, text="Undo Box", shortcut=QKeySequence.Undo, triggered=self.undo_last_box),
            QAction(self, text="Create Box Mode", shortcut="W", triggered=self.toggle_create_mode)
        ]
        self.addActions(self.actions_list)

    def toggle_create_mode(self):
        self.create_mode = True
        self.image_label.setCursor(Qt.CrossCursor)

    def is_create_mode_enabled(self): return self.create_mode

    def load_classes(self):
        project_root = Path(__file__).resolve().parents[2]
        classes_file = project_root / "classes.txt"
        if classes_file.exists():
            with open(classes_file, 'r') as f:
                self.classes = [line.strip() for line in f if line.strip()]
            self.class_list_widget.addItems(self.classes)
            if self.classes: self.class_list_widget.setCurrentRow(0)

    def load_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if not dir_path: return
        
        self.image_dir = Path(dir_path)
        self.label_dir = self.image_dir.parent / f"{self.image_dir.name}_labels"
        self.label_dir.mkdir(parents=True, exist_ok=True)
        
        self.image_files = sorted([f for f in self.image_dir.glob("*.jpg")])
        if self.image_files:
            self.current_image_index = 0
            self.load_current_image()

    def load_current_image(self):
        if 0 <= self.current_image_index < len(self.image_files):
            filepath = self.image_files[self.current_image_index]
            pixmap = QPixmap(str(filepath))
            self.image_label.setPixmap(pixmap)
            self.load_annotations()
            self.update_box_list()

    def next_image(self):
        if self.image_dir and self.current_image_index < len(self.image_files) - 1:
            self.save_annotations()
            self.current_image_index += 1
            self.load_current_image()

    def prev_image(self):
        if self.image_dir and self.current_image_index > 0:
            self.save_annotations()
            self.current_image_index -= 1
            self.load_current_image()

    def add_new_box(self, rect):
        selected_items = self.class_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Class Selected", "Please select a class before drawing a box.")
        else:
            label = selected_items[0].text()
            self.boxes.append({'rect': rect, 'label': label})
            self.update_box_list()
        self.create_mode = False
        self.image_label.setCursor(Qt.ArrowCursor)
        
    def undo_last_box(self):
        if self.boxes:
            self.boxes.pop()
            self.update_box_list()

    def update_box_list(self):
        self.box_list_widget.clear()
        for box in self.boxes:
            self.box_list_widget.addItem(f"{box['label']} @ ({box['rect'].x()},{box['rect'].y()})")
        self.image_label.update()

    def save_annotations(self):
        if self.current_image_index == -1: return
        current_image_path = self.image_files[self.current_image_index]
        label_path = self.label_dir / f"{current_image_path.stem}.txt"
        pixmap = self.image_label.pixmap()
        if pixmap.isNull(): return
        img_w, img_h = pixmap.width(), pixmap.height()
        if img_w == 0 or img_h == 0: return

        try:
            with open(label_path, 'w') as f:
                for box in self.boxes:
                    class_id = self.classes.index(box['label'])
                    rect = box['rect']
                    x_c = (rect.x() + rect.width() / 2) / img_w
                    y_c = (rect.y() + rect.height() / 2) / img_h
                    w = rect.width() / img_w
                    h = rect.height() / img_h
                    f.write(f"{class_id} {x_c:.6f} {y_c:.6f} {w:.6f} {h:.6f}\n")
        except Exception:
            pass

    def load_annotations(self):
        self.boxes = []
        if self.current_image_index == -1: return
        current_image_path = self.image_files[self.current_image_index]
        label_path = self.label_dir / f"{current_image_path.stem}.txt"
        if not label_path.exists(): return
        pixmap = self.image_label.pixmap()
        if pixmap.isNull(): return
        img_w, img_h = pixmap.width(), pixmap.height()
        with open(label_path, 'r') as f:
            for line in f:
                try:
                    parts = line.strip().split()
                    if len(parts) != 5: continue
                    class_id, x_c, y_c, w, h = [float(p) for p in parts]
                    label = self.classes[int(class_id)]
                    box_w, box_h = w * img_w, h * img_h
                    box_x, box_y = x_c * img_w - box_w / 2, y_c * img_h - box_h / 2
                    self.boxes.append({'rect': QRect(int(box_x), int(box_y), int(box_w), int(box_h)), 'label': label})
                except Exception: continue

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    window = AnnotationWindow()
    window.show()
    sys.exit(app.exec_())