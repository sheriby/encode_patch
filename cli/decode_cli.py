import argparse
import sys
import logging

from core.decode_core import load_and_restore_from_chunks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主函数，命令行界面"""
    parser = argparse.ArgumentParser(
        description="文件解码解压缩工具 - 从分块文件中恢复原始文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python -m cli.decode_cli restore.patch                    # 使用默认参数恢复文件
  python -m cli.decode_cli restore.patch -i output/compress # 指定输入基础文件名
  python -m cli.decode_cli restore.patch -v                 # 启用详细输出模式
        """
    )

    parser.add_argument('output_file', help='保存还原文件的路径')
    parser.add_argument('-i', '--input', default='compress',
                       help='输入分块文件基础名称，默认"compress"')
    parser.add_argument('-a', '--algorithm', choices=['zlib', 'lzma', 'brotli'], default='brotli',
                       help='解压缩算法 (zlib/lzma/brotli)，默认brotli')
    parser.add_argument('-d', '--decrypt', action='store_true', default=True,
                       help='启用AES解密（默认启用）')
    parser.add_argument('-k', '--key', default='encode_patch',
                       help='AES解密密钥，默认"encode_patch"')
    parser.add_argument('--no-decrypt', action='store_true',
                       help='禁用AES解密')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='启用详细输出模式')

    args = parser.parse_args()

    # 处理解密参数：--no-decrypt优先级高于默认解密
    decrypt_enabled = args.decrypt and not args.no_decrypt

    # 根据详细标志设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    logger.info("开始文件解码解压缩过程...")
    logger.info(f"输出文件: {args.output_file}")
    logger.info(f"输入基础名称: {args.input}")
    logger.info(f"解压缩算法: {args.algorithm}")
    logger.info(f"AES解密: {'启用' if decrypt_enabled else '禁用'}")
    if decrypt_enabled:
        logger.info(f"解密密钥: {args.key}")

    # 加载分块并还原
    success = load_and_restore_from_chunks(
        args.output_file,
        args.input,
        args.algorithm,
        decrypt_enabled,
        args.key
    )

    if success:
        logger.info("文件解码解压缩完成")
    else:
        logger.error("文件解码解压缩失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
