import json
import subprocess
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

basis = Path(__file__).resolve().parent

predigten = json.loads(
    (basis / "predigten.json").read_text(encoding="utf-8-sig")
)["predigten"]

links = json.loads(
    (basis / "videolinks.json").read_text(encoding="utf-8-sig")
)

zeilen = (basis / "youtube_sync_aktuell.txt").read_text(
    encoding="utf-8-sig"
).splitlines()

def normalisiere(text):
    text = text.removesuffix(".mp4").casefold()
    text = text.replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        c for c in text if not unicodedata.combining(c)
    )
    return "".join(re.findall(r"[a-z0-9]+", text))

def ist_oeffentlich(video_id):
    adresse = f"https://www.youtube.com/watch?v={video_id}"
    try:
        ergebnis = subprocess.run(
            [
                sys.executable, "-m", "yt_dlp",
                "--skip-download",
                "--no-warnings",
                "--print", "%(availability)s",
                adresse
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if video_id == "OU7gtkVSDwc":
            print("=== YOUTUBE-OEFFENTLICHKEIT ===")
            print("Returncode:", ergebnis.returncode)
            print("Stdout:", repr(ergebnis.stdout.strip()))
            print("Stderr:", ergebnis.stderr[-1500:])
            print("=== ENDE YOUTUBE-OEFFENTLICHKEIT ===")

        return (
            ergebnis.returncode == 0
            and ergebnis.stdout.strip() == "public"
        )

    except (subprocess.TimeoutExpired, OSError):
        return False
videos = defaultdict(set)

for zeile in zeilen:
    teile = zeile.split("\t", 1)
    if len(teile) != 2:
        continue

    video_id, titel = teile

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        continue

    videos[normalisiere(titel)].add(video_id)

if sum(len(ids) for ids in videos.values()) < 400:
    sys.exit("SICHERHEITSSTOPP: YouTube-Liste unvollstaendig.")

neue_links = dict(links)
hinzugefuegt = 0
mehrdeutig = 0

for predigt in predigten:
    datei = predigt.get("video", "")

    if not datei:
        continue

    if datei in neue_links and "youtube.com" in neue_links[datei]:
        continue

    titel = Path(datei).stem
    kandidaten = videos.get(normalisiere(titel), set())
    
    if "WER IST GOTT" in titel.upper():
        print("=== DIAGNOSE WER IST GOTT ===", flush=True)
        print("Gesuchter Titel:", titel, flush=True)
        print("Normalisierter Titel:", normalisiere(titel), flush=True)
        print("Gefundene Video-IDs:", sorted(kandidaten), flush=True)
        print(
            "Erwartete Video-ID gefunden:",
            "HGPstOAQras" in kandidaten,
            flush=True
        )

        if len(kandidaten) == 1:
            video_id = next(iter(kandidaten))
            print(
                "Oeffentlichkeitspruefung:",
                ist_oeffentlich(video_id),
                flush=True
            )

        print("=== ENDE DIAGNOSE ===", flush=True)

    if "Die Religion ist nicht daran interessiert" in titel:
        print("=== DIAGNOSE NEUE PREDIGT ===")
        print("Gesuchter Titel:", titel)
        print("Normalisierter Titel:", normalisiere(titel))
        print("Gefundene Kandidaten:", kandidaten)
        print("Erwartete Video-ID vorhanden:",
              "OU7gtkVSDwc" in kandidaten)
        if len(kandidaten) == 1:
            print("Oeffentlich:", ist_oeffentlich(next(iter(kandidaten))))
        print("=== ENDE DIAGNOSE ===")

       if len(kandidaten) == 1:
        video_id = next(iter(kandidaten))
        neue_links[datei] = (
            f"https://www.youtube.com/watch?v={video_id}"
        )
        hinzugefuegt += 1
        print(f"NEUER TREFFER: {datei}")
        print(f"YOUTUBE-LINK: {neue_links[datei]}")
    elif len(kandidaten) > 1:
        mehrdeutig += 1

ausgabe = basis / "videolinks_sync_test.json"
ausgabe.write_text(
    json.dumps(neue_links, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)

print("Neue Zuordnungen:", hinzugefuegt)
print("Mehrdeutige Titel:", mehrdeutig)
print("YouTube-Links insgesamt:", sum(
    "youtube.com" in wert for wert in neue_links.values()
))
print("Testdatei:", ausgabe.name)
print("GitHub wurde nicht veraendert.")
