# Architettura

## Pipeline logica

```
Input (--target + --topic + --date-from)
        │
        ▼
  ┌──────────────────────────────────────────────────┐
  │                COLLECTORS (18 fonti)             │
  │  news · gdelt · guardian · nyt · gnews_it        │
  │  bbc · ansa                                      │
  │  youtube · youtube_comments · bluesky            │
  │  mastodon · lemmy · reddit · stackexchange*      │
  │  wikipedia · wikitalk · brave · hackernews*      │
  │  (* opt-in: richiedono --sources esplicito)      │
  └──────────────────────────────────────────────────┘
        │
        ▼
  Persistenza raw  →  data/raw/
        │
        ▼
  ┌──────────────────────────┐
  │         PIPELINE         │
  │  1. Normalizer           │  RawRecord → Record (date YYYY-MM-DD, URL, domain)
  │  2. Cleaner              │  strip, encoding UTF-8, filtro qualità
  │  3. Date filter          │  mantiene solo record in [date_from, date_until]
  │  4. Deduplicator         │  URL + titolo+dominio
  │  5. Enricher             │  language detection + sentiment analysis
  └──────────────────────────┘
        │
        ▼
  ┌──────────────────────────┐
  │        EXPORTERS         │
  │  JSON · CSV · Summary    │
  └──────────────────────────┘
        │
        ▼
  data/final/  →  IBM Cloud Pak for Data (DataStage)
```

## Moduli

### models/record.py

Definisce i due tipi fondamentali della pipeline:

- **`RawRecord`** — payload grezzo prodotto dai collector. Contiene la risposta API senza alcuna trasformazione. Campi: `source`, `query`, `target`, `payload`, `retrieved_at`.
- **`Record`** — modello normalizzato e unico in tutta la pipeline. Prodotto dal normalizer, attraversa cleaner → date_filter → deduplicator → enricher → exporter. Vedi [Schema Dati](Schema-Dati) per la specifica completa.

### collectors/

Un file per fonte (18 collector). Ogni collector eredita da `BaseCollector` (definito in `collectors/base.py`) ed espone:

```python
def collect(self, target: str, query: str, max_results: int = 20,
            date_from: str | None = None, date_until: str | None = None,
            **kwargs) -> list[RawRecord]:
    ...
```

`BaseCollector` fornisce utility condivise (`_make_raw()`, `_now_iso()`, `_log_collected()`) e garantisce che ogni sottoclasse dichiari un `source_id` univoco.

Il modulo **`collectors/retry.py`** espone `http_get_with_retry()`, drop-in replacement di `requests.get()` con retry su HTTP 429 (jitter casuale) e 5xx (backoff esponenziale). Usato dai collector che non hanno logica di retry custom.

Le sorgenti **Wikipedia** e **WikiTalk** sono marcate `is_static = True`: se il file di output per (target, topic) esiste già e contiene record di quella fonte, vengono saltate automaticamente senza effettuare nuove richieste.

### normalizers/

Package separato con un modulo per fonte. Ogni modulo registra la propria funzione `_normalize(raw: RawRecord) -> Record` tramite `register(source_id, fn)`.

Il discovery avviene tramite **auto-discovery con `pkgutil`**: `normalizers/__init__.py` scansiona automaticamente il package e importa ogni file che non sia `registry.py` o `utils.py`. Aggiungere una nuova sorgente richiede solo la creazione del file — `__init__.py` non va mai modificato.

Il campo `topic` viene calcolato in un unico punto nel dispatcher centrale (`normalizers/registry.py`) tramite `_extract_topic(target, query)`: se la query inizia con `"{target} "`, restituisce la parte rimanente (es. `"Zendaya Euphoria"` → `"Euphoria"`); altrimenti restituisce la query intera.

**Fallback normalizer:** se una sorgente non ha normalizer registrato, viene tentata l'estrazione da chiavi comuni del payload (`title`/`headline`, `text`/`body`, `url`/`link`/`webUrl`, ecc.). Il record viene scartato solo se nessun URL è recuperabile. Il fallback emette un log `WARNING`.

### pipeline/

Applicati in sequenza da `PipelineRunner.run()`:

- **`cleaner.py`** — pulisce il testo (strip, encoding UTF-8), imposta `null` per valori mancanti, filtra record sotto soglia di qualità (`MIN_TEXT_LENGTH`, `MIN_TITLE_LENGTH` da `config.py`).
- **`date_filter.py`** — mantiene solo i record con `date` compresa in `[date_from, date_until]`. I record senza data (es. Wikipedia) vengono **sempre mantenuti**.
- **`deduplicator.py`** — rimuove duplicati a due livelli: URL identico (dopo stripping parametri tracking); titolo+dominio normalizzati (il secondo livello è saltato per sorgenti "parent-child" come `youtube_comments` e `wikitalk`).
- **`enricher.py`** — classe `Enricher` con lazy loading del modello. Arricchisce ogni `Record` con language detection (`langdetect`) e sentiment analysis (XLM-RoBERTa multilingue). Posizionato dopo la deduplicazione per non sprecare NLP su duplicati.

### pipeline/runner.py

`PipelineRunner` è l'orchestratore. Coordina `collect → normalize → clean → filter → deduplicate → enrich` ed è disaccoppiato da CLI e file I/O tramite dependency injection (`raw_store`, `enricher` iniettati nel costruttore). Il metodo `run()` restituisce `list[Record]`.

La raccolta è parallelizzata tramite `ThreadPoolExecutor` (I/O-bound HTTP). Due parametri in `PipelineConfig` controllano il comportamento:

| Parametro | Default | Descrizione |
|---|---|---|
| `parallel_collectors` | `True` | Se `False`, l'esecuzione torna sequenziale |
| `max_workers` | `8` | Numero massimo di task concorrenti |

L'ordine di output è deterministico anche in modalità parallela: i task vengono indicizzati e i `RawRecord` riordinati prima di uscire da `_collect()`.

### storage/raw_store.py

`RawStore` salva i `RawRecord` grezzi in `data/raw/` in formato JSON. È disabilitabile con `--no-raw`.

### exporters/

- **`json_exporter.py`** — file unico per (target, topic). Implementa la logica di merge: carica i record esistenti, aggiunge i nuovi, deduplica per URL e restituisce `(insieme_completo, n_aggiunti)`.
- **`csv_exporter.py`** — CSV flat riscritto a ogni run. Ogni riga include i campi del record + metadati del run corrente (`date_from`, `date_until`, `scan_timestamp`).
- **`summary_exporter.py`** — JSON di riepilogo: totale record, date range, distribuzione per fonte.

### config.py

Configurazione centralizzata: API key (da `.env`), soglie di qualità per il cleaner (`MIN_TEXT_LENGTH`, `MIN_TITLE_LENGTH`), istanze per i collector multi-istanza (Mastodon, Lemmy).

### utils/

- **`filename.py`** — `build_filename(target, topic)` produce il nome file canonico in CamelCase (es. `"Zendaya"` + `"Euphoria"` → `"ZendayaEuphoria"`).
- **`logging_config.py`** — configura il root logger e silenzia i logger di librerie terze rumorose.
- **`timestamp.py`** — `now_timestamp()` restituisce il timestamp nel formato `"YYYYMMDDTHHMMSSz"`.
- **`slugify.py`** — utility di normalizzazione stringhe.

## Fault tolerance

Ogni collector è avvolto in un `try/except` in `PipelineRunner._collect()`: un errore (rate limit, timeout, chiave mancante) produce un log di errore e la pipeline continua con le sorgenti restanti, senza interruzioni.
