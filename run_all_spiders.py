import subprocess

def run_all_spiders(keyword):
    # 三支要執行的 spider 名稱
    spiders = ["cna_spider", "udn_spider", "ltn_spider"]
    for spider in spiders:
        # 指令可自行調整輸出的檔案名稱等
        command = [
            "scrapy", "crawl", spider,
            "-a", f"keyword={keyword}",
            "-o", f"{spider}_result.json"
        ]
        # 呼叫 subprocess
        subprocess.run(command, check=True)

if __name__ == "__main__":
    user_keyword = input("請輸入關鍵字：")
    run_all_spiders(user_keyword)
    print("所有爬蟲執行完畢!")
