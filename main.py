from curl_cffi import requests
import re
import os
import time

def main():
    # 步骤 1：先获取主页 HTML，目的是提取里面隐藏的动态 API Key，并获取 CF 的通行 Cookie
    base_url = 'https://api.uouin.com/cloudflare.html'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://api.uouin.com/'
    }

    try:
        print("1. 正在获取主页，穿透防火墙并提取动态 Key...")
        # 必须使用 Session，这样第一步获取到的 Cloudflare 验证通过的 Cookie 才能带到第二步去
        session = requests.Session(impersonate="chrome110")
        
        resp_html = session.get(base_url, headers=headers, timeout=30)
        html_text = resp_html.text
        
        # 尝试在网页源码中捕捉这个 32 位的 key
        # 兼容各种写法，比如 key="9f8..." 或 key: '9f8...' 或 URL 里的 key=9f8...
        api_key = "9f82787dee401e1cc0b86facb626b503" # 使用你抓到的 key 作为保底
        key_match = re.search(r'key\s*(?:=|:)\s*[\'"]?([a-fA-F0-9]{32})[\'"]?', html_text)
        url_match = re.search(r'key=([a-fA-F0-9]{32})', html_text)
        
        if key_match:
            api_key = key_match.group(1)
            print(f"-> 成功从网页变量中提取到最新 Key: {api_key}")
        elif url_match:
            api_key = url_match.group(1)
            print(f"-> 成功从接口地址中提取到最新 Key: {api_key}")
        else:
            print("-> 未能自动提取，将使用默认抓包 Key 尝试获取。")

        # 步骤 2：构造真实的 API 请求
        # 自动生成当前的 13 位毫秒级时间戳，完全模拟浏览器的 Date.now()
        current_time_ms = int(time.time() * 1000)
        
        # 拼接你刚才抓包抓到的真实底层接口
        api_url = f'https://api.uouin.com/index.php/index/Cloudflare?key={api_key}&time={current_time_ms}'
        print(f"2. 正在请求真实数据接口...")
        
        # 加上 AJAX 异步请求专属的请求头
        headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        headers['X-Requested-With'] = 'XMLHttpRequest' 
        
        # 去请求真实接口（此时带着第一步拿到的 Session Cookie，不会再被拦截）
        resp_data = session.get(api_url, headers=headers, timeout=30)
        resp_data.encoding = 'utf-8'
        data_text = resp_data.text
        
        print("3. 开始解析最新 IP 数据...")
        
        # 步骤 3：通用正则解析（无视它是返回 JSON 还是 HTML，直接暴力提取 IP）
        seen_ips = set()
        results = []
        
        # 处理 JSON 中可能出现的转义斜杠和换行符
        data_text = data_text.replace('\\/', '/').replace('\\n', '\n')
        blocks = re.split(r'(?i)<tr[^>]*>|<li[^>]*>|<div[^>]*>|<br\s*/?>|\\n|\n', data_text)
        
        for block in blocks:
            clean_text = re.sub(r'<[^>]+>', ' ', block).strip()
            if not clean_text:
                continue
                
            # 提取 IP
            ip_match = re.search(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', clean_text)
            if not ip_match:
                continue
            
            ip = ip_match.group(0)
            if ip in seen_ips:
                continue
            seen_ips.add(ip)
            
            # 提取端口
            port_match = re.search(r'\b(80|443|8080|8443|2052|2053|2082|2083|2086|2087|2095|2096)\b', clean_text)
            port = port_match.group(1) if port_match else "443"
            
            # 提取运营商
            isp = "CF 优选"
            if "电信" in clean_text: isp = "CF 电信优选"
            elif "联通" in clean_text: isp = "CF 联通优选"
            elif "移动" in clean_text: isp = "CF 移动优选"
            
            results.append(f"{ip}:{port}#{isp}")

        if results:
            os.makedirs('public', exist_ok=True)
            with open('public/ip.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(results))
            print(f"🎉 成功提取 {len(results)} 个最新 IP并保存至 public/ip.txt！")
        else:
            print("⚠️ 未能在数据接口中提取到任何 IP。")
            print("接口返回的部分内容:", data_text[:200])

    except Exception as e:
        print(f"抓取发生错误: {e}")

if __name__ == '__main__':
    main()
