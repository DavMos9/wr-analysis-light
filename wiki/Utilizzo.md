# Utilizzo

## Sintassi base

```bash
python main.py --target "ENTITÀ" --topic "TOPIC" --date-from YYYY-MM-DD [opzioni]
```

La query finale inviata alle API viene composta automaticamente come `"{target} {topic}"`. Se il topic contiene già parole del target, viene usato as-is (passthrough).

| Input CLI | Query effettiva |
|---|---|
| `--target "Zendaya" --topic "Euphoria"` | `"Zendaya Euphoria"` |
| `--target "Giorgia Meloni" --topic "governo"` | `"Giorgia Meloni governo"` |
| `--target "Apple" --topic "Apple iPhone"` | `"Apple iPhone"` (passthrough) |

## Esempi

### Run base

```bash
python main.py --target "Zendaya" --topic "Euphoria" --date-from 2026-04-01
```

### Range temporale esplicito

```bash
python main.py --target "OpenAI" --topic "GPT" \
  --date-from 2026-03-01 --date-to 2026-03-31
```

### Solo alcune fonti

```bash
python main.py --target "Apple" --topic "iPhone" \
  --date-from 2026-04-01 --sources news gdelt guardian brave
```

### News italiane

```bash
python main.py --target "Giorgia Meloni" --topic "governo" \
  --date-from 2026-01-01 --news-language it \
  --sources news gnews_it ansa guardian
```

### Senza salvare i raw (più veloce)

```bash
python main.py --target "Ferrari" --topic "F1" --date-from 2026-04-01 --no-raw
```

### Dry run (verifica API senza consumare quota)

```bash
python main.py --target "Apple" --topic "iPhone" --date-from 2026-04-01 --dry-run
```

Forza `max_results=1` per ogni fonte. Utile per verificare che tutte le chiavi API siano valide prima di un run completo.

### Fonti opt-in

Le fonti **`stackexchange`** e **`hackernews`** non sono incluse nel set di default — richiedono invocazione esplicita:

```bash
# Stack Exchange: utile per target tecnici (librerie, framework)
python main.py --target "pandas" --topic "dataframe" \
  --date-from 2026-01-01 --sources stackexchange news

# Hacker News: utile per target tech/startup
python main.py --target "OpenAI" --topic "GPT" \
  --date-from 2026-01-01 --sources hackernews news guardian
```

## Parametri disponibili

| Parametro | Tipo | Default | Descrizione |
|---|---|---|---|
| `--target` | string | obbligatorio | Entità da analizzare (es. `"Zendaya"`) |
| `--topic` | string | obbligatorio | Topic di ricerca (es. `"Euphoria"`) |
| `--date-from` | YYYY-MM-DD | obbligatorio | Inizio range di ricerca (incluso) |
| `--date-to` | YYYY-MM-DD | oggi | Fine range di ricerca (incluso). Default: data odierna |
| `--sources` | list | vedi sotto | Fonti da interrogare. Default: tutte eccetto `stackexchange` e `hackernews` |
| `--max-results` | int | `20` | Risultati massimi per fonte |
| `--no-raw` | flag | `False` | Non salva i payload grezzi in `data/raw/` |
| `--news-language` | string | `en` | Lingua per NewsAPI (codice ISO 639-1, es. `it`, `fr`) |
| `--dry-run` | flag | `False` | Forza `max_results=1` per fonte — verifica API senza consumare quota |

## Output

```
data/
├── raw/    ← payload originali delle API (per debug/audit)
└── final/
    ├── ZendayaEuphoria.json          ← record individuali
    ├── ZendayaEuphoria.csv           ← record individuali (flat, con metadati run)
    └── ZendayaEuphoria_summary.json  ← riepilogo statistico
```

Il file è **unico per (target, topic)** e si aggiorna a ogni run: i nuovi record vengono aggiunti e deduplicati rispetto a quelli già presenti. L'output CLI mostra quanti record sono stati aggiunti nel run corrente e quanti sono in totale nel file.

### Esempio output CLI

```
2026-04-08T16:12:15 [INFO] Query composta: 'Zendaya Euphoria'
2026-04-08T16:12:15 [INFO] Range date: 2026-04-01 → 2026-04-08
2026-04-08T16:12:15 [INFO] File output: ZendayaEuphoria
2026-04-08T16:12:16 [INFO] [news] Raccolti 18 record
2026-04-08T16:12:17 [INFO] [gdelt] Raccolti 20 record
...
2026-04-08T16:12:30 [INFO] Puliti: 143 validi, 12 scartati.
2026-04-08T16:12:30 [INFO] Filtro date [2026-04-01, 2026-04-08]: 141 mantenuti, 2 scartati.
2026-04-08T16:12:30 [INFO] Deduplicati: 8 rimossi, 133 unici.
2026-04-08T16:12:44 [INFO] === Pipeline completata: 133 record finali ===

Aggiunti in questo run: 133  |  Totale nel file: 133
Output: data/final/ZendayaEuphoria.json | .csv | _summary.json
```

### Esempio record JSON

```json
{
  "source":       "guardian",
  "title":        "Zendaya shines in Euphoria season 3",
  "text":         "The actress delivers another standout performance...",
  "domain":       "theguardian.com",
  "language":     "en",
  "sentiment":    0.8821,
  "date":         "2026-04-05",
  "url":          "https://www.theguardian.com/tv-and-radio/2026/apr/05/zendaya-euphoria",
  "target":       "Zendaya",
  "topic":        "Euphoria",
  "retrieved_at": "2026-04-08T16:12:18+00:00"
}
```

### Esempio summary JSON

```json
{
  "target":         "Zendaya",
  "topic":          "Euphoria",
  "execution_date": "2026-04-08",
  "scan_timestamp": "20260408T161218Z",
  "total_records":  133,
  "date_range": {
    "from": "2026-04-01",
    "to":   "2026-04-08"
  },
  "sources": {
    "gdelt":    20,
    "news":     18,
    "guardian": 15,
    "youtube":  14,
    "reddit":   12,
    "bluesky":  10,
    "mastodon":  8,
    "brave":     8,
    "gnews_it":  7,
    "nyt":       6,
    "bbc":       5,
    "ansa":      4,
    "wikipedia": 1,
    "wikitalk":  1
  }
}
```

## Codici lingua (--news-language)

Il parametro `--news-language` filtra la lingua **in ingresso** per NewsAPI. La colonna **Sentiment** indica se la lingua è supportata dall'enricher (XLM-RoBERTa).

| Codice | Lingua | Sentiment |
|:---:|---|:---:|
| `ar` | Arabo | ✅ |
| `de` | Tedesco | ✅ |
| `en` | Inglese | ✅ |
| `es` | Spagnolo | ✅ |
| `fr` | Francese | ✅ |
| `hi` | Hindi | ✅ |
| `it` | Italiano | ✅ |
| `pt` | Portoghese | ✅ |
| `zh` | Cinese | ❌ |
| `ja` | Giapponese | ❌ |
| `ru` | Russo | ❌ |

Le lingue senza supporto sentiment vengono comunque raccolte e incluse nel dataset — il campo `sentiment` resterà `null`.
