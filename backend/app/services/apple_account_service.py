"""
Apple ID 账号管理服务
"""
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
import csv
import io

from app.models.apple_account import AppleAccount, PasswordHistory
from app.models.permission import UserPermission
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data, get_password_hash
from app.schemas.account import (
    AppleAccountCreate,
    AppleAccountUpdate,
    AppleAccountResponse,
    AppleAccountDetailResponse,
    AppleAccountImportResponse,
    PasswordHistoryResponse,
)


class AppleAccountService:
    """Apple ID 账号管理服务类"""

    @staticmethod
    async def check_account_quota(
        db: AsyncSession,
        user_id: int
    ) -> Tuple[bool, str]:
        """
        检查账号配额

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Tuple[bool, str]: (是否有配额, 错误信息)
        """
        # 获取用户权限
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return False, "用户权限不存在"

        # 检查是否过期
        if permission.is_expired():
            return False, "用户权限已过期"

        # 检查账号数量配额
        result = await db.execute(
            select(func.count(AppleAccount.id)).where(AppleAccount.user_id == user_id)
        )
        current_count = result.scalar() or 0

        if current_count >= permission.max_accounts:
            return False, f"账号数量已达上限（{permission.max_accounts}）"

        return True, ""

    @staticmethod
    async def create_account(
        db: AsyncSession,
        user_id: int,
        data: AppleAccountCreate
    ) -> AppleAccount:
        """
        创建 Apple ID 账号

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 创建数据

        Returns:
            AppleAccount: 创建的账号对象
        """
        # 检查配额
        has_quota, error_msg = await AppleAccountService.check_account_quota(db, user_id)
        if not has_quota:
            raise ValueError(error_msg)

        # 检查账号是否已存在
        result = await db.execute(
            select(AppleAccount).where(
                and_(
                    AppleAccount.user_id == user_id,
                    AppleAccount.apple_id == data.apple_id
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("该 Apple ID 已存在")

        # 加密密码和密保
        encrypted_password = encrypt_sensitive_data(data.password)
        encrypted_questions = None
        if data.security_questions:
            import json
            encrypted_questions = json.loads(
                encrypt_sensitive_data(json.dumps(data.security_questions))
            )

        # 计算下次检测时间
        next_check_at = datetime.utcnow() + timedelta(seconds=data.check_interval)

        # 创建账号
        account = AppleAccount(
            user_id=user_id,
            apple_id=data.apple_id,
            current_password=encrypted_password,
            security_questions=encrypted_questions,
            tags=data.tags,
            category=data.category,
            note=data.note,
            auto_unlock=data.auto_unlock,
            auto_disable_2fa=data.auto_disable_2fa,
            auto_change_password=data.auto_change_password,
            auto_remove_devices=data.auto_remove_devices,
            check_interval=data.check_interval,
            next_check_at=next_check_at,
            status="normal",
        )

        db.add(account)
        await db.flush()

        # 创建初始密码历史
        password_history = PasswordHistory(
            account_id=account.id,
            password_hash=get_password_hash(data.password),
            changed_by="manual",
        )
        db.add(password_history)

        # 更新用户权限计数
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one()
        permission.accounts_count += 1

        await db.commit()
        await db.refresh(account)

        return account

    @staticmethod
    async def get_account(
        db: AsyncSession,
        account_id: int,
        user_id: int,
        include_password: bool = False
    ) -> Optional[AppleAccount]:
        """
        获取账号详情

        Args:
            db: 数据库会话
            account_id: 账号ID
            user_id: 用户ID
            include_password: 是否包含密码

        Returns:
            AppleAccount: 账号对象
        """
        result = await db.execute(
            select(AppleAccount).where(
                and_(
                    AppleAccount.id == account_id,
                    AppleAccount.user_id == user_id
                )
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return None

        # 如果需要密码，解密密码和密保
        if include_password and account.current_password:
            account.current_password = decrypt_sensitive_data(account.current_password)
            if account.security_questions:
                import json
                account.security_questions = json.loads(
                    decrypt_sensitive_data(json.dumps(account.security_questions))
                )

        return account

    @staticmethod
    async def update_account(
        db: AsyncSession,
        account_id: int,
        user_id: int,
        data: AppleAccountUpdate
    ) -> Optional[AppleAccount]:
        """
        更新账号信息

        Args:
            db: 数据库会话
            account_id: 账号ID
            user_id: 用户ID
            data: 更新数据

        Returns:
            AppleAccount: 更新后的账号对象
        """
        # 获取账号
        result = await db.execute(
            select(AppleAccount).where(
                and_(
                    AppleAccount.id == account_id,
                    AppleAccount.user_id == user_id
                )
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)

        # 如果更新密码，需要加密并记录历史
        if "password" in update_data:
            password = update_data.pop("password")
            encrypted_password = encrypt_sensitive_data(password)
            account.current_password = encrypted_password

            # 记录密码历史
            password_history = PasswordHistory(
                account_id=account.id,
                password_hash=get_password_hash(password),
                changed_by="manual",
            )
            db.add(password_history)

        # 如果更新密保，需要加密
        if "security_questions" in update_data:
            questions = update_data.pop("security_questions")
            if questions:
                import json
                encrypted_questions = json.loads(
                    encrypt_sensitive_data(json.dumps(questions))
                )
                account.security_questions = encrypted_questions
            else:
                account.security_questions = None

        # 更新其他字段
        for field, value in update_data.items():
            setattr(account, field, value)

        # 如果修改了检测间隔，重新计算下次检测时间
        if "check_interval" in update_data:
            account.next_check_at = datetime.utcnow() + timedelta(seconds=account.check_interval)

        account.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(account)

        return account

    @staticmethod
    async def delete_account(
        db: AsyncSession,
        account_id: int,
        user_id: int
    ) -> bool:
        """
        删除账号

        Args:
            db: 数据库会话
            account_id: 账号ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        # 获取账号
        result = await db.execute(
            select(AppleAccount).where(
                and_(
                    AppleAccount.id == account_id,
                    AppleAccount.user_id == user_id
                )
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return False

        # 删除账号（级联删除密码历史和任务）
        await db.delete(account)

        # 更新用户权限计数
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()
        if permission and permission.accounts_count > 0:
            permission.accounts_count -= 1

        await db.commit()
        return True

    @staticmethod
    async def get_account_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        lock_status: Optional[bool] = None,
        tag: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[AppleAccount], int]:
        """
        获取账号列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            status: 状态过滤
            lock_status: 锁定状态过滤
            tag: 标签过滤
            category: 分类过滤
            search: 搜索关键词

        Returns:
            Tuple[List[AppleAccount], int]: (账号列表, 总数)
        """
        # 构建基础查询
        query = select(AppleAccount).where(AppleAccount.user_id == user_id)

        # 应用过滤条件
        if status:
            query = query.where(AppleAccount.status == status)

        if lock_status is not None:
            query = query.where(AppleAccount.lock_status == lock_status)

        if tag:
            # JSONB 数组包含查询
            query = query.where(AppleAccount.tags.contains([tag]))

        if category:
            query = query.where(AppleAccount.category == category)

        if search:
            # 搜索 Apple ID、账号名称、备注
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    AppleAccount.apple_id.ilike(search_pattern),
                    AppleAccount.account_name.ilike(search_pattern),
                    AppleAccount.note.ilike(search_pattern),
                )
            )

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()

        # 排序和分页
        query = query.order_by(desc(AppleAccount.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)

        # 执行查询
        result = await db.execute(query)
        accounts = result.scalars().all()

        return list(accounts), total

    @staticmethod
    async def import_accounts(
        db: AsyncSession,
        user_id: int,
        accounts_data: List[dict],
    ) -> AppleAccountImportResponse:
        """
        批量导入账号

        Args:
            db: 数据库会话
            user_id: 用户ID
            accounts_data: 账号数据列表

        Returns:
            AppleAccountImportResponse: 导入结果
        """
        # 检查导入数量权限
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()

        if not permission:
            raise ValueError("用户权限不存在")

        if not permission.allow_batch_import:
            raise ValueError("没有批量导入权限")

        if len(accounts_data) > permission.max_import_per_time:
            raise ValueError(f"单次导入数量超过限制（{permission.max_import_per_time}）")

        # 检查配额
        result = await db.execute(
            select(func.count(AppleAccount.id)).where(AppleAccount.user_id == user_id)
        )
        current_count = result.scalar() or 0

        available_quota = permission.max_accounts - current_count
        if len(accounts_data) > available_quota:
            raise ValueError(f"账号配额不足，剩余配额：{available_quota}")

        # 批量导入
        success_count = 0
        failed_count = 0
        errors = []

        for idx, account_data in enumerate(accounts_data):
            try:
                # 验证必需字段
                if "apple_id" not in account_data or "password" not in account_data:
                    raise ValueError("缺少必需字段：apple_id 或 password")

                # 检查是否已存在
                result = await db.execute(
                    select(AppleAccount).where(
                        and_(
                            AppleAccount.user_id == user_id,
                            AppleAccount.apple_id == account_data["apple_id"]
                        )
                    )
                )
                if result.scalar_one_or_none():
                    raise ValueError("该 Apple ID 已存在")

                # 加密密码
                encrypted_password = encrypt_sensitive_data(account_data["password"])

                # 加密密保（如果有）
                encrypted_questions = None
                if "security_questions" in account_data and account_data["security_questions"]:
                    import json
                    encrypted_questions = json.loads(
                        encrypt_sensitive_data(json.dumps(account_data["security_questions"]))
                    )

                # 创建账号
                check_interval = account_data.get("check_interval", 3600)
                next_check_at = datetime.utcnow() + timedelta(seconds=check_interval)

                account = AppleAccount(
                    user_id=user_id,
                    apple_id=account_data["apple_id"],
                    current_password=encrypted_password,
                    security_questions=encrypted_questions,
                    tags=account_data.get("tags"),
                    category=account_data.get("category"),
                    note=account_data.get("note"),
                    auto_unlock=account_data.get("auto_unlock", True),
                    auto_disable_2fa=account_data.get("auto_disable_2fa", False),
                    auto_change_password=account_data.get("auto_change_password", False),
                    auto_remove_devices=account_data.get("auto_remove_devices", False),
                    check_interval=check_interval,
                    next_check_at=next_check_at,
                    status="normal",
                )
                db.add(account)
                await db.flush()

                # 创建密码历史
                password_history = PasswordHistory(
                    account_id=account.id,
                    password_hash=get_password_hash(account_data["password"]),
                    changed_by="import",
                )
                db.add(password_history)

                success_count += 1

            except Exception as e:
                failed_count += 1
                errors.append({
                    "index": idx,
                    "apple_id": account_data.get("apple_id", "未知"),
                    "error": str(e),
                })

        # 更新用户权限计数
        permission.accounts_count += success_count

        await db.commit()

        return AppleAccountImportResponse(
            total=len(accounts_data),
            success=success_count,
            failed=failed_count,
            errors=errors,
            message=f"导入完成，成功：{success_count}，失败：{failed_count}"
        )

    @staticmethod
    async def export_accounts(
        db: AsyncSession,
        user_id: int,
        format: str = "csv",
        include_password: bool = False,
    ) -> str:
        """
        批量导出账号

        Args:
            db: 数据库会话
            user_id: 用户ID
            format: 导出格式（csv 或 json）
            include_password: 是否包含密码

        Returns:
            str: 导出的数据
        """
        # 获取所有账号
        result = await db.execute(
            select(AppleAccount)
            .where(AppleAccount.user_id == user_id)
            .order_by(AppleAccount.created_at)
        )
        accounts = result.scalars().all()

        if format == "csv":
            # CSV 格式
            output = io.StringIO()

            if include_password:
                fieldnames = [
                    "apple_id", "password", "status", "lock_status",
                    "two_factor_enabled", "category", "tags", "note",
                    "auto_unlock", "check_interval", "created_at"
                ]
            else:
                fieldnames = [
                    "apple_id", "status", "lock_status", "two_factor_enabled",
                    "category", "tags", "note", "auto_unlock",
                    "check_interval", "created_at"
                ]

            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for account in accounts:
                row = {
                    "apple_id": account.apple_id,
                    "status": account.status,
                    "lock_status": account.lock_status,
                    "two_factor_enabled": account.two_factor_enabled,
                    "category": account.category or "",
                    "tags": ",".join(account.tags) if account.tags else "",
                    "note": account.note or "",
                    "auto_unlock": account.auto_unlock,
                    "check_interval": account.check_interval,
                    "created_at": account.created_at.isoformat(),
                }

                if include_password and account.current_password:
                    row["password"] = decrypt_sensitive_data(account.current_password)

                writer.writerow(row)

            return output.getvalue()

        else:
            # JSON 格式
            import json

            accounts_list = []
            for account in accounts:
                account_dict = {
                    "apple_id": account.apple_id,
                    "status": account.status,
                    "lock_status": account.lock_status,
                    "two_factor_enabled": account.two_factor_enabled,
                    "category": account.category,
                    "tags": account.tags,
                    "note": account.note,
                    "auto_unlock": account.auto_unlock,
                    "check_interval": account.check_interval,
                    "created_at": account.created_at.isoformat(),
                }

                if include_password and account.current_password:
                    account_dict["password"] = decrypt_sensitive_data(account.current_password)

                accounts_list.append(account_dict)

            return json.dumps(accounts_list, ensure_ascii=False, indent=2)

    @staticmethod
    async def get_password_history(
        db: AsyncSession,
        account_id: int,
        user_id: int,
        limit: int = 10,
    ) -> List[PasswordHistory]:
        """
        获取密码历史

        Args:
            db: 数据库会话
            account_id: 账号ID
            user_id: 用户ID
            limit: 返回数量

        Returns:
            List[PasswordHistory]: 密码历史列表
        """
        # 检查账号是否属于用户
        result = await db.execute(
            select(AppleAccount).where(
                and_(
                    AppleAccount.id == account_id,
                    AppleAccount.user_id == user_id
                )
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError("账号不存在")

        # 检查权限
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()

        if not permission or not permission.allow_view_password_history:
            raise ValueError("没有查看密码历史的权限")

        # 获取密码历史
        result = await db.execute(
            select(PasswordHistory)
            .where(PasswordHistory.account_id == account_id)
            .order_by(desc(PasswordHistory.created_at))
            .limit(limit)
        )
        history = result.scalars().all()

        return list(history)

    @staticmethod
    async def update_password(
        db: AsyncSession,
        account_id: int,
        new_password: str,
        changed_by: str = "manual",
    ) -> bool:
        """
        更新账号密码（内部使用，如自动修改密码任务）

        Args:
            db: 数据库会话
            account_id: 账号ID
            new_password: 新密码
            changed_by: 修改来源（manual, auto, system）

        Returns:
            bool: 是否成功
        """
        # 获取账号
        result = await db.execute(
            select(AppleAccount).where(AppleAccount.id == account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            return False

        # 加密并更新密码
        encrypted_password = encrypt_sensitive_data(new_password)
        account.current_password = encrypted_password
        account.updated_at = datetime.utcnow()

        # 记录密码历史
        password_history = PasswordHistory(
            account_id=account.id,
            password_hash=get_password_hash(new_password),
            changed_by=changed_by,
        )
        db.add(password_history)

        await db.commit()
        return True

    @staticmethod
    async def update_account_status(
        db: AsyncSession,
        account_id: int,
        status: str,
        lock_status: Optional[bool] = None,
        error_msg: Optional[str] = None,
    ) -> bool:
        """
        更新账号状态（内部使用，如检测任务）

        Args:
            db: 数据库会话
            account_id: 账号ID
            status: 状态
            lock_status: 锁定状态
            error_msg: 错误信息

        Returns:
            bool: 是否成功
        """
        result = await db.execute(
            select(AppleAccount).where(AppleAccount.id == account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            return False

        account.status = status

        if lock_status is not None:
            account.lock_status = lock_status

        if error_msg:
            account.last_error = error_msg
            account.error_count += 1
        else:
            # 成功时清空错误
            account.last_error = None
            account.error_count = 0

        account.last_checked_at = datetime.utcnow()
        account.next_check_at = datetime.utcnow() + timedelta(seconds=account.check_interval)
        account.updated_at = datetime.utcnow()

        await db.commit()
        return True
