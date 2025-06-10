import os
from pathlib import Path
import json
import logging

# === 配置输出路径 ===
PROJECT_ROOT = Path("E:/Qwen_V2.5_CHN2LaTeX")
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_FILE = DATA_DIR / "raw\\raw_data.jsonl"
DATAWASH_LOG_FILE = DATA_DIR / "processeed\\datawash.log"
DATASPLITS_NO_CHN_FILE = DATA_DIR / "splits\\data_splits_NO_CHN.jsonl"
# === 全局常量初始化(暂时没有) ===
# === 全局第三方库/第三方包初始化 ===


# === 全局变量初始化 ===
processNotes = None
underProcessNote = None
resultNote = None

# === 配置日志系统 ===
def setup_logger():
    """配置日志系统，同时输出到文件和终端"""
    logger = logging.getLogger("data_wash")
    logger.setLevel(logging.INFO)
    
    # 文件处理器（追加模式）
    file_handler = logging.FileHandler(DATAWASH_LOG_FILE, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
logger = setup_logger()

# === LaTeX————>中文映射表保存 ===
# === 格式：{"LaTeX":"**LaTeX格式公式**","CHINESE":"**中文字串(暂时用None代替)**"} ==
def save_data(data, filename):
    """保存数据到JSONL文件（追加模式）"""
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            for item in data:
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + '\n')
        logger.info(f"成功保存 {len(data)} 条数据到 {filename}")
    except Exception as e:
        logger.error(f"保存数据失败: {str(e)}")

# === 定义数据录入格式 ===
def dataInputJsonl(latexFormular)
        
# === 主函数 ===
# 打开文件"raw_data.jsonl"
# TODO:这里先使用raw_data_Example.jsonl作为测试对象，避免使用raw_data.jsonl污染源文件。等到真正要处理时在手动更改回Raw_data.jsonl
#      要更改路径，参考上文“配置输出路径”下的路径地址。
with open ("E:\Qwen_V2.5_CHN2LaTeX\data\raw_data_Example.jsonl","r",encoding="utf-8") as f:
    for line in f:
        underProcessNote = json.loads(line)
        resultNote = underProcessNote["latex"]
        
        
        