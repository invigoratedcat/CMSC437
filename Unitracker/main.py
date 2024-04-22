# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QDockWidget, QLabel
from PySide6.QtWidgets import QGridLayout, QBoxLayout, QVBoxLayout, QPushButton, QLayout
from PySide6.QtWidgets import QTableView, QHeaderView, QFrame, QRadioButton, QLineEdit
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt, QSize, QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPalette
from database import database
import qdarkstyle

class Widget(QWidget):
    def __init__(self):
        QWidget.__init__(self)

class Palette(QPalette):
    def __init__(self, ID):
        QPalette.__init__(self)
        self.ID = ID

class MainWindow(QMainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)
        self.app = app
        self.setWindowTitle("Unitracker")
        # member vars
        self.main_scene = QBoxLayout(QBoxLayout.LeftToRight)
        self.setCentralWidget(Widget())
        self.centralWidget().setLayout(self.main_scene)
        dark_p = Palette("dark")
        light_p = Palette("light")
        self.dark_theme = qdarkstyle.load_stylesheet(qt_api="pyside6", palette=dark_p)
        self.light_theme = qdarkstyle.load_stylesheet(qt_api="pyside6", palette=light_p)
        self.set_dark()

        self.current_menu = "games"
        self.menu_dict = {}

        # db stuff
        self.db = database()
        if (not self.db.create_db()):
            print("Database creation failed.")

        # load and create menus
        self.create_navbar()
        self.create_games_menu()
        self.load_settings()
        self.load_add()
        self.load_edit()

        test1 = {"name": "Final Fantasy", "progress": 75, "hours_played": 123}
        print(self.db.add_item(test1))
        print(self.db.db.lastError())
        self.game_table.setModel(self.db.get_games())

    def create_games_menu(self):
        """
        construct and show the table of games;
        takes the main window as argument
        """
        games_frame = QFrame()
        games_layout = QVBoxLayout()
        game_table = QTableView()
        self.game_table = game_table
        model = self.db.get_games()        
        game_table.setModel(model)

        # set view properties
        #game_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        game_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #game_table.horizontalHeader().setStretchLastSection(1)
        game_table.verticalHeader().hide()
        game_table.setGridStyle(Qt.SolidLine)
        game_table.setSortingEnabled(True)
        game_table.sortByColumn(0, Qt.DescendingOrder) # set default order to descending by game name

        title = QLabel()
        title.setText("Games")

        game_table.setVisible(True)
        games_layout.addWidget(title)
        games_layout.addWidget(game_table)

        games_frame.setLayout(games_layout)

        self.menu_dict["games"] = games_frame

        self.main_scene.addWidget(games_frame)

    def resizeEvent(self, event):
        #for i in range(self.db.MAX_VALUES):
            #self.game_table.setColumnWidth(i, self.game_table.width()/self.db.MAX_VALUES)
            #self.game_table.setColumnWidth(i, )
        return super(QMainWindow, self).resizeEvent(event)

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
        add_game.clicked.connect(self.show_add)
        edit_game.clicked.connect(self.show_edit)

        self.main_scene.addLayout(nav_bar)
        self.main_scene.setStretchFactor(nav_bar, 0)

    # functions to set themes
    def set_light(self):
        self.app.setStyleSheet(self.light_theme)

    def set_dark(self):
        self.app.setStyleSheet(self.dark_theme)

    def set_system(self):
        pass

    def update_font(self, size):
        """
        update the app's text size based on preset options: small, medium, large
        """
        pass

    def add_game(self):
        """
        constructs the item dict and genre and platform lists, then adds the game and updates the model
        """
        add = self.menu_dict["add_game"]
        game = {}
        genres = None
        platforms = None
        # name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name
        for v in add.fields:
            obj = add.fields[v]
            if (obj is not None):
                f = obj.text()
                obj.clear()
                if (v == "genre"):
                   f = f.split(',')
                   if (len(f[0]) > 0):
                       genres = f
                elif (v == "platform"):
                    f = f.split(',')
                    if (len(f[0]) > 0):
                        platforms = f
                elif (len(f) > 0):
                    game[v] = f

        self.db.add_item(game, genres, platforms)
        self.game_table.setModel(self.db.get_games())

    def edit_game(self):
        """
        will get the current edit_game's fields and update the tuple in the game table
        takes a QSqlRecord containing the old version of the game
        """
        game = {}
        genres = []
        platforms = []
        edit = self.menu_dict["edit_game"]
        for v in edit.fields:
            obj = edit.fields[v]
            if (obj is not None):
                f = obj.text()
                obj.clear()
                if (v == "genre"):
                   f = f.split(',')
                   for i in range(len(f)):
                       f[i] = f[i].strip()
                   if (len(f[0]) > 0):
                       genres = f
                elif (v == "platform"):
                    f = f.split(',')
                    for i in range(len(f)):
                        f[i] = f[i].strip()
                    if (len(f[0]) > 0):
                        platforms = f
                elif (len(f) > 0):
                    game[v] = f

        self.db.edit_item(self.old_game_name, game, genres, platforms)
        self.game_table.setModel(self.db.get_games())

    def delete_game(self, name):
        """
        Prompts user for confirmation, then deletes the selected game
        """
        pass

    def load_settings(self):
        """
        loads the settings menu and connects functions to buttons
        """
        if ("settings" not in self.menu_dict):
            settings_ui = QFile("settings.ui")
            loader = QUiLoader()
            s = loader.load(settings_ui)
            settings_ui.close()
            if not s:
                print(loader.errorString())
                sys.exit(-1)
            s.hide()
            self.main_scene.addWidget(s)
            self.main_scene.setStretchFactor(s, 1)
            self.menu_dict["settings"] = s

            # connect buttons
            set_light = s.findChild(QRadioButton, "light_theme")
            set_dark = s.findChild(QRadioButton, "dark_theme")
            set_system = s.findChild(QRadioButton, "system_theme")
            set_light.clicked.connect(self.set_light)
            set_dark.clicked.connect(self.set_dark)
            set_system.clicked.connect(self.set_system)

    def load_edit(self):
        """
        loads the edit game menu, sets up functionality
        """
        if ("edit_game" not in self.menu_dict):
            # load add_game ui file, then modify it
            edit_game_ui = QFile("add_game.ui")
            loader = QUiLoader()
            edit = loader.load(edit_game_ui)
            edit_game_ui.close()
            if not edit:
                print(loader.errorString())
                sys.exit(-1)
            edit.hide()

            self.main_scene.addWidget(edit)
            self.main_scene.setStretchFactor(edit, 1)
            self.menu_dict["edit_game"] = edit

            title = edit.findChild(QLabel, "title")
            title.setText("Edit Game")

            # set up functionality
            edit = self.menu_dict["edit_game"]
            edit_game = edit.findChild(QPushButton, "add_game")
            edit_game.setText("Edit Game")

            edit.fields = {}
            edit.fields["name"] = edit.findChild(QLineEdit, "name_edit")
            edit.fields["progress"] = edit.findChild(QLineEdit, "progress_edit")
            edit.fields["hours_played"] = edit.findChild(QLineEdit, "hours_edit")
            edit.fields["start_date"] = edit.findChild(QLineEdit, "startdate_edit")
            edit.fields["end_date"] = edit.findChild(QLineEdit, "enddate_edit")
            edit.fields["total_achievements"] = edit.findChild(QLineEdit, "total_edit")
            edit.fields["completed_achievements"] = edit.findChild(QLineEdit, "completed_edit")
            edit.fields["series_name"] = edit.findChild(QLineEdit, "series_edit")

            edit.fields["genre"] = edit.findChild(QLineEdit, "genre_edit")
            edit.fields["platform"] = edit.findChild(QLineEdit, "platform_edit")

            edit_game.clicked.connect(self.edit_game)


    def load_add(self):
        """
        loads the add game menu and connects function to button
        """
        if ("add_game" not in self.menu_dict):
            add_game_ui = QFile("add_game.ui")
            loader = QUiLoader()
            add = loader.load(add_game_ui)
            add_game_ui.close()

            if not add:
                print(loader.errorString())
                sys.exit(-1)

            add.hide()
            self.main_scene.addWidget(add)
            self.main_scene.setStretchFactor(add, 1)
            self.menu_dict["add_game"] = add

            add_game = add.findChild(QPushButton, "add_game")
            add.fields = {}
            add.fields["name"] = add.findChild(QLineEdit, "name_edit")
            add.fields["progress"] = add.findChild(QLineEdit, "progress_edit")
            add.fields["hours_played"] = add.findChild(QLineEdit, "hours_edit")
            add.fields["start_date"] = add.findChild(QLineEdit, "startdate_edit")
            add.fields["end_date"] = add.findChild(QLineEdit, "enddate_edit")
            add.fields["total_achievements"] = add.findChild(QLineEdit, "total_edit")
            add.fields["completed_achievements"] = add.findChild(QLineEdit, "completed_edit")
            add.fields["series_name"] = add.findChild(QLineEdit, "series_edit")

            add.fields["genre"] = add.findChild(QLineEdit, "genre_edit")
            add.fields["platform"] = add.findChild(QLineEdit, "platform_edit")

            add_game.clicked.connect(self.add_game)

    def show_games(self):
        if (not self.current_menu == "games"):
            self.menu_dict[self.current_menu].hide()
            self.current_menu = "games"
            self.menu_dict["games"].show()

    def show_add(self):
        if (not self.current_menu == "add_game"):
            self.menu_dict[self.current_menu].hide()
            self.current_menu = "add_game"
            self.menu_dict[self.current_menu].show()

    def show_edit(self):
        """
        shows the edit game menu if a game row has been selected (and populates its fields with the related data),
        otherwise tells the user to select a row to edit
        """
        selected_indexes = self.game_table.selectionModel().selectedIndexes()
        selected_rows = sorted(set(i.row() for i in selected_indexes))

        if (len(selected_rows) > 1):
            msg = QMessageBox()
            msg.setText("More than one game selected; please select exactly one game for editing.")
            msg.exec()
        elif (len(selected_rows) == 0):
            msg = QMessageBox()
            msg.setText("No game selected; please select one game for editing.")
            msg.exec()
        else:
            # get game and populate menu fields
            row = selected_rows[0]
            game_name = self.game_table.model().index(row, 0).data()
            game = self.db.get_game(game_name)

            edit = self.menu_dict["edit_game"]
            for i, f in enumerate(edit.fields):
                if (game.isNull(f)):
                    edit.fields[f].setText("")
                else:
                    edit.fields[f].setText(str(game.value(i)))

            if (not self.current_menu == "edit_game"):
                self.menu_dict[self.current_menu].hide()
                self.current_menu = "edit_game"
                self.menu_dict[self.current_menu].show()
                self.old_game_name = game_name

    def show_settings(self):
        if (not self.current_menu == "settings"):
            self.menu_dict[self.current_menu].hide()
            self.current_menu = "settings"
            self.menu_dict["settings"].show()


if __name__ == "__main__":
    app = QApplication([])

    main_window = MainWindow(app)

    main_window.setMinimumHeight(480)
    main_window.setMinimumWidth(720)
    main_window.show()
    sys.exit(app.exec())



