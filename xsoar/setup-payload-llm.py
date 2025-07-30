def main():
    ctx = demisto.context() or {}

    # 1) Leggi Presidio.Grouped (anche in subplaybook)
    grouped = {}
    if 'Presidio' in ctx:
        presidio_obj = ctx['Presidio']
        if isinstance(presidio_obj, list):
            for entry in presidio_obj:
                if isinstance(entry, dict) and 'Grouped' in entry:
                    grouped = entry.get('Grouped', {})
                    break
        elif isinstance(presidio_obj, dict):
            grouped = presidio_obj.get('Grouped', {})
    else:
        for v in ctx.values():
            if isinstance(v, dict) and 'Presidio' in v:
                presidio_obj = v['Presidio']
                if isinstance(presidio_obj, list):
                    for entry in presidio_obj:
                        if isinstance(entry, dict) and 'Grouped' in entry:
                            grouped = entry.get('Grouped', {})
                            break
                elif isinstance(presidio_obj, dict):
                    grouped = presidio_obj.get('Grouped', {})

    if isinstance(grouped, list):
        for g in grouped:
            if isinstance(g, dict):
                grouped = g
                break
        else:
            return_error("Nessun dizionario valido trovato in 'Grouped'.")
    elif not isinstance(grouped, dict):
        return_error("'Grouped' non è né una lista né un dizionario.")

    mail_entries    = grouped.get('mail', [])
    headers_entries = grouped.get('headers', [])
    ip_entries      = grouped.get('ips', [])
    domain_entries  = grouped.get('domains', [])
    url_entries     = grouped.get('urls', [])

    # 2) Deduplica mail per 'field'
    seen_fields = set()
    dedup_mail = []
    for m in mail_entries:
        fld = m.get('name')
        if fld and fld not in seen_fields:
            seen_fields.add(fld)
            dedup_mail.append(m)

    # 3) Deduplica headers per 'field'
    seen_header_fields = set()
    dedup_headers = []
    for h in headers_entries:
        fld = h.get('name')
        if fld and fld not in seen_header_fields:
            seen_header_fields.add(fld)
            dedup_headers.append(h)

    # 4) Deduplica generica per lista di dict basata su 'anonymized'
    def dedup_anonymized(entries):
        if not entries:
            return []
        seen = set()
        out = []
        for e in entries:
            anon = e.get('anonymized')
            if anon and anon not in seen:
                seen.add(anon)
                out.append(e)
        return out


    ip_entries     = dedup_anonymized(ip_entries)
    domain_entries = dedup_anonymized(domain_entries)
    url_entries    = dedup_anonymized(url_entries)

    # 5) Costruisci mappa da DBotScore (anche in subkeys)
    raw_scores = demisto.get(ctx, 'DBotScore') or []

    score_map = {}
    for rec in raw_scores:
        inds   = rec.get('Indicator')
        rels   = rec.get('Reliability')
        scores = rec.get('Score')
        vends  = rec.get('Vendor')
        if not isinstance(inds, list):
            inds   = [inds]
            rels   = [rels]
            scores = [scores]
            vends  = [vends]
        for i, ind in enumerate(inds):
            if ind:
                score_map[ind] = {
                    'score':       scores[i] if i < len(scores) else None,
                    'reliability': rels[i]   if i < len(rels)   else None,
                    'vendor':      vends[i]  if i < len(vends)  else None
                }

    # 6) Arricchisci liste
    def enrich_list(entries):
        return [
            {
                'anonymized':  e['anonymized'],
                'score':       score_map.get(e['original'], {}).get('score'),
                'reliability': score_map.get(e['original'], {}).get('reliability'),
                'vendor':      score_map.get(e['original'], {}).get('vendor')
            }
            for e in entries
        ]

    # 7) Crea payload (con headers)
    payload = {
        'mail': [
            {
                'field':      m['name'],
                'anonymized': m['anonymized']
            }
            for m in dedup_mail
        ],
        'headers': [
            {
                'field':      h['name'],
                'anonymized': h['anonymized']
            }
            for h in dedup_headers
        ],
        'ips':     enrich_list(ip_entries),
        'domains': enrich_list(domain_entries),
        'urls':    enrich_list(url_entries)
    }

    # 8) Scrivi in context
    return_results(CommandResults(
        outputs_prefix='LLM.Payload',
        outputs={'payload': payload},
        readable_output=tableToMarkdown('LLM Payload', payload)
    ))

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
