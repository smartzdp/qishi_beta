#!/usr/bin/env python3
"""
安全检查脚本 - 确保没有敏感信息被提交到代码仓库
"""

import os
import re
import sys
from pathlib import Path

def check_sensitive_info():
    """检查代码中是否包含敏感信息"""
    print("🔍 开始安全检查...")
    
    # 敏感信息模式
    sensitive_patterns = [
        r'[a-f0-9]{32}\.[a-zA-Z0-9]{20}',  # API密钥格式
        r'api[_-]?key["\']?\s*[:=]\s*["\'][^"\']+["\']',  # API密钥赋值
        r'secret["\']?\s*[:=]\s*["\'][^"\']+["\']',  # 密钥赋值
        r'token["\']?\s*[:=]\s*["\'][^"\']+["\']',  # 令牌赋值
        r'password["\']?\s*[:=]\s*["\'][^"\']+["\']',  # 密码赋值
    ]
    
    # 要检查的文件类型
    file_extensions = ['.py', '.sh', '.md', '.txt', '.json', '.yaml', '.yml']
    
    # 要忽略的目录
    ignore_dirs = {'venv', '__pycache__', '.git', 'node_modules'}
    
    issues = []
    
    for root, dirs, files in os.walk('.'):
        # 过滤忽略的目录
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for i, line in enumerate(content.split('\n'), 1):
                            for pattern in sensitive_patterns:
                                if re.search(pattern, line, re.IGNORECASE):
                                    # 检查是否是示例代码
                                    if not any(keyword in line.lower() for keyword in ['example', 'your-', 'placeholder', 'template']):
                                        issues.append(f"{file_path}:{i} - {line.strip()}")
                except Exception as e:
                    print(f"⚠️  无法读取文件 {file_path}: {e}")
    
    if issues:
        print("❌ 发现潜在敏感信息:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ 安全检查通过，未发现敏感信息")
        return True

def check_gitignore():
    """检查.gitignore文件是否包含必要的忽略规则"""
    print("\n🔍 检查.gitignore文件...")
    
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        print("❌ 缺少.gitignore文件")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    required_patterns = [
        '.env',
        '*.key',
        '*api*key*',
        '*secret*',
        '*token*',
        'venv/',
        '__pycache__/',
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"❌ .gitignore缺少以下模式: {missing_patterns}")
        return False
    else:
        print("✅ .gitignore文件配置正确")
        return True

def main():
    """主函数"""
    print("🛡️  GLM-4-Voice API Demo 安全检查")
    print("=" * 50)
    
    # 切换到项目目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 执行检查
    security_ok = check_sensitive_info()
    gitignore_ok = check_gitignore()
    
    print("\n" + "=" * 50)
    if security_ok and gitignore_ok:
        print("🎉 所有安全检查通过！可以安全提交到GitHub")
        sys.exit(0)
    else:
        print("⚠️  发现问题，请修复后再提交")
        sys.exit(1)

if __name__ == "__main__":
    main()
