from curl_cffi import requests
import re
import os

def main():
    url = 'https://api.uouin.com/cloudflare.html'
    try:
        # impersonate="chrome110" 完美伪装真实浏览器指纹，绕过 CF 盾
        response = requests.get(url, impersonate="chrome110", timeout=30)
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
            # 创建 public 文件夹并将结果保存为 ip.txt
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
