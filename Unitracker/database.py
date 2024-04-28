# This Python file uses the following encoding: utf-8
from PySide6.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel
from PySide6.QtCore import Qt, QSortFilterProxyModel
import json
import shutil
import os
from math import ceil


class database:
    def __init__(self, filepath="./"):
        self.files_path = filepath
        self.db_name = self.files_path + "UnitrackerGames.sqlite"
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(self.db_name)
        self.DEFAULT_IPP = 10
        self.items_per_page = self.DEFAULT_IPP
        self.current_page = 0

        try:
            file = open(self.db_name, 'x')
            file.close()
        except FileExistsError:
            pass

    def set_items_per_page(self, ipp):
        """
        sets items per page as ipp
        """
        self.items_per_page = ipp if ipp > 0 else self.DEFAULT_IPP

    def has_next_page(self):
        """
        returns whether the game table has a page after the current one
        """
        next_page = QSqlQuery()
        query = "SELECT * FROM game LIMIT " + str(self.items_per_page)
        query += " OFFSET " + str(self.items_per_page*(self.current_page + 1))
        next_page.prepare(query)
        next_page.exec()
        next_page.next()

        return not next_page.record().isNull("name")

    def forward_page(self):
        """
        Tries to move the table to the next page;
        if successful, returns the model of the next page,
        otherwise returns None
        """
        if (self.has_next_page()):
            self.current_page += 1
            return self.get_games(self.current_page)
        return None

    def backward_page(self):
        """
        Tries to move the table to the previous page;
        if successful, returns the model of the previous page,
        otherwise returns None
        """
        if (self.current_page > 0):
            self.current_page -= 1
            return self.get_games(self.current_page)
        return None

    def get_current_page(self):
        return self.current_page

    def create_db(self, db=None):
        """
        creates the main database
        """
        con = self.db if db is None else db
        if not con.isOpen():
            con.open()

        # load file
        f = open(self.files_path + "createDB.sql")
        cmds = []
        s = f.readline()
        while (len(s) > 0):
            if not s.isspace():
                cmds.append(s[:-2])
            s = f.readline()

        # execute creation queries
        for i in cmds:
            q = QSqlQuery(con)
            q.prepare(i)
            if not q.exec():
                return False
        f.close()
        return True

    def remove_db(self, con_name, db_name):
        """
        removes the given database and its file
        """
        QSqlDatabase.removeDatabase(con_name)
        try:
            f = db_name + ".sqlite"
            os.remove(f)
        except FileNotFoundError:
            pass

    def import_db(self, filename):
        """
        given a .sqlite filename, will check if it has the valid table and attribute setup
        before overwriting the current database with it
        """
        try:
            file = open(filename, 'r')
            file.close()
            CONNECTION = "test_connection"
            test_db = QSqlDatabase.addDatabase("QSQLITE", CONNECTION)
            test_db.setDatabaseName(filename)
            test_db.open()

            # test that each table exists and has all the attributes
            q_test = QSqlQuery(test_db)
            q_test.prepare("SELECT name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name FROM game")
            if (not q_test.exec()):
                test_db.close()
                del test_db
                QSqlDatabase.removeDatabase(CONNECTION)
                return False

            if not (q_test.exec("SELECT game_name, name FROM genre")):
                test_db.close()
                del test_db
                QSqlDatabase.removeDatabase(CONNECTION)
                return False

            if not (q_test.exec("SELECT game_name, name FROM platform")):
                test_db.close()
                del test_db
                QSqlDatabase.removeDatabase(CONNECTION)
                return False

            if (not q_test.exec("SELECT name, num_games, total_playtime FROM series")):
                test_db.close()
                del test_db
                QSqlDatabase.removeDatabase(CONNECTION)
                return False

            q_test.finish()
            test_db.close()
            del test_db
            QSqlDatabase.removeDatabase(CONNECTION)

            # overwrite the database
            try:
                shutil.copy(filename, self.db_name)
            except shutil.SameFileError:
                return False
            return True
        except FileNotFoundError:
            return False

    def import_json(self, filename):
        """
        given a json file name, creates a temporary database, populates it,
        then replaces the current database with it
        """
        try:
            with open(filename) as f:
                to_import = json.load(f)

            # create temp database for importing
            CONNECTION = "temp_connection"
            TEMP_NAME = "JSONImport"
            temp_db = self.db.addDatabase("QSQLITE", CONNECTION)
            temp_db.setDatabaseName(TEMP_NAME + ".sqlite")

            # cleanup and return False if temp_db could not be created
            if (not self.create_db(db=temp_db)):
                temp_db.close()
                del temp_db
                self.remove_db(CONNECTION, TEMP_NAME)
                return False
            q = QSqlQuery(temp_db)

            # import series
            for i in range(len(to_import["series"])):
                q.prepare("INSERT INTO series VALUES (?, ?, ?)")
                q.bindValue(0, to_import["series"][i]["name"])
                q.bindValue(1, int(to_import["series"][i]["num_games"]))
                q.bindValue(2, float(to_import["series"][i]["total_playtime"]))
                if (not q.exec()):
                    temp_db.close()
                    del temp_db
                    self.remove_db(CONNECTION, TEMP_NAME)
                    return False

            # import games
            for i in range(len(to_import["games"])):
                query = "INSERT INTO game ("
                num_fields = len(to_import["games"][i])
                # set up the query string
                for v in to_import["games"][i]:
                    query += v + ","

                query = query [:len(query) - 1] + ")"
                query += " VALUES ("
                for j in range(num_fields):
                    if (j != num_fields - 1):
                        query += "?, "
                    else:
                        query += "?)"
                q.prepare(query)

                # bind values
                for j, k in enumerate(to_import["games"][i]):
                    q.bindValue(j, to_import["games"][i][k])

                if (not q.exec()):
                    temp_db.close()
                    del temp_db
                    self.remove_db(CONNECTION, TEMP_NAME)
                    return False

            # import genres
            for i in range(len(to_import["genres"])):
                q.prepare("INSERT INTO genre VALUES (?, ?)")
                q.bindValue(0, to_import["genres"][i]["game_name"])
                q.bindValue(1, to_import["genres"][i]["name"])
                if (not q.exec()):
                    temp_db.close()
                    del temp_db
                    self.remove_db(CONNECTION, TEMP_NAME)
                    return False

            # import platforms
            for i in range(len(to_import["platforms"])):
                q.prepare("INSERT INTO platform VALUES (?, ?)")
                q.bindValue(0, to_import["platforms"][i]["game_name"])
                q.bindValue(1, to_import["platforms"][i]["name"])
                if (not q.exec()):
                    temp_db.close()
                    del temp_db
                    self.remove_db(CONNECTION, TEMP_NAME)
                    return False

            # copy the database over
            try:
                dst = shutil.copy("JSONImport.sqlite", self.db_name)
            except shutil.SameFileError:
                temp_db.close()
                del temp_db
                self.remove_db(CONNECTION, TEMP_NAME)
                return False

            # cleanup
            temp_db.close()
            del temp_db
            self.remove_db(CONNECTION, TEMP_NAME)
            return True
        except FileNotFoundError:
            return False


    def export_db(self, filename):
        return shutil.copy(self.db_name, filename)

    def export_json(self, filename):
        """
        exports the database as a json file
        """
        games = []
        genres = []
        platforms = []
        series = []
        q = QSqlQuery()
        q.prepare("SELECT * FROM game")
        if (not q.exec() or q.record().count() < 1):
            return False

        # convert game records to list of dictionaries
        while (q.next()):
            game = q.record()
            dict = {}
            for i in range(game.count()):
                f = game.field(i).name()
                dict[f] = game.value(f)
            games.append(dict)

        q.prepare("SELECT * FROM genre")
        if (not q.exec() or q.record().count() < 1):
            print("genre select error")
            return False

        # convert genre records to list of dicts
        while (q.next()):
            genre = q.record()
            dict = {}
            for i in range(genre.count()):
                f = genre.field(i).name()
                dict[f] = genre.value(f)
            genres.append(dict)

        q.prepare("SELECT * FROM platform")
        if (not q.exec() or q.record().count() < 1):
            return False
        # convert platform records to list of dicts
        while (q.next()):
            platform = q.record()
            dict = {}
            for i in range(platform.count()):
                f = platform.field(i).name()
                dict[f] = platform.value(f)
            platforms.append(dict)

        q.prepare("SELECT * FROM series")
        if (not q.exec() or q.record().count() < 1):
            return False

        # convert series records to list of dicts
        while (q.next()):
            s = q.record()
            dict = {}
            for i in range(s.count()):
                f = s.field(i).name()
                dict[f] = s.value(f)
            series.append(dict)
        to_export = {"games": games, "genres": genres, "platforms": platforms, "series": series}
        with open(filename, 'w') as fp:
            json.dump(to_export, fp)
        return True

    def get_games(self, page=0):
        """
        return a QSortFilterProxyModel with a QSqlQueryModel as its source model,
        which contains all the game records joined with genre and platform records;
        supports pagination: 1 page = self.items_per_page records
        """
        headers = ["Name","Progress (%)", "Hours\nPlayed", "Start\nDate", "End\nDate", "Total\nAchievements", "Completed\nAchievements", "Series\nName", "Genre(s)", "Platform(s)"]
        model = QSqlQueryModel()
        query = """
        SELECT game.name, progress, hours_played, start_date, end_date, total_achievements, completed_achievements, series_name,
        group_concat(DISTINCT genre.name) AS genre_name,
        group_concat(DISTINCT platform.name) AS platform_name
        FROM game LEFT JOIN genre ON (game.name == genre.game_name) LEFT JOIN platform ON (game.name == platform.game_name)
        GROUP BY game.name
        """
        # handles pages by using LIMIT and OFFSET clauses
        if (page == 0):
            self.current_page = 0
        offset = self.items_per_page*page
        query = query + " LIMIT " + str(self.items_per_page)
        if (offset > 0):
            query = query + " OFFSET " + str(offset)
        model.setQuery(query)

        for i in range(len(headers)):
            model.setHeaderData(i, Qt.Horizontal, headers[i])

        # proxy model does sorting for us
        proxy = QSortFilterProxyModel()
        proxy.setSourceModel(model)
        return proxy

    def get_series(self):
        """
        return a QSortFilterProxyModel with a QSqlQueryModel as its source model,
        which contains all the series records
        """
        headers = ["Name", "Number of\nGames", "Total Hours\nPlayed"]
        model = QSqlQueryModel()
        model.setQuery("SELECT * FROM series")

        for i in range(len(headers)):
            model.setHeaderData(i, Qt.Horizontal, headers[i])

        proxy = QSortFilterProxyModel()
        proxy.setSourceModel(model)
        return proxy

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

            if (old_series.isNull("name")):
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
                q_obj.bindValue(1, old_series.value("total_playtime") + float(item["hours_played"]))
                q_obj.bindValue(2, item["series_name"])
                q_obj.exec()

        # add the actual game
        q_obj.prepare(query)
        for i, v in enumerate(item):
            q_obj.bindValue(i, item[v])
        rv = q_obj.exec()

        # add genres
        if (genres is not None):
            for i in range(len(genres)):
                q_obj.prepare("INSERT INTO genre (game_name, name) VALUES (?, ?)")
                q_obj.bindValue(0, item["name"])
                q_obj.bindValue(1, genres[i])
                q_obj.exec()

        # add platforms
        if (platforms is not None):
            for i in range(len(platforms)):
                q_obj.prepare("INSERT INTO platform (game_name, name) VALUES (?, ?)")
                q_obj.bindValue(0, item["name"])
                q_obj.bindValue(1, platforms[i])
                q_obj.exec()

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
            return False

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
        return rv

    def delete_item(self, name):
        """
        deletes the game with the given name
        """
        q_obj = QSqlQuery()
        q_obj.prepare("SELECT * FROM game WHERE name=?")
        q_obj.bindValue(0, name)
        q_obj.exec()
        q_obj.next()
        old_game = q_obj.record()

        q_obj.prepare("DELETE FROM game WHERE name=?")
        q_obj.bindValue(0, name)
        rv = q_obj.exec()
        if not rv:
            return False

        # delete associated genres and platforms
        q_obj.prepare("DELETE FROM genre WHERE game_name=?")
        q_obj.bindValue(0, name)
        rv = q_obj.exec()

        q_obj.prepare("DELETE FROM platform WHERE game_name=?")
        q_obj.bindValue(0, name)
        q_obj.exec()

        # update series
        if (not old_game.isNull("series_name")):
            q_obj.prepare("SELECT * FROM series WHERE name=?")
            q_obj.bindValue(0, old_game.value("series_name"))
            q_obj.exec()
            q_obj.next()
            old_series = q_obj.record()

            if (old_series is not None and not old_series.isNull("num_games")):
                if (old_series.value("num_games") - 1 > 0):
                    old_hours = 0.0 if old_game.isNull("hours_played") else float(old_game.value("hours_played"))
                    old_total = 0.0 if old_series.isNull("total_playtime") else float(old_series.value("total_playtime"))

                    q_obj.prepare("UPDATE series SET num_games=?, total_playtime=? WHERE name=?")
                    q_obj.bindValue(0, old_series.value("num_games") - 1)
                    q_obj.bindValue(1, old_total - old_hours)
                    q_obj.bindValue(2, old_game.value("series_name"))
                    q_obj.exec()
                else:
                    q_obj.prepare("DELETE FROM series WHERE name=?")
                    q_obj.bindValue(0, old_game.value("series_name"))
                    q_obj.exec()

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
