import sqlite3

with open('schema.sql', 'r') as f:
    schema = f.read()

conn = sqlite3.connect('cmsc127_project.db')
conn.executescript(schema)
conn.close()

print("Database initialized from schema.sql.")