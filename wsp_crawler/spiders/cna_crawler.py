import scrapy

class cna_crawler(scrapy.Spider):
    name = "cna_spider"
    

    def __init__(self, keyword = None, **kwargs):
        super().__init__(keyword, **kwargs)
        self.keyword = keyword
        # 起始 URL：你想爬的首頁
        # 中央社 cna https://www.cna.com.tw

    def start_requests(self):
        # 在這裡就能使用 self.keyword 來拼接 URL 或做其他事
        if self.keyword:
            # 假設你要對某個站點做搜尋，把 keyword 放入查詢字串
            search_url = f"https://www.cna.com.tw/search/hysearchws.aspx?q={self.keyword}"
            yield scrapy.Request(url=search_url, callback=self.parse)
        else:
            # 沒有給參數，就跑預設的 URL 或處理
            yield scrapy.Request(url="https://www.cna.com.tw/search/hysearchws.aspx?q=%E8%B2%AA%E6%B1%99", callback=self.parse)

    def parse(self, response):
        """
        這個 parse() 負責處理「首頁」的回應。
        1. 找到所有子連結
        2. 產生新的 Request，交給 parse_detail() 去處理
        """
        # 假設只找頁面上所有 <a>，並抓 href
        sub_links = response.css('ul#jsMainList li a::attr(href)').getall()
        
        for link in sub_links:
            # 產生完整網址
            full_url = "https://www.cna.com.tw" + link
            
            # 這裡可以做一些過濾，例如只要同網域的連結
            if full_url.startswith("https://www.cna.com.tw"):
                # 產生 Request，並指定 callback = parse_detail
                yield scrapy.Request(url=full_url, callback=self.parse_detail)
        
    def parse_detail(self, response):
        """
        這個 parse_detail() 負責處理「子連結」的內容抓取。
        解析目標頁面，抓取「標題」「時間」「內文」。
        """

        # 1) 抓取標題
        #   HTML 結構顯示：<h1><span>台開內線交易案定讞...</span></h1>
        title = response.css('div.centralContent h1 span::text').get()

        # 2) 抓取時間
        #   HTML 結構顯示：<div class="timeBox"><div class="updatetime"><span>2024/12/7 10:56</span>
        date_time = response.css('div.timeBox div.updatetime span::text').get()

        # 3) 抓取內文（含多個 <p>）
        #   觀察可知：<div class="paragraph"><p> ...</p><p>...</p></div> 會有多段
        #   可以抓所有段落文字並組合
        paragraphs = response.css('div.paragraph p::text').getall()
        content = "\n".join([p.strip() for p in paragraphs if p.strip()])
        
        # 把結果產生出來
        yield {
            "title": title,
            "date_time": date_time,
            "content": content,
            "page_url": response.url
        }

