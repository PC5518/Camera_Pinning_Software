import sys
import cv2
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QMenu
from PyQt6.QtGui import QImage, QPixmap, QMouseEvent, QEnterEvent, QAction
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect
# I have Explained every step with comments 
# This is the main window that will show your face
class WebcamWidget(QWidget):
    def __init__(self):
        super().__init__()

        # --- CLASS MEMBERS FOR RESIZING AND MOVING ---
        self.grip_size = 8  # The thickness of the resizeable border
        self.grips = []     # A list to hold our virtual resize grips
        self.is_resizing = False
        self.is_moving = False
        self.start_pos = QPoint()
        self.start_geometry = QRect()

        # --- 1. SET UP THE WEBCAM ---
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Cannot open webcam.")
            sys.exit()

        # --- 2. CONFIGURE THE WINDOW ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 320, 240)
        self.setMinimumSize(120, 90) # Allow shrinking to a small size

        # --- 3. CREATE WIDGETS ---
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel(self)
        self.setStyleSheet("background-color: black; border-radius: 10px;")
        self.image_label.setScaledContents(True)
        self.layout.addWidget(self.image_label)
        self.setLayout(self.layout)

        # --- 4. CREATE CLOSE BUTTON (same as before) ---
        self.close_button = QPushButton("✕", self)
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("""
            QPushButton { background-color: rgba(0, 0, 0, 0.5); color: white; border-radius: 10px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255, 0, 0, 0.7); }
        """)
        self.close_button.clicked.connect(self.close)
        self.close_button.hide()

        # --- 5. SETUP TIMER ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)
        
        # ### NEW: Create the virtual resize grips ###
        self.create_grips()

    # --- Video Update Function ---
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    # ===================================================================
    # ### NEW: All mouse handling logic is rewritten below ###
    # ===================================================================

    def create_grips(self):
        """Create a list of virtual grips (rects) around the window edges."""
        self.grips = []
        # Top, Bottom, Left, Right
        self.grips.append(QRect(self.grip_size, 0, self.width() - 2 * self.grip_size, self.grip_size))
        self.grips.append(QRect(self.grip_size, self.height() - self.grip_size, self.width() - 2 * self.grip_size, self.grip_size))
        self.grips.append(QRect(0, self.grip_size, self.grip_size, self.height() - 2 * self.grip_size))
        self.grips.append(QRect(self.width() - self.grip_size, self.grip_size, self.grip_size, self.height() - 2 * self.grip_size))
        # Corners
        self.grips.append(QRect(0, 0, self.grip_size, self.grip_size))
        self.grips.append(QRect(self.width() - self.grip_size, 0, self.grip_size, self.grip_size))
        self.grips.append(QRect(0, self.height() - self.grip_size, self.grip_size, self.grip_size))
        self.grips.append(QRect(self.width() - self.grip_size, self.height() - self.grip_size, self.grip_size, self.grip_size))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            
            # Check if the click is on any of the resize grips
            for i, rect in enumerate(self.grips):
                if rect.contains(pos):
                    self.is_resizing = True
                    self.resize_edge = i
                    self.start_pos = event.globalPosition().toPoint()
                    self.start_geometry = self.geometry()
                    event.accept()
                    return

            # If not resizing, check if we should start moving the window
            if self.image_label.rect().contains(pos):
                self.is_moving = True
                self.start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        
        if self.is_resizing:
            delta = event.globalPosition().toPoint() - self.start_pos
            new_geo = QRect(self.start_geometry)

            # Adjust geometry based on which edge is being dragged
            if self.resize_edge == 0: # Top
                new_geo.setTop(new_geo.top() + delta.y())
            elif self.resize_edge == 1: # Bottom
                new_geo.setBottom(new_geo.bottom() + delta.y())
            elif self.resize_edge == 2: # Left
                new_geo.setLeft(new_geo.left() + delta.x())
            elif self.resize_edge == 3: # Right
                new_geo.setRight(new_geo.right() + delta.x())
            elif self.resize_edge == 4: # Top-Left
                new_geo.setTopLeft(new_geo.topLeft() + delta)
            elif self.resize_edge == 5: # Top-Right
                new_geo.setTopRight(new_geo.topRight() + delta)
            elif self.resize_edge == 6: # Bottom-Left
                new_geo.setBottomLeft(new_geo.bottomLeft() + delta)
            elif self.resize_edge == 7: # Bottom-Right
                new_geo.setBottomRight(new_geo.bottomRight() + delta)
            
            # Apply the new geometry, respecting minimum size
            if new_geo.width() >= self.minimumWidth() and new_geo.height() >= self.minimumHeight():
                self.setGeometry(new_geo)

        elif self.is_moving:
            self.move(event.globalPosition().toPoint() - self.start_pos)
        
        else:
            # If not resizing or moving, just update the cursor shape on hover
            cursor = Qt.CursorShape.ArrowCursor
            for i, rect in enumerate(self.grips):
                if rect.contains(pos):
                    if i in [0, 1]: cursor = Qt.CursorShape.SizeVerCursor
                    elif i in [2, 3]: cursor = Qt.CursorShape.SizeHorCursor
                    elif i in [4, 7]: cursor = Qt.CursorShape.SizeFDiagCursor
                    elif i in [5, 6]: cursor = Qt.CursorShape.SizeBDiagCursor
                    break
            self.setCursor(cursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_resizing = False
            self.is_moving = False
            self.setCursor(Qt.CursorShape.ArrowCursor) # Reset cursor

    # ===================================================================
    # --- Event handlers for close button and context menu ---
    # ===================================================================

    def resizeEvent(self, event):
        """Called when window is resized."""
        # Update the position of the close button
        self.close_button.move(self.width() - self.close_button.width() - 5, 5)
        # Re-create the virtual grips for the new size
        self.create_grips()
        super().resizeEvent(event)

    def enterEvent(self, event: QEnterEvent):
        self.close_button.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.close_button.hide()
        super().leaveEvent(event)
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        menu.addAction(close_action)
        menu.exec(event.globalPos())

    def closeEvent(self, event):
        print("Closing the application and releasing webcam.")
        self.cap.release()
        super().closeEvent(event)


# --- MAIN EXECUTION ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = WebcamWidget()
    main_window.show()
    sys.exit(app.exec())