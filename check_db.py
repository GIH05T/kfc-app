import sqlite3

conn = sqlite3.connect('kfc.db')
c = conn.cursor()

c.execute("SELECT * FROM kinder")
rows = c.fetchall()

for row in rows:
    print(row)

conn.close()
