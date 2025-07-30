def main():
    try:
        import json

        def parse_list(raw):
            if not raw:
                return []
            if isinstance(raw, str):
                try:
                    v = json.loads(raw)
                    return v if isinstance(v, list) else [v]
                except json.JSONDecodeError:
                    return [raw]
            if isinstance(raw, list):
                return raw
            return [raw]

        email_raw = demisto.args().get("email")
        if not email_raw:
            return_error("Argomento 'email' mancante.")

        email = json.loads(email_raw) if isinstance(email_raw, str) else email_raw

        # Campi base
        items = []
        for field in ["From", "To", "Subject", "Text"]:
            if email.get(field):
                items.append({"name": field.lower(), "text": email[field]})

        # Headers selezionati
        headers = email.get("Headers", [])
        if isinstance(headers, list):
            headers_seen = set()
            for h in headers:
                name = h.get("name")
                value = h.get("value")
                if name in {"Return-Path", "In-Reply-To", "Received", "X-Originating-IP", "X-Mailer", "X-Sender-IP"} and value:
                    key = f"{name}:{value}"
                    if key not in headers_seen:
                        items.append({"name": name, "text": value})
                        headers_seen.add(key)

        # Authentication-Results
        headers_map = email.get("HeadersMap") or {}
        auth_results = headers_map.get("Authentication-Results")
        if auth_results:
            items.append({"name": "Authentication-Results", "text": auth_results})

        # IOC inputs
        for arg_name, label in [("ips", "ip"), ("urls", "url"), ("domains", "domain")]:
            raw = demisto.args().get(arg_name)
            for entry in parse_list(raw):
                if entry:
                    items.append({"name": label, "text": entry})

        # Rimuove duplicati esatti
        seen = set()
        unique_items = []
        for i in items:
            key = json.dumps(i, sort_keys=True)
            if key not in seen:
                unique_items.append(i)
                seen.add(key)

        return_results(CommandResults(
            outputs_prefix="PresidioPrepared.items",
            outputs=unique_items,
            readable_output=tableToMarkdown("Prepared Presidio Items", unique_items)
        ))

    except Exception as e:
        return_error(f"Errore nella preparazione dei campi per Presidio: {str(e)}")

if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
