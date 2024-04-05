# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QDockWidget, QLabel
from PySide6.QtWidgets import QGridLayout, QBoxLayout, QVBoxLayout, QPushButton, QLayout
from PySide6.QtWidgets import QTableView, QHeaderView, QFrame
from PySide6.QtCore import Qt, QSize, QFile
from PySide6.QtUiTools import QUiLoader
from database import database

class Widget(QWidget):
    def __init__(self):
        QWidget.__init__(self)


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("Unitracker")
        # member vars
        self.main_scene = QBoxLayout(QBoxLayout.LeftToRight)
        self.setCentralWidget(Widget())
        self.centralWidget().setLayout(self.main_scene)

        self.current_menu = "games"
        self.menu_dict = {}

        self.create_navbar()
        self.create_games_menu()
        self.db = database()


    def create_games_menu(self):
        """
        construct and show the table of games;
        takes the main window as argument
        """
        games_frame = QFrame()
        games_layout = QVBoxLayout()
        game_table = QTableView()
        # game_table.setColumnCount(5)
        #game_table.setRowCount(1)

        # set headers
        h_list = ["Games", "Progress", "Hours Played", "Genre(s)", "Start Date", "End Date"]
        horizontal_header = QBoxLayout(QBoxLayout.LeftToRight)
        for i in h_list:
            label = QLabel()
            label.setText(i)
            horizontal_header.addWidget(label)

        t_header = QHeaderView(Qt.Horizontal)
        t_header.setLayout(horizontal_header)
        game_table.setHorizontalHeader(t_header)
        #game_table.setVerticalHeaderLabels([""])

        title = QLabel()
        title.setText("Games")

        game_table.setVisible(True)
        games_layout.addWidget(title)
        games_layout.addWidget(game_table)
        games_frame.setLayout(games_layout)

        self.menu_dict["games"] = games_frame

        self.main_scene.addWidget(games_frame)

    def create_navbar(self):
        """
        create and add the main navigation bar to the main window
        """
        nav_bar = QVBoxLayout()

        # create buttons
        games = QPushButton("Games")
        add_game = QPushButton("Add Game")
        edit_game = QPushButton("Edit Game")
        delete_game = QPushButton("Delete Game")
        settings = QPushButton("Settings")

        nav_bar.addWidget(games)
        nav_bar.addWidget(add_game)
        nav_bar.addWidget(edit_game)
        nav_bar.addWidget(delete_game)
        nav_bar.addWidget(settings)

        # connect functionality
        settings.clicked.connect(self.show_settings)
        games.clicked.connect(self.show_games)

        self.main_scene.addLayout(nav_bar)

    def show_games(self):
        if (not self.current_menu == "games"):
            self.menu_dict[self.current_menu].hide()
            self.current_menu = "games"
            self.menu_dict["games"].show()

    def show_settings(self):
        if (not "settings" in self.menu_dict):
            settings_ui = QFile("settings.ui")
            loader = QUiLoader()
            s = loader.load(settings_ui)
            if not s:
                print(loader.errorString())
                sys.exit(-1)
            self.main_scene.addWidget(s)
            self.menu_dict["settings"] = s

        if (not self.current_menu == "settings"):
            self.menu_dict[self.current_menu].hide()
            self.current_menu = "settings"
            self.menu_dict["settings"].show()


if __name__ == "__main__":
    app = QApplication([])

    main_window = MainWindow()

    main_window.setMinimumHeight(480)
    main_window.setMinimumWidth(720)
    main_window.show()
    sys.exit(app.exec())



