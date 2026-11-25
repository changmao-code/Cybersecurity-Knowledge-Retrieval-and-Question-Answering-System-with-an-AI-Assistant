"""Topic catalogue and MySQL-backed learning resources."""
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from database import get_connection

BASE_DIR = Path(__file__).resolve().parent
router = APIRouter()
TOPICS = {
    "networking": {"title": "Network Fundamentals", "summary": "Explore networks, addressing and communication protocols.", "color": "blue"},
    "cryptography": {"title": "Cryptography & Authentication", "summary": "Understand encryption, identity verification and account protection.", "color": "green"},
    "web-security": {"title": "Web Security", "summary": "Learn how to protect web applications and their data.", "color": "yellow"},
    "privacy": {"title": "Privacy & Protection", "summary": "Explore personal information and safer digital behaviour.", "color": "purple"},
}


def query_articles(topic="", q=""):
    if topic and topic not in TOPICS:
        raise HTTPException(404, "Topic not found.")
    # Treat %, _ and ! as literal search characters rather than SQL wildcards.
    term = q.strip().replace("!", "!!").replace("%", "!%").replace("_", "!_")
    keyword = "%" + term + "%"
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT id, slug, topic, title, summary, source_title, source_url
                FROM knowledge_articles
                WHERE topic IN ('networking', 'cryptography', 'web-security', 'privacy')
                  AND (%s = '' OR topic = %s)
                  AND (title LIKE %s ESCAPE '!' OR summary LIKE %s ESCAPE '!'
                       OR content LIKE %s ESCAPE '!' OR source_title LIKE %s ESCAPE '!')
                ORDER BY id
            """, (topic, topic, keyword, keyword, keyword, keyword))
            return cursor.fetchall()
    finally:
        connection.close()


@router.get("/topics", response_class=FileResponse)
def topic_directory():
    return FileResponse(BASE_DIR / "topics.html")


@router.get("/topics/{topic}", response_class=FileResponse)
def topic_page(topic: str):
    if topic not in TOPICS:
        raise HTTPException(404, "Topic not found.")
    return FileResponse(BASE_DIR / "networking.html")


@router.get("/knowledge-assets/{name}")
def knowledge_asset(name: str):
    if name not in ("knowledge.css", "knowledge.js"):
        raise HTTPException(404, "Asset not found.")
    return FileResponse(BASE_DIR / name)


@router.get("/api/topics")
def topic_counts():
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT topic, COUNT(*) AS total FROM knowledge_articles GROUP BY topic")
            counts = {row["topic"]: row["total"] for row in cursor.fetchall()}
    finally:
        connection.close()
    return {"topics": [{"slug": slug, **data, "count": counts.get(slug, 0)} for slug, data in TOPICS.items()]}


@router.get("/api/articles")
def all_articles(q: str = Query("", max_length=100), topic: str = ""):
    rows = query_articles(topic, q)
    return {"articles": rows, "count": len(rows)}


@router.get("/api/topics/{topic}")
def topic_articles(topic: str, q: str = Query("", max_length=100)):
    rows = query_articles(topic, q)
    return {"topic": {"slug": topic, **TOPICS[topic]}, "articles": rows, "count": len(rows)}


@router.get("/api/articles/{article_id}")
def article_detail(article_id: int):
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT id, topic, title, summary, content, source_title, source_url
                FROM knowledge_articles WHERE id = %s
            """, (article_id,))
            article = cursor.fetchone()
    finally:
        connection.close()
    if article is None or article["topic"] not in TOPICS:
        raise HTTPException(404, "Article not found.")
    logging.getLogger("uvicorn.error").info("[READ] Article %s | %s", article_id, article["title"])
    return article
