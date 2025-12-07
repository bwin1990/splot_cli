"""
核心业务逻辑模块
"""
import random
from typing import Dict, List
from .models import (
    ProcessingOptions, ProcessingResult, SequenceData, 
    PartitionData, DefectData, PrintDensity
)
from .file_handlers import (
    SequenceFileHandler, PartitionFileHandler, 
    DefectFileHandler, OutputFileHandler
)
from rich.console import Console
from tqdm import tqdm
import os

console = Console()

class SequenceProcessor:
    """序列处理器"""
    
    @staticmethod
    def extend_sequences(seq_list: List[str], max_count: int, dummy_seq: str) -> List[str]:
        """将序列列表扩增到指定数量"""
        current_count = len(seq_list)
        if current_count >= max_count:
            return seq_list[:max_count]
        
        # 计算需要扩增的倍数
        n = max_count // current_count
        additional_count = max_count - current_count * n
        
        # 使用列表乘法进行高效扩增
        extended_list = seq_list * n
        extended_list.extend([dummy_seq] * additional_count)
        
        return extended_list
    
    @staticmethod
    def shuffle_sequences(sequences: List[str]) -> List[str]:
        """随机打乱序列顺序"""
        shuffled = sequences.copy()
        random.shuffle(shuffled)
        return shuffled

class PartitionManager:
    """分区管理器"""
    
    def __init__(self, chip_rows: int, chip_cols: int, density: PrintDensity):
        self.chip_rows = chip_rows
        self.chip_cols = chip_cols
        self.density = density
    
    def calculate_total_capacity(self) -> int:
        """计算芯片总容量"""
        if self.density == PrintDensity.DPI150:
            return self.chip_rows * self.chip_cols
        elif self.density == PrintDensity.DPI150_PLUS:
            return (self.chip_rows * self.chip_cols + 
                    (self.chip_rows - 1) * (self.chip_cols - 1))
        elif self.density == PrintDensity.DPI300:
            return (2 * self.chip_rows) * (2 * self.chip_cols)
        else:
            raise ValueError(f"不支持的打印密度：{self.density}")
    
    def apply_defect_mask(self, partition_flags: List[str], 
                         defect_data: DefectData) -> List[str]:
        """应用坏孔屏蔽到分区标志"""
        dest_flags = partition_flags.copy()
        
        if self.density == PrintDensity.DPI150:
            divisor = self.chip_rows
        elif self.density == PrintDensity.DPI150_PLUS:
            divisor = self.chip_rows * 2 - 1
        elif self.density == PrintDensity.DPI300:
            divisor = self.chip_rows * 2
        else:
            raise ValueError(f"不支持的打印密度：{self.density}")
        
        # 标记坏孔位置
        for i in range(len(dest_flags)):
            pos = i % divisor + 1  # 芯片上对应的喷孔位置，序号从1开始
            
            is_defect = (pos in defect_data.defect_a_locations or 
                        pos in defect_data.defect_b_locations)
            
            if is_defect:
                dest_flags[i] = "0"  # 标记为无效位置
        
        return dest_flags
    
    def count_valid_positions(self, partition_flags: List[str]) -> Dict[str, int]:
        """计算各分区的有效喷点数量"""
        valid_counts = {}
        
        for flag in partition_flags:
            if flag == "0":
                continue  # 跳过无效位置
            
            if flag in valid_counts:
                valid_counts[flag] += 1
            else:
                valid_counts[flag] = 1
        
        return valid_counts

class ChipLayoutOptimizer:
    """芯片布局优化器"""
    
class SPLOTCore:
    """SPLOT核心处理器"""
    
    def __init__(self):
        self.sequence_processor = SequenceProcessor()
    
    def process_sequences(self, options: ProcessingOptions) -> ProcessingResult:
        """处理DNA序列的主要流程"""
        try:
            console.print("[bold cyan]开始处理DNA序列...[/bold cyan]")
            
            # 1. 加载输入文件
            console.print("\n[yellow]步骤 1/8: 加载输入文件[/yellow]")
            sequence_data = self._load_sequence_data(options)

            # 若未显式指定屏蔽位长度，则自动使用序列最大长度
            if options.mask_length == 0:
                options.mask_length = sequence_data.sequence_length
                console.print(f"[cyan]未指定屏蔽位长度，自动使用序列最大长度: {options.mask_length}[/cyan]")
            
            partition_data = PartitionFileHandler.load_partition_data(options.partition_file)
            defect_data = DefectFileHandler.load_defect_data(options.defect_file)
            
            # 2. 数据验证
            console.print("\n[yellow]步骤 2/8: 数据验证[/yellow]")
            self._validate_data(sequence_data, partition_data, defect_data, options)
            
            # 3. 初始化分区管理器
            console.print("\n[yellow]步骤 3/8: 初始化分区管理器[/yellow]")
            partition_mgr = PartitionManager(options.chip_rows, options.chip_cols, options.density)
            
            # 4. 应用坏孔屏蔽
            console.print("\n[yellow]步骤 4/8: 应用坏孔屏蔽[/yellow]")
            masked_flags = partition_mgr.apply_defect_mask(partition_data.partition_flags, defect_data)
            valid_counts = partition_mgr.count_valid_positions(masked_flags)
            
            # 5. 检查容量匹配
            console.print("\n[yellow]步骤 5/8: 检查容量匹配[/yellow]")
            self._check_capacity(sequence_data, valid_counts, options)
            
            # 6. 扩增和随机化序列
            console.print("\n[yellow]步骤 6/8: 扩增和随机化序列[/yellow]")
            expanded_partitions = self._expand_and_shuffle_sequences(
                sequence_data, valid_counts, options.mask_length, sequence_data.sequence_length
            )
            
            # 7. 填充分区生成最终序列
            console.print("\n[yellow]步骤 7/8: 填充分区生成最终序列[/yellow]")
            final_sequences = self._fill_partitions(masked_flags, expanded_partitions, options)
            
            # 8. 输出文件
            console.print("\n[yellow]步骤 8/8: 输出文件[/yellow]")
            output_files = self._write_output_files(final_sequences, options)
            
            console.print(f"\n[bold green]✅ 处理完成！生成了 {len(final_sequences)} 条打印序列[/bold green]")
            
            return ProcessingResult(
                success=True,
                message=f"成功处理 {len(final_sequences)} 条序列",
                output_files=output_files,
                dest_sequences=final_sequences,
                statistics={
                    "total_sequences": len(final_sequences),
                    "source_sequences": sequence_data.sequence_count,
                    "partitions": len(sequence_data.partition_sequences),
                    "defects": len(defect_data.defect_a_locations) + len(defect_data.defect_b_locations)
                }
            )
            
        except Exception as e:
            error_msg = f"处理失败：{str(e)}"
            console.print(f"[bold red]❌ {error_msg}[/bold red]")
            return ProcessingResult(success=False, message=error_msg)
    
    def _load_sequence_data(self, options: ProcessingOptions) -> SequenceData:
        """加载序列数据"""
        file_ext = os.path.splitext(options.input_file)[1].lower()
        
        if file_ext == '.tsv':
            return SequenceFileHandler.load_sequences_from_tsv(
                options.input_file, options.check_source
            )
        elif file_ext in ['.xlsx', '.xls']:
            return SequenceFileHandler.load_sequences_from_excel(options.input_file)
        else:
            raise ValueError(f"不支持的文件格式：{file_ext}")
    
    def _validate_data(self, seq_data: SequenceData, part_data: PartitionData, 
                      defect_data: DefectData, options: ProcessingOptions):
        """验证数据完整性和匹配性"""
        partition_mgr = PartitionManager(options.chip_rows, options.chip_cols, options.density)
        total_capacity = partition_mgr.calculate_total_capacity()
        
        # 检查分区容量与芯片容量是否匹配
        if len(part_data.partition_flags) != total_capacity:
            raise ValueError(
                f"分区掩模总容量与芯片总容量不匹配！\n"
                f"分区掩模容量：{len(part_data.partition_flags)}\n"
                f"芯片总容量：{total_capacity}"
            )
        
        # 检查屏蔽长度
        if options.mask_length > seq_data.sequence_length:
            raise ValueError(
                f"屏蔽位数据长度({options.mask_length})不能大于源序列长度({seq_data.sequence_length})"
            )
        
        console.print(f"[green]数据验证通过 ✓[/green]")
    
    def _check_capacity(self, seq_data: SequenceData, valid_counts: Dict[str, int], 
                       options: ProcessingOptions):
        """检查分区容量是否满足序列需求"""
        source_partitions = set(seq_data.partition_sequences.keys())
        for partition, sequences in seq_data.partition_sequences.items():
            if partition not in valid_counts:
                raise ValueError(f"在芯片分区数据中没有找到源序列的分区 {partition}")
            
            if len(sequences) > valid_counts[partition]:
                raise ValueError(
                    f"{partition}分区容量不足！\n"
                    f"有效喷点数量：{valid_counts[partition]}\n"
                    f"需要序列数量：{len(sequences)}"
                )

        extra_partitions = set(valid_counts.keys()) - source_partitions
        if extra_partitions:
            raise ValueError(
                f"芯片分区数据包含源序列未提供的分区：{', '.join(sorted(extra_partitions))}"
            )
        
        console.print(f"[green]容量检查通过 ✓[/green]")
    
    def _expand_and_shuffle_sequences(self, seq_data: SequenceData, valid_counts: Dict[str, int],
                                    mask_length: int, seq_length: int) -> Dict[str, List[str]]:
        """扩增和随机化各分区序列"""
        # 创建虚拟序列
        dummy_seq = "0" * (seq_length - mask_length) + "0" * mask_length
        
        expanded_partitions = {}
        
        for partition, sequences in tqdm(seq_data.partition_sequences.items(), 
                                       desc="扩增序列"):
            # 扩增序列
            expanded = self.sequence_processor.extend_sequences(
                sequences, valid_counts[partition], dummy_seq
            )
            
            # 随机化
            shuffled = self.sequence_processor.shuffle_sequences(expanded)
            expanded_partitions[partition] = shuffled
        
        return expanded_partitions
    
    def _fill_partitions(self, masked_flags: List[str], expanded_partitions: Dict[str, List[str]],
                        options: ProcessingOptions) -> List[str]:
        """填充分区生成最终序列"""
        final_sequences = []
        partition_indices = {partition: 0 for partition in expanded_partitions.keys()}
        
        # 创建虚拟序列
        if expanded_partitions:
            first_partition = list(expanded_partitions.keys())[0]
            if expanded_partitions[first_partition]:
                seq_length = len(expanded_partitions[first_partition][0])
                dummy_seq = "0" * seq_length
            else:
                dummy_seq = "0" * options.mask_length
        else:
            dummy_seq = "0" * options.mask_length
        
        for flag in tqdm(masked_flags, desc="填充分区"):
            if flag == "0":
                final_sequences.append(dummy_seq)
            else:
                if flag in expanded_partitions and partition_indices[flag] < len(expanded_partitions[flag]):
                    final_sequences.append(expanded_partitions[flag][partition_indices[flag]])
                    partition_indices[flag] += 1
                else:
                    final_sequences.append(dummy_seq)
        
        return final_sequences
    
    def _write_output_files(self, sequences: List[str], options: ProcessingOptions) -> List[str]:
        """输出文件"""
        output_files = []
        base_name = os.path.splitext(os.path.basename(options.input_file))[0]
        output_dir = options.output_path if os.path.isdir(options.output_path) else os.path.dirname(options.output_path)
        if not output_dir:
            output_dir = "."
        
        # 生成输出文件名
        density_suffix = {
            PrintDensity.DPI150: "_150DPI_out",
            PrintDensity.DPI150_PLUS: "_150DPI_PLUS_out", 
            PrintDensity.DPI300: "_300DPI_out"
        }
        
        output_file = os.path.join(output_dir, f"{base_name}{density_suffix[options.density]}.txt")
        
        # 输出主序列文件
        OutputFileHandler.write_sequences(sequences, output_file)
        output_files.append(output_file)
        
        # 输出图案文件（如果需要）
        if options.generate_pattern:
            pattern_file = os.path.join(output_dir, "print_pattern.txt")
            OutputFileHandler.write_pattern_file(
                sequences,
                pattern_file,
                options.chip_rows,
                options.chip_cols,
                options.density.value,
                seq_range=options.pattern_seq_range
            )
            output_files.append(pattern_file)
        
        return output_files
