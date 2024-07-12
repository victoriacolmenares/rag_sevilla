import json
import sqlite3


def connect_db():
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    return conn, cursor


def initdb():
    conn, cursor = connect_db()
    # Habilitar soporte para claves foráneas en SQLite
    cursor.execute('PRAGMA foreign_keys = ON')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT 'Nuevo chat'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_question TEXT,
        llm_response TEXT,
        history TEXT,
        chat_id INTEGER,
        FOREIGN KEY (chat_id) REFERENCES chat (id) ON DELETE CASCADE
    )
    ''')
    conn.commit()


def insert_chat():
    conn, cursor = connect_db()
    cursor.execute('INSERT INTO chat DEFAULT VALUES')
    conn.commit()
    return cursor.lastrowid


def update_chat_name(chat_id, chat_name):
    conn, cursor = connect_db()
    cursor.execute('''
    UPDATE chat
    SET name = ?
    WHERE id = ? AND name = ?
    ''', (chat_name, chat_id, 'Nuevo chat'))
    conn.commit()


def get_all_chat():
    _, cursor = connect_db()
    cursor.execute('SELECT * FROM chat ORDER BY id DESC')
    return cursor.fetchall()


def delete_chat_by_id(chat_id):
    conn, c = connect_db()
    c.execute('DELETE FROM chat WHERE id = ?', (chat_id,))
    conn.commit()
    conn.close()


def save_chat_history(user_question, llm_response, chat_id):
    conn, cursor = connect_db()

    history_json = json.dumps([
        {
            "role": "user",
            "content": user_question,
            "avatar": "👦",
        },
        {
            "role": "assistant",
            "content": llm_response,
            "avatar": "💃",
        }
    ])
    cursor.execute('''
    INSERT INTO chat_history (user_question, llm_response, history, chat_id)
    VALUES (?, ?, ?, ?)
    ''', (user_question, llm_response, history_json, chat_id))
    conn.commit()


def get_chat_history_by_chat_id(chat_id):
    _, cursor = connect_db()
    cursor.execute('SELECT * FROM chat_history WHERE chat_id = ?', (chat_id,))
    rows = cursor.fetchall()
    # Deserializar el campo 'history' de JSON a lista de diccionarios
    result = []
    for row in rows:
        row = list(row)
        row[3] = json.loads(row[3])
        result.append(row)
    return result
