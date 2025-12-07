from setuptools import setup, find_packages

setup(
    name="splot-python",
    version="2.1.4",
    description="DNA打印序列分区排版优化工具 Python版本",
    author="SPLOT Team",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5.0",
        "openpyxl>=3.0.0", 
        "numpy>=1.21.0",
        "click>=8.0.0",
        "pydantic>=1.10.0",
        "rich>=12.0.0",
        "tqdm>=4.64.0"
    ],
    entry_points={
        'console_scripts': [
            'splot=splot_cli.main:cli',
        ],
    },
    python_requires=">=3.8",
)
