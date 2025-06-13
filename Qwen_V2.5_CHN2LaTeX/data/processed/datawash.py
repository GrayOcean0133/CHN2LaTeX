import os
from pathlib import Path
import json
import logging
import hashlib
from collections import defaultdict
import uuid  # 导入 uuid 库用于生成唯一 ID

# ================== 配置参数 ==================
PROJECT_ROOT = Path("E:/Qwen_V2.5_CHN2LaTeX")
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_FILE = DATA_DIR / "raw/raw_data.jsonl"
DATAWASH_LOG_FILE = DATA_DIR / "processed/datawash.log"
DATASPLITS_FILE = DATA_DIR / "splits/data_splits_NO_CHN.jsonl"
ERROR_LOG_FILE = DATA_DIR / "splits/error_log.jsonl"
DUPLICATE_LOG_FILE = DATA_DIR / "processed/duplicates.jsonl"

# ================== 日志系统优化 ==================
class EnhancedLogger:
    """增强型日志系统，支持不同级别的日志文件分离"""
    def __init__(self):
        self.logger = logging.getLogger("data_wash")
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 创建日志目录
        DATA_DIR.joinpath("processed").mkdir(parents=True, exist_ok=True)
        
        # 主日志文件（包含所有级别）
        self._setup_file_handler(DATAWASH_LOG_FILE, logging.INFO)
        
        # 错误日志文件（单独记录错误）
        self._setup_file_handler(ERROR_LOG_FILE, logging.ERROR)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self, filename, level):
        """为指定文件创建日志处理器"""
        handler = logging.FileHandler(filename, mode='a', encoding='utf-8')
        handler.setLevel(level)
        handler.setFormatter(self.formatter)
        self.logger.addHandler(handler)
    
    def log(self, level, message, **kwargs):
        """增强日志方法，支持附加数据"""
        extra = {k: v for k, v in kwargs.items() if v is not None}
        self.logger.log(level, message, extra=extra if extra else None)

# 初始化全局日志器
logger = EnhancedLogger().logger

# ================== 数据处理函数 ==================
def calculate_hash(content):
    """计算内容的SHA256哈希值"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def save_data(data, filename):
    """优化版数据保存，支持大文件分批写入"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        batch_size = 100  # 分批保存减少内存压力
        
        with open(filename, 'a', encoding='utf-8') as f:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                for item in batch:
                    # 创建新的字典，排除"hash"字段
                    item_to_save = {k: v for k, v in item.items() if k != "hash"}
                    json_line = json.dumps(item_to_save, ensure_ascii=False)
                    f.write(json_line + '\n')
        
        logger.info(f"成功保存 {len(data)} 条数据到 {filename}")
        return True
    except Exception as e:
        logger.error(f"保存数据失败: {str(e)}", exc_info=True)
        return False

def process_raw_data():
    """高效处理原始数据，处理重复项和错误"""
    logger.info("="*50)
    logger.info("开始数据处理流程")
    logger.info(f"输入文件: {RAW_DATA_FILE}")
    logger.info(f"输出文件: {DATASPLITS_FILE}")
    logger.info("="*50)
    
    # 使用哈希值跟踪已处理的公式（更高效）
    seen_hashes = set()
    duplicates = []
    errors = []
    processed_data = []
    total_lines = 0
    
    try:
        # 先统计文件行数用于进度显示
        with open(RAW_DATA_FILE, "r", encoding="utf-8") as f:
            total_lines = sum(1 for _ in f)
        
        if total_lines == 0:
            logger.warning("输入文件为空！")
            return 0, 0, errors, duplicates
        
        logger.info(f"开始处理 {total_lines} 行数据...")
        
        with open(RAW_DATA_FILE, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    note = json.loads(line)
                    latex_content = note.get("latex")
                    
                    if not latex_content:
                        error_msg = "缺少 'latex' 字段"
                        errors.append({"line": line_num, "error": error_msg, "data": note})
                        logger.warning(error_msg, extra={"line": line_num, "data": note})
                        continue
                    
                    # 使用哈希值检查重复
                    content_hash = calculate_hash(latex_content)
                    
                    if content_hash in seen_hashes:
                        dup_info = {
                            "line": line_num,
                            "hash": content_hash,
                            "latex": latex_content
                        }
                        duplicates.append(dup_info)
                        logger.debug(f"检测到重复公式 (哈希: {content_hash[:8]})", extra=dup_info)
                        continue
                    
                    seen_hashes.add(content_hash)
                    
                    # 创建规范化的数据结构（保留哈希值用于内部处理）
                    # 重要修改：添加 custom_id 字段用于百炼 API
                    mapping_entry = {
                        "custom_id": f"latex_{uuid.uuid4().hex}",
                        "method": "POST",  # 必须字段
                        "input": latex_content,
                        "request_parameters": {   # API调用参数
                            "temperature": 0.2,
                            "max_tokens": 256,
                            "top_p": 0.9
                        },
                        "LaTeX": latex_content,
                        "CHINESE": None,
                        "Meaning": None,
                        "Solve" : None,
                        "source_line": line_num,
                        "metadata": {
                        "length": len(latex_content),
                        "complexity": len(latex_content.split())
                        }
                    }
                    
                    processed_data.append(mapping_entry)
                    
                    # 定期保存并输出进度
                    if line_num % 100 == 0 or line_num == total_lines:
                        save_success = save_data(processed_data, DATASPLITS_FILE)
                        if save_success:
                            processed_data = []  # 清空已保存数据
                        logger.info(f"进度: {line_num}/{total_lines} ({line_num/total_lines:.1%}) | 唯一公式: {len(seen_hashes)}")
                    
                except json.JSONDecodeError:
                    error_msg = "JSON解析错误"
                    errors.append({"line": line_num, "error": error_msg, "raw_line": line.strip()})
                    logger.error(error_msg, exc_info=True, extra={"line": line_num})
                except Exception as e:
                    error_msg = f"处理错误: {str(e)}"
                    errors.append({"line": line_num, "error": error_msg, "raw_line": line.strip()})
                    logger.error(error_msg, exc_info=True, extra={"line": line_num})
    
    except Exception as e:
        logger.critical(f"文件处理发生致命错误: {str(e)}", exc_info=True)
    
    # 保存剩余数据和错误信息
    if processed_data:
        save_data(processed_data, DATASPLITS_FILE)
    
    if duplicates:
        save_data(duplicates, DUPLICATE_LOG_FILE)
        logger.info(f"检测到 {len(duplicates)} 条重复数据，已保存到 {DUPLICATE_LOG_FILE}")
    
    if errors:
        save_data(errors, ERROR_LOG_FILE)
        logger.info(f"检测到 {len(errors)} 条错误数据，已保存到 {ERROR_LOG_FILE}")
    
    return len(seen_hashes), total_lines, errors, duplicates

# ================== 主程序 ==================
def initialize_data_dir():
    """确保所有必要的目录存在"""
    DATA_DIR.joinpath("raw").mkdir(parents=True, exist_ok=True)
    DATA_DIR.joinpath("processed").mkdir(parents=True, exist_ok=True)
    DATA_DIR.joinpath("splits").mkdir(parents=True, exist_ok=True)
    
    logger.info("数据目录初始化完成")

def create_sample_file():
    """创建示例文件（如果不存在）"""
    if not RAW_DATA_FILE.exists():
        logger.warning(f"输入文件不存在: {RAW_DATA_FILE}")
        
        sample_content = [
            {"note_id": 1, "latex": "E = mc^2", "content": "质能方程"},
            {"note_id": 2, "latex": "\\int_a^b f(x)dx", "content": "定积分"},
            {"note_id": 3, "latex": "\\sum_{i=1}^n i = \\frac{n(n+1)}{2}", "content": "求和公式"},
            {"note_id": 4, "latex": "E = mc^2", "content": "重复的质能方程"}
        ]
        
        try:
            save_data(sample_content, RAW_DATA_FILE)
            logger.info(f"已创建示例文件: {RAW_DATA_FILE} 包含 {len(sample_content)} 条示例")
        except Exception as e:
            logger.critical(f"创建示例文件失败: {str(e)}", exc_info=True)
            return False
    return True

def generate_report(unique_count, total_lines, errors, duplicates):
    """生成处理结果报告"""
    logger.info("="*50)
    logger.info("数据处理结果报告:")
    logger.info(f"处理总行数: {total_lines}")
    logger.info(f"提取唯一公式: {unique_count} 条")
    logger.info(f"重复公式数量: {len(duplicates)}")
    logger.info(f"错误/无效行数: {len(errors)}")
    logger.info(f"唯一率: {unique_count/max(total_lines, 1):.2%}")
    
    if errors:
        # 错误类型分析
        error_types = defaultdict(int)
        for error in errors:
            error_types[error["error"]] += 1
        
        logger.warning("错误类型统计:")
        for err_type, count in error_types.items():
            logger.warning(f"  {err_type}: {count} 处")

if __name__ == "__main__":
    try:
        initialize_data_dir()
        
        if not create_sample_file():
            exit(1)
            
        unique_formulas, total_lines, errors, duplicates = process_raw_data()
        generate_report(unique_formulas, total_lines, errors, duplicates)
        
        logger.info("="*50)
        logger.info(f"处理完成! 结果保存至: {DATASPLITS_FILE}")
        logger.info("文件格式已适配百炼API：每条记录包含唯一的custom_id和input字段")
    except Exception as e:
        logger.critical(f"程序初始化失败: {str(e)}", exc_info=True)
        exit(1)