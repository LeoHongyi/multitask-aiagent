"""
内存缓存与会话管理（无 Redis 依赖）
"""
import json
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from schemas.models import Session, Message


class MemoryManager:
    """内存会话管理器"""

    def __init__(self):
        """初始化内存存储"""
        self._sessions: Dict[str, str] = {}  # session_id -> session_json
        self._cache: Dict[str, str] = {}  # cache_key -> value
        print("✓ 内存存储初始化成功")

    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id)
        self._sessions[session_id] = session.model_dump_json()
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        data = self._sessions.get(session_id)
        if data:
            return Session(**json.loads(data))
        return None

    def get_or_create_session(self, session_id: str = None) -> tuple[str, Session]:
        """获取或创建会话"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session_id, session

        # 创建新会话
        new_session_id = str(uuid.uuid4())
        session = Session(session_id=new_session_id)
        self._sessions[new_session_id] = session.model_dump_json()
        return new_session_id, session

    def save_session(self, session: Session) -> None:
        """保存会话"""
        session.last_updated = datetime.now()
        self._sessions[session.session_id] = session.model_dump_json()

    def delete_session(self, session_id: str) -> None:
        """删除会话"""
        self._sessions.pop(session_id, None)

    def cache_result(self, key: str, value: str, ttl: int = 3600) -> None:
        """缓存结果"""
        self._cache[key] = value

    def get_cache(self, key: str) -> Optional[str]:
        """获取缓存"""
        return self._cache.get(key)

    def clear_cache(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def health_check(self) -> bool:
        """健康检查"""
        return True

    def get_all_sessions(self) -> Dict[str, Any]:
        """获取所有会话（调试用）"""
        return {
            "count": len(self._sessions),
            "session_ids": list(self._sessions.keys())
        }


# 向后兼容的别名
RedisManager = MemoryManager
