# This Python file uses the following encoding: utf-8
import sys
import qdarktheme
import json
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QLabel, QButtonGroup
from PySide6.QtWidgets import QBoxLayout, QVBoxLayout, QPushButton, QGridLayout
from PySide6.QtWidgets import QTableView, QHeaderView, QFrame, QRadioButton, QLineEdit
from PySide6.QtWidgets import QMessageBox, QComboBox, QFileDialog, QSizePolicy, QSpacerItem
from PySide6 import QtCore
from PySide6.QtCore import Qt, QFile
from PySide6.QtGui import QShortcut, QKeySequence, QIntValidator
from PySide6.QtUiTools import QUiLoader
from database import database


class MainWindow(QMainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)
        self.app = app
        self.setWindowTitle("Unitracker")
        # member vars
        self.main_scene = QBoxLayout(QBoxLayout.LeftToRight)
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.main_scene)
        self.current_theme = "dark"
        self.current_menu = "games"
        self.menu_dict = {} # contains all menus
        self.settings_buttons = {} # contains most of the settings ui elements
        self.page_bar = {} # contains the ui elements for game pages
        self.game_search = {} # contains most of the ui elements for game search bar
        self.files_path = "./resources/"  # used for accessing ui and database files

        # load and create menus
        self.create_navbar()
        self.create_games_menu()
        self.create_series_menu()

        self.load_settings()
        self.load_add()
        self.load_edit()
        self.load_help()
        self.create_shortcuts()

        # initialize database handler
        self.db = database(self.files_path)
        if (not self.db.create_db()):
            QMessageBox.critical(self, "Database Error", "Database creation failed.")
            sys.exit(-1)
        else:
            # load config, set up games and series tables, page bar
            self.load_config()
            self.game_table.setModel(self.db.get_games())
            self.game_table.model().setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.series_table.setModel(self.db.get_series())
            self.update_page_bar()

    # manual menu creation functions
    def create_games_menu(self):
        """
        construct and show the menu containing the games table, search bar, and page bar
        """
        games_frame = QFrame()
        games_layout = QVBoxLayout()
        self.game_table = QTableView()

        # set view properties
        self.game_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.game_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.game_table.verticalHeader().hide()
        self.game_table.setGridStyle(Qt.SolidLine)
        self.game_table.setSortingEnabled(True)
        # set default order to descending by game name
        self.game_table.sortByColumn(0, Qt.DescendingOrder)

        title = QLabel("Games")
        title.setAlignment(Qt.AlignCenter)

        # create page bar
        page_layout = self.create_page_bar()

        # add search bar
        self.create_search_box()

        # connect everything
        games_layout.addWidget(title)
        games_layout.addLayout(self.game_search["box"])
        games_layout.addWidget(self.game_table)
        games_layout.addLayout(page_layout)
        games_frame.setLayout(games_layout)

        self.menu_dict["games"] = games_frame
        self.main_scene.addWidget(games_frame)


    def create_page_bar(self):
        """
        creates the page bar ui and sets up the functionality
        """
        page_label = QLabel("Page 1")
        page_label.setAlignment(Qt.AlignCenter)
        next_page = QPushButton("Next")
        previous_page = QPushButton("Previous")
        next_page.hide()
        previous_page.hide()

        page_layout = QGridLayout()
        self.page_bar["next"] = next_page
        self.page_bar["previous"] = previous_page
        self.page_bar["label"] = page_label

        # layout page stuff in a grid with horizontal spacers to keep them centered
        h_spacer1 = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacer2 = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        page_layout.addItem(h_spacer1)
        page_layout.addWidget(previous_page, 0, 1)
        page_layout.addWidget(page_label, 0, 2)
        page_layout.addWidget(next_page, 0, 3)
        page_layout.addItem(h_spacer2, 0, 4)

        next_page.clicked.connect(self.next_page)
        previous_page.clicked.connect(self.previous_page)

        return page_layout

    def create_search_box(self):
        """
        creates the search bar ui and sets up its functionality
        """
        self.game_search["bar"] = QLineEdit()
        self.game_search["bar"].setToolTip("Enter what you want to search here")
        self.game_search["options"] = QButtonGroup()

        search_label = QLabel("Search\nGames:")
        search_label.setAlignment(Qt.AlignRight)
        search_box = QGridLayout()
        self.game_search["box"] = search_box
        option_label = QLabel("Search by:")
        option_label.setAlignment(Qt.AlignRight)

        # filter options
        search_name = QRadioButton("Name")
        search_prog = QRadioButton("Progress")
        search_hours = QRadioButton("Hours\nPlayed")
        search_start = QRadioButton("Start\nDate")
        search_end = QRadioButton("End\nDate")
        search_total = QRadioButton("Total\nAchievements")
        search_completed = QRadioButton("Completed\nAchievements")
        search_series = QRadioButton("Series")
        search_genre = QRadioButton("Genre")
        search_platform = QRadioButton("Platform")
        sbl = [search_name, search_prog, search_hours, search_start, search_end,
            search_total, search_completed, search_series, search_genre, search_platform]

        search_box.addWidget(search_label)
        search_box.addWidget(self.game_search["bar"], 0, 1, 1, -1)
        search_box.addWidget(option_label, 1, 0)

        for i in range(1, len(sbl) + 1):
            self.game_search["options"].addButton(sbl[i - 1], i)
            if (i == 1):
                sbl[i].setChecked(True)
            sbl[i - 1].setToolTip("Filter by " + sbl[i - 1].text())
            search_box.addWidget(sbl[i - 1], 1, i)

        self.game_search["options"].buttonPressed.connect(self.set_game_filter)
        self.game_search["bar"].returnPressed.connect(self.search_games)

    def create_series_menu(self):
        """
        set up the table of series
        """
        series_frame = QFrame()
        series_layout = QVBoxLayout()
        series_table = QTableView()
        self.series_table = series_table

        series_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        series_table.verticalHeader().hide()
        series_table.setSortingEnabled(True)
        series_table.sortByColumn(0, Qt.DescendingOrder)

        title = QLabel("Series")
        title.setAlignment(Qt.AlignCenter)
        series_layout.addWidget(title)
        series_layout.addWidget(series_table)
        series_frame.setLayout(series_layout)
        series_frame.hide()

        self.menu_dict["series"] = series_frame
        self.main_scene.addWidget(series_frame)

    def create_shortcuts(self):
        """
        create/set all the keyboard shortcuts
        """
        exit = QShortcut(QKeySequence("Ctrl+Q"), self)
        goto_games = QShortcut(QKeySequence("Alt+G"), self)
        goto_series = QShortcut(QKeySequence("Alt+R"), self)
        goto_add = QShortcut(QKeySequence("Alt+A"), self)
        goto_settings = QShortcut(QKeySequence("Alt+S"), self)
        goto_edit = QShortcut(QKeySequence("Alt+E"), self)
        goto_delete = QShortcut(QKeySequence("Alt+D"), self)
        goto_help = QShortcut(QKeySequence("Alt+H"), self)

        exit.activated.connect(sys.exit)
        goto_games.activated.connect(self.show_games)
        goto_series.activated.connect(self.show_series)
        goto_add.activated.connect(self.show_add)
        goto_settings.activated.connect(self.show_settings)
        goto_edit.activated.connect(self.show_edit)
        goto_delete.activated.connect(self.delete_game)
        goto_help.activated.connect(self.show_help)

    def create_navbar(self):
        """
        create and add the main navigation bar to the main window
        """
        nav_bar = QVBoxLayout()

        # create buttons
        games = QPushButton("Games")
        games.setToolTip("Opens the games menu")
        series = QPushButton("Series")
        series.setToolTip("Opens the series menu")
        add_game = QPushButton("Add Game")
        add_game.setToolTip("Opens the add game menu")
        edit_game = QPushButton("Edit Game")
        edit_game.setToolTip("Opens the edit game menu if a game is selected")
        delete_game = QPushButton("Delete Game")
        delete_game.setToolTip("Prompts you for deletion of the currently selected game(s)")
        settings = QPushButton("Settings")
        settings.setToolTip("Opens the settings menu")
        help = QPushButton("Help")
        help.setToolTip("Opens the help menu")

        nav_bar.addWidget(games)
        nav_bar.addWidget(series)
        nav_bar.addWidget(add_game)
        nav_bar.addWidget(edit_game)
        nav_bar.addWidget(delete_game)
        nav_bar.addWidget(settings)
        nav_bar.addWidget(help)

        # connect functionality
        settings.clicked.connect(self.show_settings)
        games.clicked.connect(self.show_games)
        series.clicked.connect(self.show_series)
        add_game.clicked.connect(self.show_add)
        edit_game.clicked.connect(self.show_edit)
        delete_game.clicked.connect(self.delete_game)
        help.clicked.connect(self.show_help)

        self.main_scene.addLayout(nav_bar)
        self.main_scene.setStretchFactor(nav_bar, 0)

    # config saving/loading functions
    def save_config(self):
        """
        saves the current config to a json file
        """
        with open(self.files_path + "config.json", 'w') as f:
            json.dump(self.config, f)

    def load_config(self):
        """
        opens the config file and updates settings to match,
        or if no valid config file exists, uses defaults
        """
        # try loading a config file
        try:
            f = open(self.files_path + "config.json")
            config = json.load(f)
            if (config is None or "text_size" not in config or "theme" not in config
                or "screen_size" not in config or "items_per_page" not in config):
                f.close()
                raise FileNotFoundError
            self.config = config
            f.close()
        except FileNotFoundError:
            # no file found so use defaults
            self.config = {"text_size": 1, "theme": "auto", "items_per_page": 15, "screen_size": 1}

        # update configuration
        self.update_font(self.config["text_size"])
        self.set_theme(theme=self.config["theme"])
        self.settings_buttons["set_text"].setCurrentIndex(self.config["text_size"])
        self.settings_buttons[self.config["theme"]].setChecked(True)
        self.db.set_items_per_page(self.config["items_per_page"])
        self.settings_buttons["ipp"].setText(str(self.config["items_per_page"]))
        screen_button = self.settings_buttons["screen_size"].button(self.config["screen_size"])
        self.set_screen_size(screen_button)

    # functions to set options
    def set_theme(self, checked=False, theme=None):
        """
        sets the app's theme based on either a given theme
        or which button in settings is checked
        """
        if (theme is not None):
            qdarktheme.setup_theme(theme, additional_qss=self.font_qss)
            self.current_theme = theme
        else:
            light_b = self.settings_buttons["light"]
            dark_b = self.settings_buttons["dark"]
            system_b = self.settings_buttons["auto"]

            # set theme
            if (light_b.isChecked()):
                qdarktheme.setup_theme("light", additional_qss=self.font_qss)
                self.current_theme = "light"
            elif (dark_b.isChecked()):
                qdarktheme.setup_theme("dark", additional_qss=self.font_qss)
                self.current_theme = "dark"
            elif (system_b.isChecked()):
                qdarktheme.setup_theme("auto", additional_qss=self.font_qss)
                self.current_theme = "auto"
            self.update_font(self.config["text_size"])
            self.config["theme"] = self.current_theme
            self.save_config()

    def update_font(self, index):
        """
        update the app's text size based on preset options: small, medium, large
        """
        if (index == 0):
            self.font_qss = """
            * {
                font-size: 14px;
            }
            QLabel#title {
                font-size: 16px;
            }
            QTextBrowser#help_text {
                font-size: 14px;
            }
            """            
        elif (index == 1):
            self.font_qss = """
            * {
                font-size: 20px;
            }
            QLabel#title {
                font-size: 30px;
            }
            QTextBrowser#help_text {
                font-size: 20px;
            }
            """
        elif (index == 2):
            self.font_qss = """
            * {
                font-size: 26px;
            }
            QLabel#title {
                font-size: 48px;
            }
            QTextBrowser#help_text {
                font-size: 28px;
            }
            """

        # ensure pushbuttons are actually highlighted when tabbed through
        if (self.current_theme == "dark"):
            self.font_qss += """
            QPushButton:focus {
                background-color: white;
            }
            """
        else:
            self.font_qss += """
            QPushButton:focus {
                background-color: lightgrey;
            }
            """

        qdarktheme.setup_theme(self.current_theme, additional_qss=self.font_qss)
        self.config["text_size"] = index
        self.save_config()

    def set_screen_size(self, button_pressed):
        """
        sets the screen size
        """
        id = self.settings_buttons["screen_size"].id(button_pressed)
        if (id == 1):
            self.setWindowState(Qt.WindowNoState)
        elif (id == 2):
            self.setWindowState(Qt.WindowMaximized)
        elif (id == 3):
            self.setWindowState(Qt.WindowFullScreen)
        self.config["screen_size"] = id
        button_pressed.setChecked(True)
        self.save_config()

    def update_ipp(self):
        """
        updates the items (games) per page; only called when valid input is given
        """
        ipp = self.menu_dict["settings"].findChild(QLineEdit, "ipp").text()
        t = int(ipp)
        self.db.set_items_per_page(t)
        self.config["items_per_page"] = t
        self.game_table.setModel(self.db.get_games())
        self.update_page_bar()
        self.save_config()
        QMessageBox.information(self, "Success", "Games per page successfully updated")

    # import/export functions
    def start_import(self):
        """
        prompts user for file, and displays chosen file name
        """
        file_name = QFileDialog.getOpenFileName(self.menu_dict["settings"], "Choose import file", "~/", "(*.sqlite *.json)")
        chosen = self.menu_dict["settings"].findChild(QLabel, "chosen_import")
        chosen.setText(file_name[0])

    def finish_import(self):
        """
        called when user clicks "Import"; handles the actual importing
        and displaying the result to the user
        """
        chosen = self.menu_dict["settings"].findChild(QLabel, "chosen_import")
        to_import = chosen.text()
        success = False
        if (to_import[-6:] == "sqlite"):
            if (self.db.import_db(to_import)):
                success = True
        elif (to_import[-4:] == "json"):
            if (self.db.import_json(to_import)):
                success = True
        else:
            QMessageBox.critical(self, "Import Error", "Unsupported file format selected.")
            return

        if (success):
            QMessageBox.information(self, "Import Success", "Games successfully imported!")
            self.game_table.setModel(self.db.get_games())
            self.series_table.setModel(self.db.get_series())
            self.update_page_bar()
        else:
            QMessageBox.critical(self, "Import Error", "Import failed")

    def start_export(self):
        """
        handle calling the right export function and displaying result to user
        """
        file_name = QFileDialog.getSaveFileName(self.menu_dict["settings"], "Choose export file", "~/", "(*.sqlite *.json)")[0]
        success = False
        if (file_name[-6:] == "sqlite"):
            if (self.db.export_db(file_name)):
                success = True
        elif (file_name[-4:] == "json"):
            if (self.db.export_json(file_name)):
                success = True
        else:
            QMessageBox.critical(self, "Export Error", "Unsupported file format selected.")
            return

        if (success):
            QMessageBox.information(self, "Export Success", "Games successfully exported!")
        else:
            QMessageBox.critical(self, "Export Error", "Export failed")

    # page functions
    def next_page(self):
        """
        tries going to next page; updates visibility of next page button,
        and updates the table view
        """
        new_model = self.db.forward_page()
        if (new_model is not None):
            self.game_table.setModel(new_model)
            if (not self.db.has_next_page()):
                self.page_bar["next"].hide()
            self.page_bar["label"].setText(f'Page {self.db.get_current_page() + 1}')
        else:
            self.page_bar["next"].hide()
        if (not self.page_bar["previous"].isVisible()):
            self.page_bar["previous"].show()

    def previous_page(self):
        """
        tries going to previous page; updates visibility of previous page button,
        and updates the table view
        """
        new_model = self.db.backward_page()
        if (new_model is not None):
            self.game_table.setModel(new_model)
            if (self.db.get_current_page() == 0):
                self.page_bar["previous"].hide()
            self.page_bar["label"].setText(f'Page {self.db.get_current_page() + 1}')
        else:
            self.page_bar["previous"].hide()
        if (not self.page_bar["next"].isVisible()):
            self.page_bar["next"].show()

    def update_page_bar(self):
        """
        update page buttons, label
        """
        if (self.db.get_current_page() == 0):
            self.page_bar["previous"].hide()
        else:
            self.page_bar["previous"].show()

        if (self.db.has_next_page()):
            self.page_bar["next"].show()
        else:
            self.page_bar["next"].hide()
        self.page_bar["label"].setText(f'Page {self.db.get_current_page() + 1}')

    # search functions
    def set_game_filter(self, button):
        """
        sets which column the proxy model will filter on
        """
        column = self.game_search["options"].id(button) - 1
        self.game_table.model().setFilterKeyColumn(column)

    def search_games(self):
        """
        make proxy model perform the "search"/filter
        based on what's in the search bar
        """
        filter = self.game_search["bar"].text()
        self.game_table.model().setFilterRegularExpression(filter)

    # game functions
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

        if (not self.db.add_item(game, genres, platforms)):
            QMessageBox.critical(self, "Add Error", "Game was not successfully added")
        self.game_table.setModel(self.db.get_games())
        self.series_table.setModel(self.db.get_series())
        self.update_page_bar()

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
                    # convert comma separated list to actual list
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
        self.series_table.setModel(self.db.get_series())
        self.show_games()

    def delete_game(self):
        """
        Prompts user for confirmation, then deletes the selected games if user confirms
        """
        # Don't allow the user to delete a game unless they're on the games menu
        if (not self.current_menu == "games"):
            return

        selected_indexes = self.game_table.selectionModel().selectedIndexes()
        selected_rows = sorted(set(i.row() for i in selected_indexes))

        if (len(selected_rows) < 1):
            msg = QMessageBox.critical(self, "Delete Error", "No game selected; please choose at least one game to delete and try again.")
        # try to delete multiple games
        elif (len(selected_rows) > 1):
            game_names = ""
            to_delete = []
            for i in range(len(selected_rows)):
                temp = self.game_table.model().index(selected_rows[i], 0).data()
                game_names += temp + ", "
                to_delete.append(temp)
            game_names = game_names[:len(game_names) - 2]

            msg = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete the following games: \n" + game_names)
            if (msg == QMessageBox.Yes):
                for i in range(len(to_delete)):
                    self.db.delete_item(to_delete[i])
                self.game_table.setModel(self.db.get_games())
                self.series_table.setModel(self.db.get_series())
        # try to delete one game
        else:
            row = selected_rows[0]
            game_name = self.game_table.model().index(row, 0).data()

            msg = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete the game " + game_name)
            if (msg == QMessageBox.Yes):
                self.db.delete_item(game_name)
                self.game_table.setModel(self.db.get_games())
                self.series_table.setModel(self.db.get_series())
                self.update_page_bar()

    # functions for loading ui files/menus
    def load_settings(self):
        """
        loads the settings menu and connects functions to buttons
        """
        if ("settings" not in self.menu_dict):
            settings_ui = QFile(self.files_path + "settings.ui")
            loader = QUiLoader()
            s = loader.load(settings_ui)
            settings_ui.close()
            if not s:
                QMessageBox.critical(self, "Loading Error", "Settings menu failed to load!")
                print(loader.errorString())
                sys.exit(-1)
            s.hide()
            self.main_scene.addWidget(s)
            self.main_scene.setStretchFactor(s, 1)
            self.menu_dict["settings"] = s

            # connect buttons
            self.settings_buttons["set_text"] = s.findChild(QComboBox, "text_size")
            self.settings_buttons["light"] = s.findChild(QRadioButton, "light_theme")
            self.settings_buttons["dark"] = s.findChild(QRadioButton, "dark_theme")
            self.settings_buttons["auto"] = s.findChild(QRadioButton, "system_theme")
            self.settings_buttons["screen_size"] = QButtonGroup()
            start_import = s.findChild(QPushButton, "import_button")
            select_import = s.findChild(QPushButton, "select_import")
            start_export = s.findChild(QPushButton, "export_button")

            windowed = s.findChild(QRadioButton, "windowed")
            maximized = s.findChild(QRadioButton, "maximized")
            fullscreen = s.findChild(QRadioButton, "fullscreen")
            self.settings_buttons["screen_size"].addButton(windowed, 1)
            self.settings_buttons["screen_size"].addButton(maximized, 2)
            self.settings_buttons["screen_size"].addButton(fullscreen, 3)

            ipp = s.findChild(QLineEdit, "ipp")
            self.settings_buttons["ipp"] = ipp
            ipp_val = QIntValidator()
            ipp_val.setRange(1, 40)
            ipp.setValidator(ipp_val)

            self.settings_buttons["screen_size"].buttonPressed.connect(self.set_screen_size)
            self.settings_buttons["light"].clicked.connect(self.set_theme)
            self.settings_buttons["dark"].clicked.connect(self.set_theme)
            self.settings_buttons["auto"].clicked.connect(self.set_theme)
            self.settings_buttons["set_text"].currentIndexChanged.connect(self.update_font)
            ipp.returnPressed.connect(self.update_ipp)
            select_import.clicked.connect(self.start_import)
            start_import.clicked.connect(self.finish_import)
            start_export.clicked.connect(self.start_export)

    def load_help(self):
        """
        load the help menu
        """
        if ("help" not in self.menu_dict):
            help_ui = QFile(self.files_path + "help.ui")
            loader = QUiLoader()
            h = loader.load(help_ui)
            help_ui.close()
            if not h:
                QMessageBox.critical(self, "Loading Error", "Help menu failed to load!")
                print(loader.errorString())
                sys.exit(-1)
            h.hide()
            self.main_scene.addWidget(h)
            self.main_scene.setStretchFactor(h, 1)
            self.menu_dict["help"] = h

    def load_edit(self):
        """
        loads the edit game menu, sets up functionality
        """
        if ("edit_game" not in self.menu_dict):
            # load add_game ui file, then modify it
            edit_game_ui = QFile(self.files_path + "add_game.ui")
            loader = QUiLoader()
            edit = loader.load(edit_game_ui)
            edit_game_ui.close()
            if not edit:
                QMessageBox.critical(self, "Loading Error", "Edit menu failed to load!")
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
            edit_game.setToolTip("Updates the game with the currently entered information")

            edit.fields = {}
            edit.fields["name"] = edit.findChild(QLineEdit, "name_edit")
            edit.fields["progress"] = edit.findChild(QLineEdit, "progress_edit")

            prog_val = QIntValidator()
            prog_val.setRange(0,100)
            edit.fields["progress"].setValidator(prog_val)

            edit.fields["hours_played"] = edit.findChild(QLineEdit, "hours_edit")
            hours_val = QIntValidator()
            hours_val.setBottom(0)
            edit.fields["hours_played"].setValidator(hours_val)

            edit.fields["start_date"] = edit.findChild(QLineEdit, "startdate_edit")
            edit.fields["end_date"] = edit.findChild(QLineEdit, "enddate_edit")
            edit.fields["total_achievements"] = edit.findChild(QLineEdit, "total_edit")
            edit.fields["total_achievements"].setValidator(hours_val)
            edit.fields["completed_achievements"] = edit.findChild(QLineEdit, "completed_edit")
            edit.fields["completed_achievements"].setValidator(hours_val)
            edit.fields["series_name"] = edit.findChild(QLineEdit, "series_edit")

            edit.fields["genre"] = edit.findChild(QLineEdit, "genre_edit")
            edit.fields["platform"] = edit.findChild(QLineEdit, "platform_edit")

            edit_game.clicked.connect(self.edit_game)


    def load_add(self):
        """
        loads the add game menu and connects function to button
        """
        if ("add_game" not in self.menu_dict):
            add_game_ui = QFile(self.files_path + "add_game.ui")
            loader = QUiLoader()
            add = loader.load(add_game_ui)
            add_game_ui.close()

            if not add:
                QMessageBox.critical(self, "Loading Error", "Add menu failed to load!")
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
            prog_val = QIntValidator()
            prog_val.setRange(0, 100)
            add.fields["progress"].setValidator(prog_val)
            add.fields["hours_played"] = add.findChild(QLineEdit, "hours_edit")
            hours_val = QIntValidator()
            hours_val.setBottom(0)
            add.fields["hours_played"].setValidator(hours_val)
            add.fields["start_date"] = add.findChild(QLineEdit, "startdate_edit")
            add.fields["end_date"] = add.findChild(QLineEdit, "enddate_edit")
            add.fields["total_achievements"] = add.findChild(QLineEdit, "total_edit")
            add.fields["completed_achievements"] = add.findChild(QLineEdit, "completed_edit")
            add.fields["series_name"] = add.findChild(QLineEdit, "series_edit")

            add.fields["genre"] = add.findChild(QLineEdit, "genre_edit")
            add.fields["platform"] = add.findChild(QLineEdit, "platform_edit")

            add_game.clicked.connect(self.add_game)

    # functions to show menus
    def show_games(self):
        if (not self.current_menu == "games"):
            self.menu_dict[self.current_menu].hide()
            self.current_menu = "games"
            self.menu_dict["games"].show()

    def show_series(self):
        if (not self.current_menu == "series"):
            self.menu_dict[self.current_menu].hide()
            self.current_menu = "series"
            self.menu_dict["series"].show()

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
            msg = QMessageBox
            msg.setText("More than one game selected; please select exactly one game for editing.")
            msg.exec()
        elif (len(selected_rows) == 0):
            msg = QMessageBox()
            msg.setText("No game selected; please select one game for editing.")
            msg.exec()
        else:
            # get game, genre, and platform records
            row = selected_rows[0]
            game_name = self.game_table.model().index(row, 0).data()
            game = self.db.get_game(game_name)
            genres = self.db.get_genres(game_name)
            platforms = self.db.get_platforms(game_name)

            # populate menu fields
            edit = self.menu_dict["edit_game"]
            for i, f in enumerate(edit.fields):
                if (platforms is not None and f == "platform"):
                    pforms = ""
                    for j in range(len(platforms)):
                        pforms += platforms[j] + ","
                    pforms = pforms[:len(pforms) - 1]
                    edit.fields[f].setText(pforms)
                elif (genres is not None and f == "genre"):
                    g = ""
                    for j in range(len(genres)):
                        g += genres[j] + ","
                    g = g[:len(g) - 1]
                    edit.fields[f].setText(g)
                elif (game.isNull(f)):
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

    def show_help(self):
        if (not self.current_menu == "help"):
            self.menu_dict[self.current_menu].hide()
            self.current_menu = "help"
            self.menu_dict["help"].show()

if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)
    app = QApplication()

    main_window = MainWindow(app)
    main_window.setAttribute(Qt.WA_DeleteOnClose, True)

    main_window.setMinimumHeight(480)
    main_window.setMinimumWidth(720)
    main_window.show()
    sys.exit(app.exec())
