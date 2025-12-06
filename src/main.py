"""
FastAPI 服务器 - RESTful API
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os
from typing import Optional
from pathlib import Path

from schemas.models import ChatRequest, ChatResponse, Message
from utils.redis_manager import RedisManager
from tools.tool_manager import ToolManager
from core.agent import MultiTaskAgent
from core.customer_service_agent import CustomerServiceAgent
from api.customer_service_api import router as customer_service_router  # 客服中心API
from agents.agent_router import router as agent_router  # 多Agent客服系统路由

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
redis_manager: Optional[RedisManager] = None
tool_manager: Optional[ToolManager] = None
agent: Optional[MultiTaskAgent] = None
cs_agent: Optional[CustomerServiceAgent] = None

# 前端静态文件路径
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global redis_manager, tool_manager, agent

    # 启动
    logger.info("🚀 启动应用...")
    redis_manager = RedisManager()
    tool_manager = ToolManager()
    agent = MultiTaskAgent(tool_manager)
    cs_agent = CustomerServiceAgent()

    logger.info("✅ 内存存储初始化成功")
    logger.info("✅ 智能客服中心Agent初始化成功")

    # 检查前端文件
    if FRONTEND_DIR.exists():
        logger.info(f"✅ 前端文件已加载: {FRONTEND_DIR}")
    else:
        logger.warning(f"⚠️ 前端文件未找到: {FRONTEND_DIR}")
        logger.warning("   请运行: cd frontend && npm install && npm run build")

    yield

    # 清理
    logger.info("🛑 应用关闭中...")


# 创建 FastAPI 应用
app = FastAPI(
    title="多任务AI问答助手",
    description="支持天气、新闻、搜索等多任务的AI问答系统",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(customer_service_router)
app.include_router(agent_router)


# ==================== API 端点 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "redis": redis_manager.health_check() if redis_manager else False,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    单次问答接口

    示例:
    ```json
    {
        "query": "北京今天天气如何?",
        "session_id": "optional-session-id"
    }
    ```
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent 未初始化")

    if not request.query:
        raise HTTPException(status_code=400, detail="Query 不能为空")

    # 获取或创建会话（不再报错，自动创建）
    session_id, session = redis_manager.get_or_create_session(request.session_id)

    try:
        # 处理查询
        result = await agent.process_query(request.query)

        # 保存会话
        user_msg = Message(role="user", content=request.query)
        session.messages.append(user_msg)

        assistant_msg = Message(
            role="assistant",
            content=result["response"],
            tool_calls=result["tool_calls"]
        )
        session.messages.append(assistant_msg)
        redis_manager.save_session(session)

        return ChatResponse(
            session_id=session_id,
            response=result["response"],
            tool_calls=result["tool_calls"],
            task_type=result["task_type"]
        )

    except Exception as e:
        logger.error(f"处理查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.post("/api/customer-service/chat")
async def customer_service_chat(
    query: str,
    session_id: Optional[str] = None,
    channel: str = "web"
):
    """
    智能客服专用对话接口

    Args:
        query: 客户查询内容
        session_id: 会话ID（可选）
        channel: 接入渠道

    Returns:
        客服回复结果
    """
    try:
        global cs_agent
        if cs_agent is None:
            cs_agent = CustomerServiceAgent()

        logger.info(f"客服对话请求: {query[:50]}...")

        # 处理查询
        result = await cs_agent.process_customer_service_query(query)

        # 如果有会话ID，保存对话历史
        if session_id and redis_manager:
            try:
                # 保存客户消息
                redis_manager.cache_result(
                    f"cs_session:{session_id}:customer",
                    {"query": query, "timestamp": datetime.now().isoformat()},
                    ttl=86400  # 24小时
                )

                # 保存客服回复
                redis_manager.cache_result(
                    f"cs_session:{session_id}:agent",
                    {"response": result["response"], "timestamp": datetime.now().isoformat()},
                    ttl=86400
                )
            except Exception as e:
                logger.warning(f"保存会话历史失败: {e}")

        # 添加会话信息
        result["session_id"] = session_id
        result["channel"] = channel

        return result

    except Exception as e:
        logger.error(f"客服对话处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"客服对话处理失败: {str(e)}")


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """获取会话历史"""
    session = redis_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "last_updated": session.last_updated.isoformat(),
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages
        ]
    }


@app.post("/api/session/{session_id}/start")
async def start_session(session_id: str = None):
    """创建新会话"""
    new_session_id = redis_manager.create_session()
    return {
        "session_id": new_session_id,
        "created_at": __import__("datetime").datetime.now().isoformat()
    }


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    session = redis_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    redis_manager.delete_session(session_id)

    return {"message": "会话已删除", "session_id": session_id}


@app.get("/api/tools")
async def get_available_tools():
    """获取可用工具列表"""
    return {
        "tools": tool_manager.get_tool_descriptions()
    }


@app.post("/api/cache/clear")
async def clear_cache(background_tasks: BackgroundTasks):
    """清空缓存"""
    def clear_in_background():
        redis_manager.clear_cache()
        logger.info("缓存已清空")

    background_tasks.add_task(clear_in_background)
    return {"message": "清空缓存任务已提交"}


# ==================== 前端静态文件服务 ====================

@app.get("/")
async def serve_index():
    """服务前端首页"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "多任务AI问答助手",
        "version": "0.1.0",
        "docs": "/docs",
        "frontend": "请先构建前端: cd frontend && npm install && npm run build"
    }


# 挂载静态资源目录（仅当目录存在时）
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """服务前端单页应用 - 处理所有其他路由"""
    # 尝试提供静态文件
    file_path = FRONTEND_DIR / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)

    # 对于 SPA，返回 index.html
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Not Found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
