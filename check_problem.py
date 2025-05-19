import sqlite3

"""
Script to check and print the schema (columns) of the 'problems' table
in the contests.db SQLite database.
"""

conn = sqlite3.connect("D:/UIT SUBJECTS/Nam 1 - hoc ki 2 - Cau truc du lieu va giai thuat/Big Task 1/contests.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(problems);")
columns = cursor.fetchall()
for column in columns:
    print(column)
conn.close()