#!/usr/bin/env python3
"""
macOS Python SSL 证书修复和依赖安装脚本
解决: SSLError(SSLCertVerificationError) 问题
"""

import subprocess
import sys
import os
import ssl
import certifi

def run_command(cmd, description=""):
    """运行命令并显示结果"""
    if description:
        print(f"\n{description}...")
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    print("\n" + "="*70)
    print("🔧 macOS Python SSL 证书修复和依赖安装")
    print("="*70)

    print(f"\n📍 Python 版本: {sys.version}")
    print(f"📍 Python 路径: {sys.executable}")
    print(f"📍 certifi 位置: {certifi.where()}")

    # 步骤 1: 为 macOS 安装 Python 证书
    print("\n" + "="*70)
    print("步骤 1️⃣: 为 macOS 安装 Python 证书")
    print("="*70)

    # 查找 Python 版本
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    install_commands = [
        # macOS Homebrew 安装的 Python
        f"/usr/local/opt/python@{python_version}/bin/python{python_version} -m pip install --upgrade certifi",
        # Python.org 安装的 Python
        f"/Library/Frameworks/Python.framework/Versions/{python_version}/bin/python{python_version} -m pip install --upgrade certifi",
        # Anaconda
        "conda install --yes certifi",
        # 通用命令
        "pip install --upgrade certifi",
    ]

    print("\n尝试升级 certifi...")
    for cmd in install_commands:
        if run_command(cmd):
            print(f"✓ 成功: {cmd}")
            break

    # 步骤 2: 安装 Python SSL 证书（仅 Python.org 和 Homebrew）
    print("\n" + "="*70)
    print("步骤 2️⃣: 安装 Python SSL 根证书")
    print("="*70)

    cert_install_commands = [
        # Python.org 安装的 Python
        f"/Applications/Python\\ {python_version}/Install\\ Certificates.command",
        # Homebrew
        f"brew install python-certifi@{python_version}",
        # 直接运行 certifi 配置
        "python -c \"import certifi; print(certifi.where())\"",
    ]

    for cmd in cert_install_commands:
        print(f"\n尝试: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ 成功执行")
            if result.stdout:
                print(f"  输出: {result.stdout.strip()}")
            break

    # 步骤 3: 配置 pip
    print("\n" + "="*70)
    print("步骤 3️⃣: 配置 pip")
    print("="*70)

    pip_config = """[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host = mirrors.aliyun.com
               mirrors.tsinghua.edu.cn
               files.pythonhosted.org
               pypi.python.org
"""

    # 创建 pip 配置目录
    config_dir = os.path.expanduser("~/.pip")
    os.makedirs(config_dir, exist_ok=True)

    config_file = os.path.join(config_dir, "pip.conf")

    print(f"\n配置文件位置: {config_file}")
    print("\n配置内容:")
    print(pip_config)

    with open(config_file, "w") as f:
        f.write(pip_config)

    print(f"✓ 配置已保存到 {config_file}")

    # 步骤 4: 升级 pip
    print("\n" + "="*70)
    print("步骤 4️⃣: 升级 pip 本身")
    print("="*70)

    upgrade_commands = [
        "pip install --upgrade pip --no-cert --trusted-host mirrors.aliyun.com",
        "pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/",
        "python -m pip install --upgrade pip",
    ]

    for cmd in upgrade_commands:
        if run_command(cmd):
            print(f"✓ pip 升级成功")
            break

    # 步骤 5: 安装项目依赖
    print("\n" + "="*70)
    print("步骤 5️⃣: 安装项目依赖")
    print("="*70)

    # 获取 requirements.txt 位置
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_file = os.path.join(script_dir, "requirements.txt")

    if not os.path.exists(requirements_file):
        print(f"❌ 找不到 {requirements_file}")
        return False

    print(f"\n安装文件: {requirements_file}")

    install_commands = [
        f"pip install -r {requirements_file} -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com",
        f"pip install -r {requirements_file} --no-cert --trusted-host mirrors.aliyun.com",
        f"pip install -r {requirements_file}",
    ]

    for i, cmd in enumerate(install_commands, 1):
        print(f"\n方案 {i}/{ len(install_commands)}: 尝试安装...")
        if run_command(cmd, f"运行: {cmd}"):
            print(f"\n✅ 方案 {i} 成功！依赖已安装")
            return True
        print(f"❌ 方案 {i} 失败，尝试下一个...")

    return False

if __name__ == "__main__":
    success = main()

    print("\n" + "="*70)
    if success:
        print("✅ 安装完成！")
        print("\n下一步:")
        print("  1. python verify.py")
        print("  2. cd src && python -m uvicorn main:app --reload")
    else:
        print("❌ 自动安装失败")
        print("\n请手动执行:")
        print("  pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt")
        print("\n或使用 HTTP (不安全):")
        print("  pip install -i http://mirrors.aliyun.com/pypi/simple -r requirements.txt")
    print("="*70 + "\n")

    sys.exit(0 if success else 1)
