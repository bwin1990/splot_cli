"""
文件处理模块
"""
import pandas as pd
import os
from typing import Dict, List, Tuple
from .models import SequenceData, PartitionData, DefectData, validate_sequence
from rich.console import Console
from tqdm import tqdm

console = Console()

class FileHandler:
    """文件处理器基类"""
    
    @staticmethod
    def read_text_file(file_path: str) -> List[str]:
        """读取文本文件的所有行"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except UnicodeDecodeError:
            # 尝试GBK编码
            with open(file_path, 'r', encoding='gbk') as f:
                return [line.strip() for line in f.readlines() if line.strip()]

class SequenceFileHandler(FileHandler):
    """序列文件处理器"""
    
    @classmethod
    def load_sequences_from_tsv(cls, file_path: str, check_source: bool = True) -> SequenceData:
        """从TSV文件加载分区序列数据，支持 Partition/ID 列"""
        try:
            console.print(f"[cyan]正在读取序列文件：{file_path}[/cyan]")
            
            # 使用pandas读取TSV文件
            df = pd.read_csv(file_path, sep='\t')
            
            if 'Seq' not in df.columns:
                raise ValueError("在序列表单文件的表头中未找到Seq列！")
            
            # 分区字段解析，优先使用 Partition，其次 ID，再次首列
            partition_col = None
            if 'Partition' in df.columns:
                partition_col = 'Partition'
            elif 'ID' in df.columns:
                partition_col = 'ID'
            else:
                partition_col = df.columns[0]
            
            partition_sequences = {}
            all_sequences = []
            
            # 使用tqdm显示进度
            for idx, row in tqdm(df.iterrows(), total=len(df), desc="处理序列"):
                key_raw = str(row[partition_col]).strip()
                # 若使用 ID 列，则按 "-" 分隔后取第一段作为分区索引，
                # 以支持更多类型的分区编号（例如 "P01-001" -> "P01"）
                if partition_col == 'ID':
                    key = key_raw.split('-', 1)[0]
                else:
                    key = key_raw
                seq = str(row['Seq'])
                
                # 序列合法性检查
                if check_source and not validate_sequence(seq):
                    raise ValueError(f"检测到源序列中含有非法字符，序列：{seq}")
                
                if key not in partition_sequences:
                    partition_sequences[key] = []
                
                partition_sequences[key].append(seq)
                all_sequences.append(seq)
            
            # 计算序列长度（取最长序列的长度）
            max_length = max(len(seq) for seq in all_sequences) if all_sequences else 0
            
            console.print(f"[green]成功加载 {len(all_sequences)} 条序列，分区数量：{len(partition_sequences)}[/green]")
            console.print(f"  最大序列长度: {max_length}")
            
            return SequenceData(
                sequences=all_sequences,
                partition_sequences=partition_sequences,
                sequence_length=max_length,
                sequence_count=len(all_sequences)
            )
            
        except Exception as e:
            console.print(f"[red]加载序列文件失败：{str(e)}[/red]")
            raise
    
    @classmethod
    def load_sequences_from_excel(cls, file_path: str, sheet_name: str = "flank") -> SequenceData:
        """从Excel文件加载序列数据（兼容旧版本）"""
        try:
            console.print(f"[cyan]正在读取Excel文件：{file_path}[/cyan]")
            
            # 读取指定工作表
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            if 'Seq' not in df.columns:
                raise ValueError("在序列表单文件的表头中未找到Seq列！")
            
            partition_sequences = {}
            all_sequences = []

            # 分区字段解析，优先使用 Partition，其次 ID，再次首列
            if 'Partition' in df.columns:
                partition_col = 'Partition'
            elif 'ID' in df.columns:
                partition_col = 'ID'
            else:
                partition_col = df.columns[0]

            for idx, row in tqdm(df.iterrows(), total=len(df), desc="处理Excel序列"):
                key_raw = str(row[partition_col]).strip()
                if partition_col == 'ID':
                    key = key_raw.split('-', 1)[0]
                else:
                    key = key_raw
                seq = str(row['Seq'])
                
                if key not in partition_sequences:
                    partition_sequences[key] = []
                
                partition_sequences[key].append(seq)
                all_sequences.append(seq)
            
            max_length = max(len(seq) for seq in all_sequences) if all_sequences else 0
            
            console.print(f"[green]成功加载 {len(all_sequences)} 条序列[/green]")
            console.print(f"  最大序列长度: {max_length}")
            
            return SequenceData(
                sequences=all_sequences,
                partition_sequences=partition_sequences,
                sequence_length=max_length,
                sequence_count=len(all_sequences)
            )
            
        except Exception as e:
            console.print(f"[red]加载Excel文件失败：{str(e)}[/red]")
            raise

class PartitionFileHandler(FileHandler):
    """分区文件处理器"""
    
    @classmethod
    def load_partition_data(cls, file_path: str) -> PartitionData:
        """加载分区掩模数据"""
        try:
            console.print(f"[cyan]正在读取分区文件：{file_path}[/cyan]")
            
            partition_flags = cls.read_text_file(file_path)
            
            if not partition_flags:
                raise ValueError("分区文件为空或格式错误")
            
            # 计算分区标志长度
            flag_length = max(len(flag) for flag in partition_flags)
            
            # 计算分区数量（排除"0"标志）
            unique_flags = set(partition_flags)
            partition_count = len(unique_flags) - (1 if "0" in unique_flags else 0)
            
            console.print(f"[green]成功加载分区数据，总容量：{len(partition_flags)}，分区数：{partition_count}[/green]")
            
            return PartitionData(
                partition_flags=partition_flags,
                partition_count=partition_count,
                flag_length=flag_length
            )
            
        except Exception as e:
            console.print(f"[red]加载分区文件失败：{str(e)}[/red]")
            raise

class DefectFileHandler(FileHandler):
    """坏孔文件处理器"""
    
    @classmethod
    def load_defect_data(cls, file_path: str) -> DefectData:
        """加载坏孔屏蔽数据"""
        try:
            console.print(f"[cyan]正在读取坏孔文件：{file_path}[/cyan]")
            
            defect_lines = cls.read_text_file(file_path)
            defect_a_locations = []
            defect_b_locations = []
            
            for line in defect_lines:
                # 解析坏孔位置，支持逗号、空格、中文逗号分隔
                positions = []
                for sep in [',', ' ', '，']:
                    if sep in line:
                        positions = [pos.strip() for pos in line.split(sep) if pos.strip()]
                        break
                else:
                    positions = [line.strip()] if line.strip() else []
                
                for pos_str in positions:
                    try:
                        pos = int(pos_str)
                        if pos < 319:  # A线坏孔
                            defect_a_locations.append(pos)
                        else:  # B线坏孔
                            defect_b_locations.append(pos)
                    except ValueError:
                        console.print(f"[yellow]警告：忽略无效的坏孔位置：{pos_str}[/yellow]")
                        continue
            
            console.print(f"[green]成功加载坏孔数据，A线：{len(defect_a_locations)}个，B线：{len(defect_b_locations)}个[/green]")
            
            return DefectData(
                defect_a_locations=defect_a_locations,
                defect_b_locations=defect_b_locations
            )
            
        except Exception as e:
            console.print(f"[red]加载坏孔文件失败：{str(e)}[/red]")
            raise

class ChipLayoutOptimizer:
    """芯片布局优化器，用于生成打印图案"""

    def __init__(self, chip_rows: int, chip_cols: int):
        self.chip_rows = chip_rows
        self.chip_cols = chip_cols

    def generate_pattern_content(self, sequences: List[str], density: str,
                                 seq_range: Tuple[int, int] = None) -> str:
        """生成完整图案文件内容"""
        if seq_range is None:
            from_pos, to_pos = 1, len(sequences[0]) if sequences else 1
        else:
            from_pos, to_pos = seq_range

        display_length = to_pos - from_pos + 1
        if density == "DPI150":
            lines = self._generate_150dpi_pattern(sequences, from_pos, display_length)
        elif density == "DPI150_PLUS":
            lines = self._generate_150dpi_plus_pattern(sequences, from_pos, display_length)
        elif density == "DPI300":
            lines = self._generate_300dpi_pattern(sequences, from_pos, display_length)
        else:
            raise ValueError(f"不支持的打印密度：{density}")

        return '\n'.join(lines)

    def _generate_150dpi_pattern(self, sequences: List[str], from_pos: int, length: int) -> List[str]:
        lines = []
        for i in range(self.chip_rows):
            line_parts = []
            for j in range(self.chip_cols):
                pos = j * self.chip_rows + self.chip_rows - i - 1
                if pos < len(sequences):
                    seq_part = sequences[pos][from_pos-1:from_pos-1+length]
                    line_parts.append(self._format_output(seq_part, length + 1))
                else:
                    line_parts.append(self._format_output("0" * length, length + 1))
            lines.append(''.join(line_parts))
        return lines

    def _generate_150dpi_plus_pattern(self, sequences: List[str], from_pos: int, length: int) -> List[str]:
        lines = []
        placeholder = " " * length

        for i in range(self.chip_rows * 2 - 1):
            line_parts = []
            for j in range(self.chip_cols * 2 - 1):
                if (i % 2 == 0 and j % 2 == 0) or (i % 2 == 1 and j % 2 == 1):
                    if j % 2 == 0:
                        pos = (j // 2) * (self.chip_rows * 2 - 1) + self.chip_rows - i // 2 - 1
                    else:
                        pos = (j // 2) * (self.chip_rows * 2 - 1) + self.chip_rows + self.chip_rows - 1 - i // 2 - 1

                    if pos < len(sequences):
                        seq_part = sequences[pos][from_pos-1:from_pos-1+length]
                        line_parts.append(self._format_output(seq_part, length + 1))
                    else:
                        line_parts.append(self._format_output("0" * length, length + 1))
                else:
                    line_parts.append(self._format_output(placeholder, length + 1))
            lines.append(''.join(line_parts))
        return lines

    def _generate_300dpi_pattern(self, sequences: List[str], from_pos: int, length: int) -> List[str]:
        lines = []
        for i in range(self.chip_rows * 2):
            line_parts = []
            for j in range(self.chip_cols * 2):
                pos = (2 * self.chip_rows) * (j + 1) - i - 1
                if pos < len(sequences):
                    seq_part = sequences[pos][from_pos-1:from_pos-1+length]
                    line_parts.append(self._format_output(seq_part, length + 1))
                else:
                    line_parts.append(self._format_output("0" * length, length + 1))
            lines.append(''.join(line_parts))
        return lines

    def _format_output(self, text: str, width: int) -> str:
        if len(text) >= width:
            return text[:width]
        return ' ' * (width - len(text)) + text

class OutputFileHandler:
    """输出文件处理器"""
    
    @staticmethod
    def write_sequences(sequences: List[str], file_path: str):
        """输出序列到文件"""
        try:
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, seq in enumerate(sequences):
                    if i == len(sequences) - 1:
                        f.write(seq)  # 最后一行不加换行
                    else:
                        f.write(seq + '\n')
            
            console.print(f"[green]成功输出序列文件：{file_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]输出序列文件失败：{str(e)}[/red]")
            raise
    
    @staticmethod
    def write_pattern_file(sequences: List[str], file_path: str, 
                          chip_rows: int, chip_cols: int, 
                          density: str, seq_range: Tuple[int, int] = None):
        """输出完整图案文件"""
        try:
            optimizer = ChipLayoutOptimizer(chip_rows, chip_cols)
            content = optimizer.generate_pattern_content(sequences, density, seq_range)

            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            console.print(f"[green]成功输出图案文件：{file_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]输出图案文件失败：{str(e)}[/red]")
            raise
