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

def decode_and_decompress(encoded_string: str, algorithm: str = 'brotli') -> Optional[str]:
    """
    解码Base64字符串并使用指定算法解压缩

    参数:
    encoded_string (str): 要解码解压缩的编码字符串
    algorithm (str): 解压缩算法 ('zlib', 'lzma', 'brotli')，默认'brotli'

    返回:
    Optional[str]: 原始解压缩字符串，如果出错则返回None
    """
    if not encoded_string or encoded_string.strip() == "":
        logger.error("输入的编码字符串为空")
        return None

    try:
        logger.debug("开始Base64解码...")
        encoded_bytes = encoded_string.encode('utf-8')
        decoded_bytes = base64.b64decode(encoded_bytes)

        logger.debug(f"开始{algorithm}解压缩...")

        # 根据算法选择解压缩方法
        if algorithm == 'zlib':
            decompressed_bytes = zlib.decompress(decoded_bytes)
        elif algorithm == 'lzma':
            if not LZMA_AVAILABLE:
                logger.error("lzma模块不可用，无法解压缩lzma格式文件")
                return None
            decompressed_bytes = lzma.decompress(decoded_bytes)
        elif algorithm == 'brotli':
            if not BROTLI_AVAILABLE:
                logger.error("brotli模块不可用，无法解压缩brotli格式文件")
                return None
            decompressed_bytes = brotli.decompress(decoded_bytes)
        else:
            logger.error(f"不支持的解压缩算法: {algorithm}")
            return None

        logger.debug("开始UTF-8解码...")
        original_string = decompressed_bytes.decode('utf-8')

        logger.info(f"成功解码解压缩，原始大小: {len(decompressed_bytes)} 字节")
        return original_string

    except base64.binascii.Error as e:
        logger.error(f"Base64解码错误: {e}")
        return None
    except zlib.error as e:
        logger.error(f"zlib解压缩错误: {e}")
        return None
    except UnicodeDecodeError as e:
        logger.error(f"UTF-8解码错误: {e}")
        return None
    except Exception as e:
        logger.error(f"解码解压缩过程中出现未知错误: {e}")
        return None

def load_and_restore_from_chunks(restored_code_path: str, base_filename: str = "compress", algorithm: str = 'zlib') -> bool:
    """
    从分块文件中加载数据，解码解压缩，然后保存到目标文件

    参数:
    restored_code_path (str): 保存还原文件的路径
    base_filename (str): 分块文件的基础文件名
    algorithm (str): 解压缩算法 ('zlib', 'lzma', 'brotli')，默认'brotli'

    返回:
    bool: 还原成功返回True，否则返回False
    """
    combined_string = ""
    file_index = 0

    logger.info("开始加载分块文件...")

    while True:
        file_path = f"{base_filename}{file_index}.txt"
        if not os.path.exists(file_path):
            if file_index == 0:
                logger.error(f"找不到分块文件: {file_path}")
                return False
            break  # 没有更多分块文件可读取

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chunk = f.read()
                combined_string += chunk

            file_index += 1

            if file_index % 10 == 0:
                logger.info(f"已加载 {file_index} 个分块文件")

        except Exception as e:
            logger.error(f"读取分块文件出错 {file_path}: {e}")
            return False

    if not combined_string:
        logger.error("未找到分块文件或文件为空")
        return False

    logger.info(f"共加载 {file_index} 个分块文件")
    logger.info(f"组合字符串长度: {len(combined_string)} 字符")

    # 解码解压缩组合字符串
    original_code = decode_and_decompress(combined_string, algorithm)

    if original_code is None:
        logger.error("解码解压缩失败")
        return False

    # 创建输出目录（如果需要）
    output_dir = os.path.dirname(restored_code_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"创建输出目录: {output_dir}")
        except Exception as e:
            logger.error(f"创建输出目录失败: {e}")
            return False

    # 保存还原代码到文件
    try:
        with open(restored_code_path, 'w', encoding='utf-8') as f_out:
            f_out.write(original_code)

        logger.info(f"成功保存还原文件: {restored_code_path}")
        logger.info(f"文件大小: {len(original_code)} 字符")

        return True

    except Exception as e:
        logger.error(f"保存还原文件出错: {e}")
        return False

def main():
    """主函数，命令行界面"""
    parser = argparse.ArgumentParser(
        description="文件解码解压缩工具 - 从分块文件中恢复原始文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python decode.py restore.patch                    # 使用默认参数恢复文件
  python decode.py restore.patch -i output/compress # 指定输入基础文件名
  python decode.py restore.patch -v                 # 启用详细输出模式
        """
    )

    parser.add_argument('output_file', help='保存还原文件的路径')
    parser.add_argument('-i', '--input', default='compress',
                       help='输入分块文件基础名称，默认"compress"')
    parser.add_argument('-a', '--algorithm', choices=['zlib', 'lzma', 'brotli'], default='brotli',
                       help='解压缩算法 (zlib/lzma/brotli)，默认brotil')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='启用详细输出模式')

    args = parser.parse_args()

    # 根据详细标志设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    logger.info("开始文件解码解压缩过程...")
    logger.info(f"输出文件: {args.output_file}")
    logger.info(f"输入基础名称: {args.input}")
    logger.info(f"解压缩算法: {args.algorithm}")

    # 加载分块并还原
    success = load_and_restore_from_chunks(
        args.output_file,
        args.input,
        args.algorithm
    )

    if success:
        logger.info("文件解码解压缩完成")
    else:
        logger.error("文件解码解压缩失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
