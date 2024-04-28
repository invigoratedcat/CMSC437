[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/QB74hIJx)

Project Name: Unitracker

Author: Logan Seely

Email: lz50375@umbc.edu

Required to build: Qt6, PySide6, Python 3, qdarktheme (https://pypi.org/project/pyqtdarktheme/)

Description: A desktop application made to track user inputted games using a SQLite database. Attributes included are: progress, hours played, start date, end date, genre(s), platform(s), total achievements, completed achievements, and a series the game belongs to.

Features:
- basic series information (name, number of games, total playtime across all games)
- storing your progress in games
  - decide your own progress %
  - hours played
  - start date, end date for when you started and/or finished playing it
  - total achievements and completed achievements
  - put in the genre(s) you think they are
  - put in the platform(s) you've played them on
- menus to view series and games tables
 - can sort the tables in ascending/descending order of chosen columns
- pages for games
- importing/exporting for sqlite, json
- adding games with as much information as you want (minimum of the game's name)
- editing games by selecting the row it's in
- deleting as many games as you have rows selected
- keyboard shortcuts for navigating between menus and exiting the app
- settings saved in a json file
  - light and dark themes, with an option to automatically set the theme based on your system's
  - text size: small, medium, or large
  - set screen size (windowed, maximized, fullscreen)
  - set items per page for the games menu
- tab selecting
- help menu describing how to do everything
- tooltips to help you remember what each button does
Future ideas:
- Choose to use Steam to easily fill in data from Steam's database when adding/editing games
  - maybe use https://github.com/ValvePython/steam
- Port to Android
- Support other formats for importing/exporting
- Connect to cloud storage (e.g., Dropbox, Google Drive) for synchronization