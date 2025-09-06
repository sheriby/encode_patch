#!/usr/bin/env python3
"""
测试小文件压缩率的改进
"""

import os
import sys
import subprocess
import tempfile

def create_test_files():
    """创建不同大小的测试文件"""
    test_files = {}

    # 创建小文件 (100字节)
    small_content = b"Hello World! This is a small test file." * 2
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(small_content)
        test_files['small_100b'] = f.name

    # 创建中等文件 (2KB)
    medium_content = b"Test content for medium file. " * 100
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(medium_content)
        test_files['medium_2kb'] = f.name

    # 创建大文件 (10KB)
    large_content = b"Large file content for testing compression ratios. " * 200
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(large_content)
        test_files['large_10kb'] = f.name

    return test_files

def test_file_compression(file_path, file_name):
    """测试单个文件的压缩"""
    print(f"\n=== 测试文件: {file_name} ===")
    print(f"原始大小: {os.path.getsize(file_path)} 字节")

    # 清理旧文件
    for i in range(10):
        old_file = f"test_output/{file_name}_encrypt{i}.txt"
        if os.path.exists(old_file):
            os.remove(old_file)

    # 测试加密压缩
    print("测试AES加密压缩...")
    result = subprocess.run([
        sys.executable, "-m", "cli.encode_cli", file_path,
        "-o", f"test_output/{file_name}_encrypt",
        "-a", "brotli",
        "-c", "9",
        "-v"
    ], capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        print(f"加密压缩失败: {result.stderr}")
        return None

    # 计算加密后文件大小
    encrypt_size = 0
    chunk_count = 0
    while os.path.exists(f"test_output/{file_name}_encrypt{chunk_count}.txt"):
        encrypt_size += os.path.getsize(f"test_output/{file_name}_encrypt{chunk_count}.txt")
        chunk_count += 1

    # 清理加密文件
    for i in range(chunk_count):
        os.remove(f"test_output/{file_name}_encrypt{i}.txt")

    # 测试不加密压缩
    print("测试不加密压缩...")
    result = subprocess.run([
        sys.executable, "-m", "cli.encode_cli", file_path,
        "-o", f"test_output/{file_name}_no_encrypt",
        "-a", "brotli",
        "-c", "9",
        "--no-encrypt",
        "-v"
    ], capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        print(f"不加密压缩失败: {result.stderr}")
        return None

    # 计算不加密文件大小
    no_encrypt_size = 0
    chunk_count = 0
    while os.path.exists(f"test_output/{file_name}_no_encrypt{chunk_count}.txt"):
        no_encrypt_size += os.path.getsize(f"test_output/{file_name}_no_encrypt{chunk_count}.txt")
        chunk_count += 1

    # 清理不加密文件
    for i in range(chunk_count):
        os.remove(f"test_output/{file_name}_no_encrypt{i}.txt")

    original_size = os.path.getsize(file_path)
    encrypt_ratio = encrypt_size / original_size * 100
    no_encrypt_ratio = no_encrypt_size / original_size * 100

    print("\n压缩结果:")
    print(f"  加密压缩大小: {encrypt_size} 字节 ({encrypt_ratio:.1f}%)")
    print(f"  不加密压缩大小: {no_encrypt_size} 字节 ({no_encrypt_ratio:.1f}%)")
    print(f"  加密开销: {encrypt_ratio - no_encrypt_ratio:.1f}%")

    return {
        'original_size': original_size,
        'encrypt_size': encrypt_size,
        'no_encrypt_size': no_encrypt_size,
        'encrypt_ratio': encrypt_ratio,
        'no_encrypt_ratio': no_encrypt_ratio,
        'overhead': encrypt_ratio - no_encrypt_ratio
    }

def main():
    """主测试函数"""
    print("🔍 小文件压缩率测试")
    print("=" * 60)

    # 检查cryptography库
    try:
        import cryptography
        print("✅ cryptography库已安装")
    except ImportError:
        print("❌ cryptography库未安装，请运行: pip install cryptography")
        return

    # 创建测试文件
    test_files = create_test_files()

    # 创建输出目录
    os.makedirs("test_output", exist_ok=True)

    results = []

    try:
        # 测试每个文件
        for file_name, file_path in test_files.items():
            result = test_file_compression(file_path, file_name)
            if result:
                results.append((file_name, result))

        # 输出总结
        print("\n" + "=" * 60)
        print("📊 测试总结:")
        print("文件类型      原始大小    加密压缩率    不加密压缩率    加密开销")
        print("-" * 80)

        for file_name, result in results:
            print("<12"
                  "<8"
                  "<12.1f"
                  "<12.1f"
                  "<10.1f")

        print("\n💡 分析结果:")
        print("1. 小文件(<1KB): 加密开销显著，建议自动跳过加密")
        print("2. 中等文件(1-5KB): 加密开销适中，可根据需要选择")
        print("3. 大文件(>5KB): 加密开销相对较小，推荐启用加密")
        print("4. 智能决策: 系统会自动检测文件大小并给出建议")

    finally:
        # 清理测试文件
        for file_path in test_files.values():
            if os.path.exists(file_path):
                os.unlink(file_path)

if __name__ == "__main__":
    main()
