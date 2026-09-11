#!/usr/bin/env python3
"""Controlla gli interpelli CN e manda su ntfy le righe nuove che contengono una KEYWORD."""
import base64, json, os, re, urllib.request
from pathlib import Path

URL = "https://servizi.istruzionepiemonte.it/interpello2025/ric_interpello_ambito_cn.php"
NTFY = os.environ["NTFY"]  # secret GitHub, es. https://ntfy.sh/<topic>
KEYWORDS = [""]  # "" = ogni riga nuova; es. ["A027", "MATEMATICA E FISICA"], match case-insensitive su tutta la riga
SEEN = Path(__file__).with_suffix(".seen.json")

def rows(html):
    for tr in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        m = re.search(r'name="progr" value="(\d+)"', tr)
        if not m:
            continue
        tds = [re.sub(r"<[^>]+>|\s+", " ", td).strip() for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        yield m.group(1), tds

def main():
    html = urllib.request.urlopen(URL, timeout=30).read().decode("iso-8859-1")
    seen = set(json.loads(SEEN.read_text())) if SEEN.exists() else None
    cur = dict(rows(html))
    if seen is not None:
        for progr, tds in cur.items():
            line = " | ".join(tds[:7] + tds[8:10])
            if progr not in seen and any(k.lower() in line.lower() for k in KEYWORDS):
                print(progr, line)
                urllib.request.urlopen(urllib.request.Request(NTFY, data=line.encode(), headers={"Title": "=?UTF-8?B?" + base64.b64encode(f"{tds[2]} - {tds[1]}".encode()).decode() + "?=", "Tags": progr, "Priority": "high"}))
    SEEN.write_text(json.dumps(sorted(cur)))

if __name__ == "__main__":
    main()
