#
#  Copyright (c) 2021 Jan Tošovský <jan.tosovsky.cz@gmail.com>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import sys
import zipfile
from PySide6 import QtCore, QtGui, QtWidgets

zip_file_path = None
path_list = []
image_file_index = 0
image_file_name = None
image = None
graphics_view = None
resized = False
screen_rect = None
image_rect = None
DEFAULT_DELTA = 1.2


class CustomGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, scene):
        QtWidgets.QGraphicsView.__init__(self, scene)
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setStyleSheet("background-color: black; border: none")
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        global resized
        if not resized:
            if self.width() == screen_rect.width():
                fit_height()
                resized = True

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        anchor = self.transformationAnchor()
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        if event.angleDelta().y() > 0:
            factor = DEFAULT_DELTA
        else:
            factor = 1 / DEFAULT_DELTA

        self.scale(factor, factor)
        self.setTransformationAnchor(anchor)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        global image_file_index, screen_rect
        if (event.key() == QtCore.Qt.Key_Right or
                event.key() == QtCore.Qt.Key_Left or
                event.key() == QtCore.Qt.Key_Home or
                event.key() == QtCore.Qt.Key_End):

            new_image_image_file_index = image_file_index

            if event.key() == QtCore.Qt.Key_Home:
                new_image_image_file_index = 0
            elif event.key() == QtCore.Qt.Key_End:
                new_image_image_file_index = len(path_list) - 1
            else:
                delta = 1
                if event.modifiers() == QtCore.Qt.ShiftModifier:
                    delta = 5
                elif event.modifiers() == QtCore.Qt.ControlModifier:
                    delta = 20

                if event.key() == QtCore.Qt.Key_Left:
                    new_image_image_file_index = max(image_file_index - delta, 0)
                elif event.key() == QtCore.Qt.Key_Right:
                    new_image_image_file_index = min(image_file_index + delta, len(path_list) - 1)

            if new_image_image_file_index != image_file_index:
                image_file_index = new_image_image_file_index
                update_image()

        elif event.key() == QtCore.Qt.Key_W:
            fit_width()
        elif event.key() == QtCore.Qt.Key_H:
            fit_height()
        elif event.key() == QtCore.Qt.Key_R:
            image.resetTransform()
            graphics_view.resetTransform()
            self.scale(1, 1)
            image.setPos(self.mapToScene(0, 0))

        elif event.key() == QtCore.Qt.Key_C:
            QtWidgets.QApplication.clipboard().setText(image_file_name)


def update_image():
    global image_rect, image_file_name
    with zipfile.ZipFile(zip_file_path, "r") as zip_file:
        path = path_list[image_file_index]
        image_file_name = path[path.rfind("/") + 1:]
        graphics_view.setWindowTitle(image_file_name)
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(zip_file.read(path))
        image_rect = pixmap.rect()
        image.setPixmap(pixmap)
    zipFile.close()


# fit_height doesn't work on zoomed or translated content
def fit_height():
    reset()
    scale = graphics_view.height() / image_rect.height()
    graphics_view.scale(scale, scale)


def fit_width():
    reset()
    scale = graphics_view.width() / image_rect.width()
    graphics_view.scale(scale, scale)
    image.setPos(graphics_view.mapToScene(0, 0))


def reset():
    graphics_view.resetTransform()
    image.resetTransform()
    offset = QtCore.QRectF(image_rect).center()
    graphics_view.setSceneRect(-offset.x() * 5, -offset.y() * 5, offset.x() * 10, offset.y() * 10)
    image.setPos(-offset)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen_rect = app.primaryScreen().availableGeometry()

    zip_file_path = app.arguments()[1]
    with zipfile.ZipFile(zip_file_path, "r") as zipFile:
        for zipEntry in zipFile.infolist():
            if not zipEntry.is_dir():
                if zipEntry.filename.lower().endswith(".jpg"):
                    path_list.append(zipEntry.filename)
    zipFile.close()

    graphics_scene = QtWidgets.QGraphicsScene()
    graphics_view = CustomGraphicsView(graphics_scene)
    image = QtWidgets.QGraphicsPixmapItem()
    graphics_scene.addItem(image)
    update_image()

    graphics_view.showMaximized()

    sys.exit(app.exec_())
