# Configurazione

## File .env

Il progetto usa un file `.env` (mai versionato) per le API key. Il file `.env.example` contiene tutte le variabili supportate:

```env
NEWS_API_KEY=
GUARDIAN_API_KEY=
NYT_API_KEY=
BRAVE_API_KEY=
YOUTUBE_API_KEY=

BLUESKY_HANDLE=
BLUESKY_APP_PASSWORD=

MASTODON_ACCESS_TOKEN=
MASTODON_TOKEN_INSTANCE=mastodon.social
# MASTODON_INSTANCES=mastodon.social,mastodon.online,techhub.social
# LEMMY_INSTANCES=lemmy.world,lemmy.ml,sh.itjust.works

STACKEXCHANGE_API_KEY=

HF_TOKEN=
```

## Come ottenere le API key

### NewsAPI
1. Registrati su [newsapi.org](https://newsapi.org/register)
2. La chiave è disponibile nella dashboard

### The Guardian
1. Registrati su [open-platform.theguardian.com/access](https://open-platform.theguardian.com/access/)
2. Seleziona **Developer key** (gratuito)
3. La chiave arriva via email in pochi minuti

### New York Times
1. Crea un account su [developer.nytimes.com](https://developer.nytimes.com/accounts/create)
2. Vai su **My Apps** → **New App**
3. Abilita **Article Search API** e copia la **Key**

### YouTube Data API v3
1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un progetto e abilita **YouTube Data API v3**
3. Vai su **Credenziali** → Crea chiave API

### Brave Search
Piano gratuito "Data for AI" Free: 2.000 query/mese, 1 query/sec.

1. Registrati su [api-dashboard.search.brave.com](https://api-dashboard.search.brave.com/)
2. Sottoscrivi il piano **Data for AI — Free** (richiede carta di credito per verifica, nessun addebito sul tier gratuito)
3. Vai su **API Keys** → **Add API Key** e copia il token

Senza chiave il collector viene skippato con un warning e le altre fonti continuano normalmente.

### Bluesky (App Password)

L'endpoint `searchPosts` di Bluesky richiede autenticazione. È necessaria una **App Password** (diversa dalla password principale dell'account).

1. Accedi su [bsky.app/settings/app-passwords](https://bsky.app/settings/app-passwords)
2. Clicca **Add App Password**, assegna un nome (es. `wr-analysis`)
3. Copia il codice generato (formato `xxxx-xxxx-xxxx-xxxx`)
4. Imposta nel file `.env`:
   ```
   BLUESKY_HANDLE=tuo.handle.bsky.social
   BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```

Senza credenziali il collector viene skippato con un warning.

### Mastodon (opzionale)

Il token è **specifico dell'istanza** dove viene creato. Senza token il collector usa il fallback sulla timeline hashtag pubblica.

1. Vai su **Preferences** → **Development** → **New Application** sulla tua istanza
2. Scope richiesto: `read` (sola lettura)
3. Copia **Your access token** nel file `.env`:
   ```
   MASTODON_ACCESS_TOKEN=il_tuo_token
   MASTODON_TOKEN_INSTANCE=mastodon.social
   ```

Le istanze interrogate sono configurabili via `.env`:
```env
MASTODON_INSTANCES=mastodon.social,mastodon.online,techhub.social
LEMMY_INSTANCES=lemmy.world,lemmy.ml,sh.itjust.works
```

### Stack Exchange (opzionale)

Senza key: 300 richieste/giorno per IP. Con key: 10.000/giorno.

1. Vai su [stackapps.com/apps/oauth/register](https://stackapps.com/apps/oauth/register)
2. Registra l'applicazione e copia la **Key**

### HuggingFace Token (opzionale)

Il modello di sentiment scarica automaticamente ~1.1 GB. Senza token il download funziona ugualmente, ma è soggetto al rate limit anonimo.

1. Registrati su [huggingface.co](https://huggingface.co/join)
2. Vai su **Settings** → **Access Tokens** → **New token** (tipo: Read)
3. Aggiungi `HF_TOKEN=hf_...` nel file `.env`

## Fonti senza chiave

**GDELT DOC 2.0**, **Wikipedia**, **Wikipedia Talk Pages**, **Lemmy**, **BBC News**, **ANSA** e **Google News IT** non richiedono registrazione né API key.
