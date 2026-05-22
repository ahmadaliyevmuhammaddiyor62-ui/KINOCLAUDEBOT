"""
🗄️ database.py — Asinxron SQLite ma'lumotlar bazasi
aiosqlite orqali barcha CRUD operatsiyalari.
"""

import aiosqlite
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from config import config

logger = logging.getLogger(__name__)


class Database:
    """Asosiy database sinfi — barcha jadvallar va so'rovlar shu yerda."""

    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path

    # ═══════════════════════════════════════════════════════════
    # 🏗️  JADVAL YARATISH
    # ═══════════════════════════════════════════════════════════

    async def create_tables(self):
        """Barcha jadvallarni yaratish (agar mavjud bo'lmasa)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                -- Foydalanuvchilar jadvali
                CREATE TABLE IF NOT EXISTS users (
                    id          INTEGER PRIMARY KEY,
                    user_id     INTEGER UNIQUE NOT NULL,
                    username    TEXT,
                    full_name   TEXT,
                    is_banned   INTEGER DEFAULT 0,
                    is_admin    INTEGER DEFAULT 0,
                    joined_at   TEXT DEFAULT (datetime('now')),
                    last_seen   TEXT DEFAULT (datetime('now'))
                );

                -- Kategoriyalar jadvali
                CREATE TABLE IF NOT EXISTS categories (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT UNIQUE NOT NULL,
                    emoji       TEXT DEFAULT '🎬',
                    created_at  TEXT DEFAULT (datetime('now'))
                );

                -- Kinolar jadvali
                CREATE TABLE IF NOT EXISTS movies (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    code        TEXT UNIQUE NOT NULL,        -- Qidiruv kodi (masalan: 001)
                    title       TEXT NOT NULL,
                    description TEXT,
                    category_id INTEGER REFERENCES categories(id),
                    year        INTEGER,
                    language    TEXT DEFAULT 'O''zbek',
                    quality     TEXT DEFAULT 'HD',
                    file_id     TEXT NOT NULL,               -- Telegram file_id
                    poster_id   TEXT,                        -- Poster rasm file_id
                    trailer_url TEXT,                        -- YouTube trailer linki
                    views       INTEGER DEFAULT 0,
                    is_active   INTEGER DEFAULT 1,
                    added_by    INTEGER,
                    created_at  TEXT DEFAULT (datetime('now'))
                );

                -- Qidiruv tarixi jadvali
                CREATE TABLE IF NOT EXISTS search_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    query       TEXT NOT NULL,
                    found       INTEGER DEFAULT 0,
                    searched_at TEXT DEFAULT (datetime('now'))
                );

                -- Reklama jadvali
                CREATE TABLE IF NOT EXISTS ads (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    content     TEXT NOT NULL,
                    media_id    TEXT,
                    media_type  TEXT,
                    sent_count  INTEGER DEFAULT 0,
                    created_at  TEXT DEFAULT (datetime('now'))
                );

                -- Indekslar (tezlashtirish uchun)
                CREATE INDEX IF NOT EXISTS idx_movies_code ON movies(code);
                CREATE INDEX IF NOT EXISTS idx_movies_active ON movies(is_active);
                CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
            """)
            await db.commit()
        logger.info("✅ Barcha jadvallar yaratildi/tekshirildi.")

    # ═══════════════════════════════════════════════════════════
    # 👤  FOYDALANUVCHILAR
    # ═══════════════════════════════════════════════════════════

    async def add_or_update_user(self, user_id: int, username: str, full_name: str):
        """Foydalanuvchini qo'shish yoki yangilash."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, username, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username  = excluded.username,
                    full_name = excluded.full_name,
                    last_seen = datetime('now')
            """, (user_id, username, full_name))
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_users(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE is_banned = 0 ORDER BY joined_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_users_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def ban_user(self, user_id: int, ban: bool = True):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_banned = ? WHERE user_id = ?",
                (1 if ban else 0, user_id)
            )
            await db.commit()

    async def set_admin(self, user_id: int, is_admin: bool = True):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_admin = ? WHERE user_id = ?",
                (1 if is_admin else 0, user_id)
            )
            await db.commit()

    async def is_banned(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        return bool(user and user.get("is_banned"))

    async def is_admin(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        return bool(user and user.get("is_admin"))

    # ═══════════════════════════════════════════════════════════
    # 🎬  KINOLAR
    # ═══════════════════════════════════════════════════════════

    async def add_movie(
        self,
        code: str,
        title: str,
        file_id: str,
        description: str = "",
        category_id: Optional[int] = None,
        year: Optional[int] = None,
        language: str = "O'zbek",
        quality: str = "HD",
        poster_id: Optional[str] = None,
        trailer_url: Optional[str] = None,
        added_by: Optional[int] = None,
    ) -> bool:
        """Yangi kino qo'shish. Muvaffaqiyatli bo'lsa True qaytaradi."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO movies
                        (code, title, description, category_id, year, language,
                         quality, file_id, poster_id, trailer_url, added_by)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (code, title, description, category_id, year, language,
                      quality, file_id, poster_id, trailer_url, added_by))
                await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False  # Kod allaqachon mavjud

    async def get_movie_by_code(self, code: str) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT m.*, c.name AS category_name, c.emoji AS category_emoji
                FROM movies m
                LEFT JOIN categories c ON m.category_id = c.id
                WHERE m.code = ? AND m.is_active = 1
            """, (code,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    await db.execute(
                        "UPDATE movies SET views = views + 1 WHERE code = ?", (code,)
                    )
                    await db.commit()
                    return dict(row)
                return None

    async def search_movies(self, query: str, page: int = 1) -> Tuple[List[Dict], int]:
        """Kino nomi bo'yicha qidiruv, pagination bilan."""
        offset = (page - 1) * config.PAGE_SIZE
        like = f"%{query}%"
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT COUNT(*) FROM movies WHERE title LIKE ? AND is_active = 1",
                (like,)
            ) as cursor:
                total = (await cursor.fetchone())[0]

            async with db.execute("""
                SELECT m.*, c.name AS category_name, c.emoji AS category_emoji
                FROM movies m
                LEFT JOIN categories c ON m.category_id = c.id
                WHERE m.title LIKE ? AND m.is_active = 1
                ORDER BY m.views DESC
                LIMIT ? OFFSET ?
            """, (like, config.PAGE_SIZE, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows], total

    async def get_movies_paginated(self, page: int = 1, category_id: Optional[int] = None) -> Tuple[List[Dict], int]:
        """Barcha kinolar, kategoriya filtri bilan."""
        offset = (page - 1) * config.PAGE_SIZE
        where = "m.is_active = 1"
        params: list = []
        if category_id:
            where += " AND m.category_id = ?"
            params.append(category_id)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"SELECT COUNT(*) FROM movies m WHERE {where}", params
            ) as cursor:
                total = (await cursor.fetchone())[0]

            async with db.execute(f"""
                SELECT m.*, c.name AS category_name, c.emoji AS category_emoji
                FROM movies m
                LEFT JOIN categories c ON m.category_id = c.id
                WHERE {where}
                ORDER BY m.created_at DESC
                LIMIT ? OFFSET ?
            """, params + [config.PAGE_SIZE, offset]) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows], total

    async def update_movie(self, code: str, **fields) -> bool:
        if not fields:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [code]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE movies SET {set_clause} WHERE code = ?", values
            )
            await db.commit()
        return True

    async def delete_movie(self, code: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM movies WHERE code = ?", (code,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_movies_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM movies WHERE is_active=1") as c:
                return (await c.fetchone())[0]

    async def get_top_movies(self, limit: int = 10) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM movies WHERE is_active=1 ORDER BY views DESC LIMIT ?",
                (limit,)
            ) as cursor:
                return [dict(r) for r in await cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════
    # 📂  KATEGORIYALAR
    # ═══════════════════════════════════════════════════════════

    async def add_category(self, name: str, emoji: str = "🎬") -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO categories (name, emoji) VALUES (?, ?)", (name, emoji)
                )
                await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def get_categories(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM categories ORDER BY name") as cursor:
                return [dict(r) for r in await cursor.fetchall()]

    async def delete_category(self, cat_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            await db.commit()
            return cursor.rowcount > 0

    # ═══════════════════════════════════════════════════════════
    # 📊  STATISTIKA
    # ═══════════════════════════════════════════════════════════

    async def log_search(self, user_id: int, query: str, found: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO search_history (user_id, query, found) VALUES (?,?,?)",
                (user_id, query, 1 if found else 0)
            )
            await db.commit()

    async def get_stats(self) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            async with db.execute("SELECT COUNT(*) FROM users") as c:
                stats["total_users"] = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM movies WHERE is_active=1") as c:
                stats["total_movies"] = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM categories") as c:
                stats["total_categories"] = (await c.fetchone())[0]
            async with db.execute("SELECT SUM(views) FROM movies") as c:
                row = await c.fetchone()
                stats["total_views"] = row[0] or 0
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE joined_at >= date('now','-1 day')"
            ) as c:
                stats["new_users_today"] = (await c.fetchone())[0]
            return stats


# Singleton instance
db = Database()
