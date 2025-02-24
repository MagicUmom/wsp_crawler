import scrapy
import json

class company_crawler(scrapy.Spider):
    name = "company_spider"
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' \
                      'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                      'Chrome/90.0.4430.93 Safari/537.36'
    }

    def __init__(self, keyword = None, **kwargs):
        super().__init__(keyword, **kwargs)
        self.keyword = keyword
        # 起始 URL：你想爬的首頁
        # 中央社 cna https://www.cna.com.tw

    def start_requests(self):
        # 在這裡就能使用 self.keyword 來拼接 URL 或做其他事
        if self.keyword:
            # 假設你要對某個站點做搜尋，把 keyword 放入查詢字串
            search_url = f"https://www.twincn.com/Lq.aspx?q={self.keyword}"
            yield scrapy.Request(url=search_url, callback=self.parse)

    def parse(self, response):
        """
        這個 parse() 負責處理「首頁」的回應。
        1. 找到所有子連結
        2. 產生新的 Request，交給 parse_detail() 去處理
        """
        
        # 選取 table 中 tbody 下所有 tr（排除 thead）
        for row in response.css("table.table-striped tbody tr"):
            # 取得第二個 <td> 中所有 <a> 標籤的 href 屬性
            sub_link = row.css("td:nth-child(2) a::attr(href)").getall()
            full_url = "https://www.twincn.com/" + sub_link[0]
            yield scrapy.Request(url=full_url, callback=self.parse_detail)  


    def parse_detail(self, response):
        def extract_field(field_keyword):
            """
            根據傳入的欄位關鍵字，從 table 中尋找包含該關鍵字的 <strong>，
            並取得同一列中第二個 <td> 內所有文字，整理後回傳。
            """
            xpath_expr = f'//table[@id="basic-data"]//tr[td/strong[contains(text(), "{field_keyword}")]]/td[2]//text()'
            texts = response.xpath(xpath_expr).getall()
            return ' '.join([t.strip() for t in texts if t.strip()])

        # 統編：以「統一編號」關鍵字搜尋（原始資料為「統一編號（統編）」）
        company_id = extract_field("統一編號")
        
        # 公司名稱（中文）：以「公司名稱」搜尋
        company_name_cn = extract_field("公司名稱")
        
        # 公司名稱（英文）：以「英文名稱」搜尋
        company_name_en = extract_field("英文名稱")
        
        # 代表人姓名（作為負責人）：以「代表人姓名」搜尋
        representative = extract_field("代表人姓名")
        
        # 地址：以「公司所在地」搜尋
        address = extract_field("公司所在地")
        
        # 行業別：以「所營事業資料」搜尋
        industry = extract_field("所營事業資料")

        yield {
            "統編": company_id,
            "公司名稱_中文": company_name_cn,
            "公司名稱_英文": company_name_en,
            "負責人": representative,
            "地址": address,
            "行業別": industry,
        }

import subprocess

def run_all_spiders(keyword):
    # 三支要執行的 spider 名稱
    spiders = ["company_spider"]
    for spider in spiders:
        # 指令可自行調整輸出的檔案名稱等
        command = [
            "scrapy", "crawl", spider,
            "-a", f"keyword={keyword}",
            "-o", f"{spider}_result.json"
        ]
        # 呼叫 subprocess
        subprocess.run(command, check=True)

    # 讀取 output.json 檔案
    with open("company_spider_result.json", "r", encoding="utf-8") as f:
        data = json.load(f)

        # 使用列表生成式過濾出「負責人」欄位不為空的公司，
        # 並只保留其中文公司名稱
        companies_with_person = [
            company["公司名稱_中文"] 
            for company in data 
            if company.get("負責人", "").strip()  # 檢查負責人欄位是否非空（移除多餘空白）
        ]

        print(companies_with_person)



if __name__ == "__main__":
    user_keyword = input("請輸入關鍵字：")
    run_all_spiders(user_keyword)
    print("所有爬蟲執行完畢!")


