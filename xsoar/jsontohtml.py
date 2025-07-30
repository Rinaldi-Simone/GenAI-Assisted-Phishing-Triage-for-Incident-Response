import json
import tempfile
import os
import re

def render_ioc_section(title, iocs):
    if not iocs:
        return ''
    html = f'<h3>{title}</h3><table><tr><th>IOC</th><th>Score</th><th>Reliability</th><th>Vendor</th><th>Interpretazione</th></tr>'
    for ioc in iocs:
        html += f"<tr><td>{ioc.get('ioc')}</td><td>{ioc.get('score')}</td><td>{ioc.get('reliability')}</td><td>{ioc.get('vendor')}</td><td>{ioc.get('interpretation')}</td></tr>"
    html += '</table>'
    return html

def render_list(title, items):
    if not items:
        return ''
    html = f'<h3>{title}</h3><ul>'
    for item in items:
        html += f"<li>{item}</li>"
    html += '</ul>'
    return html

def main():
    try:
        payload_str = demisto.args().get("payload", "")
        if not payload_str:
            return_error("Parametro 'payload' mancante.")

        # Pulizia da blocchi markdown tipo ```json ... ```
        payload_str = re.sub(r'^```json\s*', '', payload_str.strip(), flags=re.IGNORECASE)
        payload_str = re.sub(r'\s*```$', '', payload_str.strip())

        payload = json.loads(payload_str)

        # Estrazione campi
        verdict = payload.get("verdict", "Unknown")
        severity = payload.get("severity", "Unknown")
        summary = payload.get("summary", "")

        metadata = payload.get("metadata", {})
        sender = metadata.get("sender", "")
        recipient = metadata.get("recipient", "")
        subject = metadata.get("subject", "")
        dkim = metadata.get("dkim", "")
        spf = metadata.get("spf", "")
        dmarc = metadata.get("dmarc", "")

        html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <title>Phishing Report</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, sans-serif;
      background-color: #f9f9fb;
      color: #222;
      padding: 2em;
      max-width: 900px;
      margin: auto;
    }}
    h1 {{
      color: #5b2c6f;
      text-align: center;
    }}
    h2 {{
      color: #76448a;
      border-bottom: 2px solid #ddd;
      padding-bottom: 0.2em;
    }}
    h3 {{
      color: #5b2c6f;
      margin-top: 1.5em;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1em;
      font-size: 0.95em;
    }}
    th, td {{
      border: 1px solid #ccc;
      padding: 0.6em;
      text-align: left;
    }}
    th {{
      background-color: #f2f2f2;
    }}
    ul {{
      margin-top: 0.5em;
      margin-left: 1.2em;
    }}
    .verdict {{
      font-size: 2em;
      font-weight: bold;
      text-align: center;
      color: {'#c0392b' if verdict.lower() == 'malicious' else '#27ae60' if verdict.lower() == 'benign' else '#f39c12'};
    }}
    .severity {{
      text-align: center;
      font-size: 1.2em;
      margin-bottom: 2em;
    }}
    .section {{
      margin-bottom: 2em;
    }}
  </style>
</head>
<body>
  <h1>Phishing Email Analysis Report</h1>
  <div class="verdict">{verdict}</div>
  <div class="severity"><strong>Severity:</strong> {severity}</div>

  <div class="section">
    <h2>1. Sintesi dell'analisi</h2>
    <p>{summary}</p>
  </div>

  <div class="section">
    <h2>2. Overview dell’incidente</h2>
    <table>
      <tr><th>Mittente</th><td>{sender}</td></tr>
      <tr><th>Destinatario</th><td>{recipient}</td></tr>
      <tr><th>Oggetto</th><td>{subject}</td></tr>
      <tr><th>DKIM</th><td>{dkim}</td></tr>
      <tr><th>SPF</th><td>{spf}</td></tr>
      <tr><th>DMARC</th><td>{dmarc}</td></tr>
    </table>
  </div>

  <div class="section">
    <h2>3. Analisi del contenuto</h2>
    {render_list("Osservazioni semantiche", payload.get("text_analysis", []))}
  </div>

  <div class="section">
    <h2>4. Indicatori di Compromissione (IOC)</h2>
    {render_ioc_section("Indirizzi IP", payload.get("ioc_analysis", {}).get("ips", []))}
    {render_ioc_section("Domini", payload.get("ioc_analysis", {}).get("domains", []))}
    {render_ioc_section("URL", payload.get("ioc_analysis", {}).get("urls", []))}
  </div>

  <div class="section">
    <h2>5. Header Analizzati</h2>
    {render_list("Header rilevanti", payload.get("smtp_headers", []))}
  </div>

  <div class="section">
    <h2>6. Next Steps consigliati</h2>
    {render_list("Azioni operative", payload.get("recommended_actions", []))}
  </div>
</body>
</html>
"""

        # Scrittura su file temporaneo
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
            f.write(html)
            html_path = f.name

        with open(html_path, "rb") as f:
            file_entry = fileResult("Phishing_Report.html", f.read(), file_type=EntryType.FILE)

        # Restituisce sia il file che il contenuto HTML in chiaro (context)
        return_results([
            file_entry,
            CommandResults(
                outputs_prefix="Phishing.Report",
                outputs={"html": html},
                readable_output="✅ Report HTML generato correttamente e allegato."
            )
        ])

    except Exception as e:
        return_error(f"Errore durante la generazione del report HTML: {str(e)}")

if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
