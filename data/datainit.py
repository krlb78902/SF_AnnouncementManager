import sqlite3
from datetime import datetime

def init_database(db_path='announcements.db'):
    """
    初始化数据库和公告表。

    Args:
        db_path (str): 数据库文件路径。默认为 'announcements.db'.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 使用更简洁、规范的SQL语句格式
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,     -- 主键，自增
                title TEXT NOT NULL,                      -- 公告标题，非空
                content TEXT NOT NULL,                    -- 公告内容，非空
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新时间
                deleted_at DATETIME DEFAULT NULL          -- 软删除时间
            )
            """
            # 执行建表语句
            cursor.execute(create_table_sql)

            # （可选）创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_announcements_deleted_at ON announcements(deleted_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_announcements_created_at ON announcements(created_at);")

            conn.commit()
            print(f"数据库初始化成功！数据库文件位于: {db_path}")
            print("表 'announcements' 已就绪。")

    except sqlite3.Error as e:
        print(f"数据库初始化过程中出错: {e}")

if __name__ == "__main__":
    init_database()