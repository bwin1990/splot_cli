SPLOT 分区避坏孔实现说明
========================

目标
----
将源序列按分区填充到芯片点阵中，遇到坏孔位置用“0”填充，确保每个分区的有效喷点数能容纳对应分区的序列。

核心输入
--------
- 序列文件：TSV/Excel，列包含 Partition 或 ID（首字符为分区标识）+ Seq。
- 分区掩模：TXT，每行一个分区标志（如 A/B/C/M 或 “0” 表示无效位）。
- 坏孔列表：TXT，整数编号。编号规则依据打印密度划分 A 线 / B 线。

流程概览（C# 与 Python 共性）
---------------------------
1. 加载序列、分区掩模、坏孔列表。
2. 计算芯片容量并校验掩模容量与芯片容量一致；校验 mask 长度不超过源序列长度。
3. 按密度将坏孔位置标记为无效（置为 “0”）。
4. 按分区统计有效喷点数，检查分区容量是否足够。
5. 将分区序列倍增到有效喷点数，不足补全 dummy 序列，并随机打乱。
6. 按掩蔽后的分区标志依次填充目标序列；坏孔位置填 dummy。
7. 输出主序列文件；可选输出图案文件（按密度几何映射全芯片）。

密度与编号规则
--------------
- DPI150：divisor = rows；坏孔编号按 1..rows 循环。
- DPI150_PLUS：divisor = 2*rows - 1；有效点在偶偶/奇奇坐标；坏孔编号按 1..(2*rows-1) 循环。
- DPI300：divisor = 2*rows；坏孔编号按 1..(2*rows) 循环。

主序列→图案的几何映射
---------------------
- DPI150：`pos = j*rows + rows - i - 1`
- DPI150_PLUS：
  - 有效点：行列同为偶或同为奇
  - 正列：`pos = (j/2)*(rows*2-1) + rows - i/2 - 1`
  - 斜列：`pos = (j/2)*(rows*2-1) + rows + rows - 1 - i/2 - 1`
- DPI300：`pos = (2*rows)*(j+1) - i - 1`

C# 版实现（`SPLOT/MainForm.cs`）
-------------------------------
- 加载
  - 序列：`LoadAMSeqsFromTSV`（约 900 行）读取 TSV，首列首字符作分区，存入 `srcAMPartitionSeqs`；记录 `seqLength`/`seqNumber`。
  - 分区掩模：`LoadPartition` → `srcPartitionFlags`。
  - 坏孔：`LoadDefectData`（约 1140 行）解析坏孔编号，<319 为 A 线，其余 B 线；排序后存 `defectALocations`/`defectBLocations`。
- 校验与容量
  - 目标容量：DPI150=rows*cols；DPI150_PLUS=rows*cols+(rows-1)*(cols-1)；DPI300=4*rows*cols。
  - 检查掩模容量等于芯片容量；屏蔽位长度不大于源序列长度；每分区序列数不超过有效喷点数。
- 坏孔掩蔽
  - 在 `Generate_Click` 中复制 `srcPartitionFlags` 为 `destPartitionFlags`。
  - 选择 divisor（见上），遍历掩模索引 `i` 计算 `pos = i % divisor + 1`，命中坏孔则将该位标记为 `"0"`。
- 有效喷点计数
  - 遍历 `destPartitionFlags` 统计非零标志到 `destPartitionValidPosCounts`。
- 扩增与随机
  - `ExtendList`（约 1434 行）：倍增序列到目标数量，不足部分填 `dummySeq`（“0”*maskSeqLen，前缀补到全长）。
  - `Shuffle`：原地随机交换。
- 填充
  - 初始化每分区指针 `partitionIndices`。
  - 遍历 `destPartitionFlags`：标志为 "0" 写 `dummySeq`，否则写 `destPartitionSeqs[flag][partitionIndices[flag]]` 并递增指针。
- 输出
  - `DumpSeq` 写 `{basename}_{density}_out.txt`。
  - `OutputPrintPatternFile` 按几何映射输出全芯片图案。

Python 版实现（CLI）
-------------------
- 主要文件：`splot_cli/core.py`, `splot_cli/file_handlers.py`, `splot_cli/main.py`, `splot_cli/models.py`。
- 加载
  - 序列：`SequenceFileHandler.load_sequences_from_tsv`（`file_handlers.py`）寻找 `Seq` 列，分区列优先 Partition、ID，或首列首字符；可用 `validate_sequence` 检查合法性；记录并返回 `SequenceData`（包括**最大序列长度 `sequence_length`**，并在终端打印出来，便于后续选择 `mask_length`）。
  - Excel：`load_sequences_from_excel`（sheet 默认 flank）。
  - 分区掩模：`PartitionFileHandler.load_partition_data` 读列表，计算分区数量/标志长度。
  - 坏孔：`DefectFileHandler.load_defect_data` 解析坏孔编号，<319 为 A 线，其余 B 线，排序。
- 校验与容量（`core.py`）
  - `PartitionManager.calculate_total_capacity`：三种密度公式同 C#。
  - 在 `process_sequences` 中，如果 `mask_length == 0`，会自动将其设为当前输入文件的最大序列长度，并在终端提示。
  - `_validate_data`：掩模容量=芯片容量；`mask_length` ≤ 源序列最长长度。
  - `_check_capacity`：源分区都存在且序列数不超有效喷点；额外阻止“掩模包含源文件未提供的分区”。
- 坏孔掩蔽
  - `PartitionManager.apply_defect_mask`：按密度选择 divisor，遍历掩模 `pos = i % divisor + 1`，命中坏孔置 `"0"`。
  - `count_valid_positions` 统计非零标志。
- 扩增与随机
  - `SequenceProcessor.extend_sequences`：倍增序列到有效喷点数，不足用 dummy（全 0）补齐。
  - `shuffle_sequences`：`random.shuffle`。
- 填充
  - `_fill_partitions`：遍历掩蔽后的 flags，"0" 写 dummy，否则按分区指针取序列，指针递增。
- 输出
  - `_write_output_files`：写 `{basename}_{density}_out.txt`，可选 `print_pattern.txt`。
  - 图案：`ChipLayoutOptimizer`（`file_handlers.py`）按密度几何映射全芯片，映射公式同上；支持通过 `seq_range` 仅输出序列的某一段（例如单一碱基位点）用于图案展示。
- 交互模式（缺少文件参数时）
  - `main.py` 使用 tkinter 依次弹窗选择 序列/分区/坏孔 文件，并打印调试信息（包括当前文件的最大序列长度）；随后在终端询问芯片行列、密度、屏蔽长度（默认采用该最大长度）、是否生成图案、是否检查源序列、输出路径。
  - 当选择生成图案文件时，终端会额外询问“图案文件中用于表示喷点的碱基位置（1 为第一位）”，只用该位置的碱基生成 `print_pattern.txt`，避免输出整条长序列。

使用示例
--------
命令行（推荐）：
```
splot -i seq.tsv -p partition.txt -d defect.txt -o output \
      --rows 318 --cols 540 --density DPI150_PLUS --mask-length 130 --pattern
```
交互模式：不带必需文件参数直接运行 `splot` 或 `python -m splot_cli.main`，按弹窗选择三个文件，终端确认其余参数；如不显式指定 `--mask-length` 或设为 0，则自动使用当前序列文件的最大长度。
