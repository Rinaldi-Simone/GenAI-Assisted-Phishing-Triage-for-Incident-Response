import sys
import json
import re
import ipaddress
from urllib.parse import urlparse

import mailparser
from bs4 import BeautifulSoup

# Estensioni considerate risorsa statica
STATIC_EXTENSIONS = (
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg',
    '.webp', '.css', '.js', '.ico', '.woff', '.woff2', '.ttf', '.eot'
)

def clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return ' '.join(lines)

def extract_iocs(text):
    urls = re.findall(r'https?://[^\s<>"\']+', text)
    emails = re.findall(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', text, re.I)

    ipv4 = re.findall(
        r"\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
        r"\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
        r"\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
        r"\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", text)

    ipv6_pattern = r'(?<![a-fA-F0-9])(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}(?![a-fA-F0-9])'
    ipv6_candidates = re.findall(ipv6_pattern, text)

    ipv6_compressed_pattern = r'(?<![a-fA-F0-9])(?:[0-9a-fA-F]{0,4}::?){1,7}[0-9a-fA-F]{0,4}(?![a-fA-F0-9])'
    ipv6_compressed = re.findall(ipv6_compressed_pattern, text)

    all_ipv6_candidates = ipv6_candidates + ipv6_compressed

    ipv6 = set()
    for ip in all_ipv6_candidates:
        if len(ip) < 3 or ip.count(':') < 2:
            continue
        if re.match(r'^[0-9]+:[0-9]+$', ip):
            continue
        try:
            ipaddress.IPv6Address(ip)
            if ip != "::1" and re.match(r'^::?[0-9]$', ip):
                continue
            ipv6.add(ip)
        except ValueError:
            continue

    normal_urls, static_urls = set(), set()
    for url in urls:
        ext = urlparse(url).path.lower()
        (static_urls if ext.endswith(STATIC_EXTENSIONS) else normal_urls).add(url)

    return (
        list(normal_urls),
        list(static_urls),
        list(set(emails)),
        list(set(ipv4)),
        list(ipv6)
    )

# Parsing della mail
mail = mailparser.parse_from_file(sys.argv[1])

# Pulisci headers
headers = {}
for k, v in mail.headers.items():
    if isinstance(v, list):
        headers[k.lower()] = [clean_text(str(i)) for i in v]
    else:
        headers[k.lower()] = clean_text(str(v))

# HTML e plain
body_html = clean_text("\n".join(mail.text_html)) if mail.text_html else ""
body_plain_raw = "\n".join(mail.text_plain) if mail.text_plain else ""

# Estrai testo visibile da HTML
body_plain_html = ""
if body_html:
    soup = BeautifulSoup(body_html, 'html.parser')
    body_plain_html = clean_text(soup.get_text(separator='\n', strip=True))

# Pulisci plain text
body_plain = clean_text(body_plain_raw)

# IOC
combined = "\n".join(f"{k}: {v}" for k, v in headers.items()) + "\n\n" + body_plain
normal_urls, static_urls, emails, ipv4, ipv6 = extract_iocs(combined)

# Output JSON
output = {
    "subject": clean_text(mail.subject or ""),
    "from": [clean_text(f"{name} <{addr}>") for name, addr in mail.from_],
    "to": [clean_text(f"{name} <{addr}>") for name, addr in mail.to],
    "headers": headers,
    "body_html": body_html,
    "body_plain": body_plain,
    "body_plain_html": body_plain_html,
    "iocs": {
        "urls_normal": normal_urls,
        "urls_static": static_urls,
        "emails": emails,
        "ipv4": ipv4,
        "ipv6": ipv6
    },
    "ioc_counts": {
        "urls_normal": len(normal_urls),
        "urls_static": len(static_urls),
        "emails": len(emails),
        "ipv4": len(ipv4),
        "ipv6": len(ipv6)
    }
}

print(json.dumps(output, indent=2))
