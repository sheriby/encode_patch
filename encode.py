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

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

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

def aes_encrypt(data: bytes, key: str, mode: str = 'ctr') -> bytes:
    """
    使用AES加密数据（支持多种模式）

    参数:
    data (bytes): 要加密的数据
    key (str): 加密密钥
    mode (str): 加密模式 ('cbc', 'ctr', 'ofb')

    返回:
    bytes: 加密后的数据
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise ImportError("cryptography库不可用，请安装: pip install cryptography")

    # 将密钥转换为32字节（256位）
    key_bytes = key.encode('utf-8')
    if len(key_bytes) < 32:
        # 如果密钥太短，用0填充
        key_bytes = key_bytes.ljust(32, b'\x00')
    elif len(key_bytes) > 32:
        # 如果密钥太长，截取前32字节
        key_bytes = key_bytes[:32]

    # 根据模式选择不同的加密方式
    if mode == 'ctr':
        # CTR模式：不需要填充，输出大小等于输入大小 + 16字节nonce
        nonce = os.urandom(16)
        cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        return nonce + encrypted_data

    elif mode == 'ofb':
        # OFB模式：不需要填充，输出大小等于输入大小 + 16字节IV
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key_bytes), modes.OFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        return iv + encrypted_data

    else:  # 默认CBC模式（向后兼容）
        # 生成随机IV
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # PKCS7填充 (AES块大小为16字节 = 128位)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()

        # 加密
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # 返回 IV + 加密数据
        return iv + encrypted_data

def aes_decrypt(encrypted_data: bytes, key: str) -> bytes:
    """
    使用AES解密数据（自动检测模式）

    参数:
    encrypted_data (bytes): 要解密的数据（包含IV/nonce）
    key (str): 解密密钥

    返回:
    bytes: 解密后的数据
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise ImportError("cryptography库不可用，请安装: pip install cryptography")

    if len(encrypted_data) < 16:
        raise ValueError("加密数据太短")

    # 提取IV/nonce和加密数据
    iv_or_nonce = encrypted_data[:16]
    encrypted_content = encrypted_data[16:]

    # 将密钥转换为32字节（256位）
    key_bytes = key.encode('utf-8')
    if len(key_bytes) < 32:
        key_bytes = key_bytes.ljust(32, b'\x00')
    elif len(key_bytes) > 32:
        key_bytes = key_bytes[:32]

    # 首先尝试CTR模式解密（默认模式）
    try:
        cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(iv_or_nonce), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_content) + decryptor.finalize()
        return decrypted_data
    except Exception as ctr_error:
        # CTR模式失败，尝试CBC模式（向后兼容）
        try:
            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_or_nonce), backend=default_backend())
            decryptor = cipher.decryptor()

            # 解密
            decrypted_padded = decryptor.update(encrypted_content) + decryptor.finalize()

            # 移除PKCS7填充 (AES块大小为16字节 = 128位)
            unpadder = padding.PKCS7(128).unpadder()
            decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()

            return decrypted_data
        except Exception as cbc_error:
            # CBC也失败，尝试OFB模式
            try:
                cipher = Cipher(algorithms.AES(key_bytes), modes.OFB(iv_or_nonce), backend=default_backend())
                decryptor = cipher.decryptor()
                decrypted_data = decryptor.update(encrypted_content) + decryptor.finalize()
                return decrypted_data
            except Exception as ofb_error:
                # 所有模式都失败，提供详细错误信息
                error_msg = f"无法解密数据，所有解密模式均失败:\n"
                error_msg += f"  CTR模式错误: {str(ctr_error)}\n"
                error_msg += f"  CBC模式错误: {str(cbc_error)}\n"
                error_msg += f"  OFB模式错误: {str(ofb_error)}\n"
                error_msg += "可能原因: 密钥错误、数据损坏或使用了不支持的加密模式"
                raise ValueError(error_msg)

def should_encrypt_file(file_size: int, force_encrypt: bool = False) -> bool:
    """
    智能判断是否应该对文件进行加密

    参数:
    file_size (int): 文件大小（字节）
    force_encrypt (bool): 是否强制加密

    返回:
    bool: 是否应该加密
    """
    if force_encrypt:
        return True

    # 对于小文件，加密开销较大
    if file_size < 512:
        return False  # 小于512字节的文件不建议加密
    elif file_size < 2048:
        return False  # 小于2KB的文件建议不加密
    else:
        return True   # 大于2KB的文件建议加密

def compress_and_encode(file_path: str, compression_level: int = 9, algorithm: str = 'brotli', encrypt: bool = False, key: str = 'encode_patch', smart_encrypt: bool = True) -> Tuple[Optional[str], Optional[str]]:
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

        original_size = len(file_bytes)
        logger.info(f"原始文件大小: {original_size} 字节")

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

        # 可选AES加密（在压缩之后）
        if encrypt:
            logger.info("启用AES加密")
            logger.info(f"加密密钥: {key}")
            try:
                encrypted_bytes = aes_encrypt(compressed_data, key, mode='ctr')
                logger.info(f"加密后大小: {len(encrypted_bytes)} 字节")

                # CTR模式只会增加16字节IV，不会显著改变大小
                size_increase = len(encrypted_bytes) - len(compressed_data)
                logger.info(f"加密开销: {size_increase} 字节 (CTR模式IV)")

                compressed_data = encrypted_bytes
            except ImportError as e:
                logger.error(f"AES加密失败: {e}")
                return None, None
        else:
            logger.info("跳过AES加密")

        # 编码为Base64
        encoded_bytes = base64.b64encode(compressed_data)
        encoded_string = encoded_bytes.decode('utf-8')

        # 计算更准确的压缩率
        final_size = len(encoded_string)
        compression_ratio = final_size / original_size * 100

        # 显示详细的压缩统计
        logger.info(f"Base64编码后大小: {final_size} 字符")
        logger.info(f"总压缩率: {compression_ratio:.2f}%")

        if encrypt:
            # 显示各个阶段的开销
            encrypt_ratio = len(file_bytes) / original_size * 100
            compress_ratio = len(compressed_data) / len(file_bytes) * 100
            base64_ratio = final_size / len(compressed_data) * 100

            logger.info(f"加密开销: {encrypt_ratio:.2f}% (相对原始大小)")
            logger.info(f"压缩效率: {compress_ratio:.2f}% (相对加密后大小)")
            logger.info(f"Base64开销: {base64_ratio:.2f}% (相对压缩后大小)")

            # 给出建议
            if compression_ratio > 150:
                logger.warning("最终文件大小显著增加，建议检查是否需要对该文件启用加密")
            elif compression_ratio > 120:
                logger.info("文件大小有所增加，但加密安全性优先")

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
    
    if chunk_size == 0:
        chunk_size = len(encoded_string)

    if chunk_size < 0:
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
    parser.add_argument('-e', '--encrypt', action='store_true', default=True,
                       help='启用AES加密（默认启用）')
    parser.add_argument('-k', '--key', default='encode_patch',
                       help='AES加密密钥，默认"encode_patch"')
    parser.add_argument('--no-encrypt', action='store_true',
                       help='禁用AES加密')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='启用详细输出模式')

    args = parser.parse_args()

    # 获取文件大小用于智能决策
    if os.path.exists(args.input_file):
        file_size = os.path.getsize(args.input_file)
    else:
        file_size = 0

    # 处理加密参数：--no-encrypt优先级高于默认加密
    encrypt_enabled = args.encrypt and not args.no_encrypt

    # 如果启用了智能加密，对小文件进行智能决策
    if encrypt_enabled and file_size > 0:
        should_encrypt = should_encrypt_file(file_size, force_encrypt=not args.no_encrypt)
        if not should_encrypt and file_size < 2048:
            logger.info(f"智能决策: 文件大小 {file_size} 字节较小，建议不加密以避免开销增加")
            logger.info("如需强制加密，请使用 --no-encrypt=False 或检查文件大小")
            encrypt_enabled = False

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
    logger.info(f"AES加密: {'启用' if encrypt_enabled else '禁用'}")
    if encrypt_enabled:
        logger.info(f"加密密钥: {args.key}")

    # 压缩编码文件
    encoded_string, file_hash = compress_and_encode(args.input_file, args.compression, args.algorithm, encrypt_enabled, args.key)

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
