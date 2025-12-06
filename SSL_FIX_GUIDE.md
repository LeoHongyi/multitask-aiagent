# SSL 证书验证错误 - 解决方案

## 问题
```
SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]...
```

这通常发生在以下场景：
- 企业网络/代理环境
- macOS 需要安装证书
- 网络连接问题

---

## ✅ 解决方案（按推荐顺序）

### 方案 1: 使用 --trusted-host 参数（推荐快速修复）

```bash
pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

或者针对官方源：

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### 方案 2: 禁用 SSL 验证（快速但不推荐用于生产）

```bash
pip install --index-url https://pypi.org/simple/ --trusted-host pypi.org -r requirements.txt
```

或者：

```bash
pip install -i https://pypi.org/simple/ --cert /dev/null -r requirements.txt
```

### 方案 3: 配置 pip 配置文件（永久解决）

创建或编辑 `~/.pip/pip.conf`（macOS/Linux）或 `%APPDATA%\pip\pip.ini`（Windows）：

```ini
[global]
index-url = https://pypi.org/simple/
trusted-host = pypi.org
               files.pythonhosted.org
```

然后运行：
```bash
pip install -r requirements.txt
```

### 方案 4: 使用国内镜像（推荐用于国内用户）

#### 4a. 阿里云镜像
```bash
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```

#### 4b. 豆瓣镜像
```bash
pip install -i http://pypi.douban.com/simple -r requirements.txt
```

#### 4c. 腾讯云镜像
```bash
pip install -i http://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt
```

### 方案 5: 更新 Python 证书（macOS）

macOS 用户可能需要安装根证书：

```bash
# 对于 Python 3.x
/Applications/Python\ 3.x/Install\ Certificates.command

# 或者使用 Homebrew Python
brew install python-certifi
```

### 方案 6: 使用 HTTP 而不是 HTTPS（最后手段）

```bash
pip install -i http://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```

---

## 🔍 诊断命令

检查你的网络连接：

```bash
# 测试能否访问 pypi
curl -I https://pypi.org/simple/

# 测试 SSL 连接
python -m pip install --upgrade certifi

# 显示当前 pip 配置
pip config list
```

---

## 🎯 推荐步骤

### 对于国内用户（最快）：

```bash
# 使用阿里云镜像
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```

### 对于国外用户：

```bash
# 方案 1（快速）
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# 方案 2（永久）
# 编辑 ~/.pip/pip.conf 添加 trusted-host 配置
pip install -r requirements.txt
```

### 对于 macOS 用户：

```bash
# 先更新证书
/Applications/Python\ 3.13/Install\ Certificates.command

# 然后安装
pip install -r requirements.txt
```

---

## 📝 一键修复脚本

创建 `install.sh`：

```bash
#!/bin/bash

echo "尝试安装依赖..."

# 方案 1: 使用 trusted-host
echo "方案 1: 使用 --trusted-host..."
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ 安装成功！"
    exit 0
fi

# 方案 2: 使用国内镜像
echo "方案 1 失败，尝试方案 2: 使用阿里云镜像..."
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ 安装成功！"
    exit 0
fi

# 方案 3: 禁用 SSL
echo "方案 2 失败，尝试方案 3: 禁用 SSL 验证..."
pip install --index-url https://pypi.org/simple/ \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ 安装成功！"
    exit 0
fi

echo "✗ 所有方案都失败了，请检查网络连接或手动配置"
exit 1
```

运行：
```bash
chmod +x install.sh
./install.sh
```

---

## 🚨 如果以上都不工作

### 1. 检查网络代理

```bash
# 如果在公司网络，可能需要配置代理
pip install -r requirements.txt \
  --proxy [user:passwd@]proxy.server:port
```

### 2. 手动下载安装

访问 https://pypi.org/ 手动下载 wheel 文件，然后：

```bash
pip install /path/to/downloaded/package.whl
```

### 3. 使用代理 PyPI

如果在公司网络，使用企业 PyPI 镜像：

```bash
pip install -i http://your-company-pypi/simple/ -r requirements.txt
```

---

## ✅ 验证安装

安装完成后验证：

```bash
python verify.py
```

或逐个检查：

```bash
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import langchain; print(f'LangChain: {langchain.__version__}')"
python -c "import openai; print(f'OpenAI: {openai.__version__}')"
```

---

## 🔗 参考资源

- [pip SSL 证书问题](https://pip.pypa.io/en/latest/topics/https-certificates/)
- [Python SSL 文档](https://docs.python.org/3/library/ssl.html)
- [PyPI 镜像列表](https://mirrors.aliyun.com/pypi/simple/)

---

## 💡 预防措施

1. **定期更新 pip 和 certifi**：
   ```bash
   pip install --upgrade pip certifi
   ```

2. **使用 requirements.txt 固定版本**：
   ```bash
   pip freeze > requirements.txt
   ```

3. **配置永久的信任主机列表**：
   编辑 `~/.pip/pip.conf`

4. **使用虚拟环境**：
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
