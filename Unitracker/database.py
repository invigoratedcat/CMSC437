# This Python file uses the following encoding: utf-8
from PySide6.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel
from PySide6.QtCore import Qt, QSortFilterProxyModel
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

    def import_db(self, filename):
        """
        given a .sqlite filename, will check if it has the valid table and attribute setup
        before overwriting the current database with it
        """
        try:
            file = open(filename, 'r')
            file.close()
            test_db = self.db.addDatabase("QSQLITE", filename)
            test_db.setDatabaseName("test_connection")
            test_db.open()

            # test that each table exists and has all the attributes
            q_test = QSqlQuery("test_connection")
            q_test.prepare("SELECT name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name FROM game")
            if (not q_test.exec()):
                print("game table error")
                return False

            if not (q_test.exec("SELECT game_name, name FROM genre")):
                print("genre table error")
                return False

            if not (q_test.exec("SELECT game_name, name FROM platform")):
                print("platform table error")
                return False

            if (not q_test.exec("SELECT name, num_games, total_playtime FROM series")):
                print("series table error")
                return False

            test_db.close()
            test_db.removeDatabase("test_connection")

            # TODO: overwrite the database
            return True
        except FileNotFoundError:
            return False

    def get_games(self):
        """
        return a QSqlQueryModel with all the game records
        """
        headers = ["Name","Progress", "Hours Played", "Start Date", "End Date", "Total\nAchievements", "Completed\nAchievements", "Series name", "Genre", "Platform"]
        model = QSqlQueryModel()
        q = "WITH genres AS (SELECT * FROM genre) platforms AS (SELECT * FROM platform)"
        # name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name, genre.name AS genre
        #model.setQuery("SELECT game.name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name, group_concat(genre.name, ',') AS genre_name, group_concat(platform.name, ',') AS platform_name FROM game LEFT JOIN (genre NATURAL JOIN platform) GROUP BY game.name")
        #model.setQuery("WITH g_genres AS (SELECT * FROM game LEFT JOIN genre ON (game.name == genre.game_name)), g_platform AS (SELECT * FROM game LEFT JOIN platform ON (game.name == platform.game_name)) SELECT * FROM g_genre LEFT JOIN g_platform")
        #model.setQuery("WITH g_genres AS (SELECT *, group_concat(genre.name, ',') FROM game LEFT JOIN genre ON (game.name == genre.game_name) GROUP BY game.name), p AS (SELECT *, group_concat(platform.name, ',') FROM platform) SELECT * FROM g_genres LEFT JOIN p ON (g_genres.name == p.game_name)")

        # mostly working, just has duplicate genre/platform due to joining...
        model.setQuery("SELECT game.name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name, group_concat(genre.name, ',') AS genre_name, group_concat(platform.name, ',') AS platform_name FROM game LEFT JOIN genre ON (game.name == genre.game_name) LEFT JOIN platform ON (game.name == platform.game_name) GROUP BY game.name")

        #model.setQuery("SELECT game.name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name, genre.name, platform.name FROM game LEFT JOIN genre ON (game.name == genre.game_name) LEFT JOIN platform ON (game.name == platform.game_name)")
        for i in range(len(headers)):
            model.setHeaderData(i, Qt.Horizontal, headers[i])

        proxyModel = QSortFilterProxyModel()
        proxyModel.setSourceModel(model)

        return proxyModel

    def add_item(self, item, genres=None, platforms=None):
        """
        item: dict of values to make a game item from; adds said item to the db
        and returns the result
        genres: list of genres to add for a game
        platforms: list of platforms to add for a game
        """

        # construct the query string
        query = "INSERT INTO game ("
        for v in item:
            query += v + ", "

        query = query [:len(query) - 2] + ")"
        query += " VALUES ("
        num_fields = len(item)
        for i in range(num_fields):
            if (i != num_fields - 1):
                query += "?, "
            else:
                query += "?)"

        q_obj = QSqlQuery()
        # insert series into the series table in case it doesn't exist
        if ("series_name" in item.keys()):
            # check for old series
            q_obj.prepare("SELECT * FROM series WHERE name=?")
            q_obj.bindValue(0, item["series_name"])
            q_obj.exec()
            q_obj.next()
            old_series = q_obj.record()

            if (old_series.isNull("series_name")):
                # series doesn't exist so just add it
                q_obj.prepare("INSERT INTO series (name, num_games, total_playtime) VALUES (?, ?, ?)")
                q_obj.bindValue(0, item["series_name"])
                q_obj.bindValue(1, 1)
                q_obj.bindValue(2, item["hours_played"])
                q_obj.exec()
            else:
                # series exists so update derived attributes
                q_obj.prepare("UPDATE series SET num_games=?, total_playtime=? WHERE name=?")
                q_obj.bindValue(0, old_series.value("num_games") + 1)
                q_obj.bindValue(1, old_series.value("total_playtime") + item["hours_played"])
                q_obj.bindValue(2, item["series_name"])
                q_obj.exec()

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

    def edit_item(self, old_name, item, genres, platforms):
        """
        old_name: previous name of game
        item: dict of values to set a game item from, updates the item in the db if it exists and returns the result
        genres: list of genres to add for a game
        platforms: list of platforms to add for a game
        """
        q_obj = QSqlQuery()
        # retrieve old record of the game
        q_obj.prepare("SELECT * FROM game WHERE name=?")
        q_obj.bindValue(0, old_name)
        q_obj.exec()
        q_obj.last()
        old_game = q_obj.record()

        # construct update query for game table
        query = "UPDATE game SET "
        for k in item:
            query += k + "=?,"

        query = query [:len(query) - 1] + " "
        query += "WHERE name=?"

        # bind values and execute query
        q_obj.prepare(query)
        for i, k in enumerate(item):
            q_obj.bindValue(i, item[k])
            if (i == len(item) - 1):
                q_obj.bindValue(i + 1, item["name"])
        rv = q_obj.exec()
        if (not rv):
            # TODO: display error message?
            print(self.db.lastError())

        # add new series
        if ("series_name" in item.keys()):
            # check if old series is the same as new series and update derived attributes
            old_series = None
            if (not old_game.isNull("series_name")):
                q_obj.prepare("SELECT * FROM series WHERE name=?")
                q_obj.bindValue(0, old_game.value("series_name"))
                q_obj.exec()
                q_obj.next()
                old_series = q_obj.record()

            # old series = new series so update attributes based on new series
            if (not old_series is None and (item["series_name"] == old_game.value("series_name"))):
                old_hours = 0.0 if old_game.isNull("hours_played") else float(old_game.value("hours_played"))
                old_total = 0.0 if old_series.isNull("total_playtime") else float(old_series.value("total_playtime"))

                q_obj.prepare("UPDATE series SET total_playtime=? WHERE name=?")
                q_obj.bindValue(0, float(item["hours_played"]) + old_total - old_hours)
                q_obj.bindValue(1, old_game.value("series_name"))
                q_obj.exec()
            # old series and new series are different
            elif (not old_series is None and (item["series_name"] != old_game.value("series_name"))):
                # if old series still has at least one game attached, update it
                old_hours = 0.0 if old_game.isNull("hours_played") else float(old_game.value("hours_played"))
                old_total = 0.0 if old_series.isNull("total_playtime") else float(old_series.value("total_playtime"))
                old_num = old_series.value("num_games")

                if (old_num - 1 > 0):
                    q_obj.prepare("UPDATE series SET num_games=?, total_playtime=? WHERE name=?")
                    q_obj.bindValue(0, old_num - 1)
                    q_obj.bindValue(1, old_total - old_hours)
                    q_obj.bindValue(2, old_game.value("series_name"))
                    q_obj.exec()
                # old series has no games left, delete it
                else:
                    q_obj.prepare("DELETE FROM series WHERE name=?")
                    q_obj.bindValue(0, old_game.value("series_name"))
                    q_obj.exec()
            # no old series, so add new series
            else:
                q_obj.prepare("INSERT INTO series (name, num_games, total_playtime) VALUES (?, ?, ?)")
                q_obj.bindValue(0, item["series_name"])
                q_obj.bindValue(1, 1)
                q_obj.bindValue(2, item["hours_played"])
                q_obj.exec()

        q_obj.prepare("SELECT * FROM genre WHERE game_name=?")
        q_obj.bindValue(0, old_game.value("name"))
        q_obj.exec()
        q_obj.next()
        old_genres = self.get_genres(old_game.value("name"))

        # replace old genre records with new ones
        if (set(old_genres) != set(genres)):
            q_obj.prepare("DELETE FROM genre WHERE game_name=?")
            q_obj.bindValue(0, old_game.value("name"))
            q_obj.exec()

            if (genres is not None):
                # add genres
                for i in range(len(genres)):
                    q_obj.prepare("INSERT INTO genre (game_name, name) VALUES (?, ?)")
                    q_obj.bindValue(0, item["name"])
                    q_obj.bindValue(1, genres[i])
                    rv = q_obj.exec()

        q_obj.prepare("SELECT * FROM platform WHERE game_name=?")
        q_obj.bindValue(0, old_game.value("name"))
        q_obj.exec()
        q_obj.next()
        old_platforms = self.get_platforms(old_game.value("name"))

        # replace old platform records with new ones
        if (set(old_platforms) != set(platforms)):
            q_obj.prepare("DELETE FROM platform WHERE game_name=?")
            q_obj.bindValue(0, old_game.value("name"))
            q_obj.exec()

            # add platforms
            if (platforms is not None):
                for i in range(len(platforms)):
                    q_obj.prepare("INSERT INTO platform (game_name, name) VALUES (?, ?)")
                    q_obj.bindValue(0, item["name"])
                    q_obj.bindValue(1, platforms[i])
                    rv = q_obj.exec()
            elif (old_game.value("name") == item["name"]):
                pass

    def get_game(self, name):
        """
        returns a game item given a name
        """
        q_obj = QSqlQuery()
        q_obj.prepare("SELECT * FROM game WHERE name=?")
        q_obj.bindValue(0, name)
        q_obj.exec()
        q_obj.next()
        return q_obj.record()

    def get_genres(self, name):
        """
        returns a list of all genres given a game's name
        """
        q_obj = QSqlQuery()
        q_obj.prepare("SELECT * FROM genre WHERE game_name=?")
        q_obj.bindValue(0, name)
        q_obj.exec()
        genres = []
        while (q_obj.next()):
            genres.append(q_obj.record().value("name"))
        return genres

    def get_platforms(self, name):
        """
        returns a list of all platforms given a game's name
        """
        q_obj = QSqlQuery()
        q_obj.prepare("SELECT * FROM platform WHERE game_name=?")
        q_obj.bindValue(0, name)
        q_obj.exec()
        platforms = []
        while (q_obj.next()):
            platforms.append(q_obj.record().value("name"))

        return platforms

    def close(self):
        if self.db.isOpen():
            self.db.close()

    def open(self):
        if not self.db.isOpen():
            self.db.open()
