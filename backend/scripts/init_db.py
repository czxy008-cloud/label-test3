"""
数据库初始化脚本
================
功能说明:
1. 创建数据库表结构
2. 插入基础种子数据（管理员用户、普通用户、会议室数据）

使用方法:
    python scripts/init_db.py

注意: 运行前请确保 PostgreSQL 服务已启动，并在 .env 中配置正确的数据库连接
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.database import Base
from app.models import User, Room, Booking
from app.auth import get_password_hash
from datetime import datetime, timedelta

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/meeting_room")


def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    db_name = DATABASE_URL.rsplit('/', 1)[-1]
    base_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'

    print(f"检查数据库 {db_name} 是否存在...")

    try:
        engine = create_engine(base_url)
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
            exists = result.scalar()
            if not exists:
                print(f"创建数据库 {db_name}...")
                conn.execute(text("COMMIT"))
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"数据库 {db_name} 创建成功")
            else:
                print(f"数据库 {db_name} 已存在")
    except Exception as e:
        print(f"数据库检查/创建失败: {e}")
        print("请手动创建数据库后重试")
        sys.exit(1)


def create_tables():
    """创建所有数据表"""
    print("\n创建数据表...")
    engine = create_engine(DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("数据表创建完成")
    return engine


def seed_data(engine):
    """插入种子数据"""
    print("\n插入种子数据...")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # ========== 创建用户 ==========
        print("  - 创建管理员用户")
        admin_user = User(
            username="admin",
            email="admin@example.com",
            full_name="系统管理员",
            hashed_password=get_password_hash("admin123"),
            is_admin=True,
            is_active=True
        )
        db.add(admin_user)

        print("  - 创建普通用户")
        user1 = User(
            username="zhangsan",
            email="zhangsan@example.com",
            full_name="张三",
            hashed_password=get_password_hash("123456"),
            is_admin=False,
            is_active=True
        )
        user2 = User(
            username="lisi",
            email="lisi@example.com",
            full_name="李四",
            hashed_password=get_password_hash("123456"),
            is_admin=False,
            is_active=True
        )
        user3 = User(
            username="wangwu",
            email="wangwu@example.com",
            full_name="王五",
            hashed_password=get_password_hash("123456"),
            is_admin=False,
            is_active=True
        )
        db.add_all([user1, user2, user3])
        db.flush()

        # ========== 创建会议室 ==========
        print("  - 创建会议室")
        rooms = [
            Room(
                name="会议室 A101",
                capacity=10,
                description="小型会议室，适合小组讨论",
                facilities=["投影仪", "白板", "视频会议"]
            ),
            Room(
                name="会议室 B201",
                capacity=20,
                description="中型会议室，适合部门会议",
                facilities=["投影仪", "白板", "视频会议", "音响系统"]
            ),
            Room(
                name="多功能厅 C301",
                capacity=50,
                description="大型多功能厅，适合全体会议、培训",
                facilities=["投影仪", "白板", "音响系统", "麦克风", "视频会议"]
            ),
            Room(
                name="洽谈室 D101",
                capacity=6,
                description="小型洽谈室，适合客户接待",
                facilities=["电视", "白板"]
            ),
            Room(
                name="培训室 E201",
                capacity=30,
                description="培训专用会议室",
                facilities=["投影仪", "白板", "音响系统", "电脑"]
            )
        ]
        db.add_all(rooms)
        db.flush()

        # ========== 创建示例预约 ==========
        print("  - 创建示例预约数据")
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)

        bookings = [
            Booking(
                room_id=rooms[0].id,
                user_id=user1.id,
                title="产品需求讨论会",
                start_time=tomorrow.replace(hour=9, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=10, minute=30, second=0, microsecond=0),
                attendees=8,
                description="讨论新功能需求评审"
            ),
            Booking(
                room_id=rooms[1].id,
                user_id=user2.id,
                title="周例会",
                start_time=tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=15, minute=0, second=0, microsecond=0),
                attendees=15,
                description="技术部周例会"
            ),
            Booking(
                room_id=rooms[2].id,
                user_id=user3.id,
                title="全员大会",
                start_time=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=12, minute=0, second=0, microsecond=0),
                attendees=40,
                description="公司全体员工大会"
            )
        ]
        db.add_all(bookings)

        db.commit()
        print("\n种子数据插入完成！")
        print("\n默认账号:")
        print("  管理员: admin / admin123")
        print("  普通用户: zhangsan / 123456")
        print("            lisi / 123456")
        print("            wangwu / 123456")

    except Exception as e:
        db.rollback()
        print(f"种子数据插入失败: {e}")
        raise
    finally:
        db.close()


def main():
    print("=" * 60)
    print("会议室预约系统 - 数据库初始化")
    print("=" * 60)

    create_database_if_not_exists()
    engine = create_tables()
    seed_data(engine)

    print("\n" + "=" * 60)
    print("数据库初始化完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
