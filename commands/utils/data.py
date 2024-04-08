import sqlite3
import logging

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        return self.conn.cursor()
    
    def __exit__(self, exec_type, exc_value, traceback):
        if exec_type:
            self.conn.rollback()
            logging.error(f"Erro: {exc_value}")
        else:
            self.conn.commit()
        self.conn.close()

class DataManager:
    def __init__(self, db_name):
        self.db_name = db_name

    def create_connection(self):
        self.conn = sqlite3.connect(self.db_name)

    def __enter__(self):
        return self

    def __exit__(self, exec_type, exc_value, traceback):
        if exec_type:
            self.conn.rollback()
            logging.error(f"Erro: {exc_value}")
        else:
            self.conn.commit()
        self.conn.close()

    def create_tables(self):
        create_table_query = [
            """
            CREATE TABLE IF NOT EXISTS economy (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 0
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item TEXT,
                quantidade INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES economy (user_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS protected_users (
                user_id INTEGER PRIMARY KEY,
                protected INTEGER DEFAULT 0
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS items_for_sale (
                item TEXT PRIMARY KEY,
                descricao TEXT,
                valor INTEGER
            );
            """
        ]
        try:
            with self.conn:
                for query in create_table_query:
                    self.conn.execute(query)
            logging.info("Tabelas criadas com sucesso!")
        except sqlite3.Error as e:
            logging.error(f"Erro ao criar as tabelas: {e}")

    def user_exists(self, user_id):
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM economy WHERE user_id=?", (user_id,))
            row = c.fetchone()
            return row is not None
        except sqlite3.Error as e:
            logging.error(f"Erro ao verificar se o usuário existe: {e}")
            return False
    
    def register_new_user(self, user_id):
        try:
            with self.conn:
                self.conn.execute("INSERT INTO economy (user_id, coins) VALUES (?, ?)", (user_id, 100))
            logging.info(f"Novo usuário registrado: {user_id}")
        except sqlite3.IntegrityError:
            logging.warning(f"Usuário {user_id} já existe.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao criar novo usuário: {e}")
    
    def is_protected(self, user_id):
        try:
            c = self.conn.cursor()
            c.execute("SELECT protected FROM protected_users WHERE user_id=?", (user_id,))
            row = c.fetchone()
            return row is not None and row[0] == 1
        except sqlite3.Error as e:
            logging.error(f"Erro ao verificar se o usuário está protegido: {e}")
            return False

    def add_coins(self, user_id, amount):
        try:
            with self.conn:
                self.conn.execute("UPDATE economy SET coins = coins + ? WHERE user_id=?", (amount, user_id))
            logging.info(f"{amount} moedas adicionadas à conta de {user_id}.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar moedas: {e}")
    
    def remove_coins(self, user_id, amount):
        try:
            with self.conn:
                self.conn.execute("UPDATE economy SET coins = coins - ? WHERE user_id=?", (amount, user_id))
            logging.info(f"{amount} moedas removidas da conta de {user_id}!")
        except sqlite3.Error as e:
            logging.error(f"Erro ao remover moedas: {e}")

    def get_inventory(self, user_id):
        try:
            c = self.conn.cursor()
            c.execute("SELECT item, quantidade FROM inventory WHERE user_id=?", (user_id,))
            rows = c.fetchall()
            inventario = {}
            for row in rows:
                item, quantidade = row
                inventario[item] = quantidade
            return inventario
        except sqlite3.Error as e:
            logging.error(f"Erro ao obter inventário: {e}")
            return {}

    def get_items_for_sale(self):
        try:
            c = self.conn.cursor()
            c.execute("SELECT item, valor FROM items_for_sale")
            rows = c.fetchall()
            itens_para_venda = {}
            for row in rows:
                item, preco = row
                itens_para_venda[item] = preco
            return itens_para_venda
        except sqlite3.Error as e:
            logging.error(f"Erro ao obter itens para venda: {e}")
            return {}
