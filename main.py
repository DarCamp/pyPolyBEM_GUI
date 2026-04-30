import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QSplitter, QToolBar
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt


class MorphologyPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        label = QLabel("Morphology editor (work in progress)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        self.setLayout(layout)


class VTKPlaceholder(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        label = QLabel("VTK viewer")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("pyPolyBEM")

        # ===== MENU =====
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        edit_menu = menu.addMenu("Edit")
        about_menu = menu.addMenu("About")

        # ===== TOOLBAR =====
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        test_action = QAction("Test", self)
        toolbar.addAction(test_action)

        # ===== CENTRAL LAYOUT =====
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT: MODEL TREE
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Model tree")

        self.morphology_item = QTreeWidgetItem(["Morphology"])
        self.material_item = QTreeWidgetItem(["Material"])
        self.bcs_item = QTreeWidgetItem(["BCs"])
        self.job_item = QTreeWidgetItem(["Job"])

        self.tree.addTopLevelItem(self.morphology_item)
        self.tree.addTopLevelItem(self.material_item)
        self.tree.addTopLevelItem(self.bcs_item)
        self.tree.addTopLevelItem(self.job_item)

        self.tree.itemClicked.connect(self.on_tree_clicked)

        # RIGHT: STACK (placeholder dinamico)
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_container.setLayout(self.right_layout)

        self.vtk_view = VTKPlaceholder()
        self.right_layout.addWidget(self.vtk_view)

        splitter.addWidget(self.tree)
        splitter.addWidget(self.right_container)
        splitter.setSizes([200, 600])

        self.setCentralWidget(splitter)

    def on_tree_clicked(self, item, column):
        text = item.text(0)

        # Pulisce layout
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if text == "Morphology":
            self.right_layout.addWidget(MorphologyPanel())
        else:
            self.right_layout.addWidget(self.vtk_view)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())