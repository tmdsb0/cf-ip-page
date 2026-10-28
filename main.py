from curl_cffi import requests
import re
import os
import time

def main():
    base_url = 'https://api.uouin.com/cloudflare.html'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://api.uouin.com/'
    }

    try:
        print("1. 正在获取主页，提取动态 Key...")
        session = requests.Session(impersonate="chrome110")
        resp_html = session.get(base_url, headers=headers, timeout=30)
        html_text = resp_html.text
        
        # 提取动态 Key
        api_key = "9f82787dee401e1cc0b86facb626b503"
        key_match = re.search(r'key\s*(?:=|:)\s*[\'"]?([a-fA-F0-9]{32})[\'"]?', html_text)
        url_match = re.search(r'key=([a-fA-F0-9]{32})', html_text)
        
        if key_match:
            api_key = key_match.group(1)
            print(f"-> 成功提取最新 Key: {api_key}")
        elif url_match:
            api_key = url_match.group(1)
            print(f"-> 成功提取最新 Key: {api_key}")
        else:
            print("-> 警告: 未能自动提取，使用保底 Key。")

        # 构造并请求真实数据接口
        current_time_ms = int(time.time() * 1000)
        api_url = f'https://api.uouin.com/index.php/index/Cloudflare?key={api_key}&time={current_time_ms}'
        print(f"2. 正在请求数据接口: {api_url}")
        
        headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        headers['X-Requested-With'] = 'XMLHttpRequest' 
        
        resp_data = session.get(api_url, headers=headers, timeout=30)
        resp_data.encoding = 'utf-8'
        data_text = resp_data.text
        
        # 打印部分返回内容到日志，方便排错
        print(f"-> 接口返回内容长度: {len(data_text)}")
        print(f"-> 接口返回前200字符: {data_text[:200]}")
        
        print("3. 开始使用滑动窗口智能解析 IP 数据...")
        seen_ips = set()
        results = []
        
        # 正则匹配全局所有的 IPv4 地址
        ip_pattern = r'\b((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))\b'
        matches = re.finditer(ip_pattern, data_text)
        
        for match in matches:
            ip = match.group(1)
            if ip in seen_ips:
                continue
            seen_ips.add(ip)
            
            # 截取该 IP 前后各 60 个字符作为“上下文”，在里面找端口和运营商
            start = max(0, match.start() - 60)
            end = min(len(data_text), match.end() + 60)
            context = data_text[start:end]
            
            # 提取端口
            port_match = re.search(r'\b(80|443|8080|8443|2052|2053|2082|2083|2086|2087|2095|2096)\b', context)
            port = port_match.group(1) if port_match else "443"
            
            # 提取运营商
            isp = "CF 优选"
            if "电信" in context: isp = "CF 电信优选"
            elif "联通" in context: isp = "CF 联通优选"
            elif "移动" in context: isp = "CF 移动优选"
            
            results.append(f"{ip}:{port}#{isp}")

        if results:
            os.makedirs('public', exist_ok=True)
            with open('public/ip.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(results))
            print(f"🎉 成功提取 {len(results)} 个最新 IP，并保存至 public/ip.txt！")
        else:
            print("⚠️ 依然未能提取到任何 IP。请检查上面打印的【接口返回前200字符】，看看网站是不是返回了错误提示（比如 key 错误或拦截信息）。")

    except Exception as e:
        print(f"抓取发生错误: {e}")

if __name__ == '__main__':
    main()
