import argparse
import sys
import logging
import os

from core.encode_core import compress_and_encode, save_encoded_string_in_chunks, should_encrypt_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主函数，命令行界面"""
    parser = argparse.ArgumentParser(
        description="文件压缩编码工具 - 将文件压缩为Base64字符串并分块保存",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python -m cli.encode_cli test.patch                    # 使用默认参数压缩文件
  python -m cli.encode_cli test.patch -c 9 -s 5000       # 使用最高压缩级别，分块大小5000
  python -m cli.encode_cli test.patch -o output/compress # 指定输出文件名
  python -m cli.encode_cli test.patch -v                 # 启用详细输出模式
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
