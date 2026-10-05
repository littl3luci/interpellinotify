#!/usr/bin/env python3
"""Controlla gli interpelli CN e manda su ntfy le righe nuove che contengono una KEYWORD."""
import base64, json, os, re, urllib.request
from pathlib import Path

URL = "https://servizi.istruzionepiemonte.it/interpello2025/ric_interpello_ambito_cn.php"
NTFY = os.environ["NTFY"]  # secret GitHub, es. https://ntfy.sh/<topic>
KEYWORDS = [""]  # "" = ogni riga nuova; es. ["A027", "MATEMATICA E FISICA"], match case-insensitive su tutta la riga
SEEN = Path(__file__).with_suffix(".seen.json")
PRIMA = 12  # righe già chiuse/cancellate al primo giro (11/09/2026), mai viste aperte

def rows(html):
    for tr in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        m = re.search(r'name="progr" value="(\d+)"', tr)
        if not m:
            continue
        tds = [re.sub(r"<[^>]+>|\s+", " ", td).strip() for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        yield m.group(1), tds

def main():
    html = urllib.request.urlopen(URL, timeout=30).read().decode("iso-8859-1")
    cur = dict(rows(html))
    seen = set(json.loads(SEEN.read_text())) if SEEN.exists() else set(cur)  # primo giro: nessuna notifica
    try:
        for progr, tds in cur.items():
            if progr in seen:
                continue
            line = " | ".join(tds[:7] + tds[8:10])
            if any(k.lower() in line.lower() for k in KEYWORDS):
                print(progr, line)
                try:
                    urllib.request.urlopen(urllib.request.Request(NTFY, data=line.encode(), headers={"Title": "=?UTF-8?B?" + base64.b64encode(f"{tds[2]} - {tds[1]}".encode()).decode() + "?=", "Tags": progr, "Priority": "high"}), timeout=30)
                except OSError as e:
                    print(progr, "ntfy fallito, riprovo al prossimo giro:", e)
                    continue  # non segno come visto -> ritentato, mai perso
            seen.add(progr)
        # le righe non spariscono mai, chiuse/cancellate perdono il progr: ogni chiusa deve avere un id visto (o PRIMA)
        chiuse = sum("Stato interpello*" not in tr for tr in re.findall(r"<tr>(.*?)</tr>", html, re.S)) - len(cur)
        persi = chiuse - len(seen - cur.keys()) - PRIMA
        if persi > 0:  # aperte e chiuse tra due giri (notte, cron saltato, ntfy giù)
            print("persi", persi)
            try:
                urllib.request.urlopen(urllib.request.Request(NTFY, data=f"{persi} interpelli aperti e chiusi senza notifica: {URL}".encode(), headers={"Title": "Interpelli persi", "Priority": "high"}), timeout=30)
                for _ in range(persi):
                    seen.add(f"perso-{len(seen)}")  # segnaposto: avviso una volta sola
            except OSError as e:
                print("ntfy fallito, riprovo al prossimo giro:", e)
    finally:
        # seen è solo-crescita (unione): una pagina vuota/parziale non lo azzera e non rinotifica tutto al giro dopo
        SEEN.write_text(json.dumps(sorted(seen)))

if __name__ == "__main__":
    main()
