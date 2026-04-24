import sqlite3

class DAO:
    def __init__(self, db):
        self.db = db
        self.conn = sqlite3.connect(self.db)
        self.cursor = self.conn.cursor()
    
    def create_table(self, table, schema):
        query = f"CREATE TABLE IF NOT EXISTS {table} ({schema})"
        self.cursor.execute(query)
        self.conn.commit()

    def read(self, table):
        query = f"SELECT * FROM {table}"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def write(self, table, data):
        placeholders = ', '.join(['?'] * len(data[0]))
        print(placeholders)
        query = f"INSERT INTO {table} VALUES ({placeholders})"
        self.cursor.executemany(query, data)
        self.conn.commit()

    def drop(self, table):
        query = f"DROP TABLE {table}"
        self.cursor.execute(query)
        self.conn.commit()
    
    def execute_custom_query(self, query: str):
        self.cursor.execute(query)
        self.conn.commit 
    