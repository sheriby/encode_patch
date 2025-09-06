import zlib
import base64
import os
import hashlib
import logging
from typing import Optional

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
logger = logging.getLogger(__name__)

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

def decode_and_decompress(encoded_string: str, algorithm: str = 'brotli', decrypt: bool = False, key: str = 'encode_patch') -> Optional[str]:
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

        # 可选AES解密（在解压缩之前）
        if decrypt:
            logger.info("启用AES解密")
            logger.info(f"解密密钥: {key}")
            try:
                decrypted_bytes = aes_decrypt(decoded_bytes, key)
                logger.info(f"解密后大小: {len(decrypted_bytes)} 字节")
                decoded_bytes = decrypted_bytes
            except ImportError as e:
                logger.error(f"AES解密失败: {e}")
                return None
        else:
            logger.info("跳过AES解密")

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

def load_and_restore_from_chunks(restored_code_path: str, base_filename: str = "compress", algorithm: str = 'brotli', decrypt: bool = False, key: str = 'encode_patch') -> bool:
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
    original_code = decode_and_decompress(combined_string, algorithm, decrypt, key)

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
