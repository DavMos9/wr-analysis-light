# Schema Dati

Il tipo canonico è `Record`, definito in `models/record.py`.

## Struttura del record

```json
{
  "source":       "guardian",
  "title":        "Zendaya shines in Euphoria season 3",
  "text":         "The actress delivers another standout performance...",
  "domain":       "theguardian.com",
  "language":     "en",
  "sentiment":    0.8821,
  "date":         "2026-04-05",
  "url":          "https://www.theguardian.com/tv-and-radio/2026/apr/05/...",
  "target":       "Zendaya",
  "topic":        "Euphoria",
  "retrieved_at": "2026-04-08T16:12:18+00:00"
}
```

## Definizione campi

| Campo | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `source` | string | sì | Identificatore della sorgente (vedi tabella sotto) |
| `title` | string | sì | Titolo del contenuto |
| `text` | string | sì | Corpo del testo o estratto. Troncato a 1500 caratteri al confine di frase |
| `domain` | string | no | Dominio estratto automaticamente dall'URL |
| `language` | string | no | Codice lingua ISO 639-1. Fornito dalla sorgente dove disponibile; altrimenti rilevato da `langdetect`. `null` se non determinabile |
| `sentiment` | float | no | Score `[-1.0, 1.0]` calcolato come `P(positive) − P(negative)` da XLM-RoBERTa multilingue. `null` se lingua non supportata, testo troppo corto, o dipendenze `[nlp]` non installate |
| `date` | string | no | Data di pubblicazione `YYYY-MM-DD`. `null` se assente o non parsabile |
| `url` | string | sì | URL completo del contenuto |
| `target` | string | sì | Entità oggetto dell'analisi |
| `topic` | string | no | Topic di ricerca, estratto dalla query rimuovendo il target. Stringa vuota se la query coincide con il target |
| `retrieved_at` | string | no | Timestamp ISO 8601 della raccolta |

## Campi obbligatori

Un `Record` è valido solo se questi campi sono presenti e non vuoti:

- `source`
- `target`
- `url`
- `title`
- `text`

## Valori di `source`

| Valore | Fonte |
|---|---|
| `news` | NewsAPI |
| `gdelt` | GDELT DOC 2.0 |
| `guardian` | The Guardian |
| `nyt` | New York Times |
| `gnews_it` | Google News Italia (RSS) |
| `bbc` | BBC News (RSS) |
| `ansa` | ANSA (RSS) |
| `youtube` | YouTube Data API v3 |
| `youtube_comments` | YouTube Comments |
| `bluesky` | Bluesky (AT Protocol) |
| `mastodon` | Mastodon (Fediverse) |
| `lemmy` | Lemmy (Fediverse) |
| `reddit` | Reddit (endpoint JSON pubblico) |
| `wikipedia` | Wikipedia |
| `wikitalk` | Wikipedia Talk Pages |
| `brave` | Brave Search API |
| `stackexchange` | Stack Exchange (opt-in) |
| `hackernews` | Hacker News (opt-in) |

## Regole di normalizzazione

- **Date:** formato `YYYY-MM-DD`. `null` se non disponibile o non parsabile.
- **URL:** completi, con protocollo `https://`. Parametri di tracking (`utm_*`, `fbclid`, ecc.) rimossi prima della deduplicazione.
- **Domain:** estratto automaticamente tramite `urllib.parse`.
- **Stringhe:** strip degli spazi, encoding UTF-8 NFC.
- **Valori mancanti:** `null` (mai stringa vuota `""`).

## Deduplicazione

Due livelli applicati in sequenza:

1. **URL identico** — stesso URL dopo rimozione dei parametri di tracking. Per `wikitalk` il fragment URL (`#Section`) viene preservato come chiave discriminante.
2. **Titolo + dominio** — stessa combinazione normalizzata (lowercase, punteggiatura rimossa). Saltato per `youtube_comments` e `wikitalk`, dove più record distinti condividono lo stesso titolo.

## Export

### JSON record-level

File: `{Target}{Topic}.json`

Campi nell'ordine canonico (definito in `Record._EXPORT_FIELDS`):
`source`, `title`, `text`, `domain`, `language`, `sentiment`, `date`, `url`, `target`, `topic`, `retrieved_at`

Il file è unico per (target, topic). I nuovi record vengono aggiunti e deduplicati rispetto a quelli già presenti a ogni run.

### CSV record-level

File: `{Target}{Topic}.csv`

Colonne: `source`, `date`, `target`, `topic`, `language`, `sentiment`, `url`, `retrieved_at` + **metadati run**: `date_from`, `date_until`, `scan_timestamp`.

I metadati run (`date_from`, `date_until`, `scan_timestamp`) sono identici per tutti i record del file e riflettono i parametri del run corrente. Utili per tracciabilità in DataStage.

Il CSV viene **riscritto** a ogni run (non è un append): contiene sempre l'insieme completo e deduplicato.

### Summary JSON

File: `{Target}{Topic}_summary.json`

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
    "youtube":  14
  }
}
```

| Campo | Descrizione |
|---|---|
| `target` | Entità analizzata |
| `topic` | Topic di ricerca |
| `execution_date` | Data del run (`YYYY-MM-DD`) |
| `scan_timestamp` | Timestamp del run (`YYYYMMDDTHHMMSSz`) |
| `total_records` | Numero totale di record nel file (inclusi quelli dei run precedenti) |
| `date_range` | Range delle date dei record presenti (`min`, `max` su `date` non null) |
| `sources` | Conteggio record per sorgente |

## Naming convention file

Il nome file viene derivato dal target e dal topic tramite `build_filename(target, topic)` in `utils/filename.py`:

- Ogni parola viene capitalizzata (CamelCase)
- Gli spazi vengono rimossi
- I caratteri non alfanumerici vengono eliminati

Esempi:

| target | topic | Filename |
|---|---|---|
| `"Zendaya"` | `"Euphoria"` | `ZendayaEuphoria` |
| `"Giorgia Meloni"` | `"governo"` | `GiorgiaMeloniGoverno` |
| `"Elon Musk"` | `"Tesla"` | `ElonMuskTesla` |
| `"Apple"` | `"iPhone 16"` | `AppleIPhone16` |
