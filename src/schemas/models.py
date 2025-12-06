"""
数据模型定义
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskType(str, Enum):
    """任务类型"""
    WEATHER = "weather"
    NEWS = "news"
    SEARCH = "search"
    QA = "qa"
    OTHER = "other"


class ToolCall(BaseModel):
    """工具调用记录"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[str] = None


class Message(BaseModel):
    """对话消息"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_calls: List[ToolCall] = []


class ChatRequest(BaseModel):
    """聊天请求"""
    query: str
    session_id: Optional[str] = None
    context: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    response: str
    tool_calls: List[ToolCall] = []
    task_type: TaskType = TaskType.OTHER
    timestamp: datetime = Field(default_factory=datetime.now)


class Session(BaseModel):
    """会话数据"""
    session_id: str
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}
