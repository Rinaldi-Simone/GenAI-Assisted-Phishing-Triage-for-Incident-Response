import json

def recursive_deanonymize(obj, mapping):
    if isinstance(obj, str):
        for anon, orig in mapping.items():
            obj = obj.replace(anon, orig)
        return obj
    elif isinstance(obj, list):
        return [recursive_deanonymize(item, mapping) for item in obj]
    elif isinstance(obj, dict):
        return {key: recursive_deanonymize(value, mapping) for key, value in obj.items()}
    else:
        return obj

def main():
    try:
        ctx = demisto.context() or {}
        llm = ctx.get("AnythingLLM", {})
        ws = llm.get("workspace_settings", [])
        if len(ws) < 2 or not isinstance(ws[1], dict):
            return_error("Impossibile trovare workspace_settings[1] in AnythingLLM.")
        text = ws[1].get("textResponse")
        if not text:
            return_error("Campo 'textResponse' mancante in workspace_settings[1].")

        # Carica il batch
        batch_arg = demisto.args().get("batch")
        if not batch_arg:
            return_error("Argomento 'batch' mancante.")
        batch = json.loads(batch_arg) if isinstance(batch_arg, str) else batch_arg

        # Prepara dizionario di mapping anonymized → original
        mapping = {}
        attempted_anon_keys = []

        for category in ("domains", "ips", "urls", "mail", "headers"):
            entries = batch.get(category) or []
            for entry in entries:
                if isinstance(entry, dict):
                    anon = str(entry.get("anonymized") or "").strip()
                    orig = str(entry.get("original") or "").strip()
                    if anon and orig:
                        if anon not in mapping:
                            mapping[anon] = orig
                            attempted_anon_keys.append(anon)
                        if anon.startswith("<") and anon.endswith(">"):
                            stripped = anon[1:-1]
                            if stripped not in mapping:
                                mapping[stripped] = orig
                                attempted_anon_keys.append(stripped)

        # Prova a de-anonimizzare come JSON
        try:
            parsed = json.loads(text)
            deanonymized = recursive_deanonymize(parsed, mapping)
            result_text = json.dumps(deanonymized, ensure_ascii=False, indent=2)
        except Exception:
            result_text = text
            for anon, orig in mapping.items():
                result_text = result_text.replace(anon, orig)

        readable_output = (
            "✅ Testo de-anonimizzato correttamente.\n\n"
            f"**Chiavi cercate nel testo:**\n```\n{json.dumps(attempted_anon_keys, indent=2)}\n```"
        )

        return_results(CommandResults(
            outputs_prefix="DeanonymizedText",
            outputs={"text": result_text},
            readable_output=readable_output
        ))

    except Exception as e:
        return_error(f"Errore durante la de-anonimizzazione: {str(e)}")

if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
