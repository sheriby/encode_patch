#!/usr/bin/env python3
"""
encode_patch 主程序
提供简单的命令行接口来调用编码和解码功能
"""

import sys
import argparse
import logging
from core.encode_core import compress_and_encode, save_encoded_string_in_chunks
from core.decode_core import load_and_restore_from_chunks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def encode_file(input_file, output='compress', algorithm='brotli', compression=9, encrypt=True, key='encode_patch', chunk_size=3000):
    """编码文件"""
    logger.info(f"开始编码文件: {input_file}")

    # 压缩编码文件
    encoded_string, file_hash = compress_and_encode(input_file, compression, algorithm, encrypt, key)

    if encoded_string is None:
        logger.error("压缩编码失败")
        return False

    # 分块保存
    success = save_encoded_string_in_chunks(encoded_string, chunk_size, output)

    if success:
        logger.info("文件编码完成")
        logger.info(f"输出文件: {output}*.txt")
        return True
    else:
        logger.error("保存分块文件失败")
        return False

def decode_file(output_file, input='compress', algorithm='brotli', decrypt=True, key='encode_patch'):
    """解码文件"""
    logger.info(f"开始解码文件到: {output_file}")

    success = load_and_restore_from_chunks(output_file, input, algorithm, decrypt, key)

    if success:
        logger.info("文件解码完成")
        return True
    else:
        logger.error("文件解码失败")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="encode_patch - 文件压缩编码工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py encode test.patch                    # 编码文件
  python main.py decode restore.patch                 # 解码文件
  python main.py encode test.patch -o output/compress # 指定输出文件名
  python main.py decode restore.patch -i output/compress # 指定输入文件名
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # encode 子命令
    encode_parser = subparsers.add_parser('encode', help='编码文件')
    encode_parser.add_argument('input_file', help='要编码的输入文件')
    encode_parser.add_argument('-o', '--output', default='compress', help='输出基础文件名')
    encode_parser.add_argument('-a', '--algorithm', choices=['zlib', 'lzma', 'brotli'], default='brotli', help='压缩算法')
    encode_parser.add_argument('-c', '--compression', type=int, default=9, choices=range(10), help='压缩级别 (0-9)')
    encode_parser.add_argument('-s', '--chunk-size', type=int, default=3000, help='分块大小')
    encode_parser.add_argument('-e', '--encrypt', action='store_true', default=True, help='启用加密')
    encode_parser.add_argument('-k', '--key', default='encode_patch', help='加密密钥')
    encode_parser.add_argument('--no-encrypt', action='store_true', help='禁用加密')

    # decode 子命令
    decode_parser = subparsers.add_parser('decode', help='解码文件')
    decode_parser.add_argument('output_file', help='保存解码文件的路径')
    decode_parser.add_argument('-i', '--input', default='compress', help='输入分块文件基础名称')
    decode_parser.add_argument('-a', '--algorithm', choices=['zlib', 'lzma', 'brotli'], default='brotli', help='解压缩算法')
    decode_parser.add_argument('-d', '--decrypt', action='store_true', default=True, help='启用解密')
    decode_parser.add_argument('-k', '--key', default='encode_patch', help='解密密钥')
    decode_parser.add_argument('--no-decrypt', action='store_true', help='禁用解密')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 处理加密/解密参数
    if args.command == 'encode':
        encrypt_enabled = args.encrypt and not getattr(args, 'no_encrypt', False)
        success = encode_file(
            args.input_file,
            args.output,
            args.algorithm,
            args.compression,
            encrypt_enabled,
            args.key,
            args.chunk_size
        )
    elif args.command == 'decode':
        decrypt_enabled = args.decrypt and not getattr(args, 'no_decrypt', False)
        success = decode_file(
            args.output_file,
            args.input,
            args.algorithm,
            decrypt_enabled,
            args.key
        )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
