
import json
from pathlib import Path

basis = Path(__file__).resolve().parent
texte_ordner = basis / "texte"
json_datei = basis / "predigten.json"

from datetime import datetime, timezone

datums_datei = basis / "predigt_daten.json"

if datums_datei.exists():
    datums_map = json.loads(
        datums_datei.read_text(encoding="utf-8-sig")
    )
else:
    datums_map = {}

heute = datetime.now(timezone.utc).strftime("%Y-%m-%d")

if not texte_ordner.is_dir():
    raise SystemExit("FEHLER: Ordner texte fehlt.")

daten = json.loads(
    json_datei.read_text(encoding="utf-8-sig")
)

predigten = daten["predigten"]

if not isinstance(predigten, list):
    raise SystemExit("FEHLER: Ungueltige Predigtliste.")

vorhandene = {
    eintrag["datei"]
    for eintrag in predigten
}

txt_dateien = sorted(
    texte_ordner.glob("*.txt"),
    key=lambda p: p.name.casefold()
)

if not txt_dateien:
    raise SystemExit("SICHERHEITSSTOPP: Keine TXT-Dateien.")

neu = 0

for datei in txt_dateien:
    if datei.name in vorhandene:
        continue

    titel = datei.stem

    predigten.append({
        "titel": titel,
        "datei": datei.name,
        "video": titel + ".mp4"
    })


    vorhandene.add(datei.name)
    neu += 1

    if datei.name not in datums_map:
        datums_map[datei.name] = heute


    print("Neue Predigt:", titel)

if neu > 0:
    json_datei.write_text(
        json.dumps(
            daten,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

print("TXT-Dateien gefunden:", len(txt_dateien))
print("Neue Predigten:", neu)
print("Predigten insgesamt:", len(predigten))
print("Bestehende Zuordnungen beibehalten.")
