"""MySQL connection settings and the existing project's tables."""
from configparser import ConfigParser
from pathlib import Path

import mysql.connector


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "mysql.local.ini"


def get_connection():
    # Disable interpolation so a percent sign in a password stays literal.
    config = ConfigParser(interpolation=None)
    if not config.read(CONFIG_PATH, encoding="utf-8-sig"):
        raise RuntimeError("mysql.local.ini was not found beside database.py.")
    if not config.has_section("mysql"):
        raise RuntimeError("mysql.local.ini must contain a [mysql] section.")
    settings = config["mysql"]
    for name in ("host", "user", "password", "database"):
        if not settings.get(name):
            raise RuntimeError(f"Missing MySQL setting: {name}")
    return mysql.connector.connect(
        host=settings["host"],
        port=settings.getint("port", 3306),
        user=settings["user"],
        password=settings["password"],
        database=settings["database"],
        charset="utf8mb4",
        collation="utf8mb4_0900_ai_ci",
        connection_timeout=10,
        autocommit=False,
    )


def initialise_database():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(30) COLLATE utf8mb4_bin NOT NULL UNIQUE,
                    password_hash VARCHAR(512) NOT NULL,
                    role ENUM('student', 'admin') NOT NULL DEFAULT 'student',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_articles (
                    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    slug VARCHAR(191) COLLATE utf8mb4_bin NOT NULL UNIQUE,
                    topic VARCHAR(100) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    summary TEXT NOT NULL,
                    content LONGTEXT NOT NULL,
                    source_title VARCHAR(500) NOT NULL,
                    source_url TEXT NOT NULL,
                    INDEX idx_articles_topic (topic)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    initialise_database()
    print("[OK] Connected to MySQL. Users and knowledge tables are ready.")
