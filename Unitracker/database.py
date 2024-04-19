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
        headers = ["Name","Progress", "Hours Played", "Start Date", "End Date", "Total\nAchievements", "Completed\nAchievements", "Series name", "Genre", "Platform"]
        model = QSqlQueryModel()
        q = "WITH genres AS (SELECT name FROM genre) SELECT * FROM game LEFT JOIN ()"
        # name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name, genre.name AS genre
        #model.setQuery("SELECT * FROM game LEFT JOIN genre ON (game.name == genre.game_name)")
        model.setQuery("SELECT game.name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name, genre.name FROM game LEFT JOIN genre ON (game.name == genre.game_name)")
        for i in range(len(headers)):
            model.setHeaderData(i, Qt.Horizontal, headers[i])
        return model

    def add_item(self, item, genres=None, platforms=None):
        """
        item: dict of values to make a game item from, adds said item to the db and returns the result
        genres: list of genres to add for a game
        platforms: list of platforms to add for a game
        """

        # fields = ["name", "progress", "hours_played", "start_date", "end_date", "total_achievements", "completed_achievements", "series_name"]
        query = "INSERT INTO game ("
        for v in item:
            query += v + ", "

        query = query [:len(query) - 2] + ")"
        query += " VALUES ("
        print(query)
        num_fields = len(item)
        for i in range(num_fields):
            if (i != num_fields - 1):
                query += "?, "
            else:
                query += "?)"
        print(query)


        q_obj = QSqlQuery()
        # q_obj.prepare("INSERT INTO game (name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
        q_obj.prepare(query)

        # bind values
        for i, v in enumerate(item):
            q_obj.bindValue(i, item[v])
            # q_obj.bindValue(i, "NULL")
        rv = q_obj.exec()

        # add genres
        if (genres is not None):
            for i in range(len(genres)):
                q_obj.prepare("INSERT INTO genre (game_name, name) VALUES (?, ?)")
                q_obj.bindValue(0, item["name"])
                q_obj.bindValue(1, genres[i])
                rv = q_obj.exec()

        # add platforms
        if (platforms is not None):
            for i in range(len(platforms)):
                q_obj.prepare("INSERT INTO platform (game_name, name) VALUES (?, ?)")
                q_obj.bindValue(0, item["name"])
                q_obj.bindValue(1, platforms[i])
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
