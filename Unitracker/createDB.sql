CREATE TABLE IF NOT EXISTS game(name VARCHAR(25), progress INT(3) DEFAULT 0, hours_played NUMERIC(30) DEFAULT 0, start_date DATE, end_date DATE, total_achievements INT(20), completed_achievements INT(20), series_name VARCHAR(25), PRIMARY KEY(name), FOREIGN KEY(series_name) REFERENCES series(name) ON DELETE SET NULL, CHECK (hours_played >= 0 AND progress >= 0));

CREATE TABLE IF NOT EXISTS genre(game_name VARCHAR(25), name VARCHAR(20), FOREIGN KEY(game_name) REFERENCES game(name) ON DELETE CASCADE ON UPDATE CASCADE);

CREATE TABLE IF NOT EXISTS platform(game_name VARCHAR(25), name VARCHAR(20), FOREIGN KEY(game_name) REFERENCES game(name) ON DELETE CASCADE ON UPDATE CASCADE);

CREATE TABLE IF NOT EXISTS series(name VARCHAR(25), num_games INT(10) DEFAULT 0, total_playtime INT(10) DEFAULT 0, PRIMARY KEY(name));
