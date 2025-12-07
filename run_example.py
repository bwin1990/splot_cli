#!/usr/bin/env python3
"""
SPLOT Python CLI 示例运行脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """运行示例"""
    print("🧬 SPLOT Python CLI 示例运行")
    print("=" * 50)
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    # 检查示例文件
    example_files = {
        'sequences': project_root / 'examples' / 'sample_sequences.tsv',
        'partition': project_root / 'examples' / 'sample_partition.txt', 
        'defects': project_root / 'examples' / 'sample_defects.txt'
    }
    
    for name, file_path in example_files.items():
        if not file_path.exists():
            print(f"❌ 示例文件不存在: {file_path}")
            return 1
        print(f"✅ {name}: {file_path}")
    
    # 创建输出目录
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    print(f"📁 输出目录: {output_dir}")
    
    # 构建命令
    cmd = [
        sys.executable, '-m', 'splot_cli.main',
        '--input', str(example_files['sequences']),
        '--partition', str(example_files['partition']),
        '--defect', str(example_files['defects']),
        '--output', str(output_dir),
        '--rows', '25',  # 使用较小的尺寸用于示例
        '--cols', '5',
        '--density', 'DPI150',
        '--mask-length', '50',
        '--pattern',
        '--verbose'
    ]
    
    print("\n🚀 执行命令:")
    print(' '.join(cmd))
    print()
    
    # 切换到项目目录
    os.chdir(project_root)
    
    # 执行命令
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ 示例运行成功! 退出码: {result.returncode}")
        print(f"📂 查看输出文件: {output_dir}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 示例运行失败! 退出码: {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        return 1

if __name__ == '__main__':
    sys.exit(main())
