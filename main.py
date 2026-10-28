from curl_cffi import requests
import re
import os
import time
import random

def main():
    # 核心修改1：在 URL 后加入随机时间戳，强行打破 Cloudflare 的 CDN 缓存
    timestamp = int(time.time())
    url = f'https://api.uouin.com/cloudflare.html?_nocache={timestamp}&r={random.random()}'
    
    # 核心修改2：深度伪装请求头，假装是国内真实用户，防止机房 IP 被地域歧视
    headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://api.uouin.com/'
    }

    try:
        # impersonate="chrome110" 完美伪装浏览器指纹，绕过盾
        response = requests.get(url, impersonate="chrome110", headers=headers, timeout=30)
        response.encoding = 'utf-8'
        html = response.text

        seen_ips = set()
        results = []
        
        # 兼容性分割 HTML
        blocks = re.split(r'(?i)<tr[^>]*>|<li[^>]*>|<div[^>]*>|<br\s*/?>|\n', html)
        
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
            print(f"成功提取 {len(results)} 个 IP并保存。")
        else:
            print("未提取到任何 IP。")

    except Exception as e:
        print(f"抓取发生错误: {e}")

if __name__ == '__main__':
    main()
