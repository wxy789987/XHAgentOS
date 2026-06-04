import hashlib
import secrets
import sqlite3

from app.models.db import get_connection


def _hash_password(password: str, salt: bytes) -> str:
	dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
	return dk.hex()


class UserRepository:
	@staticmethod
	def create_user(username: str, password: str) -> bool:
		"""创建用户，成功返回 True，用户名重复返回 False"""
		salt = secrets.token_bytes(16)
		password_hash = _hash_password(password, salt)
		try:
			with get_connection() as conn:
				conn.execute(
					"INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
					(username, password_hash, salt.hex()),
				)
			return True
		except sqlite3.IntegrityError:
			return False

	@staticmethod
	def get_user_by_username(username: str):
		with get_connection() as conn:
			row = conn.execute(
				"SELECT id, username, password_hash, salt, create_at FROM users WHERE username = ?",
				(username,),
			).fetchone()
			return row

	@staticmethod
	def get_user_by_id(user_id: int):
		with get_connection() as conn:
			row = conn.execute(
				"SELECT id, username, create_at FROM users WHERE id = ?",
				(user_id,),
			).fetchone()
			return row

	@staticmethod
	def verify_user(username: str, password: str) -> bool:
		row = UserRepository.get_user_by_username(username)
		if not row:
			return False
		salt = bytes.fromhex(row["salt"])
		return _hash_password(password, salt) == row["password_hash"]

	@staticmethod
	def list_users(page: int = 1, page_size: int = 28):
		"""分页查询用户列表，返回 (rows, total)"""
		offset = (page - 1) * page_size
		with get_connection() as conn:
			rows = conn.execute(
				"SELECT id, username, create_at FROM users ORDER BY id DESC LIMIT ? OFFSET ?",
				(page_size, offset),
			).fetchall()
			total = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()["cnt"]
		return rows, total

	@staticmethod
	def update_user(user_id: int, username: str = None, password: str = None) -> bool:
		"""更新用户信息，至少提供 username 或 password 之一"""
		with get_connection() as conn:
			if password:
				salt = secrets.token_bytes(16)
				password_hash = _hash_password(password, salt)
				conn.execute(
					"UPDATE users SET password_hash=?, salt=? WHERE id=?",
					(password_hash, salt.hex(), user_id),
				)
			if username:
				try:
					conn.execute(
						"UPDATE users SET username=? WHERE id=?",
						(username, user_id),
					)
				except sqlite3.IntegrityError:
					return False
		return True

	@staticmethod
	def delete_user(user_id: int) -> bool:
		with get_connection() as conn:
			conn.execute("DELETE FROM users WHERE id=?", (user_id,))
		return True