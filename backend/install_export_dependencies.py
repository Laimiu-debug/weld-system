"""
安装文档导出所需的依赖
"""
import subprocess
import sys

def install_dependencies():
    """安装python-docx, weasyprint和beautifulsoup4"""
    packages = [
        'python-docx',
        'weasyprint',
        'beautifulsoup4',
        'lxml'  # BeautifulSoup的解析器
    ]
    
    print("正在安装文档导出依赖...")
    print(f"包列表: {', '.join(packages)}")
    
    for package in packages:
        print(f"\n安装 {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"✗ {package} 安装失败: {e}")
            return False
    
    print("\n所有依赖安装完成！")
    return True

if __name__ == "__main__":
    success = install_dependencies()
    sys.exit(0 if success else 1)

