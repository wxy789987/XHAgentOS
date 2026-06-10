# 用户侧对话功能 - 数据访问层
import json
from app.models.db import get_connection


class FriendRepository:
    @staticmethod
    def get_friends(user_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT u.id, u.username, f.remark, f.create_at FROM user_friends f "
                "JOIN users u ON u.id = f.friend_id "
                "WHERE f.user_id=? AND f.status='accepted' "
                "ORDER BY u.username", (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def add_friend(user_id, friend_id):
        with get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO user_friends (user_id, friend_id) VALUES (?, ?)",
                (user_id, friend_id)
            )
            conn.execute(
                "INSERT OR IGNORE INTO user_friends (user_id, friend_id) VALUES (?, ?)",
                (friend_id, user_id)
            )

    @staticmethod
    def remove_friend(user_id, friend_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM user_friends WHERE user_id=? AND friend_id=?", (user_id, friend_id))
            conn.execute("DELETE FROM user_friends WHERE user_id=? AND friend_id=?", (friend_id, user_id))

    @staticmethod
    def search_users(keyword):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, username FROM users WHERE username LIKE ? LIMIT 20",
                (f"%{keyword}%",)
            ).fetchall()
            return [dict(r) for r in rows]


class FriendRequestRepository:
    @staticmethod
    def send_request(from_user_id, to_user_id, message=""):
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM friend_requests WHERE from_user_id=? AND to_user_id=? AND status='pending'",
                (from_user_id, to_user_id)
            ).fetchone()
            if existing:
                return False
            conn.execute(
                "INSERT INTO friend_requests (from_user_id, to_user_id, message) VALUES (?, ?, ?)",
                (from_user_id, to_user_id, message)
            )
            return True

    @staticmethod
    def get_pending_requests(user_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT r.id, r.from_user_id, u.username as from_username, r.message, r.create_at "
                "FROM friend_requests r JOIN users u ON u.id = r.from_user_id "
                "WHERE r.to_user_id=? AND r.status='pending' "
                "ORDER BY r.create_at DESC", (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def accept_request(request_id):
        with get_connection() as conn:
            req = conn.execute("SELECT * FROM friend_requests WHERE id=?", (request_id,)).fetchone()
            if not req:
                return False
            conn.execute("UPDATE friend_requests SET status='accepted', update_at=datetime('now') WHERE id=?", (request_id,))
            FriendRepository.add_friend(req["from_user_id"], req["to_user_id"])
            return True

    @staticmethod
    def reject_request(request_id):
        with get_connection() as conn:
            conn.execute("UPDATE friend_requests SET status='rejected', update_at=datetime('now') WHERE id=?", (request_id,))


class GroupRepository:
    @staticmethod
    def create(name, description, owner_id):
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO user_groups (name, description, owner_id) VALUES (?, ?, ?)",
                (name, description, owner_id)
            )
            group_id = cur.lastrowid
            conn.execute(
                "INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, 'owner')",
                (group_id, owner_id)
            )
            return group_id

    @staticmethod
    def get_my_groups(user_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT g.id, g.name, g.description, g.owner_id, "
                "(SELECT COUNT(*) FROM group_members WHERE group_id=g.id) as member_count "
                "FROM user_groups g JOIN group_members m ON m.group_id=g.id "
                "WHERE m.user_id=? ORDER BY g.name", (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def search_groups(keyword):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, description FROM user_groups WHERE name LIKE ? LIMIT 20",
                (f"%{keyword}%",)
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def join_group(group_id, user_id):
        with get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
                (group_id, user_id)
            )

    @staticmethod
    def get_members(group_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT u.id, u.username, m.role, m.create_at "
                "FROM group_members m JOIN users u ON u.id = m.user_id "
                "WHERE m.group_id=? ORDER BY m.role, u.username", (group_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def invite_member(group_id, user_id):
        with get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
                (group_id, user_id)
            )

    @staticmethod
    def remove_member(group_id, user_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id))

    @staticmethod
    def get_employees(group_id):
        """获取群组中的数字员工"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT e.id, e.name, e.description, e.model_id, e.system_prompt "
                "FROM group_employees ge JOIN digital_employees e ON e.id = ge.employee_id "
                "WHERE ge.group_id=? ORDER BY e.name", (group_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def invite_employee(group_id, employee_id, added_by=0):
        """添加数字员工到群组"""
        with get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO group_employees (group_id, employee_id, added_by) VALUES (?, ?, ?)",
                (group_id, employee_id, added_by)
            )

    @staticmethod
    def remove_employee(group_id, employee_id):
        """从群组移除数字员工"""
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM group_employees WHERE group_id=? AND employee_id=?",
                (group_id, employee_id)
            )


class GroupMessageRepository:
    @staticmethod
    def send(group_id, user_id, content, msg_type="text"):
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO group_messages (group_id, user_id, content, msg_type) VALUES (?, ?, ?, ?)",
                (group_id, user_id, content, msg_type)
            )
            return cur.lastrowid

    @staticmethod
    def get_messages(group_id, page=1, page_size=50):
        with get_connection() as conn:
            offset = (page - 1) * page_size
            rows = conn.execute(
                "SELECT m.*, COALESCE(u.username, '数字员工') as username FROM group_messages m "
                "LEFT JOIN users u ON u.id = m.user_id "
                "WHERE m.group_id=? ORDER BY m.id DESC LIMIT ? OFFSET ?",
                (group_id, page_size, offset)
            ).fetchall()
            messages = [dict(r) for r in rows]
            messages.reverse()
            return messages
