#!/usr/bin/env python3
"""
数据库初始化脚本

功能：
1. 创建所有数据库表
2. 创建默认管理员账号
3. 初始化默认管理员权限
4. 验证数据库连接

使用方法：
    python scripts/init_db.py

环境变量：
    ADMIN_USERNAME: 管理员用户名（默认：admin）
    ADMIN_EMAIL: 管理员邮箱（默认：admin@appleid-auto.local）
    ADMIN_PASSWORD: 管理员密码（默认：Admin@123456）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.database import engine, async_session_maker, Base

# 导入所有模型（确保 Base.metadata 包含所有表）
from app.models.user import User
from app.models.permission import UserPermission, Package
from app.models.card import Card, CardLog
from app.models.apple_account import AppleAccount, PasswordHistory
from app.models.task import UnlockTask
from app.models.share_page import SharePage, SharePageLog
from app.models.proxy import Proxy
from app.models.node import Node
from app.models.system import SystemSetting, APIKey, OperationLog


async def create_tables():
    """创建所有数据库表"""
    print("📋 开始创建数据库表...")

    async with engine.begin() as conn:
        # 删除所有表（仅在开发环境）
        if settings.DEBUG:
            print("⚠️  开发模式：删除现有表...")
            await conn.run_sync(Base.metadata.drop_all)

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库表创建成功！")
    print(f"   创建的表：{len(Base.metadata.tables)} 个")
    for table_name in Base.metadata.tables.keys():
        print(f"   - {table_name}")


async def create_default_admin(session: AsyncSession):
    """创建默认管理员账号"""
    print("\n👤 检查默认管理员账号...")

    # 检查管理员是否已存在
    result = await session.execute(
        select(User).where(User.username == settings.ADMIN_USERNAME)
    )
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        print(f"⚠️  管理员账号已存在：{settings.ADMIN_USERNAME}")
        return existing_admin

    # 创建管理员账号
    print(f"📝 创建管理员账号：{settings.ADMIN_USERNAME}")
    admin_user = User(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        password_hash=get_password_hash(settings.ADMIN_PASSWORD),
        role="admin",
        is_active=True,
        is_verified=True,
        full_name="系统管理员",
    )

    session.add(admin_user)
    await session.flush()  # 获取 admin_user.id

    print(f"✅ 管理员账号创建成功！")
    print(f"   用户名: {settings.ADMIN_USERNAME}")
    print(f"   邮箱: {settings.ADMIN_EMAIL}")
    print(f"   密码: {settings.ADMIN_PASSWORD}")
    print(f"   ID: {admin_user.id}")

    return admin_user


async def create_default_permission(session: AsyncSession, user_id: int):
    """创建默认管理员权限"""
    print("\n🔑 检查管理员权限...")

    # 检查权限是否已存在
    result = await session.execute(
        select(UserPermission).where(UserPermission.user_id == user_id)
    )
    existing_permission = result.scalar_one_or_none()

    if existing_permission:
        print(f"⚠️  管理员权限已存在")
        return existing_permission

    # 创建管理员权限（无限制）
    print(f"📝 创建管理员权限...")
    admin_permission = UserPermission(
        user_id=user_id,
        package_id=None,  # 管理员不需要套餐

        # 配额（-1 表示无限制）
        max_accounts=-1,
        max_share_pages=-1,
        max_nodes=-1,
        max_proxies=-1,

        # 限制
        check_interval=60,  # 1分钟检测间隔（最快）
        max_concurrent_tasks=-1,  # 无限并发

        # 功能权限（管理员全部开启）
        allow_custom_html=True,
        allow_api_access=True,
        allow_export=True,
        allow_batch_import=True,

        # 过期时间（管理员永不过期）
        expires_at=None,
        is_active=True,
    )

    session.add(admin_permission)
    await session.flush()

    print(f"✅ 管理员权限创建成功！")
    print(f"   账号配额: 无限制")
    print(f"   分享页配额: 无限制")
    print(f"   节点配额: 无限制")
    print(f"   代理配额: 无限制")
    print(f"   功能权限: 全部开启")

    return admin_permission


async def verify_database():
    """验证数据库连接和表结构"""
    print("\n🔍 验证数据库...")

    async with async_session_maker() as session:
        # 测试查询
        result = await session.execute(select(User).limit(1))
        users = result.scalars().all()

        print(f"✅ 数据库连接正常")
        print(f"   用户数量: {len(users)}")

        # 验证所有表
        tables = [
            "users", "user_permissions", "packages", "cards", "card_logs",
            "apple_accounts", "password_history", "unlock_tasks",
            "share_pages", "share_page_logs", "proxies", "nodes",
            "system_settings", "api_keys", "operation_logs"
        ]

        print(f"\n📊 数据库表验证:")
        for table in tables:
            if table in Base.metadata.tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} (缺失)")


async def init_database():
    """初始化数据库"""
    print("="*60)
    print("🚀 Apple ID 自动解锁系统 - 数据库初始化")
    print("="*60)

    try:
        # 1. 创建所有表
        await create_tables()

        # 2. 创建默认数据
        async with async_session_maker() as session:
            # 创建默认管理员账号
            admin_user = await create_default_admin(session)

            # 创建默认管理员权限
            await create_default_permission(session, admin_user.id)

            # 提交事务
            await session.commit()

        # 3. 验证数据库
        await verify_database()

        print("\n" + "="*60)
        print("🎉 数据库初始化完成！")
        print("="*60)
        print("\n📝 管理员登录信息：")
        print(f"   用户名: {settings.ADMIN_USERNAME}")
        print(f"   密码: {settings.ADMIN_PASSWORD}")
        print(f"   邮箱: {settings.ADMIN_EMAIL}")
        print("\n⚠️  请在首次登录后立即修改管理员密码！")
        print("\n🔗 API 文档: http://localhost:8000/api/docs")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await engine.dispose()


def main():
    """主函数"""
    # 运行异步初始化
    asyncio.run(init_database())


if __name__ == "__main__":
    main()
