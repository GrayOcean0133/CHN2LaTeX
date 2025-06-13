import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)

# ==== 高亮改进1：创建带重试机制的会话 ====
def create_retry_session(retries=5, backoff_factor=0.3):
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# ==== 高亮改进2：移除max_pages参数，实现无限爬取 ====
def crawl_math_wiki():
    """从数学维基百科爬取公式数据（无限制）"""
    base_url = "https://zh.wikipedia.org"
    start_url = base_url + "/wiki/Category:数学公式"
    
    data = []
    visited = set()
    session = create_retry_session()  # 使用重试会话
    
    # ==== 高亮改进3：处理分页逻辑 ====
    next_page_url = start_url
    while next_page_url:
        try:
            response = session.get(next_page_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取当前页面的所有公式页面链接
            for li in soup.select("#mw-pages li a"):
                href = li.get('href')
                if href and href.startswith("/wiki/") and href not in visited:
                    page_url = base_url + href
                    visited.add(href)
                    try:
                        page_response = session.get(page_url)
                        page_soup = BeautifulSoup(page_response.text, 'html.parser')
                        
                        # 提取页面标题
                        title = page_soup.find('h1', {'id': 'firstHeading'}).text.strip()
                        
                        # 提取所有LaTeX公式
                        math_elements = page_soup.find_all('span', {'class': 'mwe-math-element'})
                        for elem in math_elements:
                            mathml = elem.find('span', {'class': 'mwe-math-mathml-inline'})
                            if mathml:
                                latex = mathml.get('alttext', '').replace('\\displaystyle ', '')
                                if latex:
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
                                            "source": page_url
                                        })
                        
                        # ==== 高亮改进4：随机延迟防止被封 ====
                        #time.sleep(random.uniform(1, 3))  # 随机延迟1-3秒
                        
                    except Exception as e:
                        logging.error(f"页面爬取失败: {page_url} - {str(e)}")
            
            # ==== 高亮改进5：查找下一页链接 ====
            next_link = soup.find('a', text='下一页')
            next_page_url = base_url + next_link['href'] if next_link else None
            
        except Exception as e:
            logging.error(f"分类页面爬取失败: {next_page_url} - {str(e)}")
            next_page_url = None
    
    return data

# ==== 高亮改进6：arXiv爬取无限制 ====
def crawl_arxiv_abstracts():
    """从arXiv爬取论文摘要中的公式（无限制）"""
    url = "http://export.arxiv.org/api/query"
    data = []
    session = create_retry_session()
    
    start = 0
    batch_size = 100  # 每次获取100条记录
    has_more = True
    
    while has_more:
        params = {
            "search_query": "cat:math.AP",
            "start": start,
            "max_results": batch_size,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        try:
            response = session.get(url, params=params)
            soup = BeautifulSoup(response.content, 'xml')
            entries = soup.find_all('entry')
            
            if not entries:
                has_more = False
                continue
                
            for entry in entries:
                try:
                    abstract = entry.find('summary').text.strip()
                    latex_pattern = r'\$(.*?)\$'
                    formulas = re.findall(latex_pattern, abstract)
                    
                    if formulas:
                        title = entry.find('title').text.strip()
                        desc = f"论文《{title}[](@replace=10001)》中的公式"
                        
                        for formula in formulas:
                            if len(formula) > 10:
                                data.append({
                                    "chinese": desc,
                                    "latex": formula,
                                    "source": "arXiv"
                                })
                except Exception:
                    continue
            
            start += batch_size
            # ==== 高亮改进7：API请求延迟 ====
            # time.sleep(random.uniform(2, 5))  # 随机延迟2-5秒
            
        except Exception as e:
            logging.error(f"arXiv API请求失败: {str(e)}")
            has_more = False
    
    return data

# 保存数据函数保持不变
def save_data(data, filename):
    with open(filename, 'a', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    # 爬取数据（无限制）
    wiki_data = crawl_math_wiki()
    arxiv_data = crawl_arxiv_abstracts()
    
    all_data = wiki_data + arxiv_data
    print(f"共爬取 {len(all_data)} 条公式数据")
    
    # 保存原始数据
    save_data(all_data, "raw_data.jsonl")
    print("原始数据已保存到 raw_data.jsonl")