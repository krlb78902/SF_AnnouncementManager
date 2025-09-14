import sqlite3
from datetime import datetime , timedelta
import threading
import time


class AnnouncementManager:
    def __init__(self, db_path='announcements.db'):
        """
        初始化公告管理器，连接到数据库[3,7](@ref)。

        Args:
            db_path (str): 数据库文件路径。默认为 'announcements.db'.
        """
        self.db_path = db_path
        self._expiry_checker_running = False
        self._expiry_checker_thread = None

    def _get_connection(self):
        """获取数据库连接[3,7](@ref)"""
        return sqlite3.connect(self.db_path)

    def create_announcement(self, title, content, expires_after_hours=None):
        """
        创建新公告[2,3](@ref)。

        Args:
            title (str): 公告标题
            content (str): 公告内容
            expires_after_hours (int): 多少小时后自动删除公告，None表示永不过期

        Returns:
            int: 新公告的ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if expires_after_hours is not None:
                expires_at = datetime.now() + timedelta(hours=expires_after_hours)
                cursor.execute(
                    "INSERT INTO announcements (title, content, expires_at) VALUES (?, ?, ?)",
                    (title, content, expires_at)
                )
            else:
                cursor.execute(
                    "INSERT INTO announcements (title, content) VALUES (?, ?)",
                    (title, content)
                )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def check_and_delete_expired(self):
        """
        检查并删除过期的公告[1,5](@ref)。

        Returns:
            int: 删除的公告数量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 查找所有过期的公告
            cursor.execute(
                "SELECT id FROM announcements WHERE deleted_at IS NULL AND expires_at IS NOT NULL AND expires_at <= datetime('now')"
            )
            expired_ids = [row[0] for row in cursor.fetchall()]

            # 软删除过期公告
            if expired_ids:
                placeholders = ','.join('?' * len(expired_ids))
                cursor.execute(
                    f"UPDATE announcements SET deleted_at = datetime('now') WHERE id IN ({placeholders})",
                    expired_ids
                )
                conn.commit()

            return len(expired_ids)
        finally:
            conn.close()

    def start_expiry_checker(self, interval_seconds=300):
        """
        启动后台线程定期检查并删除过期公告[5,6](@ref)。

        Args:
            interval_seconds (int): 检查间隔时间（秒），默认为300秒（5分钟）
        """
        if self._expiry_checker_running:
            return

        self._expiry_checker_running = True

        def checker_loop():
            while self._expiry_checker_running:
                try:
                    deleted_count = self.check_and_delete_expired()
                    if deleted_count > 0:
                        print(f"自动删除了 {deleted_count} 个过期公告")
                except Exception as e:
                    print(f"检查过期公告时出错: {e}")

                time.sleep(interval_seconds)

        self._expiry_checker_thread = threading.Thread(target=checker_loop)
        self._expiry_checker_thread.daemon = True
        self._expiry_checker_thread.start()
        print("公告过期检查器已启动")

    def stop_expiry_checker(self):
        """停止后台过期检查器"""
        self._expiry_checker_running = False
        if self._expiry_checker_thread:
            self._expiry_checker_thread.join(timeout=5)
        print("公告过期检查器已停止")

    def get_all_announcements(self, include_deleted=False):
        """
        获取所有公告[2,3](@ref)。

        Args:
            include_deleted (bool): 是否包含已软删除的公告

        Returns:
            list: 公告列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if include_deleted:
                # 包含所有公告，包括已软删除的
                cursor.execute("SELECT * FROM announcements ORDER BY created_at DESC")
            else:
                # 只包含未删除的公告 (deleted_at IS NULL)
                cursor.execute(
                    "SELECT * FROM announcements WHERE deleted_at IS NULL ORDER BY created_at DESC"
                )

            return cursor.fetchall()
        finally:
            conn.close()

    def get_announcement_by_id(self, announcement_id):
        """
        根据ID获取公告[2](@ref)。

        Args:
            announcement_id (int): 公告ID

        Returns:
            dict: 公告信息
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM announcements WHERE id = ?",
                (announcement_id,)
            )
            return cursor.fetchone()
        finally:
            conn.close()

    def update_announcement(self, announcement_id, title, content):
        """
        更新公告[2,3](@ref)。

        Args:
            announcement_id (int): 公告ID
            title (str): 新标题
            content (str): 新内容

        Returns:
            bool: 更新是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """UPDATE announcements
                   SET title      = ?,
                       content    = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (title, content, announcement_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def soft_delete_announcement(self, announcement_id):
        """
        软删除公告（将deleted_at设置为当前时间）[2](@ref)。

        Args:
            announcement_id (int): 公告ID

        Returns:
            bool: 删除是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE announcements SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
                (announcement_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def hard_delete_announcement(self, announcement_id):
        """
        硬删除公告（从数据库中永久删除）[2,3](@ref)。

        Args:
            announcement_id (int): 公告ID

        Returns:
            bool: 删除是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM announcements WHERE id = ?",
                (announcement_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def restore_announcement(self, announcement_id):
        """
        恢复已软删除的公告（将deleted_at设置为NULL）。

        Args:
            announcement_id (int): 公告ID

        Returns:
            bool: 恢复是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE announcements SET deleted_at = NULL WHERE id = ?",
                (announcement_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def search_announcements(self, keyword, search_title=True, search_content=True):
        """
        根据关键词搜索公告。

        Args:
            keyword (str): 搜索关键词
            search_title (bool): 是否搜索标题
            search_content (bool): 是否搜索内容

        Returns:
            list: 匹配的公告列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            conditions = []
            params = []

            if search_title and search_content:
                conditions.append("(title LIKE ? OR content LIKE ?)")
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            elif search_title:
                conditions.append("title LIKE ?")
                params.append(f'%{keyword}%')
            elif search_content:
                conditions.append("content LIKE ?")
                params.append(f'%{keyword}%')

            if conditions:
                where_clause = " AND ".join(conditions)
                sql = f"SELECT * FROM announcements WHERE {where_clause} AND deleted_at IS NULL ORDER BY created_at DESC"
                cursor.execute(sql, params)
            else:
                cursor.execute("SELECT * FROM announcements WHERE deleted_at IS NULL ORDER BY created_at DESC")

            return cursor.fetchall()
        finally:
            conn.close()


# 使用示例
if __name__ == "__main__":
    # 初始化数据库（如果尚未初始化）
    from data.datainit import *

    init_database()

    # 创建公告管理器实例
    manager = AnnouncementManager()

    # 创建新公告
    new_id = manager.create_announcement("系统通知", "系统将于本周六进行维护")
    print(f"新公告已创建，ID: {new_id}")

    # 获取所有未删除的公告
    announcements = manager.get_all_announcements()
    print("所有公告:", announcements)

    # 搜索公告
    results = manager.search_announcements("系统")
    print("搜索结果:", results)

    # 软删除公告
    if manager.soft_delete_announcement(new_id):
        print("公告已软删除")

    # 恢复公告
    if manager.restore_announcement(new_id):
        print("公告已恢复")

    # 硬删除公告
    if manager.hard_delete_announcement(new_id):
        print("公告已永久删除")