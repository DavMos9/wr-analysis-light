# Collectors

La pipeline interroga 18 fonti eterogenee. Tutte raccolgono dati nel range `[date_from, date_until]` dove supportato dall'API; per le fonti senza filtro temporale nativo, il filtro viene applicato nella fase `date_filter` della pipeline.

## Fonti News / Media

### news — NewsAPI

| Attributo | Valore |
|---|---|
| Source ID | `news` |
| API | NewsAPI v2 (`everything` endpoint) |
| Chiave | `NEWS_API_KEY` |
| Quota gratuita | 100 richieste/giorno |
| Filtro date | nativo (parametro `from`/`to`) |

Interroga l'endpoint `everything` con la query composta. Supporta il parametro `--news-language` per filtrare la lingua in ingresso (default `en`).

### gdelt — GDELT DOC 2.0

| Attributo | Valore |
|---|---|
| Source ID | `gdelt` |
| API | GDELT DOC 2.0 (JSON) |
| Chiave | nessuna |
| Quota | nessuna quota fissa |
| Filtro date | nativo |

Indice globale di notizie aggiornato ogni 15 minuti. Copre oltre 65 lingue. Retry automatico ×3 con backoff esponenziale (cap 60s).

### guardian — The Guardian

| Attributo | Valore |
|---|---|
| Source ID | `guardian` |
| API | Guardian Open Platform |
| Chiave | `GUARDIAN_API_KEY` |
| Quota gratuita | 5.000 richieste/giorno |
| Filtro date | nativo (`from-date`/`to-date`) |

### nyt — New York Times

| Attributo | Valore |
|---|---|
| Source ID | `nyt` |
| API | NYT Article Search API |
| Chiave | `NYT_API_KEY` |
| Quota gratuita | 10 req/min, 4.000/giorno |
| Filtro date | nativo (`begin_date`/`end_date`) |

### gnews_it — Google News Italia

| Attributo | Valore |
|---|---|
| Source ID | `gnews_it` |
| API | RSS feed Google News |
| Chiave | nessuna |
| Quota | nessuna |
| Filtro date | post-pipeline |

Aggrega testate italiane (Corriere, ANSA, Repubblica, La Stampa, ecc.) via RSS pubblico. Non richiede API key.

### bbc — BBC News

| Attributo | Valore |
|---|---|
| Source ID | `bbc` |
| API | Feed RSS pubblici (world, business, technology, sport, politics) |
| Chiave | nessuna |
| Quota | nessuna |
| Filtro date | post-pipeline |

### ansa — ANSA

| Attributo | Valore |
|---|---|
| Source ID | `ansa` |
| API | Feed RSS pubblici ANSA |
| Chiave | nessuna |
| Quota | nessuna |
| Filtro date | post-pipeline |

Agenzia di stampa italiana. Copertura news nazionali in tempo reale.

## Fonti Social / UGC

### youtube — YouTube Data API v3

| Attributo | Valore |
|---|---|
| Source ID | `youtube` |
| API | YouTube Data API v3 (`search.list` + `videos.list`) |
| Chiave | `YOUTUBE_API_KEY` |
| Quota gratuita | 10.000 unità/giorno |
| Filtro date | nativo (`publishedAfter`/`publishedBefore`) |

Raccoglie video. Per ogni video recupera le statistiche (`viewCount`, `likeCount`, `commentCount`) via `videos.list`.

### youtube_comments — YouTube Comments

| Attributo | Valore |
|---|---|
| Source ID | `youtube_comments` |
| API | YouTube Data API v3 (`commentThreads.list`) |
| Chiave | `YOUTUBE_API_KEY` |
| Quota gratuita | condivisa con `youtube` |
| Filtro date | post-pipeline |

Raccoglie i commenti dei video trovati da `youtube`. Ogni commento produce un `Record` distinto con il titolo del video come `title`. Il deduplicator non applica il livello titolo+dominio per questa fonte (parent-child).

### bluesky — Bluesky (AT Protocol)

| Attributo | Valore |
|---|---|
| Source ID | `bluesky` |
| API | AT Protocol (`app.bsky.feed.searchPosts`) |
| Chiave | `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` |
| Quota | non documentata |
| Filtro date | nativo (`since`/`until`) |

Richiede autenticazione con App Password (non la password principale). Senza credenziali il collector viene skippato.

### mastodon — Mastodon (Fediverse)

| Attributo | Valore |
|---|---|
| Source ID | `mastodon` |
| API | Mastodon REST API |
| Chiave | opzionale (`MASTODON_ACCESS_TOKEN`) |
| Quota | variabile per istanza |
| Filtro date | post-pipeline |
| Istanze default | `mastodon.social`, `mastodon.online`, `techhub.social` |

Interroga più istanze in parallelo. Senza token usa il fallback pubblico sulla timeline hashtag.

### lemmy — Lemmy (Fediverse)

| Attributo | Valore |
|---|---|
| Source ID | `lemmy` |
| API | Lemmy REST API |
| Chiave | nessuna |
| Quota | variabile per istanza |
| Filtro date | post-pipeline |
| Istanze default | `lemmy.world`, `lemmy.ml`, `sh.itjust.works` |

Raccoglie sia post che commenti. Ogni commento produce un `Record` con prefisso `[Comment]` nel titolo.

### reddit — Reddit

| Attributo | Valore |
|---|---|
| Source ID | `reddit` |
| API | Endpoint JSON pubblico (`/search.json`) |
| Chiave | nessuna |
| Quota | ~30 req/min per IP |
| Filtro date | nativo |

Usa l'endpoint JSON pubblico senza autenticazione OAuth. Retry automatico ×1 in caso di 429, con attesa di 30s.

### stackexchange — Stack Exchange *(opt-in)*

| Attributo | Valore |
|---|---|
| Source ID | `stackexchange` |
| API | Stack Exchange API v2.3 |
| Chiave | opzionale (`STACKEXCHANGE_API_KEY`) |
| Quota | 300 req/giorno (senza key), 10.000/giorno (con key) |
| Filtro date | nativo |
| Attivazione | `--sources stackexchange ...` |

Fonte **opt-in**: non inclusa nel set di default. Adatta a target tecnici (librerie, framework, prodotti software). Per nomi propri produce spesso match spuri.

### hackernews — Hacker News *(opt-in)*

| Attributo | Valore |
|---|---|
| Source ID | `hackernews` |
| API | Algolia HN Search API |
| Chiave | nessuna |
| Quota | nessuna |
| Filtro date | nativo |
| Attivazione | `--sources hackernews ...` |

Fonte **opt-in**: community prevalentemente tech-anglofona. Alta qualità per target tech/startup; basso segnale per target non-tech.

## Fonti Enciclopediche

### wikipedia — Wikipedia

| Attributo | Valore |
|---|---|
| Source ID | `wikipedia` |
| API | Wikipedia-API (Python) |
| Chiave | nessuna |
| Quota | nessuna |
| `is_static` | `True` — saltata se già presente nel file di output |
| Filtro date | — (contenuto statico, nessuna data) |

Produce sempre un singolo record con il sommario della pagina Wikipedia corrispondente al target. Se il file di output per (target, topic) esiste già e contiene un record `wikipedia`, la fonte viene saltata automaticamente.

### wikitalk — Wikipedia Talk Pages

| Attributo | Valore |
|---|---|
| Source ID | `wikitalk` |
| API | MediaWiki REST API |
| Chiave | nessuna |
| `is_static` | `True` — saltata se già presente nel file di output |
| Filtro date | — (nessuna data per le discussioni) |

Raccoglie le sezioni della pagina di discussione Wikipedia associata al target. Ogni sezione è un `Record` distinto. Utile per rilevare controversie e dibattiti sull'entità.

## Fonte Web Search

### brave — Brave Search

| Attributo | Valore |
|---|---|
| Source ID | `brave` |
| API | Brave Search API |
| Chiave | `BRAVE_API_KEY` |
| Quota gratuita | 2.000 req/mese, 1 req/sec |
| Filtro date | `page_age` (post-pipeline) |

Indice web indipendente. Utile per raccogliere risultati generalisti non coperti dalle fonti editoriali. Senza chiave il collector viene skippato con un warning.

## Gestione errori comune a tutti i collector

- **API key mancante:** il collector logga `WARNING` e restituisce `[]` senza interrompere la pipeline.
- **HTTP 429 (rate limit):** retry con jitter (via `http_get_with_retry()`) o gestione custom per le fonti con logica propria (GDELT, Reddit).
- **Timeout / connessione:** `requests.exceptions.ConnectionError` / `Timeout` catturati, log `ERROR`, restituzione `[]`.
- **Risposta malformata:** `KeyError` / `JSONDecodeError` catturati, log `ERROR`, restituzione `[]`.
