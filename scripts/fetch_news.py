import feedparser
import requests
import os
from datetime import datetime

# ===== 配置 =====
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

RSS_FEEDS = [
    "https://rsshub.app/36kr/newsflashes",
    "https://rsshub.app/jiqizhixin/posts",
    "https://rsshub.app/qbitai",
    "https://rsshub.app/huxiu/rss",
]

def fetch_all_news():
    """抓取所有 RSS 源的最新新闻"""
    all_articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                all_articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary[:200] if hasattr(entry, "summary") else "",
                })
            print(f"  ✅ 已从 {url} 获取 {min(len(feed.entries), 10)} 条")
        except Exception as e:
            print(f"  ❌ 获取失败 {url}: {e}")
    return all_articles

def summarize_with_deepseek(articles):
    """调用 DeepSeek 生成 HTML 格式的简报"""
    news_text = "\n".join([
        f"{i+1}. [{a['title']}]({a['link']}) — {a['summary']}"
        for i, a in enumerate(articles[:60])
    ])

    prompt = f"""你是一位专业的 AI 新闻编辑。请根据以下今日新闻列表，生成一份「AI 行业每日简报」。

要求：
1. 挑选最重要的 8-10 条新闻，用中文总结。
2. 将新闻分为「🔥 技术突破」「💰 商业动态」「📋 政策与行业」三个板块。
3. 每条新闻用 1-2 句话概括（不超过 60 字），必须附上原文链接。
4. 顶部写一段 100 字以内的「今日热点速览」。
5. 输出完整的 HTML 代码片段（从 <section> 开始到 </section> 结束），结构清晰，适合嵌入网页。

新闻列表：
{news_text}"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位严谨高效的 AI 新闻编辑，擅长提炼关键信息。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2500,
    }

    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
    result = resp.json()
    return result["choices"][0]["message"]["content"]

def build_html(summary_html):
    """将 DeepSeek 生成的片段包装成完整的 HTML 页面"""
    today = datetime.now().strftime("%Y年%m月%d日")
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 新闻简报 - {today}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
  .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
  .header h1 {{ margin: 0 0 10px 0; }}
  .header p {{ margin: 0; opacity: 0.9; }}
  .content {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  .content h2 {{ color: #667eea; }}
  .content h3 {{ color: #764ba2; }}
  .content ul {{ padding-left: 20px; }}
  .content li {{ margin-bottom: 8px; line-height: 1.6; }}
  .content a {{ color: #667eea; }}
  .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 14px; }}
</style>
</head>
<body>
  <div class="header">
    <h1>🤖 AI 行业每日简报</h1>
    <p>📅 {today} ｜ 基于 DeepSeek 自动生成 ｜ 每日 8:00 更新</p>
  </div>
  <div class="content">
    {summary_html}
  </div>
  <div class="footer">
    <p>🕒 最后更新：{update_time} (UTC+8)</p>
    <p>新闻来源：36氪、机器之心、量子位、虎嗅 ｜ <a href="https://github.com">GitHub</a> 托管</p>
  </div>
</body>
</html>"""

def main():
    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M')} 开始生成新闻简报...")
    
    # 1. 抓取新闻
    print("📰 第1步：抓取新闻...")
    articles = fetch_all_news()
    print(f"   共获取 {len(articles)} 条新闻")
    
    if len(articles) == 0:
        print("⚠️ 未获取到任何新闻，任务终止")
        return
    
    # 2. AI 生成
    print("🧠 第2步：调用 DeepSeek 生成简报...")
    summary_html = summarize_with_deepseek(articles)
    
    # 3. 构建完整页面
    print("🎨 第3步：构建 HTML 页面...")
    full_html = build_html(summary_html)
    
    # 4. 写入文件
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    print("✅ 简报已保存到 docs/index.html")

if __name__ == "__main__":
    main()
