import sys
import os
import subprocess
import vtk

from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTreeWidget,
    QTreeWidgetItem, QLabel, QSplitter, QToolBar,
    QFileDialog, QDialog, QFormLayout, QLineEdit, QSpinBox,
    QHBoxLayout, QPushButton
)

from PyQt6.QtGui import QAction

from PyQt6.QtCore import Qt

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor



# =========================
# MAIN WINDOW
# =========================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("pyPolyBEM")
        self.working_dir = None

        # MENU
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        edit_menu = menu.addMenu("Edit")
        about_menu = menu.addMenu("About")

        ## File Menu
        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self.create_project)
        file_menu.addAction(new_project_action)

        ## Edit Menu
        # TODO
        ## About Menu
        # TODO

        # TOOLBAR
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # LAYOUT
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Model tree")

        self.morphology_item = QTreeWidgetItem(["Morphology"])
        self.tree.addTopLevelItem(self.morphology_item)
        
        
        self.material_item = QTreeWidgetItem(["Material"])
        self.tree.addTopLevelItem(self.material_item)

        self.tree.itemDoubleClicked.connect(self.on_double_click)

        # RIGHT PANEL
        self.vtk_viewer = VTKViewer()
        self.right = self.vtk_viewer

        splitter.addWidget(self.tree)
        splitter.addWidget(self.right)
        splitter.setSizes([200, 600])

        self.setCentralWidget(splitter)

        # TOOLBAR
        reset_action = QAction("Reset View", self)
        reset_action.triggered.connect(lambda: self.vtk_viewer.reset_camera())
        toolbar.addAction(reset_action)

        wire_action = QAction("Wireframe", self)
        wire_action.triggered.connect(lambda: self.vtk_viewer.set_wireframe())
        toolbar.addAction(wire_action)

        surface_action = QAction("Surface", self)
        surface_action.triggered.connect(lambda: self.vtk_viewer.set_surface())
        toolbar.addAction(surface_action)

        edges_action = QAction("Edges ON", self)
        edges_action.triggered.connect(lambda: self.vtk_viewer.toggle_edges(True))
        toolbar.addAction(edges_action)

        bg_dark = QAction("Dark BG", self)
        bg_dark.triggered.connect(lambda: self.vtk_viewer.set_background_dark())
        toolbar.addAction(bg_dark)

        bg_light = QAction("Light BG", self)
        bg_light.triggered.connect(lambda: self.vtk_viewer.set_background_light())
        toolbar.addAction(bg_light)

    # =========================
    # CREATE PROJECT
    # =========================
    def create_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Working Directory")

        if folder:
            self.working_dir = Path(folder)

            input_dir = self.working_dir / "INPUT"
            input_dir.mkdir(exist_ok=True)

            print(f"Project created at: {self.working_dir}")

    # =========================
    # DOUBLE CLICK Model Tree
    # =========================
    def on_double_click(self, item, column):
        if item.text(0) == "Morphology":
            if not self.working_dir:
                print("Create a project first!")
                return

            dialog = MorphologyDialog()

            if dialog.exec():
                data = dialog.get_data()
                self.generate_morphology(data)
        elif item.text(0) == "Material":
            if not self.working_dir:
                print("Create a project first!")
                return

            dialog = MaterialDialog()

            if dialog.exec():
                data = dialog.get_data()
                self.generate_material(data)


    # =========================
    # GENERATE MORPHOLOGY
    # =========================
    def generate_morphology(self, data):
        code = data["code"]
        name = data["name"]
        grains = data["grains"]
        x, y, z = data["x"], data["y"], data["z"]

        base_path = self.working_dir / "INPUT" / code / "Test1"
        base_path.mkdir(parents=True, exist_ok=True)

        morphology_name = name

        # Comandi NEPER
        cmd1 = [f"neper -T -n {grains} -id 1 -domain \"cube({x},{y},{z})\" -statface id,x,y,z,polynb,polys,domface -statpoly id,x,y,z,vernb,vers,nseednb,nseeds -o {morphology_name} -reg 1"]

        cmd2 = [f"neper -M {morphology_name}.tess"]

        cmd3 = [f"neper -V {morphology_name}.tess,{morphology_name}.msh -imageformat png,vtk -print {morphology_name}"]

        try:
            print("Running NEPER...")

            # subprocess.run(cmd1, cwd=base_path, check=True)
            # subprocess.run(cmd2, cwd=base_path, check=True)
            # subprocess.run(cmd3, cwd=base_path, check=True)
            
            self.run_in_wsl(cmd1, base_path)
            self.run_in_wsl(cmd2, base_path)
            self.run_in_wsl(cmd3, base_path)



            print("Morphology generated!")

            vtk_file = base_path / f"{morphology_name}.vtk"
            self.show_vtk(vtk_file)

        except subprocess.CalledProcessError as e:
            print("Error running neper:", e)
    
    def run_in_wsl(self, command, workdir):
        # Converte path Windows → WSL
        wsl_path = str(workdir).replace("C:\\", "/mnt/c/").replace("\\", "/")

        full_cmd = ["wsl", "bash", "-c", f"cd {wsl_path} && {' '.join(command)}"]

        subprocess.run(full_cmd, check=True)

    # =========================
    # GENERATE Material
    # =========================
    def generate_material(self, data):
        pass
    
    # =========================
    # SHOW VTK (placeholder)
    # =========================
    def show_vtk(self, vtk_path):
        if vtk_path.exists():
            self.vtk_viewer.load_vtk(vtk_path)
        else:
            print("VTK file not found:", vtk_path)


# =========================
# MORPHOLOGY DIALOG
# =========================
class MorphologyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create Morphology")

        layout = QVBoxLayout()
        form = QFormLayout()

        self.name = QLineEdit()
        self.code = QLineEdit()

        self.grains = QSpinBox()
        self.grains.setValue(25)

        self.size_x = QLineEdit("1")
        self.size_y = QLineEdit("1")
        self.size_z = QLineEdit("1")

        form.addRow("Name:", self.name)
        form.addRow("Code:", self.code)
        form.addRow("Number of grains:", self.grains)
        form.addRow("Size X:", self.size_x)
        form.addRow("Size Y:", self.size_y)
        form.addRow("Size Z:", self.size_z)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.cancel_btn = QPushButton("Cancel")

        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.cancel_btn.clicked.connect(self.reject)
        self.generate_btn.clicked.connect(self.accept)

    def get_data(self):
        return {
            "name": self.name.text(),
            "code": self.code.text(),
            "grains": self.grains.value(),
            "x": self.size_x.text(),
            "y": self.size_y.text(),
            "z": self.size_z.text(),
        }

# =========================
# Material DIALOG
# =========================
class MaterialDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create Material")

        layout = QVBoxLayout()
        form = QFormLayout()

        self.name = QLineEdit()
        self.code = QLineEdit()

        self.grains = QSpinBox()
        self.grains.setValue(25)

        self.size_x = QLineEdit("1")
        self.size_y = QLineEdit("1")
        self.size_z = QLineEdit("1")

        form.addRow("Name:", self.name)
        form.addRow("Code:", self.code)
        form.addRow("Number of grains:", self.grains)
        form.addRow("Size X:", self.size_x)
        form.addRow("Size Y:", self.size_y)
        form.addRow("Size Z:", self.size_z)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.cancel_btn = QPushButton("Cancel")

        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.cancel_btn.clicked.connect(self.reject)
        self.generate_btn.clicked.connect(self.accept)

    def get_data(self):
        return {
            "name": self.name.text(),
            "code": self.code.text(),
            "grains": self.grains.value(),
            "x": self.size_x.text(),
            "y": self.size_y.text(),
            "z": self.size_z.text(),
        }

# =========================
# VTK VIEWER CLASS
# =========================
class VTKViewer(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.vtk_widget = QVTKRenderWindowInteractor(self)

        layout.addWidget(self.vtk_widget)
        self.setLayout(layout)

        # Renderer
        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)

        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()

        self.renderer.SetBackground(0.1, 0.1, 0.1)
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)

        self.interactor.Initialize()
        # self.interactor.Start()

    def load_vtk(self, file_path):
        self.renderer.RemoveAllViewProps()

        reader = vtk.vtkDataSetReader()
        reader.SetFileName(str(file_path))
        reader.Update()

        data = reader.GetOutput()

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(data)

        if data.GetCellData().GetScalars():
            mapper.SetScalarModeToUseCellData()
            mapper.ScalarVisibilityOn()
        else:
            mapper.ScalarVisibilityOff()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # opzionale: mostra bordi
        actor.GetProperty().EdgeVisibilityOn()

        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()

        self.vtk_widget.GetRenderWindow().Render()


    def reset_camera(self):
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()


    def set_wireframe(self):
        for actor in self.renderer.GetActors():
            actor.GetProperty().SetRepresentationToWireframe()
        self.vtk_widget.GetRenderWindow().Render()


    def set_surface(self):
        for actor in self.renderer.GetActors():
            actor.GetProperty().SetRepresentationToSurface()
        self.vtk_widget.GetRenderWindow().Render()


    def toggle_edges(self, state=True):
        for actor in self.renderer.GetActors():
            if state:
                actor.GetProperty().EdgeVisibilityOn()
            else:
                actor.GetProperty().EdgeVisibilityOff()
        self.vtk_widget.GetRenderWindow().Render()


    def set_background_dark(self):
        self.renderer.SetBackground(0.1, 0.1, 0.1)
        self.vtk_widget.GetRenderWindow().Render()


    def set_background_light(self):
        self.renderer.SetBackground(1, 1, 1)
        self.vtk_widget.GetRenderWindow().Render()
# =========================
# APP
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1000, 600)
    win.show()
    sys.exit(app.exec())