# 清华 PyPI 镜像兼容配置

# 如果使用清华镜像报错，请按照以下步骤操作：

## 方法 1: 使用官方 PyPI 安装（推荐）
```bash
pip install -i https://pypi.org/simple -r requirements.txt
```

## 方法 2: 配置 pip 永久使用官方源
编辑 `~/.pip/pip.conf` 或 `%APPDATA%\pip\pip.ini`：

```ini
[global]
index-url = https://pypi.org/simple
```

然后运行：
```bash
pip install -r requirements.txt
```

## 方法 3: 使用其他国内镜像

### 阿里云镜像
```bash
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```

### 腾讯云镜像
```bash
pip install -i http://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt
```

### 网易镜像
```bash
pip install -i http://mirrors.163.com/pypi/simple -r requirements.txt
```

## 问题排查

**问题**: `Could not find a version that satisfies the requirement...`

**原因**: 清华 PyPI 镜像不是完整镜像，某些新包可能缺失

**解决方案**:
1. 使用官方 PyPI 源（推荐）
2. 或切换到其他国内镜像
3. 如果都失败，检查网络连接

## 验证安装

```bash
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python -c "import langchain; print(f'LangChain version: {langchain.__version__}')"
python -c "import openai; print(f'OpenAI {openai.__version__}')"
```

已安装包版本：
- FastAPI: 0.124.0
- uvicorn: 0.38.0
- LangChain: 1.1.2
- OpenAI: 2.9.0
- Redis: 7.1.0
- Pydantic: 2.10.3+
