# Installazione

## Requisiti

- Python 3.11 o superiore
- pip
- Git

## Passi

### 1. Clona la repository

```bash
git clone https://github.com/DavMos9/wr-analysis-light.git
cd wr-analysis-light
```

### 2. Crea un ambiente virtuale

```bash
python -m venv .venv
```

Attiva l'ambiente:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Installa le dipendenze

Installazione base (pipeline senza NLP — i campi `language` e `sentiment` resteranno `null`):

```bash
pip install -e .
```

Installazione completa con language detection e sentiment analysis:

```bash
pip install -e ".[nlp]"
```

> Il flag `-e` installa il pacchetto in modalità editable: le modifiche al codice sorgente vengono recepite immediatamente senza reinstallare.
>
> Il flag `[nlp]` scarica il modello XLM-RoBERTa (`cardiffnlp/twitter-xlm-roberta-base-sentiment`, ~1.1 GB) automaticamente al primo utilizzo.

### 4. Configura le variabili d'ambiente

```bash
cp .env.example .env
```

Apri `.env` e inserisci le tue API key. Vedi la pagina [Configurazione](Configurazione) per i dettagli.

> **HuggingFace Token (opzionale):** se hai un account HuggingFace, aggiungi `HF_TOKEN=<il_tuo_token>` nel file `.env`. Non è obbligatorio, ma aumenta il rate limit per il download del modello.

## Verifica installazione

```bash
python main.py --help
```

Dovresti vedere l'elenco delle opzioni disponibili.

### Dry run (verifica API senza consumare quota)

```bash
python main.py --target "Zendaya" --topic "Euphoria" --date-from 2026-04-01 --dry-run
```

Imposta `max_results=1` per fonte. Utile per verificare che tutte le chiavi siano configurate correttamente prima di un run completo.
