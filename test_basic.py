#!/usr/bin/env python3
"""
基础功能测试
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, '.')

def test_imports():
    """测试导入"""
    print("测试模块导入...")
    
    try:
        from splot_cli.models import ProcessingOptions, PrintDensity, SequenceData
        print("✅ models 模块导入成功")
        
        from splot_cli.file_handlers import SequenceFileHandler, PartitionFileHandler, DefectFileHandler
        print("✅ file_handlers 模块导入成功")
        
        from splot_cli.core import SPLOTCore, SequenceProcessor
        print("✅ core 模块导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基础功能"""
    print("\n测试基础功能...")
    
    try:
        from splot_cli.models import ProcessingOptions, PrintDensity
        from splot_cli.core import SequenceProcessor
        
        # 测试序列处理器
        processor = SequenceProcessor()
        
        # 测试扩增功能
        test_seqs = ["ATCG", "GCTA", "CGAT"]
        extended = processor.extend_sequences(test_seqs, 10, "0000")
        print(f"✅ 序列扩增测试通过: {len(test_seqs)} -> {len(extended)}")
        
        # 测试随机化
        shuffled = processor.shuffle_sequences(extended)
        print(f"✅ 序列随机化测试通过: {len(shuffled)} 条序列")
        
        # 测试处理选项
        options = ProcessingOptions(
            input_file="test.tsv",
            partition_file="test.txt", 
            defect_file="test.txt",
            output_path="output/",
            density=PrintDensity.DPI150
        )
        print(f"✅ 处理选项创建成功: {options.density}")
        
        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_validation():
    """测试文件验证"""
    print("\n测试文件验证...")
    
    try:
        from splot_cli.models import validate_sequence
        
        # 测试合法序列
        valid_seqs = ["ATCG", "atcg", "ATCG0000", "000ATCG"]
        for seq in valid_seqs:
            if validate_sequence(seq):
                print(f"✅ 合法序列: {seq}")
            else:
                print(f"❌ 序列验证失败: {seq}")
                return False
        
        # 测试非法序列
        invalid_seqs = ["ATCGX", "123", "ATCG-"]
        for seq in invalid_seqs:
            if not validate_sequence(seq):
                print(f"✅ 正确识别非法序列: {seq}")
            else:
                print(f"❌ 应该识别为非法序列: {seq}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 验证测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧬 SPLOT Python CLI 基础功能测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_basic_functionality, 
        test_file_validation
    ]
    
    passed = 0
    for test_func in tests:
        if test_func():
            passed += 1
        print()
    
    print(f"测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️ 部分测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
