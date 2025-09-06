#!/usr/bin/env python3
"""
测试三种压缩算法的性能对比
"""

import os
import sys
import subprocess
import hashlib
import time

def calculate_md5(file_path):
    """计算文件的MD5哈希值"""
    if not os.path.exists(file_path):
        return None

    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def test_single_algorithm(algorithm, test_file):
    """测试单个压缩算法"""
    print(f"\n=== 测试 {algorithm.upper()} 算法 ===")

    output_base = f"test_output/compress_{algorithm}"
    restored_file = f"test_output/restore_{algorithm}.patch"

    # 清理旧文件
    for i in range(10):
        old_file = f"{output_base}{i}.txt"
        if os.path.exists(old_file):
            os.remove(old_file)
    if os.path.exists(restored_file):
        os.remove(restored_file)

    start_time = time.time()
    original_size = os.path.getsize(test_file)

    print(f"开始编码测试...")
    # 编码测试
    encode_result = subprocess.run([
        sys.executable, "-m", "cli.encode_cli", test_file,
        # "--no-encrypt",
        "-a", algorithm,
        "-o", output_base,
        "-c", "9",
        "-s", "3000"
    ], capture_output=True, text=True, timeout=120)

    if encode_result.returncode != 0:
        print(f"编码失败: {encode_result.stderr}")
        return None

    # 计算压缩文件大小
    chunk_count = 0
    total_compressed_size = 0
    while os.path.exists(f"{output_base}{chunk_count}.txt"):
        file_size = os.path.getsize(f"{output_base}{chunk_count}.txt")
        total_compressed_size += file_size
        chunk_count += 1

    encode_time = time.time() - start_time

    print(f"编码完成 - 用时: {encode_time:.2f}秒")
    print(f"生成分块文件: {chunk_count} 个")
    print(f"压缩后总大小: {total_compressed_size} 字节")

    # 解码测试
    print(f"开始解码测试...")
    decode_start = time.time()

    decode_result = subprocess.run([
        sys.executable, "-m", "cli.decode_cli", restored_file,
        # "--no-decrypt",
        "-i", output_base,
        "-a", algorithm
    ], capture_output=True, text=True, timeout=120)

    if decode_result.returncode != 0:
        print(f"解码失败: {decode_result.stderr}")
        return None

    decode_time = time.time() - decode_start
    total_time = time.time() - start_time

    print(f"解码完成 - 用时: {decode_time:.2f}秒")

    # 验证结果
    if os.path.exists(restored_file):
        restored_size = os.path.getsize(restored_file)
        original_md5 = calculate_md5(test_file)
        restored_md5 = calculate_md5(restored_file)

        compression_ratio = (total_compressed_size / original_size) * 100
        success = original_md5 == restored_md5

        print(f"原始文件大小: {original_size} 字节")
        print(f"还原文件大小: {restored_size} 字节")
        print(f"压缩率: {compression_ratio:.2f}%")
        print(f"MD5验证: {'通过' if success else '失败'}")
        print(f"总用时: {total_time:.2f}秒")

        return {
            'algorithm': algorithm,
            'compression_ratio': compression_ratio,
            'encode_time': encode_time,
            'decode_time': decode_time,
            'total_time': total_time,
            'success': success,
            'original_size': original_size,
            'compressed_size': total_compressed_size
        }
    else:
        print("还原文件未生成")
        return None

def main():
    """主测试函数"""
    print("=== 文件压缩算法性能测试 ===\n")

    test_file = "test.patch"

    # 检查测试文件
    if not os.path.exists(test_file):
        print(f"错误: 测试文件 '{test_file}' 不存在")
        return

    # 创建输出目录
    os.makedirs("test_output", exist_ok=True)

    # 测试的三种算法
    algorithms = ['zlib', 'lzma', 'brotli']
    results = []

    print(f"测试文件: {test_file}")
    print(f"文件大小: {os.path.getsize(test_file)} 字节")
    print("=" * 80)

    # 测试每个算法
    for algorithm in algorithms:
        result = test_single_algorithm(algorithm, test_file)
        if result:
            results.append(result)
        print("=" * 80)

    # 输出对比结果
    if results:
        print("\n=== 性能对比结果 ===")
        print("算法名称    压缩率(%)    编码时间(s)    解码时间(s)    总时间(s)    状态")
        print("-" * 80)

        for result in results:
            status = "成功" if result['success'] else "失败"
            print(f"{result['algorithm']:<12}"
                  f"{result['compression_ratio']:<12.2f}"
                  f"{result['encode_time']:<14.2f}"
                  f"{result['decode_time']:<14.2f}"
                  f"{result['total_time']:<12.2f}"
                  f"{status:<8}")

        # 分析结果
        successful_results = [r for r in results if r['success']]
        if successful_results:
            # 找出最佳算法
            best_compression = min(successful_results, key=lambda x: x['compression_ratio'])
            fastest_total = min(successful_results, key=lambda x: x['total_time'])
            fastest_encode = min(successful_results, key=lambda x: x['encode_time'])
            fastest_decode = min(successful_results, key=lambda x: x['decode_time'])

            print("=== 最佳性能分析 ===")
            print(f"最佳压缩率: {best_compression['algorithm']} ({best_compression['compression_ratio']:.2f}%)")
            print(f"最快总时间: {fastest_total['algorithm']} ({fastest_total['total_time']:.2f}秒)")
            print(f"最快编码: {fastest_encode['algorithm']} ({fastest_encode['encode_time']:.2f}秒)")
            print(f"最快解码: {fastest_decode['algorithm']} ({fastest_decode['decode_time']:.2f}秒)")

            # 检查所有算法是否成功
            all_success = all(r['success'] for r in results)
            if all_success:
                print("\n✅ 所有压缩算法测试通过!")
                print("项目优化成功，所有功能正常工作")
            else:
                print("\n⚠️  部分算法测试失败，请检查依赖安装")
        else:
            print("\n❌ 所有算法测试失败")
    else:
        print("\n❌ 没有成功的测试结果")

if __name__ == "__main__":
    main()
