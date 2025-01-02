import scrapy

class ltn_crawler(scrapy.Spider):
    name = "ltn_spider"
    

    def __init__(self, keyword = None, **kwargs):
        super().__init__(keyword, **kwargs)
        self.keyword = keyword
        # 起始 URL：你想爬的首頁
        # 自由時報 ltn https://www.ltn.com.tw/

    def start_requests(self):
        # 在這裡就能使用 self.keyword 來拼接 URL 或做其他事
        if self.keyword:
            # 假設你要對某個站點做搜尋，把 keyword 放入查詢字串
            search_url = f"https://search.ltn.com.tw/list?keyword={self.keyword}"
            yield scrapy.Request(url=search_url, callback=self.parse)
        else:
            # 沒有給參數，就跑預設的 URL 或處理
            yield scrapy.Request(url="https://search.ltn.com.tw/list?keyword=%E5%85%A7%E7%B7%9A%E4%BA%A4%E6%98%93", callback=self.parse)

    def parse(self, response):
        """
        這個 parse() 負責處理「首頁」的回應。
        1. 找到所有子連結
            1) 找到 <ul class="list boxTitle"> 中的所有 <li> 
            2) 針對每個 <li> 內的 <a> href 屬性收集起來
            3) 去除重複連結
            4) 輸出結果
        2. 產生新的 Request，交給 parse_detail() 去處理
        """
        # 先抓到 ul.list.boxTitle 中所有 li
        li_elements = response.css('ul.list.boxTitle li')
        
        all_links = []
        for li in li_elements:
            # 針對每個 <li>，取得所有 <a> 的 href
            sub_links = li.css('a::attr(href)').getall()
            # 將這些 sub_links 累積到 all_links
            all_links.extend(sub_links)


        # 去除重複：最簡單的方式 -> set()
        # 不過 set() 會打亂順序，如果想保留原順序，得自己寫邏輯判斷
        unique_links = list(set(all_links))

        for link in unique_links:
            # 有兩種不同的網站
            if link.startswith("https://ec.ltn.com.tw/"):
                yield scrapy.Request(url=link, callback=self.parse_detail_ec)
            elif link.startswith("https://news.ltn.com.tw/"):
                yield scrapy.Request(url=link, callback=self.parse_detail_news)

    def parse_detail_ec(self, response):
        """
        這個 parse_detail() 負責處理「子連結」的內容抓取。
        解析目標頁面，抓取「標題」「時間」「內文」。
        """

        # 1) 抓取標題
        #   HTML 結構顯示：<h1><span>台開內線交易案定讞...</span></h1>
        title = response.css('div.whitecon.boxTitle.boxText h1::text').get()

        # 2) 抓取時間
        #   HTML 結構顯示：<div class="timeBox"><div class="updatetime"><span>2024/12/7 10:56</span>
        date_time = response.css('div.function span.time::text').get()
        # if date_time:
        #     date_time = date_time.strip()
        # else:
        #     date_time = None

        # 3) 抓取內文（含多個 <p>）
        #   觀察可知：<div class="paragraph"><p> ...</p><p>...</p></div> 會有多段
        #   可以抓所有段落文字並組合
        paragraphs = response.css('div.text p::text').getall()
        # 移除空白並串接
        content = "\n".join([p.strip() for p in paragraphs if p.strip()])
        
        # 把結果產生出來
        yield {
            "title": title,
            "date_time": date_time,
            "content": content,
            "page_url": response.url
        }

    def parse_detail_news(self, response):
        """
        這個 parse_detail() 負責處理「子連結」的內容抓取。
        解析目標頁面，抓取「標題」「時間」「內文」。
        """

        # 1) 抓取標題
        title = response.css('div.whitecon.article h1::text').get()

        # 2) 抓取時間
        date_time = response.css('div.text.boxTitle.boxText span.time::text').get()
        # if date_time:
        #     date_time = date_time.strip()
        # else:
        #     date_time = None

        # 3) 抓取內文（多段 <p>）
        #    先取得所有 <p> 文字，再用 '\n' 串接
        paragraphs = response.css('div.text.boxTitle.boxText p::text').getall()
        content = "\n".join([p.strip() for p in paragraphs if p.strip()])
        
        # 把結果產生出來
        yield {
            "title": title,
            "date_time": date_time,
            "content": content,
            "page_url": response.url
        }

