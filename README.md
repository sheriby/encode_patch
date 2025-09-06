# encode_patch - 文件压缩编码工具

## 项目概述

这是一个专业的Python文件压缩、编码和分块存储工具，具有模块化设计、全面测试和优秀的用户体验。

## 主要特性

### 🏗️ 模块化架构
- **core/**: 核心功能模块 (压缩、加密、编码/解码)
- **cli/**: 命令行接口模块
- **tests/**: 完整的测试套件
- **main.py**: 统一程序入口

### 🔧 核心功能
- ✅ 支持多种压缩算法 (zlib/lzma/brotli)
- ✅ AES-256加密 (CTR模式，保持文件大小)
- ✅ Base64编码/解码
- ✅ 智能文件分块存储
- ✅ 自动文件大小检测和加密决策

### 🧪 全面测试
- ✅ 压缩算法性能测试
- ✅ 加密功能完整性测试
- ✅ 小文件优化测试
- ✅ 文件大小保持测试

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 基本使用

#### 使用主程序
```bash
# 编码文件
python main.py encode test.patch

# 解码文件
python main.py decode restored.patch
```

#### 使用CLI模块
```bash
# 编码文件
python -m cli.encode_cli test.patch

# 解码文件
python -m cli.decode_cli restored.patch
```

## 详细使用方法

### 编码文件
```bash
# 基本使用（推荐配置）
python main.py encode input_file.txt

# 指定压缩算法
python main.py encode input_file.txt -a lzma          # 使用LZMA压缩
python main.py encode input_file.txt -a brotli        # 使用Brotli压缩 (默认)
python main.py encode input_file.txt -a zlib -c 9     # 使用zlib最高压缩

# 高级选项
python main.py encode input_file.txt -a brotli -c 9 -s 5000 -o output/compress -v

# 参数说明
# -a, --algorithm: 压缩算法 (zlib/lzma/brotli)，默认brotli
# -c, --compression: 压缩级别 (0-9)，0=无压缩，9=最高压缩，默认9
# -s, --chunk-size: 分块大小（字符数），默认3000
# -o, --output: 输出基础文件名，默认"compress"
# -e, --encrypt: 启用AES加密（默认启用）
# -k, --key: AES加密密钥，默认"encode_patch"
# --no-encrypt: 禁用AES加密
# -v, --verbose: 启用详细输出模式
```

### 解码文件
```bash
# 基本使用
python main.py decode output_file.txt

# 指定解压缩算法
python main.py decode output_file.txt -a lzma         # 使用LZMA解压缩
python main.py decode output_file.txt -a brotli       # 使用Brotli解压缩

# 高级选项
python main.py decode output_file.txt -i input/compress -a brotli -v

# 参数说明
# -i, --input: 输入分块文件基础名称，默认"compress"
# -a, --algorithm: 解压缩算法 (zlib/lzma/brotli)，默认brotli
# -d, --decrypt: 启用AES解密（默认启用）
# -k, --key: AES解密密钥，默认"encode_patch"
# --no-decrypt: 禁用AES解密
# -v, --verbose: 启用详细输出模式
```

## 项目结构

```
encode_patch/
├── main.py                 # 主程序入口
├── core/                   # 核心功能模块
│   ├── __init__.py
│   ├── encode_core.py      # 编码核心功能
│   └── decode_core.py      # 解码核心功能
├── cli/                    # 命令行接口模块
│   ├── __init__.py
│   ├── encode_cli.py       # 编码CLI
│   └── decode_cli.py       # 解码CLI
├── tests/                  # 测试模块
│   ├── __init__.py
│   ├── test_compress.py    # 压缩算法测试
│   ├── test_encryption.py  # 加密功能测试
│   ├── test_small_file.py  # 小文件测试
│   └── test_size_preservation.py # 大小保持测试
├── requirements.txt        # 项目依赖
├── README.md              # 项目文档
├── .gitignore             # Git忽略文件
└── test.patch             # 测试文件
```

## 测试结果

### ✅ 压缩算法测试
基于测试文件 (test.patch，83KB):

| 算法 | 压缩率 | 编码时间 | 解码时间 | 总时间 | 状态 |
|------|--------|----------|----------|--------|------|
| zlib | 9.58% | 0.15s | 0.04s | 0.19s | ✅ 通过 |
| lzma | 8.24% | 0.05s | 0.04s | 0.09s | ✅ 通过 |
| brotli | 7.72% | 0.05s | 0.04s | 0.09s | ✅ 通过 |

**最佳性能**: BROTLI算法 (最快总时间 0.09秒)

### ✅ 加密功能测试
- ✅ 默认加密解密工作流
- ✅ 自定义密钥支持
- ✅ 加密禁用功能

### ✅ 小文件优化测试
- ✅ 智能文件大小检测
- ✅ 小文件自动跳过加密
- ✅ 加密开销分析

### ✅ 大小保持测试
- ✅ CTR模式完美保持文件大小
- ✅ MD5完整性验证
- ✅ 解决传统CBC模式的填充开销问题

## 技术特性

### 压缩算法
- **zlib**: 经典的无损压缩算法，速度快，压缩率适中
- **lzma**: 高压缩率算法，压缩效果更好但速度稍慢
- **brotli**: Google开发的现代压缩算法，在速度和压缩率间取得良好平衡
- 支持9个压缩级别 (0-9)
- 自动检测可用算法并提供友好的错误提示

### 加密特性
- **AES-256**: 使用CTR模式，保证文件大小不变
- **智能决策**: 小文件自动跳过加密以避免开销
- **密钥管理**: 支持自定义密钥
- **安全可靠**: 工业级加密标准

### 字符编码
- **Base64编码**: 将二进制数据转换为安全的文本格式
- **标准兼容**: 使用RFC 4648标准的Base64字符集
- **无数据丢失**: 确保完全可逆的编码解码过程

### 分块存储
- 可配置分块大小
- 支持目录自动创建
- 进度跟踪和状态报告

## 兼容性

- ✅ Python 3.6+
- ✅ 跨平台支持 (Windows/macOS/Linux)
- ✅ zlib: 无外部依赖 (Python标准库)
- ✅ lzma: Python 3.3+ (标准库)
- ✅ brotli: 需要安装 `brotli` 或 `brotlipy` 包
- ✅ cryptography: 需要安装 `cryptography` 包 (用于AES加密)

## 最佳实践

1. **选择合适的压缩算法**:
   - **brotli**: 默认推荐，平衡压缩率和速度
   - **lzma**: 需要高压缩率时选择
   - **zlib**: 需要快速处理时选择

2. **选择压缩级别**: 9通常是最佳压缩率，6是速度与压缩率的平衡点

3. **安全考虑**:
   - **AES加密**: 默认启用，对所有数据提供加密保护
   - **智能决策**: 小文件(<2KB)会自动跳过加密以避免开销过大
   - **密钥管理**: 使用强密码作为加密密钥，避免使用默认密钥
   - **自定义密钥**: 生产环境必须使用自定义密钥
   - **强制加密**: 如需对小文件强制加密，使用 `--no-encrypt=False`
   - **禁用加密**: 仅在不需要安全保护时使用 `--no-encrypt`

4. **压缩率优化**:
   - **小文件**: 建议对大于2KB的文件启用加密
   - **大文件**: 加密开销相对较小，推荐启用
   - **监控开销**: 使用 `-v` 查看详细的压缩统计信息

4. **合理设置分块大小**: 根据存储系统和使用场景调整，3000字符是通用默认值

5. **使用详细模式**: 调试时启用 `-v` 选项获取更多信息

## 故障排除

### 常见问题
- **文件未找到**: 检查输入文件路径是否正确
- **权限错误**: 确保对输入输出目录有读写权限
- **内存不足**: 对于超大文件，考虑增加分块大小
- **编码错误**: 确保文件是有效的UTF-8编码
- **cryptography模块缺失**: 运行 `pip install cryptography` 安装AES加密支持
- **解密密钥错误**: 确保使用正确的密钥进行解密
- **加密文件损坏**: 检查文件是否完整，AES加密对数据损坏很敏感

### 调试模式
使用 `-v` 选项启用详细日志输出，帮助诊断问题。
