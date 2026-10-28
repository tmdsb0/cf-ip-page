import re
import os
import time
from playwright.sync_api import sync_playwright

def main():
    url = 'https://api.uouin.com/cloudflare.html'
    
    print("🚀 启动物理降维打击：真实无头浏览器加载模式...")
    with sync_playwright() as p:
        # 启动 Chrome 内核（无头模式）
        browser = p.chromium.launch(headless=True)
        # 伪装正常用户的分辨率和指纹
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            print(f"1. 正在控制真实浏览器访问页面: {url}")
            # 打开网页，等待网络连接闲置
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 强行等待 5 秒钟！
            # 给网页里的 JS 留出充足的时间，让它自己去算密钥、请求接口、渲染 IP 列表
            print("2. 网页加载完毕，等待 5 秒钟让其动态渲染数据...")
            page.wait_for_timeout(5000) 
            
            # 获取网页渲染完成后的最终完整 HTML（此时 IP 已经显示在页面上了）
            html_text = page.content()
            title = page.title()
            print(f"-> 获取到最终渲染网页，标题为: {title}")
            
            print("3. 开始使用滑动窗口提取渲染后的 IP 数据...")
            seen_ips = set()
            results = []
            
            # 在全网页文本中暴力匹配所有 IP
            ip_pattern = r'\b((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))\b'
            matches = re.finditer(ip_pattern, html_text)
            
            for match in matches:
                ip = match.group(1)
                # 跳过一些网页代码里常见的假 IP
                if ip in seen_ips or ip.startswith('127.') or ip.startswith('0.'): 
                    continue
                seen_ips.add(ip)
                
                # 截取该 IP 前后各 60 个字符，寻找端口和运营商
                start = max(0, match.start() - 60)
                end = min(len(html_text), match.end() + 60)
                context_str = html_text[start:end]
                
                port_match = re.search(r'\b(80|443|8080|8443|2052|2053|2082|2083|2086|2087|2095|2096)\b', context_str)
                port = port_match.group(1) if port_match else "443"
                
                isp = "CF 优选"
                if "电信" in context_str: isp = "CF 电信优选"
                elif "联通" in context_str: isp = "CF 联通优选"
                elif "移动" in context_str: isp = "CF 移动优选"
                
                results.append(f"{ip}:{port}#{isp}")

            if results:
                os.makedirs('public', exist_ok=True)
                with open('public/ip.txt', 'w', encoding='utf-8') as f:
                    f.write('\n'.join(results))
                print(f"🎉 物理降维打击成功！彻底无视接口加密，成功提取 {len(results)} 个最新 IP！")
            else:
                print("⚠️ 页面已经渲染完毕，但未能提取到 IP。这通常说明网站彻底改版，或者出现了极高强度的真人验证码弹窗。")
                print("-> 页面前500字符诊断:", html_text[:500])
                
        except Exception as e:
            print(f"抓取发生错误: {e}")
        finally:
            browser.close()

if __name__ == '__main__':
    main()
