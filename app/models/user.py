import hashlib
import secrets
import sqlite3

from app.models.db import get_connection


def _hash_password(password: str, salt: bytes) -> str:
	dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
	return dk.hex()


class UserRepository:
	@staticmethod
	def create_user(username: str, password: str, role_id: int = 2) -> bool:
		"""创建用户，成功返回 True，用户名重复返回 False。默认角色为普通用户(role_id=2)"""
		salt = secrets.token_bytes(16)
		password_hash = _hash_password(password, salt)
		try:
			with get_connection() as conn:
				conn.execute(
					"INSERT INTO users (username, password_hash, salt, role_id) VALUES (?, ?, ?, ?)",
					(username, password_hash, salt.hex(), role_id),
				)
			return True
		except sqlite3.IntegrityError:
			return False

	@staticmethod
	def get_user_by_username(username: str):
		with get_connection() as conn:
			row = conn.execute(
				"SELECT id, username, password_hash, salt, role_id, create_at FROM users WHERE username = ?",
				(username,),
			).fetchone()
			return row

	@staticmethod
	def get_user_by_id(user_id: int):
		with get_connection() as conn:
			row = conn.execute(
				"SELECT u.id, u.username, u.role_id, u.create_at FROM users u WHERE u.id = ?",
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
				"SELECT u.id, u.username, u.role_id, u.create_at, COALESCE(r.name, '') AS role_name "
				"FROM users u LEFT JOIN roles r ON u.role_id = r.id "
				"ORDER BY u.id DESC LIMIT ? OFFSET ?",
				(page_size, offset),
			).fetchall()
			total = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()["cnt"]
		return rows, total

	@staticmethod
	def update_user(user_id: int, username: str = None, password: str = None, role_id: int = None) -> bool:
		"""更新用户信息，至少提供 username 或 password 或 role_id 之一"""
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
			if role_id is not None:
				conn.execute(
					"UPDATE users SET role_id=? WHERE id=?",
					(role_id, user_id),
				)
		return True

	@staticmethod
	def delete_user(user_id: int) -> bool:
		with get_connection() as conn:
			conn.execute("DELETE FROM users WHERE id=?", (user_id,))
		return True