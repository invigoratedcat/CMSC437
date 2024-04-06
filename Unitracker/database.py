# This Python file uses the following encoding: utf-8
from PySide6.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel
from PySide6.QtCore import Qt
import os


class database:
    def __init__(self):
        self.db_name = "./UnitrackerGames.sqlite"
        self.db = QSqlDatabase().addDatabase("QSQLITE")
        self.db.setDatabaseName(self.db_name)

        # name VARCHAR(25), progress INT(3), hours_played NUMERIC(30), start_date DATE, end_date DATE, total_achievements INT(20), completed_achievements INT(20), series_name VARCHAR(25)
        self.MAX_VALUES = 8

        try:
            file = open(self.db_name, 'x')
            file.close()
        except FileExistsError:
            pass

    def create_db(self):
        if not self.db.isOpen():
            self.db.open()
        # load file
        f = open("createDB.sql")
        cmds = []
        s = f.readline()
        while (len(s) > 0):
            if not s.isspace():
                cmds.append(s[:-2])
            s = f.readline()
        # execute creation queries
        for i in cmds:
            q = QSqlQuery(i)
            if not q.exec():
                print(self.db.lastError())
                return False
        f.close()
        return True

    def get_games(self):
        """
        return a QSqlQueryModel with all the game records
        """
        headers = ["Name","Progress", "Hours Played", "Start Date", "End Date", "Total achievements", "Completed achievements", "Series name"]
        model = QSqlQueryModel()
        model.setQuery("SELECT * FROM game")
        for i in range(self.MAX_VALUES):
            model.setHeaderData(i, Qt.Horizontal, headers[i])
        return model

    def add_item(self, item):
        """
        given a list of values to make a game item from, adds said item to the db and returns the result
        """

        q_obj = QSqlQuery()
        q_obj.prepare("INSERT INTO game (name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")

        # bind values

        for i in range(self.MAX_VALUES):
            if i < len(item):
                q_obj.bindValue(i, item[i])
            else:
                q_obj.bindValue(i, "NULL")
        rv = q_obj.exec()
        q_obj.finish()
        return rv

    def edit_item(self, item):
        pass

    def close(self):
        if self.db.isOpen():
            self.db.close()

    def open(self):
        if not self.db.isOpen():
            self.db.open()
