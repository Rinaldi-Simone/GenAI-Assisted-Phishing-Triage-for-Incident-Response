# parse_eml.py
import sys
import json
from email import policy
from email.parser import BytesParser
import re

def extract_iocs(text):
    urls = re.findall(r'https?://[^\s<>"\']+', text)
    emails = re.findall(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', text, re.I)
    ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text)

    return {
        "urls": urls,
        "emails": emails,
        "ips": ips,
        "ioc_counts": {
            "urls": len(urls),
            "emails": len(emails),
            "ips": len(ips)
        }
    }

with open(sys.argv[1], 'rb') as f:
    msg = BytesParser(policy=policy.default).parse(f)

body = msg.get_body(preferencelist=('plain', 'html'))
text = body.get_content() if body else ''

iocs = extract_iocs(text)

output = {
    "subject": msg['subject'],
    "from": msg['from'],
    "to": msg['to'],
    "headers": dict(msg.items()),
    "body": text,
    "iocs": {
        "urls": iocs["urls"],
        "emails": iocs["emails"],
        "ips": iocs["ips"]
    },
    "ioc_counts": iocs["ioc_counts"]
}

print(json.dumps(output))
