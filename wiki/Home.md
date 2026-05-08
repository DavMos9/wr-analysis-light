# wr-analysis-light — Wiki

Documentazione della pipeline modulare per Web Reputational Analysis (versione light).

## Pagine disponibili

| Pagina | Descrizione |
|---|---|
| [Installazione](Installazione) | Setup dell'ambiente e delle dipendenze |
| [Configurazione](Configurazione) | API key e variabili d'ambiente |
| [Utilizzo](Utilizzo) | Comandi CLI ed esempi pratici |
| [Architettura](Architettura) | Pipeline, moduli e flusso dati |
| [Collectors](Collectors) | Documentazione di ogni fonte dati |
| [Schema Dati](Schema-Dati) | Riferimento completo del data contract |
| [Troubleshooting](Troubleshooting) | Problemi comuni e soluzioni |

## Quick start

```bash
git clone https://github.com/DavMos9/wr-analysis-light.git
cd wr-analysis-light
python -m venv .venv && source .venv/bin/activate
pip install -e ".[nlp]"
cp .env.example .env  # inserisci le tue API key
python main.py --target "Zendaya" --topic "Euphoria" --date-from 2026-04-01
```

## Differenze rispetto a web-reputational-analysis

| Caratteristica | web-reputational-analysis | wr-analysis-light |
|---|---|---|
| Topic per run | multipli (`--queries`) | singolo (`--topic`) |
| Range temporale | `--since` (opzionale) | `--date-from` (obbligatorio) |
| Aggregatore | EntitySummary + reputation score | — |
| Campi record | 16 campi + contatori social | 11 campi essenziali |
| Output files | `{target}_{timestamp}_final.*` | `{Target}{Topic}.*` (unico, merge) |
| Filtro lingua post-enrichment | `--languages` | — |
| Integrazione DataStage | indiretta | diretta (CSV flat con metadati run) |
