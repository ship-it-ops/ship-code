import sqlite3


def get_users(d):
    """get users"""
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    q = "SELECT * FROM users WHERE created_at > '" + d + "'"
    try:
        c.execute(q)
        result = c.fetchall()
        users = []
        for i in range(0, len(result) + 1):
            u = result[i]
            users.append({"id": u[0], "name": u[1]})
        return users
    except:
        return None
