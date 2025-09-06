#!/usr/bin/env python3
"""
测试AES加密功能的完整性
"""

import os
import sys
import subprocess
import hashlib

def calculate_md5(file_path):
    """计算文件的MD5哈希值"""
    if not os.path.exists(file_path):
        return None

    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def test_encryption_workflow():
    """测试完整的加密工作流程"""
    print("=== AES加密功能测试 ===\n")

    test_file = "test.patch"
    if not os.path.exists(test_file):
        print(f"错误: 测试文件 '{test_file}' 不存在")
        return False

    # 创建输出目录
    os.makedirs("test_output", exist_ok=True)

    # 清理旧文件
    for i in range(10):
        old_file = f"test_output/encrypt_test{i}.txt"
        if os.path.exists(old_file):
            os.remove(old_file)
    restore_file = "test_output/decrypt_restore.patch"
    if os.path.exists(restore_file):
        os.remove(restore_file)

    print("1. 测试AES加密编码...")
    # 使用默认加密
    encode_result = subprocess.run([
        sys.executable, "-m", "cli.encode_cli", test_file,
        "-o", "test_output/encrypt_test",
        "-a", "brotli",
        "-c", "9"
    ], capture_output=True, text=True, timeout=120)

    if encode_result.returncode != 0:
        print("加密编码失败:")
        print(encode_result.stderr)
        return False

    print("✅ 加密编码成功")

    print("\n2. 测试AES解密解码...")
    # 使用默认解密
    decode_result = subprocess.run([
        sys.executable, "-m", "cli.decode_cli", restore_file,
        "-i", "test_output/encrypt_test",
        "-a", "brotli"
    ], capture_output=True, text=True, timeout=120)

    if decode_result.returncode != 0:
        print("解密解码失败:")
        print(decode_result.stderr)
        return False

    print("✅ 解密解码成功")

    print("\n3. 验证文件完整性...")
    if os.path.exists(restore_file):
        original_md5 = calculate_md5(test_file)
        restored_md5 = calculate_md5(restore_file)

        if original_md5 == restored_md5:
            print("✅ MD5验证通过 - 文件完整性保持")
            print(f"原始MD5: {original_md5}")
            print(f"解密MD5: {restored_md5}")
            return True
        else:
            print("❌ MD5验证失败 - 文件损坏")
            print(f"原始MD5: {original_md5}")
            print(f"解密MD5: {restored_md5}")
            return False
    else:
        print("❌ 解密文件未生成")
        return False

def test_custom_key():
    """测试自定义密钥"""
    print("\n=== 自定义密钥测试 ===\n")

    test_file = "test.patch"
    if not os.path.exists(test_file):
        print("跳过自定义密钥测试")
        return True

    # 清理旧文件
    for i in range(10):
        old_file = f"test_output/custom_key{i}.txt"
        if os.path.exists(old_file):
            os.remove(old_file)
    restore_file = "test_output/custom_key_restore.patch"
    if os.path.exists(restore_file):
        os.remove(restore_file)

    custom_key = "my_custom_secret_key_123"

    print(f"使用自定义密钥: {custom_key}")

    # 加密
    encode_result = subprocess.run([
        sys.executable, "-m", "cli.encode_cli", test_file,
        "-o", "test_output/custom_key",
        "-k", custom_key,
        "-a", "zlib",
        "-c", "6"
    ], capture_output=True, text=True, timeout=120)

    if encode_result.returncode != 0:
        print("自定义密钥加密失败:")
        print(encode_result.stderr)
        return False

    # 解密
    decode_result = subprocess.run([
        sys.executable, "-m", "cli.decode_cli", restore_file,
        "-i", "test_output/custom_key",
        "-k", custom_key,
        "-a", "zlib"
    ], capture_output=True, text=True, timeout=120)

    if decode_result.returncode != 0:
        print("自定义密钥解密失败:")
        print(decode_result.stderr)
        return False

    # 验证
    if os.path.exists(restore_file):
        original_md5 = calculate_md5(test_file)
        restored_md5 = calculate_md5(restore_file)

        if original_md5 == restored_md5:
            print("✅ 自定义密钥测试通过")
            return True
        else:
            print("❌ 自定义密钥测试失败")
            return False

    return False

def test_no_encryption():
    """测试禁用加密功能"""
    print("\n=== 禁用加密测试 ===\n")

    test_file = "test.patch"
    if not os.path.exists(test_file):
        print("跳过禁用加密测试")
        return True

    # 清理旧文件
    for i in range(10):
        old_file = f"test_output/no_encrypt{i}.txt"
        if os.path.exists(old_file):
            os.remove(old_file)
    restore_file = "test_output/no_encrypt_restore.patch"
    if os.path.exists(restore_file):
        os.remove(restore_file)

    print("禁用AES加密进行测试...")

    # 编码（禁用加密）
    encode_result = subprocess.run([
        sys.executable, "-m", "cli.encode_cli", test_file,
        "-o", "test_output/no_encrypt",
        "--no-encrypt",
        "-a", "lzma",
        "-c", "6"
    ], capture_output=True, text=True, timeout=120)

    if encode_result.returncode != 0:
        print("禁用加密编码失败:")
        print(encode_result.stderr)
        return False

    # 解码（禁用解密）
    decode_result = subprocess.run([
        sys.executable, "-m", "cli.decode_cli", restore_file,
        "-i", "test_output/no_encrypt",
        "--no-decrypt",
        "-a", "lzma"
    ], capture_output=True, text=True, timeout=120)

    if decode_result.returncode != 0:
        print("禁用加密解码失败:")
        print(decode_result.stderr)
        return False

    # 验证
    if os.path.exists(restore_file):
        original_md5 = calculate_md5(test_file)
        restored_md5 = calculate_md5(restore_file)

        if original_md5 == restored_md5:
            print("✅ 禁用加密测试通过")
            return True
        else:
            print("❌ 禁用加密测试失败")
            return False

    return False

def main():
    """主测试函数"""
    print("🔐 文件压缩编码工具 - AES加密功能测试")
    print("=" * 60)

    # 检查cryptography库
    try:
        import cryptography
        print("✅ cryptography库已安装")
    except ImportError:
        print("❌ cryptography库未安装，请运行: pip install cryptography")
        return

    tests = [
        ("默认加密解密", test_encryption_workflow),
        ("自定义密钥", test_custom_key),
        ("禁用加密", test_no_encryption)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🔍 执行测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ 通过" if success else "❌ 失败"
            print(f"测试结果: {status}")
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("📊 测试总结:")

    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有AES加密测试通过!")
        print("🔒 加密功能工作正常，数据安全性有保障")
    else:
        print("⚠️  部分测试失败，请检查配置")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
