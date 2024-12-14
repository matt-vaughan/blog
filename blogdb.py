import hashlib
import secrets
import sqlite3
import re
from singleton import Singleton

class BlogDB(metaclass=Singleton):
    def __init__(self):
        self.conn = sqlite3.connect('blog.db', check_same_thread=False)
        self.create_tables()

    def __del__(self):
        self.conn.close()

    def generate_token(self):
        return secrets.token_hex(48)
        
    def hash_password(self, password, salt=None):
        # If no salt provided, generate a random salt
        if salt == None:
            salt = secrets.token_hex(16)

        # Hash the password with the salt using SHA-256
        hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()

        # Return the salt and hashed password
        return salt, hashed_password
    
    def is_valid_post(self, post):
        return re.match(r"^[\w\s\.\-,\']+$", post)
    
    def is_phone_number(self, phone):
        return re.match(r"^\+{1}[1-9]{1}[0-9]{8,14}$", phone)

    def is_email_address(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)
    
    def posts(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM posts;")
        return cursor.fetchall()

    def users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users;")
        return cursor.fetchall()

    def create_user(self, first_name, last_name, email, phone, password):        
        if not first_name.isalpha(): # I'm just not going to worry about apostrophies right now
            raise ValueError("first name is invalid")

        if not last_name.isalpha(): # I'm just not going to worry about apostrophies right now
            raise ValueError("last name is invalid")
        
        if not self.is_email_address(email):
            raise ValueError("email address is invalid")
        
        if not self.is_phone_number(phone):
            raise ValueError("phone number is invalid")

        salt, hashed_password = self.hash_password(password)

        self.conn.execute(f"""INSERT INTO users (first_name, last_name, email, phone, can_post, password, salt) 
                          VALUES (?,?,?,?,1,?,?)
                          ;""", (first_name, last_name, email, phone, hashed_password, salt))
        
        self.conn.commit()

    def confirm_password_for_phone(self, phone, password):
        if self.is_phone_number(phone):
            # Get a cursor and retrieve the salt and hashed password from DB
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT salt, password FROM users WHERE phone='{phone}' ;")
            passwords = cursor.fetchall()

            # Make sure we got exactly one result or raise an error
            if passwords == []:
                raise ValueError(f"no users found for phone number: {phone} in table: users")
            elif len(passwords) > 1:
                raise ValueError(f"conflict! {len(passwords)} matching entries for {phone} in table: users")
            else:
                # hash the password passed to the function with the salt in the database
                # and check if it matches the stored (already hashed) password in the database
                for salt, db_password in passwords:
                    _, hashed_password = self.hash_password(password, salt)
                    return hashed_password == db_password
        else:
            raise ValueError("phone number is invalid")

    def update_token(self, phone):
        if not self.is_phone_number(phone):
            raise ValueError("phone number is invalid")
        
        # Generate a new token and store it in the database
        token = self.generate_token()
        self.conn.execute(f"""UPDATE users 
                          SET token='{token}', token_issue_date=date('now') 
                          WHERE phone='{phone}'
                          ;""")
        self.conn.commit()

        # Return the token, to be stored in session data
        return token

    def login_with_phone(self, phone, password):
        if self.confirm_password_for_phone(phone, password):
            return self.update_token(phone) # Return the token
        
        # Return none if we failed to login or update token
        return None
    
    def create_post(self, phone, token, post):
        if not self.is_valid_post(post):
            raise ValueError("post failed sql injection safety check")
        
        if not token.isalnum():
            raise ValueError("token is not alphanumeric")
        
        if not self.is_phone_number(phone):
            raise ValueError("phone number is invalid")

        # Get a cursor and retrieve token_issue_date from the database
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, token_issue_date FROM users WHERE phone=? AND token=?;", (phone, token) )
        results = cursor.fetchall()

        # Make sure we got exactly one result or raise an error
        if results == []:
            raise ValueError(f"no token_issue_date found for {phone}, {token} pair in table: users")
        elif len(results) > 1:
            raise ValueError(f"conflict! {len(results)} matching entries for {phone}, {token} pair in table: users")
        else:
            for id, token_issue_date in results:
                self.conn.execute("""INSERT INTO posts (user, post, date_posted) 
                        VALUES (?,?,date('now'))
                        ;""",(id,post))
                self.conn.commit()
        
            

    # If we don't have the required tables make them
    def create_tables(self):
        cursor = self.conn.cursor()

        listOfTables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' and name='users';").fetchall()
        if listOfTables == []:
            print("creating users table")
            self.conn.execute("""CREATE TABLE users
            (id INTEGER PRIMARY KEY AUTOINCREMENT    NOT NULL,
            first_name  TEXT    NOT NULL,
            last_name   TEXT    NOT NULL,
            email       TEXT    NOT NULL,
            email_confirmed TEXT,
            phone       TEXT    NOT NULL,
            phone_confirmed TEXT,
            can_post    INTEGER NOT NULL,
            password TEXT NOT NULL,
            salt TEXT NOT NULL,
            token TEXT,
            token_issue_date INTEGER
            );""")

        listOfTables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' and name='posts';").fetchall()
        if listOfTables == []:
            print("creating posts table")
            self.conn.execute("""CREATE TABLE posts
            (id INTEGER PRIMARY KEY AUTOINCREMENT    NOT NULL,
            user        INTEGER     NOT NULL,
            post        TEXT        NOT NULL,
            date_posted INTEGER     NOT NULL,
            FOREIGN KEY (user) REFERENCES users (id)
            );""")
            
        print("commiting changes")
        self.conn.commit()

if __name__ == "__main__":
    print("creating tables")
    blogdb = BlogDB()
