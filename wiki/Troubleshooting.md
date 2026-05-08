# Troubleshooting

Problemi comuni e soluzioni.

---

## API key mancante o non valida

**Sintomo:** un collector restituisce 0 record e il log mostra un warning relativo alla chiave mancante.

**Soluzione:**
1. Controlla che `.env` esista e contenga tutte le chiavi necessarie.
2. Esegui una diagnostica rapida:
   ```bash
   python -c "from config import NEWS_API_KEY; print(bool(NEWS_API_KEY))"
   ```

Vedi [Configurazione](Configurazione) per l'elenco completo delle chiavi.

---

## Rate limit (HTTP 429)

**Sintomo:** il log mostra `Rate limit raggiunto (HTTP 429)` o `Limite giornaliero raggiunto`.

| Fonte | Quota / limite | Comportamento |
|---|---|---|
| NewsAPI | 100 richieste/giorno | Log warning, restituisce 0 record |
| The Guardian | 5.000 richieste/giorno | Log warning, restituisce 0 record |
| NYT | 10 req/min, 4.000/giorno | Log warning, restituisce 0 record |
| GDELT | variabile | Retry ×3 con backoff esponenziale (cap 60s) |
| Reddit | ~30 req/min per IP | Retry ×1 dopo 30s; se persiste, fonte saltata |
| Brave Search | 1 req/sec, 2.000/mese | Log warning, restituisce 0 record |
| YouTube | 10.000 unità/giorno | Log warning, restituisce 0 record |

**Soluzioni:**
- Usa `--dry-run` per testare la pipeline senza consumare quota.
- Riduci il numero di fonti con `--sources`.
- Aspetta il reset della quota (giornaliero a mezzanotte UTC).

---

## NLP lento o out-of-memory

**Sintomo:** la fase di enrichment impiega diversi minuti o il processo viene ucciso.

**Causa:** il modello XLM-RoBERTa è ~1.1 GB e richiede RAM sufficiente per l'inferenza.

**Soluzioni:**
- Esegui su hardware con almeno 4 GB di RAM disponibile.
- Installa senza `[nlp]` per disabilitare la fase di enrichment:
  ```bash
  pip install -e .   # senza [nlp]
  ```
  I campi `language` e `sentiment` resteranno `null`.

---

## Record mancanti o in numero inferiore al previsto

**Sintomo:** il numero di record esportati è molto inferiore a `max_results × n_fonti`.

**Cause possibili:**
1. **Qualità:** il cleaner scarta record con testo o titolo troppo corti (soglie in `config.py`).
2. **Filtro temporale:** record con date fuori dal range `[date_from, date_to]` vengono scartati.
3. **Deduplicazione:** articoli identici da più fonti vengono rimossi.
4. **Rate limit:** alcune fonti hanno restituito 0 risultati per quota esaurita.

Controlla i log `INFO` per vedere i conteggi di ogni step:
```
Puliti: X validi, Y scartati.
Filtro date [...]: Z mantenuti, W scartati.
Deduplicati: N rimossi, M unici.
```

---

## Encoding e caratteri speciali

**Sintomo:** CSV o JSON contengono `?` o caratteri corrotti.

**Soluzione:**
- Tutti i file vengono scritti con `encoding="utf-8"` e `ensure_ascii=False`.
- Se apri il CSV in Excel su Windows, importa specificando UTF-8 (File → Importa → Delimitato → Codifica: 65001).

---

## File di output non aggiornato dopo il run

**Sintomo:** il contatore "Aggiunti in questo run" è 0 anche con nuovi dati.

**Cause possibili:**
1. I record raccolti hanno URL già presenti nel file esistente (deduplicazione).
2. Le date dei nuovi record sono fuori dal range specificato.
3. I record non hanno superato il filtro di qualità.

**Verifica:** controlla i log per i conteggi di ogni step della pipeline.

---

## Modulo normalizer non trovato

**Sintomo:** il log mostra `Nessun normalizer registrato per la sorgente 'X'`.

**Soluzione:** crea `normalizers/x.py` con la funzione `_normalize(raw: RawRecord) -> Record` e registrala via `register("x", _normalize)`. Il discovery è automatico — non è necessario modificare `normalizers/__init__.py`.

---

## Fonti statiche rilette inutilmente

**Sintomo:** Wikipedia o WikiTalk vengono interrogate anche se già presenti nel file.

**Comportamento corretto:** le fonti con `is_static = True` (Wikipedia, WikiTalk) vengono automaticamente saltate se il file di output per (target, topic) esiste già e contiene record di quella fonte. Il log mostra:
```
Fonti statiche già presenti, saltate: ['wikipedia', 'wikitalk']
```

Se la fonte viene comunque riletta, verifica che il file `.json` di output esista e contenga record con `source = "wikipedia"`.

---

## Test che falliscono per dipendenze NLP mancanti

**Sintomo:** la test suite fallisce con `ModuleNotFoundError: No module named 'transformers'`.

**Soluzione:** esegui i test escludendo i moduli che richiedono il modello:
```bash
pytest -q
```
oppure installa le dipendenze complete:
```bash
pip install -e ".[nlp]"
```
