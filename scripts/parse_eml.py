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

    # Regex migliorato per IPv6 con word boundaries e validazione più rigorosa
    # Pattern che cerca sequenze di gruppi esadecimali separati da :
    # Con controllo che non siano preceduti o seguiti da altri caratteri alfanumerici
    ipv6_pattern = r'(?<![a-fA-F0-9])(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}(?![a-fA-F0-9])'
    ipv6_candidates = re.findall(ipv6_pattern, text)
    
    # Trova anche indirizzi IPv6 compressi (con ::)
    ipv6_compressed_pattern = r'(?<![a-fA-F0-9])(?:[0-9a-fA-F]{0,4}::?){1,7}[0-9a-fA-F]{0,4}(?![a-fA-F0-9])'
    ipv6_compressed = re.findall(ipv6_compressed_pattern, text)
    
    # Combina tutti i candidati IPv6
    all_ipv6_candidates = ipv6_candidates + ipv6_compressed

    # Validazione rigorosa con ipaddress e filtri aggiuntivi
    ipv6 = []
    for ip in all_ipv6_candidates:
        # Salta se troppo corto o se non contiene abbastanza ":"
        if len(ip) < 3 or ip.count(':') < 2:
            continue
            
        # Salta se contiene solo numeri (potrebbe essere parte di un numero più grande)
        if re.match(r'^[0-9]+:[0-9]+$', ip):
            continue
            
        try:
            # Verifica che sia un indirizzo IPv6 valido
            ipaddress.IPv6Address(ip)
            # Controlla che non sia un indirizzo di loopback semplice come "::1"
            # a meno che non sia effettivamente ::1
            if ip != "::1" and re.match(r'^::?[0-9]$', ip):
                continue
            ipv6.append(ip)
        except ValueError:
            continue

    # Classifica URL statici
    normal_urls, static_urls = set(), set()
    for url in urls:
        ext = urlparse(url).path.lower()
        (static_urls if ext.endswith(STATIC_EXTENSIONS) else normal_urls).add(url)

    return (
        list(normal_urls),
        list(static_urls),
        list(set(emails)),
        list(set(ipv4)),
        list(set(ipv6))
    )

# Parsing della mail
mail = mailparser.parse_from_file(sys.argv[1])
headers = mail.headers

# Estratti HTML e Plain
body_html = "\n".join(mail.text_html) if mail.text_html else ""
body_plain_raw = "\n".join(mail.text_plain) if mail.text_plain else ""

# Estratto HTML → testo
body_plain_html = ""
if body_html:
    soup = BeautifulSoup(body_html, 'html.parser')
    body_plain_html = soup.get_text(separator='\n', strip=True)

# Pulisce testi
body_plain = clean_text(body_plain_raw)
body_plain_html = clean_text(body_plain_html)

# IOC
combined = "\n".join(f"{k}: {v}" for k, v in headers.items()) + "\n\n" + body_plain
normal_urls, static_urls, emails, ipv4, ipv6 = extract_iocs(combined)

# Output JSON
output = {
    "subject": mail.subject,
    "from": mail.from_,
    "to": mail.to,
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