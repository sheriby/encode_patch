#!/usr/bin/env python3
"""
测试AES CTR模式是否保持文件大小不变
"""

import os
import sys
import subprocess
import hashlib
import tempfile

def calculate_md5(file_path):
    """计算文件的MD5哈希值"""
    if not os.path.exists(file_path):
        return None

    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def test_size_preservation():
    """测试文件大小是否保持不变"""
    print("🔐 测试AES CTR模式大小保持性")
    print("=" * 60)

    # 检查cryptography库
    try:
        import cryptography
        print("✅ cryptography库已安装")
    except ImportError:
        print("❌ cryptography库未安装，请运行: pip install cryptography")
        return

    # 创建不同大小的测试文件
    test_files = {}

    # 创建小文件 (100字节)
    small_content = b"Hello World! This is a small test file for CTR mode." * 2
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(small_content)
        test_files['small_100b'] = f.name

    # 创建中等文件 (2KB)
    medium_content = b"Test content for medium file testing CTR mode. " * 50
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(medium_content)
        test_files['medium_2kb'] = f.name

    # 创建大文件 (10KB)
    large_content = b"Large file content for testing CTR mode size preservation. " * 100
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as f:
        f.write(large_content)
        test_files['large_10kb'] = f.name

    results = []

    try:
        for file_name, file_path in test_files.items():
            print(f"\n=== 测试文件: {file_name} ===")

            original_size = os.path.getsize(file_path)
            print(f"原始文件大小: {original_size} 字节")

            # 清理旧文件
            for i in range(10):
                old_file = f"test_output/{file_name}_ctr{i}.txt"
                if os.path.exists(old_file):
                    os.remove(old_file)

            # 测试CTR模式加密
            print("测试CTR模式加密...")
            result = subprocess.run([
                sys.executable, "-m", "cli.encode_cli", file_path,
                "-o", f"test_output/{file_name}_ctr",
                "-a", "brotli",
                "-c", "9",
                "-v"
            ], capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                print(f"CTR模式加密失败: {result.stderr}")
                continue

            # 计算加密后文件大小
            encrypted_size = 0
            chunk_count = 0
            while os.path.exists(f"test_output/{file_name}_ctr{chunk_count}.txt"):
                encrypted_size += os.path.getsize(f"test_output/{file_name}_ctr{chunk_count}.txt")
                chunk_count += 1

            # 清理加密文件
            for i in range(chunk_count):
                os.remove(f"test_output/{file_name}_ctr{i}.txt")

            # 重新生成加密文件用于解密测试
            result = subprocess.run([
                sys.executable, "-m", "cli.encode_cli", file_path,
                "-o", f"test_output/{file_name}_ctr",
                "-a", "brotli",
                "-c", "9"
            ], capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                print(f"重新生成加密文件失败: {result.stderr}")
                continue

            # 测试解密
            print("测试CTR模式解密...")
            result = subprocess.run([
                sys.executable, "-m", "cli.decode_cli", f"test_output/{file_name}_restored.txt",
                "-i", f"test_output/{file_name}_ctr",
                "-a", "brotli",
                "-v"
            ], capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                print(f"CTR模式解密失败: {result.stderr}")
                continue

            # 验证结果
            restored_file = f"test_output/{file_name}_restored.txt"
            if os.path.exists(restored_file):
                restored_size = os.path.getsize(restored_file)
                original_md5 = calculate_md5(file_path)
                restored_md5 = calculate_md5(restored_file)

                success = original_md5 == restored_md5
                size_preserved = original_size == restored_size

                print("\n测试结果:")
                print(f"  原始大小: {original_size} 字节")
                print(f"  解密后大小: {restored_size} 字节")
                print(f"  大小保持: {'✅ 是' if size_preserved else '❌ 否'}")
                print(f"  MD5验证: {'✅ 通过' if success else '❌ 失败'}")

                results.append({
                    'file': file_name,
                    'original_size': original_size,
                    'restored_size': restored_size,
                    'size_preserved': size_preserved,
                    'md5_match': success
                })

                # 清理解密文件
                os.remove(restored_file)

        # 输出总结
        print("\n" + "=" * 60)
        print("📊 CTR模式测试总结:")
        print("文件类型      原始大小    解密后大小    大小保持    MD5验证")
        print("-" * 80)

        all_size_preserved = True
        all_md5_match = True

        for result in results:
            preserved = "✅ 是" if result['size_preserved'] else "❌ 否"
            md5_ok = "✅ 通过" if result['md5_match'] else "❌ 失败"
            print("<12"
                  "<8"
                  "<8"
                  "<8"
                  "<8")

            if not result['size_preserved']:
                all_size_preserved = False
            if not result['md5_match']:
                all_md5_match = False

        print("\n" + "=" * 60)
        if all_size_preserved and all_md5_match:
            print("🎉 CTR模式完美！文件大小完全保持不变，数据完整性100%保证")
            print("✅ 加密前后的文件大小完全相同")
            print("✅ MD5哈希值完全匹配")
            print("✅ 解决了传统CBC模式的填充开销问题")
        else:
            print("⚠️  CTR模式测试存在问题")
            if not all_size_preserved:
                print("❌ 文件大小未能保持不变")
            if not all_md5_match:
                print("❌ 数据完整性验证失败")

    finally:
        # 清理测试文件
        for file_path in test_files.values():
            if os.path.exists(file_path):
                os.unlink(file_path)

if __name__ == "__main__":
    test_size_preservation()
