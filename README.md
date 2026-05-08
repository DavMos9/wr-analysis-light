# wr-analysis-light

Pipeline modulare per **Web Reputational Analysis** — raccolta, normalizzazione, pulizia e analisi del sentiment da 18 fonti web, senza dipendenze esterne da database o broker.

Versione "light" del progetto [web-reputational-analysis](https://github.com/DavMos9/web-reputational-analysis): un singolo target + topic per run, output su file JSON/CSV, integrazione diretta con IBM Cloud Pak for Data (DataStage).

---

## Quick start

```bash
git clone https://github.com/DavMos9/wr-analysis-light.git
cd wr-analysis-light
python -m venv .venv && source .venv/bin/activate
pip install -e ".[nlp]"
cp .env.example .env   # inserisci le tue API key
python main.py --target "Zendaya" --topic "Euphoria" --date-from 2026-04-01
```

---

## Flusso pipeline

```
collect → raw → normalize → clean → deduplicate → enrich → export
```

1. **Collectors** — interrogano le API in parallelo (ThreadPoolExecutor)
2. **Raw store** — persistenza del payload grezzo in `data/raw/` (disattivabile con `--no-raw`)
3. **Normalizer** — converte ogni risposta API in un `Record` standardizzato
4. **Cleaner** — strip, encoding UTF-8, filtro qualità (testo / titolo minimi)
5. **Date filter** — mantiene solo i record nel range `[date_from, date_until]`
6. **Deduplicator** — rimuove duplicati per URL e titolo+dominio
7. **Enricher** — language detection (`langdetect`) + sentiment analysis (XLM-RoBERTa multilingue)
8. **Exporters** — JSON · CSV · Summary per (target, topic)

---

## Utilizzo

```bash
python main.py --target TARGET --topic TOPIC --date-from YYYY-MM-DD [opzioni]
```

### Parametri

| Parametro | Tipo | Default | Descrizione |
|---|---|---|---|
| `--target` | string | obbligatorio | Entità da analizzare (es. `"Zendaya"`) |
| `--topic` | string | obbligatorio | Topic di ricerca (es. `"Euphoria"`) |
| `--date-from` | YYYY-MM-DD | obbligatorio | Inizio range di ricerca (incluso) |
| `--date-to` | YYYY-MM-DD | oggi | Fine range di ricerca (incluso) |
| `--sources` | list | vedi sotto | Fonti da interrogare |
| `--max-results` | int | `20` | Risultati massimi per fonte |
| `--no-raw` | flag | `False` | Non salva i payload grezzi |
| `--news-language` | string | `en` | Lingua per NewsAPI (ISO 639-1) |
| `--dry-run` | flag | `False` | Forza `max_results=1` — verifica API senza consumare quota |

### Fonti disponibili

| Fonte | ID | Chiave richiesta | Note |
|---|---|---|---|
| NewsAPI | `news` | `NEWS_API_KEY` | |
| GDELT DOC 2.0 | `gdelt` | — | Nessuna chiave |
| The Guardian | `guardian` | `GUARDIAN_API_KEY` | |
| New York Times | `nyt` | `NYT_API_KEY` | |
| Google News IT | `gnews_it` | — | RSS, no chiave |
| BBC News | `bbc` | — | RSS, no chiave |
| ANSA | `ansa` | — | RSS, no chiave |
| YouTube | `youtube` | `YOUTUBE_API_KEY` | |
| YouTube Comments | `youtube_comments` | `YOUTUBE_API_KEY` | |
| Bluesky | `bluesky` | `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` | |
| Mastodon | `mastodon` | opzionale | |
| Lemmy | `lemmy` | — | Nessuna chiave |
| Reddit | `reddit` | — | Endpoint JSON pubblico |
| Wikipedia | `wikipedia` | — | Fonte statica |
| Wikipedia Talk | `wikitalk` | — | Fonte statica |
| Brave Search | `brave` | `BRAVE_API_KEY` | |
| Stack Exchange | `stackexchange` | opzionale | **opt-in** |
| Hacker News | `hackernews` | — | **opt-in** |

**Default:** tutte le fonti eccetto `stackexchange` e `hackernews` (opt-in, richiedono `--sources` esplicito).

### Esempi

```bash
# Run base
python main.py --target "Zendaya" --topic "Euphoria" --date-from 2026-04-01

# Solo news editoriali, articoli in italiano
python main.py --target "Giorgia Meloni" --topic "governo" \
  --date-from 2026-01-01 --sources news guardian nyt gnews_it ansa \
  --news-language it

# Verifica API senza consumare quota
python main.py --target "Apple" --topic "iPhone" --date-from 2026-04-01 --dry-run

# Senza salvare raw, range temporale preciso
python main.py --target "OpenAI" --topic "GPT" \
  --date-from 2026-03-01 --date-to 2026-03-31 --no-raw
```

---

## Output

```
data/
├── raw/            ← payload grezzi (per debug/audit)
└── final/
    ├── ZendayaEuphoria.json          ← record individuali
    ├── ZendayaEuphoria.csv           ← record individuali (flat)
    └── ZendayaEuphoria_summary.json  ← riepilogo run
```

Il file è **unico per (target, topic)** e si aggiorna a ogni run: i nuovi record vengono aggiunti e deduplicati rispetto a quelli già presenti.

### Schema record JSON

```json
{
  "source":       "guardian",
  "title":        "Zendaya shines in Euphoria season 3",
  "text":         "...",
  "domain":       "theguardian.com",
  "language":     "en",
  "sentiment":    0.8821,
  "date":         "2026-04-05",
  "url":          "https://www.theguardian.com/...",
  "target":       "Zendaya",
  "topic":        "Euphoria",
  "retrieved_at": "2026-04-08T16:12:18+00:00"
}
```

### Schema summary JSON

```json
{
  "target":         "Zendaya",
  "topic":          "Euphoria",
  "execution_date": "2026-04-08",
  "scan_timestamp": "20260408T161218Z",
  "total_records":  143,
  "date_range":     { "from": "2026-04-01", "to": "2026-04-08" },
  "sources":        { "news": 18, "gdelt": 20, "guardian": 15, "..." : "..." }
}
```

---

## Installazione

### Requisiti

- Python 3.11+
- pip

### Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Solo pipeline (senza NLP)
pip install -e .

# Pipeline completa con language detection e sentiment analysis
pip install -e ".[nlp]"
```

Il flag `[nlp]` scarica il modello XLM-RoBERTa (`~1.1 GB`) al primo utilizzo. Senza `[nlp]` i campi `language` e `sentiment` restano `null`.

```bash
cp .env.example .env
# Inserisci le API key nel file .env
```

---

## Struttura del progetto

```
wr-analysis-light/
├── main.py                  ← entry point CLI
├── config.py                ← configurazione centralizzata
├── pyproject.toml
├── .env.example
├── collectors/              ← un file per fonte (18 collector)
├── normalizers/             ← conversione RawRecord → Record
├── pipeline/
│   ├── runner.py            ← orchestratore collect→export
│   ├── cleaner.py
│   ├── date_filter.py
│   ├── deduplicator.py
│   └── enricher.py
├── models/
│   └── record.py            ← RawRecord + Record
├── exporters/               ← JSON · CSV · Summary
├── storage/
│   └── raw_store.py
└── utils/
```

---

## Documentazione

La documentazione completa è disponibile nella [Wiki](../../wiki):

- [Installazione](../../wiki/Installazione)
- [Configurazione](../../wiki/Configurazione)
- [Utilizzo](../../wiki/Utilizzo)
- [Architettura](../../wiki/Architettura)
- [Collectors](../../wiki/Collectors)
- [Schema Dati](../../wiki/Schema-Dati)
- [Troubleshooting](../../wiki/Troubleshooting)

---

## Dipendenze principali

| Pacchetto | Uso |
|---|---|
| `requests` | HTTP collector |
| `python-dotenv` | Caricamento `.env` |
| `python-dateutil` | Parsing date flessibile |
| `Wikipedia-API` | Collector Wikipedia |
| `langdetect` *(nlp)* | Language detection |
| `transformers` *(nlp)* | Sentiment analysis (XLM-RoBERTa) |
| `torch` *(nlp)* | Backend inferenza |
