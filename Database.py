from Profile import Profile
import datetime
import sqlite3
import random
import string


def get_timestamp() -> int:
    return int(datetime.datetime.now().timestamp())


def generate_party_code() -> str:
    return ''.join(random.choice(string.ascii_letters) for _ in range(6))


class DataBase:
    def __init__(self) -> None:
        self.con = sqlite3.connect("main.db")
        self.cur = self.con.cursor()
        self.cur.execute(
            '''CREATE TABLE IF NOT EXISTS users (
                id INTEGER,  
                active INTEGER, 
                state INTEGER, 
                target INTEGER, 
                party TEXT, 
                registered INTEGER
            )''')
        self.cur.execute(
            '''CREATE TABLE IF NOT EXISTS forms (
                id INTEGER, 
                name TEXT, 
                age INTEGER, 
                photos TEXT, 
                descr TEXT, 
                sex INTEGER
            )''')
        self.cur.execute(
            '''CREATE TABLE IF NOT EXISTS displays (
                subject INTEGER, 
                object INTEGER, 
                like INTEGER, 
                ignore INTEGER, 
                time INTEGER, 
                message TEXT
            )''')
        self.cur.execute(
            '''CREATE TABLE IF NOT EXISTS party (
                code TEXT, 
                author INTEGER, 
                create_time INTEGER, 
                about TEXT
            )''')

    def add_user(self, id: int) -> None:
        self.cur.execute('''INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)''',
                         (id, 1, 0, 0, "", get_timestamp()))
        self.cur.execute('''INSERT INTO forms VALUES (?, ?, ?, ?, ?, ?)''',
                         (id, "", 0, "", "", -1))
        self.con.commit()

    def is_exists(self, id: int) -> bool:
        self.cur.execute('''SELECT id FROM users WHERE id = ?''', (id,))
        return len(self.cur.fetchall()) != 0

    def has_form(self, id: int) -> bool:
        self.cur.execute('''SELECT name FROM forms WHERE id = ?''', (id,))
        data = self.cur.fetchall()
        if len(data) == 0:
            return False
        return data[0][0] != ""

    def get_form(self, id: int):
        self.cur.execute('''SELECT * FROM forms WHERE id = ?''', (id,))
        return self.cur.fetchall()[0]

    def get_data(self, id: int):
        self.cur.execute('''SELECT * FROM users WHERE id = ?''', (id,))
        return self.cur.fetchall()[0]

    def get_profile(self, id: int) -> Profile:
        data = self.get_form(id)
        return Profile(data)

    def set_profile(self, reg: Profile) -> None:
        self.cur.execute('''UPDATE forms 
                                  SET name = ?, age = ?, photos = ?, descr = ?, sex = ? 
                                  WHERE id = ?''',
                         reg.get_sqlparams())
        self.con.commit()

    def set_state(self, id: int, state: int) -> None:
        self.cur.execute('''UPDATE users SET state = ? WHERE id = ?''', (state, id))
        self.con.commit()

    def get_state(self, id: int) -> str:
        """
        main - находится в главном меню
        inactive - отключил анкету
        like - смотрит на анкеты людей, которые лайкнули его
        looking - смотрит на анкеты обычных людей
        lastprofile - досматривает последнюю анкету (его лайкнули)
        message2bestie - пишет сообщение другому человеку
        party_selection - выбирает действие с пати
        party_joining - присоединяется к пати
        party_creation - создает пати
        """
        data = self.get_data(id)[2]
        if data == 1:
            return "main"
        elif data == 2:
            return "inactive"
        elif data == 3:
            return "like"
        elif data == 4:
            return "looking"
        elif data == 5:
            return "lastprofile"
        elif data == 6:
            return "message2bestie"
        elif data == 7:
            return "party_selection"
        elif data == 8:
            return "party_joining"
        elif data == 9:
            return "party_creation"

    def set_target(self, id: int, target: int) -> None:
        self.cur.execute('''UPDATE users SET target = ? WHERE id = ?''', (target, id))
        self.con.commit()

    def get_target(self, id: int) -> int:
        self.cur.execute('''SELECT target FROM users WHERE id = ?''', (id,))
        return self.cur.fetchall()[0][0]

    def set_active(self, id: int, state: int) -> None:
        self.cur.execute('''UPDATE users SET active = ? WHERE id = ?''', (state, id))
        self.con.commit()

    def like(self, subject: int, object: int, message: str) -> None:
        self.cur.execute('''INSERT INTO displays VALUES (?, ?, ?, ?, ?, ?)''',
                         (subject, object, 1, 0, get_timestamp(), message))
        self.con.commit()

    def ignore(self, subject: int, object: int) -> None:
        self.cur.execute('''INSERT INTO displays VALUES (?, ?, ?, ?, ?, ?)''',
                         (subject, object, 0, 1, get_timestamp(), ""))
        self.con.commit()

    def get_likes(self, id: int) -> list[int]:
        self.cur.execute('''SELECT subject FROM displays WHERE object = ? AND like = 1 ''', (id,))
        return [user[0] for user in self.cur.fetchall()]

    def mark_like(self, subject: int, object: int) -> None:
        self.cur.execute('''UPDATE displays SET like = 2 WHERE subject = ? AND object = ?''', (subject, object))
        self.con.commit()

    def is_mutually(self, subject: int, object: int) -> bool:
        self.cur.execute('''SELECT subject 
                                  FROM displays 
                                  WHERE subject = ? AND object = ? AND like != 0''',
                         (subject, object))
        if len(self.cur.fetchall()) == 0:
            return False
        self.cur.execute('''SELECT subject 
                                  FROM displays 
                                  WHERE subject = ? AND object = ? AND like != 0''',
                         (object, subject))
        return len(self.cur.fetchall()) != 0

    def get_like_message(self, subject: int, object: int) -> str:
        self.cur.execute('''SELECT message 
                                  FROM displays 
                                  WHERE object = ? AND subject = ?''',
                         (object, subject))
        return self.cur.fetchall()[0][0]

    def get_bestie(self, subject: int) -> int:
        subject_data = self.get_form(subject)
        party = self.get_party(subject)
        self.cur.execute(
            '''
            SELECT q.id, q.age 
            FROM forms q 
            LEFT JOIN displays d 
                ON q.id = d.object AND d.subject = ?
            LEFT JOIN users u
                ON q.id = u.id
            WHERE q.id != ? AND d.subject IS NULL AND u.active = 1 AND q.sex != ? AND ABS(q.age - ?) < 2 
            ORDER BY RANDOM() AND u.party = ? 
            LIMIT 1''',
            (subject, subject, subject_data[5], subject_data[2], party))
        data = self.cur.fetchall()
        if len(data) == 0:
            return 0
        return data[0][0]

    def set_party(self, user_id: int, party: str) -> None:
        self.cur.execute('''UPDATE users SET party = ? WHERE id = ?''', (party, user_id))
        self.con.commit()

    def has_party(self, user_id: int) -> bool:
        self.cur.execute('''SELECT party FROM users WHERE id = ?''', (user_id,))
        return len(self.cur.fetchall()[0][0]) > 0

    def is_party_exists(self, party: str) -> bool:
        self.cur.execute('''SELECT code FROM party WHERE code = ?''', (party,))
        return len(self.cur.fetchall()) > 0

    def create_party(self, author: int, about: str) -> str:
        party = generate_party_code()
        self.cur.execute('''INSERT INTO party VALUES (?, ?, ?, ?)''', (party, author, get_timestamp(), about))
        self.con.commit()
        self.set_party(author, party)
        return party

    def get_party_desc(self, party: str) -> str:
        self.cur.execute('''SELECT about FROM party WHERE code = ?''', (party,))
        return self.cur.fetchall()[0][0]

    def get_party_members(self, party: str) -> int:
        self.cur.execute('''SELECT id FROM users WHERE party = ?''', (party,))
        return len(self.cur.fetchall())

    def get_party(self, user_id: int) -> str:
        self.cur.execute('''SELECT party FROM users WHERE id = ?''', (user_id,))
        return self.cur.fetchall()[0][0]
