# SPLOT Python CLI

DNA打印序列分区排版优化工具 Python版本
Sequence Printing Layout Optimize Tool

## 功能特性

- ✅ **多格式支持**: TSV、Excel文件读取
- ✅ **多种打印密度**: 150DPI、150DPI_PLUS、300DPI
- ✅ **智能分区管理**: 自动分区匹配和容量检查
- ✅ **坏孔屏蔽**: 支持A线和B线坏孔屏蔽
- ✅ **序列优化**: 自动扩增和随机化
- ✅ **图案生成**: 可视化打印图案输出
- ✅ **跨平台**: Windows、Linux、macOS支持

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 基本用法

```bash
# 基本命令
python -m splot_cli.main \
  --input examples/sample_sequences.tsv \
  --partition examples/sample_partition.txt \
  --defect examples/sample_defects.txt \
  --output output/

# 带所有参数的完整命令
python -m splot_cli.main \
  --input sequences.tsv \
  --partition partition.txt \
  --defect defect.txt \
  --output result/ \
  --rows 318 \
  --cols 540 \
  --density DPI300 \
  --mask-length 0 \
  --pattern \
  --check-source \
  --verbose
```

### 3. 安装为全局命令

```bash
pip install -e .

# 安装后可以直接使用 splot 命令
splot --help
splot -i sequences.tsv -p partition.txt -d defect.txt -o output/
```

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--input` | `-i` | 输入序列文件 (TSV/Excel) | **必需** |
| `--partition` | `-p` | 分区掩模文件 | **必需** |
| `--defect` | `-d` | 坏孔屏蔽文件 | **必需** |
| `--output` | `-o` | 输出路径 | **必需** |
| `--rows` | | 芯片行数 | 318 |
| `--cols` | | 芯片列数 | 540 |
| `--density` | | 打印密度 | DPI300 |
| `--mask-length` | | 屏蔽位长度（0 表示自动使用序列最大长度） | 0 |
| `--pattern` | | 生成图案文件 | False |
| `--check-source` | | 检查源序列合法性 | True |
| `--verbose` | `-v` | 详细输出 | False |

## 打印密度说明

- **DPI150**: 基础密度，容量 = 行数 × 列数
- **DPI150_PLUS**: 斜点打印，容量 = 行×列 + (行-1)×(列-1)  
- **DPI300**: 高密度，容量 = (2×行) × (2×列)

## 文件格式要求

### 输入序列文件 (.tsv/.xlsx)
```
ID	Seq
A-xxx	ATCGATCGATCG...
B-xxx	GCTAGCTAGCTA...
M-xxx	AAAATTTTCCCC...
```

### 分区文件 (.txt) 
指明芯片合成阵列中每个position的分区index，因此分区类别应该与输入序列文件相对应
```
A
A
B
B
C
M
0
```

### 坏孔文件 (.txt)
合成阵列中整行需要避开的喷孔序列号。
```
1,5,10,15,320,325
```

## 输出文件

- **主序列文件**: `{输入文件名}_{密度}_out.txt`
- **图案文件**: `print_pattern.txt` (可选)

在载入序列文件时，程序会在终端输出：

- 加载到的序列条数和分区数量
- 当前文件中**最大序列长度**（可用于参考和设置 `--mask-length`，当其为 0 时会自动使用该长度）

## 示例用法

### 验证文件格式
```bash
python -m splot_cli.main validate examples/sample_sequences.tsv
```

### 查看软件信息
```bash
python -m splot_cli.main info
```

### 批处理脚本示例
```bash
#!/bin/bash
for file in data/*.tsv; do
    base_name=$(basename "$file" .tsv)
    python -m splot_cli.main \
        -i "$file" \
        -p config/partition.txt \
        -d config/defects.txt \
        -o "output/${base_name}/" \
        --density DPI300 \
        --pattern
done
```

## 性能优化

对于大文件处理，建议：

1. 使用SSD存储
2. 增加系统内存
3. 关闭不必要的源序列检查：`--no-check-source`

## 故障排除

### 常见错误

1. **文件格式错误**: 确保TSV文件使用Tab分隔，包含'Seq'列
2. **容量不足**: 检查分区容量是否满足序列数量需求
3. **编码问题**: 文件应使用UTF-8或GBK编码

### 获取详细错误信息
```bash
python -m splot_cli.main --verbose [其他参数]
```

## 与原版C#的差异

| 特性 | C#版本 | Python版本 |
|------|--------|-------------|
| 平台支持 | Windows | 跨平台 |
| 依赖 | .NET Framework | Python 3.8+ |
| 性能 | 原生性能 | 良好性能 |
| 扩展性 | 较低 | 很高 |
| 部署 | 需要安装.NET | pip install |

## 开发信息

- **版本**: 2.1.4
- **Python要求**: >=3.8
- **主要依赖**: pandas, numpy, click, rich
- **许可证**: 与原版保持一致
