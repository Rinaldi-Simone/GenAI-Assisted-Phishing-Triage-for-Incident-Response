import sys
import json
import re
from email import policy
from email.parser import BytesParser
from urllib.parse import urlparse

# Estensioni che indicano una risorsa statica (non HTML)
STATIC_EXTENSIONS = (
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg',
    '.webp', '.css', '.js', '.ico', '.woff', '.woff2', '.ttf', '.eot'
)

def extract_iocs(text):
    urls = re.findall(r'https?://[^\s<>"\']+', text)
    emails = re.findall(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', text, re.I)

    ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ipv6_pattern = r'\b(?:[A-F0-9]{1,4}:){1,7}[A-F0-9]{1,4}\b'

    ipv4 = re.findall(ipv4_pattern, text)
    ipv6 = re.findall(ipv6_pattern, text, re.I)

    # Separazione URL
    normal_urls = []
    static_urls = []
    for url in urls:
        path = urlparse(url).path.lower()
        if path.endswith(STATIC_EXTENSIONS):
            static_urls.append(url)
        else:
            normal_urls.append(url)

    return normal_urls, static_urls, emails, ipv4, ipv6

# Lettura e parsing dell’email
with open(sys.argv[1], 'rb') as f:
    msg = BytesParser(policy=policy.default).parse(f)

headers = dict(msg.items())
header_text = "\n".join(f"{k}: {v}" for k, v in headers.items())

body = msg.get_body(preferencelist=('plain', 'html'))
text = body.get_content() if body else ''
combined_text = f"{header_text}\n\n{text}"

normal_urls, static_urls, emails, ipv4, ipv6 = extract_iocs(combined_text)

# Output finale
output = {
    "subject": msg['subject'],
    "from": msg['from'],
    "to": msg['to'],
    "headers": headers,
    "body": text,
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
