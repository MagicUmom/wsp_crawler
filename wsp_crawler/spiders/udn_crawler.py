import scrapy

class udn_crawler(scrapy.Spider):
    name = "udn_spider"
    

    def __init__(self, keyword = None, **kwargs):
        super().__init__(keyword, **kwargs)
        self.keyword = keyword
        # 起始 URL：你想爬的首頁
        # 聯合新聞網 udn https://udn.com/news/index

    def start_requests(self):
        # 在這裡就能使用 self.keyword 來拼接 URL 或做其他事
        if self.keyword:
            # 假設你要對某個站點做搜尋，把 keyword 放入查詢字串
            search_url = f"https://udn.com/search/word/2/{self.keyword}"
            yield scrapy.Request(url=search_url, callback=self.parse)
        else:
            # 沒有給參數，就跑預設的 URL 或處理
            yield scrapy.Request(url="https://udn.com/search/word/2/%E5%85%A7%E7%B7%9A%E4%BA%A4%E6%98%93", callback=self.parse)

    def parse(self, response):
        """
        從搜尋結果清單的每個 <div class="story-list__news"> 中抓取連結。
        HTML 結構觀察到：
        - 每一則新聞有 <h2><a href="..." title="..." ...> 標題連結
        """
        # 1) 在外層先抓到所有新聞項目: <div class="story-list__news">
        news_blocks = response.css('div.story-list__news')
        
        all_links = []
        for block in news_blocks:
            # 2) 在每個 block 裡，針對 <h2>a 或 <div class="story-list__image">a 抓 href
            #    觀察 HTML 會發現標題連結: block.css('h2 a::attr(href)')
            #    也可能在圖片連結: block.css('.story-list__image--holder::attr(href)')
            
            link_in_title = block.css('h2 a::attr(href)').get()

            # 如果該 block 存在標題連結
            if link_in_title:
                all_links.append(link_in_title)

        # 去除重複：最簡單的方式 -> set()
        # 不過 set() 會打亂順序，如果想保留原順序，得自己寫邏輯判斷
        unique_links = list(set(all_links))

        for link in unique_links:
            # 有兩種不同的網站
            if link.startswith("https://udn.com/"):
                yield scrapy.Request(url=link, callback=self.parse_detail)
            # elif link.startswith("https://news.ltn.com.tw/"):
            #     yield scrapy.Request(url=link, callback=self.parse_detail_news)

    def parse_detail(self, response):
        """
        這個 parse_detail() 負責處理「子連結」的內容抓取。
        解析目標頁面，抓取「標題」「時間」「內文」。
        """

        # 1) 抓取標題
        #    觀察 HTML：標題位於 <h1 class="article-content__title">... </h1> 內
        title = response.css(".article-content__title::text").get(default="").strip()

        # 2) 抓取時間
        #    觀察 HTML：<time class="article-content__time">2024-12-31 11:08</time>
        date_time = response.css(".article-content__time::text").get(default="").strip()

        # 3) 抓取內文（含多個 <p>）
        #    先嘗試抓 <section class="article-content__editor">，若沒有再嘗試 <article class="article-content">
        content_section = response.css("section.article-content__editor")
        if not content_section:
            content_section = response.css("article.article-content")

        # 在 content_section 內抓所有 <p> 的文字
        paragraphs = content_section.css("p::text").getall()
        content = "\n".join(p.strip() for p in paragraphs if p.strip())
        
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

