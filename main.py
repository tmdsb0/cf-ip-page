from curl_cffi import requests
import re
import os
import time

def main():
    base_url = 'https://api.uouin.com/cloudflare.html'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://api.uouin.com/'
    }

    try:
        print("1. 正在获取主页，尝试穿透防火墙...")
        # 升级指纹到 chrome120
        session = requests.Session(impersonate="chrome120")
        resp_html = session.get(base_url, headers=headers, timeout=30)
        html_text = resp_html.text
        
        # 打印网页标题，检查是否被 CF 五秒盾拦截
        title_match = re.search(r'<title>(.*?)</title>', html_text, re.I)
        title = title_match.group(1) if title_match else "无标题"
        print(f"-> 获取到的网页标题: {title}")
        
        if "Just a moment" in title or "Attention Required" in title or "Cloudflare" in title:
            print("❌ 严重警告：请求被 Cloudflare 拦截了，获取到的是五秒盾页面，不是真实网页！")
        
        # 暴力提取所有独立的 32 位十六进制字符串（MD5格式）
        print("\n2. 正在全盘搜索所有疑似的 32 位 Key...")
        possible_keys = re.findall(r'(?<![a-zA-Z0-9])[a-fA-F0-9]{32}(?![a-zA-Z0-9])', html_text)
        
        # 列表去重
        possible_keys = list(set(possible_keys))
        
        if not possible_keys:
            print("❌ 网页源码中不存在任何 32 位的 Key。")
            return
            
        print(f"-> 找到了 {len(possible_keys)} 个疑似 Key，开始逐一测试接口...")
        
        success = False
        data_text = ""
        
        # 循环测试所有的 Key
        for test_key in possible_keys:
            print(f"--- 正在尝试 Key: {test_key} ---")
            current_time_ms = int(time.time() * 1000)
            api_url = f'https://api.uouin.com/index.php/index/Cloudflare?key={test_key}&time={current_time_ms}'
            
            api_headers = headers.copy()
            api_headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
            api_headers['X-Requested-With'] = 'XMLHttpRequest' 
            
            resp_data = session.get(api_url, headers=api_headers, timeout=30)
            resp_data.encoding = 'utf-8'
            test_data = resp_data.text
            
            print(f"    接口返回: {test_data[:60]}...")
            
            if "密钥错误" not in test_data and "code\":-1" not in test_data:
                print("    ✅ 这个 Key 成功了！跳出循环。")
                data_text = test_data
                success = True
                break
            else:
                print("    ❌ 密钥无效。")
                
        if not success:
            print("所有提取到的 Key 均被接口拒绝，提取失败。")
            return
            
        print("\n3. 开始使用滑动窗口解析 IP 数据...")
        seen_ips = set()
        results = []
        
        ip_pattern = r'\b((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))\b'
        matches = re.finditer(ip_pattern, data_text)
        
        for match in matches:
            ip = match.group(1)
            if ip in seen_ips: continue
            seen_ips.add(ip)
            
            start = max(0, match.start() - 60)
            end = min(len(data_text), match.end() + 60)
            context = data_text[start:end]
            
            port_match = re.search(r'\b(80|443|8080|8443|2052|2053|2082|2083|2086|2087|2095|2096)\b', context)
            port = port_match.group(1) if port_match else "443"
            
            isp = "CF 优选"
            if "电信" in context: isp = "CF 电信优选"
            elif "联通" in context: isp = "CF 联通优选"
            elif "移动" in context: isp = "CF 移动优选"
            
            results.append(f"{ip}:{port}#{isp}")

        if results:
            os.makedirs('public', exist_ok=True)
            with open('public/ip.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(results))
            print(f"🎉 大功告成！成功提取 {len(results)} 个 IP 并保存！")
        else:
            print("⚠️ 数据已拿到，但在文本中未匹配到符合格式的 IP。")

    except Exception as e:
        print(f"抓取发生错误: {e}")

if __name__ == '__main__':
    main()
