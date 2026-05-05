import sys
import os
import subprocess
import vtk
import shutil

from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTreeWidget,
    QTreeWidgetItem, QLabel, QSplitter, QToolBar,
    QFileDialog, QDialog, QFormLayout, QLineEdit, QSpinBox,
    QHBoxLayout, QPushButton, QComboBox, QMessageBox
)

from PyQt6.QtGui import QAction

from PyQt6.QtCore import Qt

import paraview.simple as pvsimple
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
vtk.vtkOutputWindow.SetInstance(vtk.vtkOutputWindow())
vtk.vtkOutputWindow.GetInstance().SetDisplayMode(0)

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
        # new_model
        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self.create_project)
        file_menu.addAction(new_project_action)
        # Load model
        load_project_action = QAction("Load Model", self)
        load_project_action.triggered.connect(self.load_project)
        file_menu.addAction(load_project_action)

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
        # self.vtk_viewer = VTKViewer()
        self.vtk_viewer = ParaViewViewer()
        self.right = self.vtk_viewer

        splitter.addWidget(self.tree)
        splitter.addWidget(self.right)
        splitter.setSizes([200, 600])

        self.setCentralWidget(splitter)

        # ===== VIEW CONTROLS =====
        self.repr_combo = QComboBox()
        self.repr_combo.addItems([
            "Surface",
            "Wireframe",
            "Surface With Edges",
            "Points"
        ])

        self.repr_combo.currentTextChanged.connect(self.change_representation)

        toolbar.addWidget(QLabel("View:"))
        toolbar.addWidget(self.repr_combo)
        toolbar.addSeparator()

        self.scalar_combo = QComboBox()
        self.scalar_combo.currentTextChanged.connect(self.change_scalar)
        toolbar.addWidget(self.scalar_combo)

    # =========================
    # CREATE PROJECT
    # =========================
    def create_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Working Directory")

        if folder:
            self.working_dir = Path(folder)

            # se esiste già qualcosa → chiedi
            if any(self.working_dir.iterdir()):
                reply = QMessageBox.question(
                    self,
                    "Overwrite Project",
                    f"The folder:\n{self.working_dir}\nalready contains files.\n\nDo you want to delete everything and create a new project?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    return

                # cancella tutto
                shutil.rmtree(self.working_dir)
                self.working_dir.mkdir()

            # crea struttura
            input_dir = self.working_dir / "INPUT"
            input_dir.mkdir(exist_ok=True)

            print(f"Project created at: {self.working_dir}")

    # =========================
    # LOAD PROJECT
    # =========================
    def load_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")

        if not folder:
            return

        self.working_dir = Path(folder)

        input_dir = self.working_dir / "INPUT"

        if not input_dir.exists():
            QMessageBox.warning(
                self,
                "Invalid Project",
                "Selected folder is not a valid project (missing INPUT folder)."
            )
            return

        vtk_files = list(input_dir.rglob("*.vtk"))

        if not vtk_files:
            QMessageBox.warning(
                self,
                "No Morphology",
                "No morphology (.vtk) found in this project."
            )
            return

        if len(vtk_files) > 1:
            dialog = MorphologySelectionDialog(vtk_files)

            if dialog.exec():
                vtk_file = dialog.get_selected()
            else:
                return
        else:
            vtk_file = vtk_files[0]

        print(f"Loading VTK: {vtk_file}")
        self.show_vtk(vtk_file)
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

        cmd3 = [f"neper -V {morphology_name}.tess,{morphology_name}.msh -imageformat vtk -print {morphology_name}"]

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
    
    def change_representation(self, text):
        if not text:
            return
        self.vtk_viewer.set_representation(text)

    def change_scalar(self, text):
        if not text:
            return
        assoc, name = text.split(":")
        self.vtk_viewer.set_coloring(assoc, name)
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
        self.grains.setValue(10)

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

class MorphologySelectionDialog(QDialog):
    def __init__(self, vtk_files):
        super().__init__()
        self.setWindowTitle("Select Morphology")

        self.selected_file = None

        layout = QVBoxLayout()

        self.combo = QComboBox()

        # mappa nome → path
        self.file_map = {}

        for f in vtk_files:
            # nome leggibile: CODE/Test1/file.vtk
            rel = f.parts[-3:]  # INPUT/CODE/Test1/file.vtk → CODE/Test1/file.vtk
            label = "/".join(rel)

            self.combo.addItem(label)
            self.file_map[label] = f

        layout.addWidget(QLabel("Select morphology to load:"))
        layout.addWidget(self.combo)

        # bottoni
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Load")
        cancel_btn = QPushButton("Cancel")

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_selected(self):
        label = self.combo.currentText()
        return self.file_map.get(label)
    
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
# PARAVIEW VIEWER CLASS
# =========================
class ParaViewViewer(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        # RenderView ParaView
        self.render_view = pvsimple.CreateRenderView()
        pvsimple.color.LoadPalette('BlueGrayBackground')

        # Widget Qt collegato
        self.vtk_widget = QVTKRenderWindowInteractor(
            rw=self.render_view.GetRenderWindow(),
            iren=self.render_view.GetInteractor()
        )

        layout.addWidget(self.vtk_widget)
        self.vtk_widget.Initialize()

        self.current_display = None

    # =========================
    # LOAD FILE
    # =========================
    def load_vtk(self, file_path):
        # Pulisci scena
        for src in list(pvsimple.GetSources().values()):
            pvsimple.Delete(src)

        # Reader
        reader = pvsimple.LegacyVTKReader(FileNames=[str(file_path)])

        # Show
        self.current_display = pvsimple.Show(reader, self.render_view)
       

        data_info = reader.GetDataInformation()
        bounds = data_info.GetBounds()

        center = [
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2,
        ]

        self.render_view.CenterOfRotation = center


        # Prova coloring automatico
        # try:
        #     pvsimple.ColorBy(self.current_display, ('CELLS', 'poly'))
        # except:
        #     pass
        
        arrays = self.get_available_arrays()

        main_window = self.parent().parent()  # risali fino a MainWindow

        main_window.scalar_combo.blockSignals(True)
        main_window.scalar_combo.clear()

        for assoc, name in arrays:
            main_window.scalar_combo.addItem(f"{assoc}:{name}")

        main_window.scalar_combo.blockSignals(False)

        for assoc, name in arrays:
            if "id" in name.lower():
                main_window.scalar_combo.setCurrentText(f"{assoc}:{name}")
                self.set_coloring(assoc, name)
                break
        
        self.render_view.ResetCamera()
        self.render()

    def render(self):
        pvsimple.Render(self.render_view)

    # =========================
    # CONTROLS
    # =========================
    def set_representation(self, rep_type):
        if self.current_display:
            self.current_display.SetRepresentationType(rep_type)
            self.render()
   
    def get_available_arrays(self):
        if not self.current_display:
            return []

        rep = self.current_display
        data_info = rep.Input.GetDataInformation()

        arrays = []

        cell_data = data_info.GetCellDataInformation()
        for i in range(cell_data.GetNumberOfArrays()):
            arrays.append(("CELLS", cell_data.GetArrayInformation(i).GetName()))

        point_data = data_info.GetPointDataInformation()
        for i in range(point_data.GetNumberOfArrays()):
            arrays.append(("POINTS", point_data.GetArrayInformation(i).GetName()))

        return arrays


    def set_coloring(self, assoc, name):
        if self.current_display:
            pvsimple.ColorBy(self.current_display, (assoc, name))

            lut = pvsimple.GetColorTransferFunction(name)
            lut.ApplyPreset("Cool to Warm", True)

            self.current_display.RescaleTransferFunctionToDataRange(True, False)

            self.render()

# =========================
# APP
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1000, 600)
    win.show()
    sys.exit(app.exec())