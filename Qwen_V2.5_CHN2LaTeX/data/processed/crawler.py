import requests
from bs4 import BeautifulSoup
import json
import re
import random
import time
import logging
import os
from pathlib import Path

# === 配置输出路径 ===
PROJECT_ROOT = Path("E:/Qwen_V2.5_CHN2LaTeX")
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_FILE = DATA_DIR / "raw\\raw_data.jsonl"
LOG_FILE = DATA_DIR / "processeed\\crawler.log"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# === 配置日志系统 ===
def setup_logger():
    """配置日志系统，同时输出到文件和终端"""
    logger = logging.getLogger("crawler")
    logger.setLevel(logging.INFO)
    
    # 文件处理器（追加模式）
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
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

# === 爬虫函数 ==
def crawl_math_wiki(max_pages=20):
    """从数学维基百科爬取公式数据"""
    base_url = "https://zh.wikipedia.org"
    start_url = base_url + "/wiki/Category:数学公式"
    
    data = []
    visited = set()
    
    logger.info(f"开始爬取维基百科数学公式，目标页面数: {max_pages}")
    
    # 获取分类页面
    try:
        response = requests.get(start_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取分类中的页面链接
        category_links = []
        for li in soup.select("#mw-pages li a"):
            href = li.get('href')
            if href and href.startswith("/wiki/") and href not in visited:
                category_links.append(base_url + href)
                visited.add(href)
        
        # 随机选择页面进行爬取
        random.shuffle(category_links)
        logger.info(f"找到 {len(category_links)} 个相关页面")
        
        for i, url in enumerate(category_links[:max_pages]):
            logger.info(f"爬取页面 {i+1}/{max_pages}: {url}")
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取页面标题作为公式描述
                title = soup.find('h1', {'id': 'firstHeading'}).text.strip()
                
                # 提取所有LaTeX公式
                math_elements = soup.find_all('span', {'class': 'mwe-math-element'})
                found_count = 0
                for elem in math_elements:
                    mathml = elem.find('span', {'class': 'mwe-math-mathml-inline'})
                    if mathml:
                        latex = mathml.get('alttext', '').replace('\\displaystyle ', '')
                        if latex:
                            # 创建中文描述变体
                            variants = [
                                f"{title}的公式",
                                f"{title}的数学表达式",
                                f"如何用LaTeX表示{title}",
                                f"{title}的标准写法"
                            ]
                            
                            for desc in variants:
                                data.append({
                                    "chinese": desc,
                                    "latex": latex,
                                    "source": url
                                })
                            found_count += 1
                
                logger.info(f"在页面中找到 {found_count} 个公式")
                time.sleep(random.uniform(0,2))  # 礼貌爬取
            except Exception as e:
                logger.error(f"爬取失败: {url} - {str(e)}")
    
    except Exception as e:
        logger.error(f"初始化爬取失败: {str(e)}")
    
    logger.info(f"维基百科爬取完成，共获取 {len(data)} 条公式数据")
    return data

def crawl_arxiv_abstracts(max_results=50):
    
    """从arXiv爬取论文摘要中的公式"""
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "cat:math.AP",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    data = []
    logger.info(f"开始爬取arXiv论文摘要，目标结果数: {max_results}")
    
    try:
        response = requests.get(url, params=params)
        soup = BeautifulSoup(response.content, 'xml')
        
        entries = soup.find_all('entry')
        logger.info(f"找到 {len(entries)} 篇论文")
        
        for entry in entries:
            try:
                abstract = entry.find('summary').text.strip()
                
                # 提取中文描述和公式
                latex_pattern = r'\$(.*?)\$'
                formulas = re.findall(latex_pattern, abstract)
                
                if formulas:
                    title = entry.find('title').text.strip()
                    # 创建中文描述
                    desc = f"论文《{title}[](@replace=10001)》中的公式"
                    
                    valid_formulas = 0
                    for formula in formulas:
                        if len(formula) > 10:  # 过滤简单公式
                            data.append({
                                "chinese": desc,
                                "latex": formula,
                                "source": "arXiv"
                            })
                            valid_formulas += 1
                    
                    logger.info(f"在论文《{title[:20]}...[](@replace=10002)》中找到 {valid_formulas} 个有效公式")
            except Exception as e:
                logger.warning(f"处理论文时出错: {str(e)}")
    
    except Exception as e:
        logger.error(f"arXiv爬取失败: {str(e)}")
    
    logger.info(f"arXiv爬取完成，共获取 {len(data)} 条公式数据")
    return data

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

# === 主程序 ===
if __name__ == "__main__":
    logger.info("="*50)
    logger.info("爬虫程序启动")
    logger.info(f"数据将保存到: {RAW_DATA_FILE}")
    logger.info(f"日志将保存到: {LOG_FILE}")
    
    # 爬取数据
    wiki_data = crawl_math_wiki(max_pages=20)
    arxiv_data = crawl_arxiv_abstracts(max_results=30)
    
    all_data = wiki_data + arxiv_data
    logger.info(f"共爬取 {len(all_data)} 条公式数据")
    
    # 保存原始数据
    save_data(all_data, RAW_DATA_FILE)
    
    logger.info("爬虫程序执行完毕")
    logger.info("="*50)