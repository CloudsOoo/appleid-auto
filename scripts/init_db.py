"""
数据库初始化脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import engine, Base, async_session_maker
from app.models import *
from app.core.security import get_password_hash
from app.core.config import settings


async def create_tables():
    """创建所有表"""
    print("🔧 创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


async def create_admin_user():
    """创建管理员账号"""
    print("👤 创建管理员账号...")

    async with async_session_maker() as db:
        from app.models.user import User
        from app.models.permission import UserPermission
        from sqlalchemy import select

        # 检查管理员是否已存在
        result = await db.execute(
            select(User).where(User.username == settings.ADMIN_USERNAME)
        )
        admin = result.scalar_one_or_none()

        if admin:
            print(f"⚠️  管理员账号已存在: {settings.ADMIN_USERNAME}")
            return

        # 创建管理员
        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role="admin",
            is_active=True,
            is_verified=True,
            full_name="系统管理员",
        )
        db.add(admin)
        await db.flush()

        # 创建管理员权限（无限制）
        permission = UserPermission(
            user_id=admin.id,
            max_accounts=9999,
            max_share_pages=100,
            max_nodes=50,
            min_unlock_interval=60,
            allow_custom_html=True,
            allow_view_password_history=True,
            allow_batch_import=True,
            allow_api_access=True,
            max_unlock_per_day=9999,
            max_import_per_time=1000,
        )
        db.add(permission)

        await db.commit()

        print(f"✅ 管理员账号创建成功")
        print(f"   用户名: {settings.ADMIN_USERNAME}")
        print(f"   邮箱: {settings.ADMIN_EMAIL}")
        print(f"   密码: {settings.ADMIN_PASSWORD}")
        print(f"   ⚠️  请立即修改默认密码！")


async def create_default_packages():
    """创建默认套餐"""
    print("📦 创建默认套餐...")

    async with async_session_maker() as db:
        from app.models.package import Package
        from sqlalchemy import select

        # 检查是否已有套餐
        result = await db.execute(select(Package))
        if result.scalars().first():
            print("⚠️  套餐已存在，跳过创建")
            return

        # 创建默认套餐
        packages = [
            Package(
                name="免费版",
                description="适合个人测试",
                max_accounts=5,
                max_share_pages=1,
                max_nodes=1,
                min_unlock_interval=3600,
                allow_custom_html=False,
                allow_view_password_history=False,
                allow_batch_import=True,
                allow_api_access=False,
                max_unlock_per_day=10,
                max_import_per_time=10,
                price=0.00,
                currency="CNY",
                is_active=True,
                sort_order=1,
            ),
            Package(
                name="基础版",
                description="适合小规模使用",
                max_accounts=50,
                max_share_pages=5,
                max_nodes=2,
                min_unlock_interval=1800,
                allow_custom_html=True,
                allow_view_password_history=True,
                allow_batch_import=True,
                allow_api_access=False,
                max_unlock_per_day=100,
                max_import_per_time=100,
                price=99.00,
                currency="CNY",
                is_active=True,
                sort_order=2,
            ),
            Package(
                name="专业版",
                description="适合中小企业",
                max_accounts=200,
                max_share_pages=20,
                max_nodes=5,
                min_unlock_interval=600,
                allow_custom_html=True,
                allow_view_password_history=True,
                allow_batch_import=True,
                allow_api_access=True,
                max_unlock_per_day=500,
                max_import_per_time=500,
                price=299.00,
                currency="CNY",
                is_active=True,
                sort_order=3,
            ),
            Package(
                name="企业版",
                description="适合大规模使用",
                max_accounts=1000,
                max_share_pages=100,
                max_nodes=20,
                min_unlock_interval=300,
                allow_custom_html=True,
                allow_view_password_history=True,
                allow_batch_import=True,
                allow_api_access=True,
                max_unlock_per_day=2000,
                max_import_per_time=1000,
                price=999.00,
                currency="CNY",
                is_active=True,
                sort_order=4,
            ),
        ]

        for package in packages:
            db.add(package)

        await db.commit()
        print(f"✅ 创建了 {len(packages)} 个默认套餐")


async def init_database():
    """初始化数据库"""
    print("=" * 60)
    print("🚀 Apple ID 自动解锁系统 - 数据库初始化")
    print("=" * 60)

    try:
        await create_tables()
        await create_admin_user()
        await create_default_packages()

        print("=" * 60)
        print("✅ 数据库初始化完成！")
        print("=" * 60)
        print("\n📌 下一步:")
        print("1. 启动后端服务: uvicorn app.main:app --reload")
        print("2. 访问 API 文档: http://localhost:8000/api/docs")
        print(f"3. 使用管理员账号登录: {settings.ADMIN_USERNAME}")
        print("4. ⚠️  立即修改默认密码！\n")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_database())
