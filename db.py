import sqlite3

class DB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def create_table(self, table_name: str, columns: dict):
        """
        Create a table with the given name and columns
        """

        if self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchone():
            print(f"Table '{table_name}' already exists, skipping...")
            return False

        columns = [f"{k} {v}" for k, v in columns.items()]

        self.cursor.execute(f"CREATE TABLE {table_name} ({', '.join(columns)})")

    def insert_row(self, table_name: str, data: dict):
        """
        Insert a row into the table
        """

        columns = [c for c in data.keys()]
        values = [v for v in data.values()]

        if self.cursor.execute(f"SELECT * FROM {table_name} WHERE " + " OR ".join([f"{c}='{v}'" for c, v in zip(columns, values)])).fetchone():
            print(f"Row already exists in table '{table_name}'")
            return False

        self.cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})", values)

        self.conn.commit()

        return self.cursor.lastrowid

    def get_row(self, table_name: str, column: str, value: str):
        """
        Get a row from the table
        """

        self.cursor.execute(f"SELECT * FROM {table_name} WHERE {column} = ?", (value,))

        return self.cursor.fetchone()



if __name__ == "__main__":
    db = DB("data/data.sqlite")

    struct = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
        "picture": "TEXT NOT NULL",
        "place": "TEXT",
    }

    db.create_table("locations", struct)

    data = {
        "picture": "eiffel_tower.jpg",
        "place": "Paris",
    }

    db.insert_row("locations", data)

    result = db.get_row("locations", "picture", "eiffel_tower.jpg")

    print(result)
