"""
SPLOT CLI 主入口
"""
import click
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# 支持直接以脚本方式运行
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from splot_cli.models import ProcessingOptions, PrintDensity, validate_file_exists
    from splot_cli.core import SPLOTCore
    from splot_cli.file_handlers import (
        SequenceFileHandler,
        PartitionFileHandler,
        DefectFileHandler,
    )
else:
    from .models import ProcessingOptions, PrintDensity, validate_file_exists
    from .core import SPLOTCore
    from .file_handlers import (
        SequenceFileHandler,
        PartitionFileHandler,
        DefectFileHandler,
    )

console = Console()

def print_banner():
    """打印程序标题"""
    banner = """
[bold cyan]
 ███████╗██████╗ ██╗      ██████╗ ████████╗
 ██╔════╝██╔══██╗██║     ██╔═══██╗╚══██╔══╝
 ███████╗██████╔╝██║     ██║   ██║   ██║   
 ╚════██║██╔═══╝ ██║     ██║   ██║   ██║   
 ███████║██║     ███████╗╚██████╔╝   ██║   
 ╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝   
[/bold cyan]
[bold white]DNA打印序列分区排版优化工具 v2.1.4 (Python版)[/bold white]
[dim]Sequence Partition Layout Optimization Tool[/dim]
"""
    console.print(Panel(banner, style="cyan"))

@click.command()
@click.option('--input', '-i', 'input_file',
              type=click.Path(exists=True), help='输入序列文件 (TSV/Excel)')
@click.option('--partition', '-p', 'partition_file',
              type=click.Path(exists=True), help='分区掩模文件')
@click.option('--defect', '-d', 'defect_file',
              type=click.Path(exists=True), help='坏孔屏蔽文件')
@click.option('--output', '-o', 'output_path', default="output", show_default=True,
              help='输出路径 (文件或目录)')
@click.option('--rows', default=318, type=int,
              help='芯片行数 (默认: 318)')
@click.option('--cols', default=540, type=int, 
              help='芯片列数 (默认: 540)')
@click.option('--density', type=click.Choice(['DPI150', 'DPI150_PLUS', 'DPI300']),
              default='DPI300', help='打印密度 (默认: DPI300)')
@click.option('--mask-length', default=0, type=int,
              help='屏蔽位数据长度 (默认: 自动使用序列最大长度)')
@click.option('--pattern/--no-pattern', default=False,
              help='是否生成图案文件')
@click.option('--check-source/--no-check-source', default=True,
              help='是否检查源序列合法性')
@click.option('--verbose', '-v', is_flag=True,
              help='详细输出模式')
def run(input_file, partition_file, defect_file, output_path, rows, cols, 
        density, mask_length, pattern, check_source, verbose):
    """
    SPLOT - DNA打印序列分区排版优化工具
    
    示例用法:
    
    \b
    # 基本用法
    splot -i sequences.tsv -p partition.txt -d defect.txt -o output/
    
    \b
    # 完整参数
    splot --input sequences.tsv \\
          --partition partition.txt \\
          --defect defect.txt \\
          --output result/ \\
          --rows 318 --cols 540 \\
          --density DPI300 \\
          --mask-length 0 \\  # 0 表示自动使用最大序列长度
          --pattern \\
          --check-source
    """
    # 用于控制图案文件中显示的碱基区间（起止位点，1-based）
    pattern_seq_range = None

    if not verbose:
        print_banner()
    
    # 如果缺少必需文件，进入交互式选择模式
    interactive = not (input_file and partition_file and defect_file)
    try:
        if interactive:
            console.print("[cyan]检测到未提供必需文件，进入交互式选择模式[/cyan]")
            input_file = input_file or _choose_file("请选择序列文件 (TSV/Excel)", [("TSV/Excel", "*.tsv *.xlsx *.xls"), ("所有文件", "*.*")])
            seq_data = _show_sequence_debug(input_file, check_source)
            partition_file = partition_file or _choose_file("请选择分区掩模文件 (TXT)", [("分区文件", "*.txt"), ("所有文件", "*.*")])
            _show_partition_debug(partition_file)
            defect_file = defect_file or _choose_file("请选择坏孔屏蔽文件 (TXT)", [("坏孔文件", "*.txt"), ("所有文件", "*.*")])
            _show_defect_debug(defect_file)
            # 交互确认其它参数
            rows = click.prompt("芯片行数", default=rows, type=int)
            cols = click.prompt("芯片列数", default=cols, type=int)
            density = click.prompt("打印密度", default=density, type=click.Choice(['DPI150', 'DPI150_PLUS', 'DPI300']))
            # 默认屏蔽位长度使用当前序列文件中的最大长度
            default_mask_length = seq_data.sequence_length if seq_data else mask_length
            mask_length = click.prompt("屏蔽位数据长度", default=default_mask_length, type=int)
            pattern = click.confirm("是否生成图案文件", default=pattern)
            if pattern:
                # 询问用户在图案文件中希望显示第几位碱基
                base_pos = click.prompt("图案文件中用于表示喷点的碱基位置（1为第一位）",
                                        default=1, type=int)
                if base_pos < 1:
                    console.print("[yellow]输入位置小于 1，已自动调整为 1[/yellow]")
                    base_pos = 1
                pattern_seq_range = (base_pos, base_pos)
            check_source = click.confirm("是否检查源序列合法性", default=check_source)
            if not output_path:
                output_path = click.prompt("输出路径 (文件或目录)", default="output")
        
        # 验证输入文件
        if not validate_file_exists(input_file):
            console.print(f"[red]错误：输入文件不存在: {input_file}[/red]")
            sys.exit(1)
        
        if not validate_file_exists(partition_file):
            console.print(f"[red]错误：分区文件不存在: {partition_file}[/red]")
            sys.exit(1)
            
        if not validate_file_exists(defect_file):
            console.print(f"[red]错误：坏孔文件不存在: {defect_file}[/red]")
            sys.exit(1)
        
        # 确保输出目录存在
        output_dir = output_path if os.path.isdir(output_path) else os.path.dirname(output_path)
        if not output_dir:
            output_dir = "."
        os.makedirs(output_dir, exist_ok=True)
        
        # 显示处理参数
        if verbose:
            show_processing_info(input_file, partition_file, defect_file, 
                                output_path, rows, cols, density, mask_length, 
                                pattern, check_source)
        
        # 创建处理选项
        options = ProcessingOptions(
            input_file=input_file,
            partition_file=partition_file, 
            defect_file=defect_file,
            output_path=output_path,
            chip_rows=rows,
            chip_cols=cols,
            density=PrintDensity(density),
            mask_length=mask_length,
            generate_pattern=pattern,
            check_source=check_source,
            pattern_seq_range=pattern_seq_range
        )
        
        # 执行处理
        core = SPLOTCore()
        result = core.process_sequences(options)
        
        if result.success:
            show_success_summary(result)
            sys.exit(0)
        else:
            console.print(f"[red]处理失败: {result.message}[/red]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]用户中断操作[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]发生未知错误: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

def _choose_file(title: str, filetypes):
    """通过图形弹窗选择文件，失败则回退命令行输入"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        root.destroy()
        if not file_path:
            file_path = click.prompt(f"{title} (输入路径)", type=str)
        return file_path
    except Exception:
        # 无图形环境或其他错误，退回命令行
        return click.prompt(f"{title} (输入路径)", type=str)

def _show_sequence_debug(path: str, check_source: bool):
    """加载序列文件并输出调试信息"""
    data = SequenceFileHandler.load_sequences_from_tsv(path, check_source=check_source) if path.lower().endswith(".tsv") else SequenceFileHandler.load_sequences_from_excel(path)
    console.print(f"[green]序列文件已加载: {path}[/green]")
    console.print(f"  总序列数: {data.sequence_count}")
    console.print(f"  最长序列长度: {data.sequence_length}")
    console.print(f"  分区数: {len(data.partition_sequences)}")
    return data

def _show_partition_debug(path: str):
    data = PartitionFileHandler.load_partition_data(path)
    console.print(f"[green]分区文件已加载: {path}[/green]")
    console.print(f"  总容量: {len(data.partition_flags)}  分区数量: {data.partition_count}")

def _show_defect_debug(path: str):
    data = DefectFileHandler.load_defect_data(path)
    console.print(f"[green]坏孔文件已加载: {path}[/green]")
    console.print(f"  A线坏孔: {len(data.defect_a_locations)}  B线坏孔: {len(data.defect_b_locations)}")

def show_processing_info(input_file, partition_file, defect_file, output_path,
                        rows, cols, density, mask_length, pattern, check_source):
    """显示处理信息"""
    table = Table(title="处理参数", show_header=True, header_style="bold magenta")
    table.add_column("参数", style="cyan")
    table.add_column("值", style="green")
    
    table.add_row("输入文件", input_file)
    table.add_row("分区文件", partition_file)
    table.add_row("坏孔文件", defect_file)
    table.add_row("输出路径", output_path)
    table.add_row("芯片尺寸", f"{rows} x {cols}")
    table.add_row("打印密度", density)
    table.add_row("屏蔽长度", str(mask_length))
    table.add_row("生成图案", "是" if pattern else "否")
    table.add_row("检查源序列", "是" if check_source else "否")
    
    console.print(table)
    console.print()

def show_success_summary(result):
    """显示成功总结"""
    console.print(Panel.fit(
        f"[bold green]✅ 处理成功完成![/bold green]\n\n"
        f"[cyan]统计信息:[/cyan]\n"
        f"• 源序列数量: {result.statistics.get('source_sequences', 0)}\n"
        f"• 生成序列数量: {result.statistics.get('total_sequences', 0)}\n"
        f"• 分区数量: {result.statistics.get('partitions', 0)}\n"
        f"• 坏孔数量: {result.statistics.get('defects', 0)}\n\n"
        f"[cyan]输出文件:[/cyan]\n" +
        "\n".join(f"• {file}" for file in result.output_files),
        title="[bold]处理结果[/bold]",
        border_style="green"
    ))

@click.group(invoke_without_command=True,
             context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
@click.option('--version', is_flag=True, help='显示版本信息')
def cli(ctx, version):
    """SPLOT CLI 工具集"""
    if version:
        console.print("[bold cyan]SPLOT v2.1.4 (Python版)[/bold cyan]")
        console.print("DNA打印序列分区排版优化工具")
        sys.exit(0)
    
    if ctx.invoked_subcommand is None:
        # 默认执行主处理命令，剥离 group 级参数
        params = ctx.params.copy()
        params.pop("version", None)
        ctx.invoke(run, **params)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def validate(input_file):
    """验证输入文件格式"""
    try:
        from .file_handlers import SequenceFileHandler
        
        console.print(f"[cyan]正在验证文件: {input_file}[/cyan]")
        
        file_ext = os.path.splitext(input_file)[1].lower()
        
        if file_ext == '.tsv':
            data = SequenceFileHandler.load_sequences_from_tsv(input_file, check_source=True)
        elif file_ext in ['.xlsx', '.xls']:
            data = SequenceFileHandler.load_sequences_from_excel(input_file)
        else:
            console.print(f"[red]不支持的文件格式: {file_ext}[/red]")
            sys.exit(1)
        
        console.print(f"[green]✅ 文件验证通过![/green]")
        console.print(f"序列数量: {data.sequence_count}")
        console.print(f"序列长度: {data.sequence_length}")
        console.print(f"分区数量: {len(data.partition_sequences)}")
        
        for partition, seqs in data.partition_sequences.items():
            console.print(f"  分区 {partition}: {len(seqs)} 条序列")
            
    except Exception as e:
        console.print(f"[red]验证失败: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
def info():
    """显示软件信息"""
    print_banner()
    
    info_text = """
[bold]功能特性:[/bold]
• 支持TSV和Excel格式的序列文件
• 多种打印密度支持 (150DPI, 150DPI_PLUS, 300DPI)
• 智能分区管理和坏孔屏蔽
• 序列扩增和随机化算法
• 可视化图案文件生成
• 跨平台支持 (Windows, Linux, macOS)

[bold]支持的文件格式:[/bold]
• 序列文件: .tsv, .xlsx, .xls
• 分区文件: .txt
• 坏孔文件: .txt

[bold]使用示例:[/bold]
splot -i sequences.tsv -p partition.txt -d defect.txt -o output/
"""
    
    console.print(Panel(info_text, title="[bold]关于 SPLOT[/bold]", border_style="blue"))

cli.add_command(run, name="run")

# 保持向后兼容，允许直接调用 main 作为入口
main = cli

if __name__ == '__main__':
    cli()
