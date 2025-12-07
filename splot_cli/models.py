"""
数据模型定义
"""
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, field_validator
import re

class PrintDensity(Enum):
    """打印密度枚举"""
    DPI150 = "DPI150"
    DPI150_PLUS = "DPI150_PLUS" 
    DPI300 = "DPI300"

class ProcessingOptions(BaseModel):
    """处理选项配置"""
    input_file: str
    partition_file: str
    defect_file: str
    output_path: str
    chip_rows: int = 318
    chip_cols: int = 540
    density: PrintDensity = PrintDensity.DPI300
    # mask_length = 0 表示自动使用序列最大长度
    mask_length: int = 0
    generate_pattern: bool = False
    check_source: bool = True
    # 图案文件中用于显示的序列区间（起止位点，1-based，闭区间），默认 None 表示使用整条序列
    pattern_seq_range: Optional[Tuple[int, int]] = None
    
    @field_validator('chip_rows', 'chip_cols')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError('芯片行列数必须为正数')
        return v
    
    @field_validator('mask_length')
    def validate_mask_length(cls, v):
        if v < 0:
            raise ValueError('屏蔽长度不能为负数')
        return v

class SequenceData(BaseModel):
    """序列数据模型"""
    sequences: List[str]
    partition_sequences: Dict[str, List[str]]
    sequence_length: int
    sequence_count: int

class PartitionData(BaseModel):
    """分区数据模型"""
    partition_flags: List[str]
    partition_count: int
    flag_length: int

class DefectData(BaseModel):
    """坏孔数据模型"""
    defect_a_locations: List[int]
    defect_b_locations: List[int]
    
    @field_validator('defect_a_locations', 'defect_b_locations')
    def validate_locations(cls, v):
        # 确保位置编号都是正数
        for loc in v:
            if loc <= 0:
                raise ValueError('坏孔位置编号必须为正数')
        return sorted(v)

class ProcessingResult(BaseModel):
    """处理结果模型"""
    success: bool
    message: str
    output_files: List[str] = []
    dest_sequences: Optional[List[str]] = None
    statistics: Optional[Dict[str, int]] = None

def validate_sequence(seq: str) -> bool:
    """验证DNA序列的合法性"""
    if not seq:
        return False
    
    # 只允许ATCG和0字符
    pattern = re.compile(r'^[ATCGatcg0]+$')
    return bool(pattern.match(seq))

def validate_file_exists(file_path: str) -> bool:
    """验证文件是否存在"""
    import os
    return os.path.exists(file_path) and os.path.isfile(file_path)
