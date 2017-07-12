import sqlite3
conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''CREATE TABLE userlist(username text, lastseen timestamp, online INT, socketnumber INT)''')

c.execute('''CREATE TABLE grouplist (
    groupname TEXT
);''')

c.execute('''CREATE TABLE group_user(
    user_id INTEGER,
    group_id INTEGER,
    seen INTEGER,
    FOREIGN KEY(user_id) REFERENCES userlist(username),
    FOREIGN KEY(group_id) REFERENCES grouplist(rowid)
);''')

c.execute('''CREATE TABLE messagelist(username text, seen INT, sentByUser text, sentByGroup text, sentTime timestamp,message text)''')

c.execute('''CREATE TABLE blocklist(blockingusername text,blockedusername text) ''')
conn.commit()
conn.close()