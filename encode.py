import zlib
import base64
import os
import hashlib
import argparse
import sys
from typing import Optional, Tuple
import logging

try:
    import lzma
    LZMA_AVAILABLE = True
except ImportError:
    LZMA_AVAILABLE = False

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_file_hash(file_path: str) -> str:
    """计算文件的SHA256哈希值"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def compress_and_encode(file_path: str, compression_level: int = 9, algorithm: str = 'brotli') -> Tuple[Optional[str], Optional[str]]:
    """
    读取文件，使用指定算法压缩，然后编码为Base64字符串

    参数:
    file_path (str): 要压缩的文件路径
    compression_level (int): 压缩级别 (0-9)，默认9
    algorithm (str): 压缩算法 ('zlib', 'lzma', 'brotli')，默认'brotli'

    返回:
    Tuple[Optional[str], Optional[str]]: (压缩编码后的字符串, 文件哈希) 或 (None, None) 如果出错
    """
    if not os.path.exists(file_path):
        logger.error(f"文件 '{file_path}' 未找到")
        return None, None

    if not os.access(file_path, os.R_OK):
        logger.error(f"没有读取文件 '{file_path}' 的权限")
        return None, None

    try:
        # 计算文件哈希
        file_hash = calculate_file_hash(file_path)
        logger.info(f"文件哈希: {file_hash}")

        # 读取文件内容
        with open(file_path, 'rb') as f:
            file_bytes = f.read()

        logger.info(f"原始文件大小: {len(file_bytes)} 字节")
        logger.info(f"使用压缩算法: {algorithm}")

        # 根据选择的算法进行压缩
        if algorithm == 'zlib':
            compressed_data = zlib.compress(file_bytes, level=compression_level)
        elif algorithm == 'lzma':
            if not LZMA_AVAILABLE:
                logger.error("lzma模块不可用，请安装lzma支持")
                return None, None
            compressed_data = lzma.compress(file_bytes, preset=compression_level)
        elif algorithm == 'brotli':
            if not BROTLI_AVAILABLE:
                logger.error("brotli模块不可用，请安装brotli支持")
                return None, None
            compressed_data = brotli.compress(file_bytes, quality=compression_level)
        else:
            logger.error(f"不支持的压缩算法: {algorithm}")
            return None, None

        logger.info(f"压缩后大小: {len(compressed_data)} 字节")

        # 编码为Base64
        encoded_bytes = base64.b64encode(compressed_data)
        encoded_string = encoded_bytes.decode('utf-8')

        compression_ratio = len(encoded_string) / len(file_bytes) * 100
        logger.info(f"编码后大小: {len(encoded_string)} 字符")
        logger.info(f"压缩率: {compression_ratio:.2f}%")

        return encoded_string, file_hash

    except Exception as e:
        logger.error(f"压缩编码过程中出错: {e}")
        return None, None
    
def save_encoded_string_in_chunks(encoded_string: str, chunk_size: int, base_filename: str = "compress") -> bool:
    """
    将编码后的字符串分块保存到多个文件中

    参数:
    encoded_string (str): 完整的编码字符串
    chunk_size (int): 每个文件的字符数
    base_filename (str): 基础文件名，如 "compress"

    返回:
    bool: 保存成功返回True，否则返回False
    """
    if encoded_string is None or encoded_string == "":
        logger.error("没有可保存的数据")
        return False

    if chunk_size <= 0:
        logger.error("分块大小必须大于0")
        return False

    # 创建输出目录（如果不存在）
    output_dir = os.path.dirname(base_filename) if os.path.dirname(base_filename) else "."
    if output_dir != "." and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"创建输出目录: {output_dir}")
        except Exception as e:
            logger.error(f"创建输出目录失败: {e}")
            return False

    num_files = 0
    total_chunks = (len(encoded_string) + chunk_size - 1) // chunk_size  # 向上取整

    logger.info(f"开始分块保存，共 {total_chunks} 个文件")

    try:
        # 按分块大小分割字符串
        for i in range(0, len(encoded_string), chunk_size):
            chunk = encoded_string[i:i + chunk_size]
            file_path = f"{base_filename}{num_files}.txt"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(chunk)

            num_files += 1

            if num_files % 10 == 0 or num_files == total_chunks:
                logger.info(f"已保存 {num_files}/{total_chunks} 个文件")

        logger.info(f"成功保存 {num_files} 个分块文件")
        return True

    except Exception as e:
        logger.error(f"保存文件时出错: {e}")
        return False

def main():
    """主函数，命令行界面"""
    parser = argparse.ArgumentParser(
        description="文件压缩编码工具 - 将文件压缩为Base64字符串并分块保存",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python encode.py test.patch                    # 使用默认参数压缩文件
  python encode.py test.patch -c 9 -s 5000       # 使用最高压缩级别，分块大小5000
  python encode.py test.patch -o output/compress # 指定输出文件名
  python encode.py test.patch -v                 # 启用详细输出模式
        """
    )

    parser.add_argument('input_file', help='要压缩的输入文件路径')
    parser.add_argument('-a', '--algorithm', choices=['zlib', 'lzma', 'brotli'], default='brotli',
                       help='压缩算法 (zlib/lzma/brotli)，默认brotli')
    parser.add_argument('-c', '--compression', type=int, default=9, choices=range(10),
                       help='压缩级别 (0-9)，0=无压缩，9=最高压缩，默认9')
    parser.add_argument('-s', '--chunk-size', type=int, default=3000,
                       help='分块大小（字符数），默认3000')
    parser.add_argument('-o', '--output', default='compress',
                       help='输出基础文件名，默认"compress"')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='启用详细输出模式')

    args = parser.parse_args()

    # 根据详细标志设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    logger.info("开始文件压缩编码过程...")
    logger.info(f"输入文件: {args.input_file}")
    logger.info(f"压缩算法: {args.algorithm}")
    logger.info(f"压缩级别: {args.compression}")
    logger.info(f"分块大小: {args.chunk_size}")
    logger.info(f"输出基础名称: {args.output}")

    # 压缩编码文件
    encoded_string, file_hash = compress_and_encode(args.input_file, args.compression, args.algorithm)

    if encoded_string is None:
        logger.error("压缩编码失败，程序退出")
        sys.exit(1)

    # 分块保存
    success = save_encoded_string_in_chunks(
        encoded_string,
        args.chunk_size,
        args.output
    )

    if success:
        logger.info("文件压缩编码完成")
        logger.info(f"输出文件保存为: {args.output}*.txt")
    else:
        logger.error("保存分块文件失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
