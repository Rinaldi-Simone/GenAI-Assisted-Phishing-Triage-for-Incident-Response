import requests
import json

def analyze_and_anonymize(text, analyzer_url, anonymizer_url):
    lang = demisto.args().get("language")
    # ANALYZE
    res_analyze = requests.post(
        analyzer_url,
        json={"text": text, "language": lang},
        headers={"Content-Type": "application/json"},
        verify=False
    )
    res_analyze.raise_for_status()
    analysis_results = res_analyze.json()

    # ANONYMIZE
    body = {
        "text": text,
        "analyzer_results": analysis_results,
        "anonymizers": {
            "EMAIL_ADDRESS":   {"type": "LLMAnonymizer", "params": {"entity_type": "EMAIL_ADDRESS"}},
            "URL":             {"type": "LLMAnonymizer", "params": {"entity_type": "URL"}},
            "DOMAIN_NAME":     {"type": "LLMAnonymizer", "params": {"entity_type": "DOMAIN_NAME"}},
            "IPV4_ADDRESS":    {"type": "LLMAnonymizer", "params": {"entity_type": "IPV4_ADDRESS"}},
            "IPV6_ADDRESS":    {"type": "LLMAnonymizer", "params": {"entity_type": "IPV6_ADDRESS"}},
            "DATE_TIME":       {"type": "LLMAnonymizer", "params": {"entity_type": "DATE_TIME"}},
            "DEFAULT":         {"type": "replace",       "new_value": "<ANONYMIZED>"}
        }
    }
    res_anonymize = requests.post(
        anonymizer_url,
        json=body,
        headers={"Content-Type": "application/json"},
        verify=False
    )
    res_anonymize.raise_for_status()
    anonymized = res_anonymize.json()
    return anonymized.get("text", "")

def presidio_analyze_and_anonymize_command():
    # build URLs
    base_analyzer   = demisto.params().get("analyzer_url", "").rstrip("/")
    base_anonymizer = demisto.params().get("anonymizer_url", "").rstrip("/")
    analyzer_url    = f"{base_analyzer}/analyze"
    anonymizer_url  = f"{base_anonymizer}/anonymize"

    # prendo gli items in input
    items_arg = demisto.args().get("items")
    if not items_arg:
        return_error("Devi fornire `items`.")

    items = json.loads(items_arg) if isinstance(items_arg, str) else items_arg

    # definisco i cluster
    mail_fields = {"from", "to", "subject", "text"}
    groups = {
        "mail":    [],   # [(field_name, text), ...]
        "ips":     [],   # [text, ...]
        "domains": [],
        "urls":    [],
        "headers": []    # nuovi header arbitrari
    }

    # raggruppo
    for entry in items:
        name = entry.get("name", "").lower()
        text = entry.get("text") or entry.get("value") or ""
        if not text:
            continue

        if name in mail_fields:
            groups["mail"].append((name, text))
        elif name == "ip":
            groups["ips"].append(text)
        elif name == "domain":
            groups["domains"].append(text)
        elif name == "url":
            groups["urls"].append(text)
        else:
            # qui colleziono tutti gli altri header (anche authentication‑results)
            groups["headers"].append((name, text))

    # funzione di elaborazione
    def process_list(lst, is_tuple):
        out = []
        seen = set()

        if is_tuple:
            for field_name, txt in lst:
                key = f"{field_name}:{txt}"
                if key in seen:
                    continue
                seen.add(key)
                anon = analyze_and_anonymize(txt, analyzer_url, anonymizer_url)
                out.append({
                    "name":       field_name,
                    "original":   txt,
                    "anonymized": anon
                })
        else:
            for txt in lst:
                if txt in seen:
                    continue
                seen.add(txt)
                anon = analyze_and_anonymize(txt, analyzer_url, anonymizer_url)
                out.append({
                    "original":   txt,
                    "anonymized": anon
                })
        return out

    # costruisco il JSON di output, includendo anche headers
    results = {
        "mail":    process_list(groups["mail"],    is_tuple=True),
        "headers": process_list(groups["headers"], is_tuple=True),
        "ips":     process_list(groups["ips"],     is_tuple=False),
        "domains": process_list(groups["domains"], is_tuple=False),
        "urls":    process_list(groups["urls"],    is_tuple=False),
    }

    # output
    return_results(CommandResults(
        outputs_prefix="Presidio.Grouped",
        outputs=results,
        readable_output=tableToMarkdown("Presidio Anonymization Results", results)
    ))

def main():
    try:
        if demisto.command() == "presidio-analyze-and-anonymize":
            presidio_analyze_and_anonymize_command()
        else:
            return_error(f"Comando non riconosciuto: {demisto.command()}")
    except Exception as e:
        return_error(f"Errore durante l'esecuzione del comando: {str(e)}")

if __name__ in ("__builtin__", "builtins", "__main__"):
    main()
