#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Word导出功能中的图片处理
验证base64图片是否能正确导出到Word文档
"""

import io
import base64
from PIL import Image
from docx import Document
from docx.shared import Inches
from bs4 import BeautifulSoup
from app.services.document_export_service import DocumentExportService


def create_test_image_base64(width=200, height=200):
    """创建一个测试图片并转换为base64"""
    # 创建一个简单的PNG图片
    img = Image.new('RGB', (width, height), color='red')
    
    # 转换为base64
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    base64_str = base64.b64encode(img_byte_arr.getvalue()).decode()
    
    return f"data:image/png;base64,{base64_str}"


def test_base64_image_parsing():
    """测试base64图片解析"""
    print("=" * 60)
    print("测试1: Base64图片解析")
    print("=" * 60)
    
    try:
        base64_url = create_test_image_base64()
        print(f"✓ 创建测试图片成功")
        print(f"  Base64长度: {len(base64_url)} 字符")
        
        # 验证格式
        if base64_url.startswith('data:image'):
            print(f"✓ Base64格式正确")
        else:
            print(f"✗ Base64格式错误")
            return False
        
        # 测试分割
        comma_index = base64_url.find(',')
        if comma_index == -1:
            print(f"✗ 找不到逗号分隔符")
            return False
        
        header = base64_url[:comma_index]
        base64_data = base64_url[comma_index + 1:]
        
        print(f"✓ 分割成功")
        print(f"  Header: {header}")
        print(f"  Base64数据长度: {len(base64_data)}")
        
        # 测试解码
        image_data = base64.b64decode(base64_data)
        print(f"✓ Base64解码成功")
        print(f"  图片数据大小: {len(image_data)} 字节")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_html_with_base64_images():
    """测试包含base64图片的HTML解析"""
    print("\n" + "=" * 60)
    print("测试2: HTML中的Base64图片解析")
    print("=" * 60)
    
    try:
        base64_url = create_test_image_base64()
        
        # 创建包含图片的HTML
        html_content = f"""
        <html>
        <body>
            <h1>测试文档</h1>
            <p>这是一个包含图片的测试文档</p>
            <img src="{base64_url}" alt="测试图片" />
            <p>图片下面的文本</p>
        </body>
        </html>
        """
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        imgs = soup.find_all('img')
        
        print(f"✓ HTML解析成功")
        print(f"  找到 {len(imgs)} 张图片")
        
        if len(imgs) > 0:
            img = imgs[0]
            src = img.get('src', '')
            print(f"✓ 图片src获取成功")
            print(f"  src长度: {len(src)} 字符")
            print(f"  src前100字符: {src[:100]}...")
            
            if src.startswith('data:image'):
                print(f"✓ Base64格式正确")
                return True
            else:
                print(f"✗ Base64格式错误")
                return False
        else:
            print(f"✗ 没有找到图片")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_word_export_with_images():
    """测试Word导出中的图片处理"""
    print("\n" + "=" * 60)
    print("测试3: Word导出中的图片处理")
    print("=" * 60)
    
    try:
        base64_url = create_test_image_base64()
        
        # 创建包含图片的HTML
        html_content = f"""
        <html>
        <body>
            <h1>测试WPS文档</h1>
            <p>文档编号: WPS-TEST-001 | 版本: A</p>
            <hr />
            <h2>基本信息</h2>
            <table>
                <tbody>
                    <tr>
                        <td style="width: 30%; font-weight: bold;">字段1</td>
                        <td style="width: 70%;">值1</td>
                    </tr>
                    <tr>
                        <td style="width: 30%; font-weight: bold;">字段2</td>
                        <td style="width: 70%;">值2</td>
                    </tr>
                </tbody>
            </table>
            <h2>图片示例</h2>
            <img src="{base64_url}" alt="测试图片" />
            <p>图片下面的文本</p>
        </body>
        </html>
        """
        
        # 创建Word文档
        doc = Document()
        section = doc.sections[0]
        section.page_height = Inches(11.69)
        section.page_width = Inches(8.27)
        
        # 使用导出服务处理HTML
        service = DocumentExportService(None)
        service._html_to_word(doc, html_content)
        
        # 保存文档
        output_file = 'test_word_export_with_images.docx'
        doc.save(output_file)
        
        print(f"✓ Word文档生成成功")
        print(f"  输出文件: {output_file}")
        
        import os
        file_size = os.path.getsize(output_file)
        print(f"  文件大小: {file_size} 字节")
        
        # 清理测试文件
        os.remove(output_file)
        print(f"✓ 测试文件已清理")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Word导出图片处理测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("Base64图片解析", test_base64_image_parsing()))
    results.append(("HTML图片解析", test_html_with_base64_images()))
    results.append(("Word导出图片", test_word_export_with_images()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print(f"\n✗ 有 {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    exit(main())

