> **Portfolio copy.** Sanitised for public reading: API keys, access key, database and caches
> removed. Runs locally with `backend/config.example.json`; put real keys in `backend/config.json`
> to fetch live odds. This is not the deployed instance.

# SportsBet Value Scanner

Scanner de cote care compară bookmakers în timp real și semnalează **value bets** și **arbitraj** pentru fotbal, tenis, baschet și darts.

> **Avertisment:** niciun sistem nu garantează profit. Pariurile implică risc de pierdere. Acest tool doar îți maximizează șansele prin compararea cotei și gestionarea bankroll-ului.

## Funcționalități

- Fetch cote live/pre-match de la mai multe bookmakers prin [the-odds-api.com](https://the-odds-api.com)
- Normalizare cote → probabilități corecte (eliminare marjă)
- Model predictiv Poisson (fotbal) + normalizare pentru restul sporturilor
- **Motor de context**: analizează știri despre echipe/jucători (accidentări, suspendări, reveniri, evenimente) via Google News + Bing News/Web (lineup-uri, gossip de pe site-uri mai puțin populare) și ajustează probabilitățile
- **Chat AI (DeepSeek/Ollama)**: dialog în dashboard care poate căuta și acționa pe datele aplicației (value bets, arbitraj, context echipe, istoric H2H, refresh, statistici) prin tool calls — persona Miki, interzis să inventeze scoruri/medii/statistici, orice cifră vine dintr-un tool verificat
- **Analiză istorică H2H**: frecvența scorurilor, pattern-uri repetate (același scor în meciuri repetate), medii de goluri și lambdas Poisson din istoric real (încărcat ca CSV) — integrare conservatoare (min. 6 meciuri + amestec cu probabilitatea casei)
- **Impact jucători**: clasifică știrile pe categorii — accidentați (cu prioritate și pondere mai mare), suspendări/cartonage roșii, jucători pe bancă, transferuri in/out, reveniri — și extrage numele jucătorilor din știri
- **Analyze match în 3 pași** (tool `analyze_match_deep`): meci+cote → context/impact echipe → jucătorii cu evenimente, apoi concluzie
- **Ligi din toată lumea**: catalog de 78 de ligi active (fotbal din toate țările, NBA/WNBA, NFL, NHL, MLB, tenis ATP/WTA, MMA, box, cricket, rugby, golf) — oricare ligă se aduce on-demand în chat prin tool-ul `fetch_league` (consumă 1-5 requesturi)
- **API-Football (plan gratuit, 100 req/zi)**: cheie de la **https://dashboard.api-football.com/register** (înregistrare gratuită, fără card) pusă în `config.json` → `api_football.api_key`. Deblochează date reale de fotbal din TOATE țările — ligi de seniori, juniori și tineret (U19/U18/U17/U20/U21), inclusiv România. Pe gratuit sunt incluse și **cotele** (pre-match) din această sursă, cu **153 de piețe**: 1X2, șansă dublă, fără egal, BTTS (ambele marcate), pauză/final, par/impar, scor exact, **cornere**, total goluri și **total goluri în prima repriză**. Tool-urile: `football_leagues`, `football_fixtures` (azi/toată lumea), `football_odds` (cote pe piețe), `football_h2h` (istoric real). Limitare plan gratuit: doar meciurile de AZI și sezoanele 2022-2024 (meciurile viitoare și sezoanele curente sunt premium); limită pe minut de la API
- **Piețe exotice**: `get_market_odds` aduce pe cerere cote pe BTTS (ambele marcate), șansă dublă, fără egal, pauză/final, par/impar (1 request/meci, rămân în cache). Note: cornerele și o piață separată de goluri până la pauză nu există pe sursă (the-odds-api) — AI-ul spune asta onest
- **Evidențiere câștigător**: AI-ul înconjoară echipa declarată câștigătoare cu `<<Echipa>>` → randată distinct (font, verde, glow animat); la egal ambele echipe
- **Widget verdict animat**: la finalul analizei, `[VERDICT] {win_pct, side, event}` → thumbs up/down animate cu procente câștig/pierdut care numără la 100%
- **Cache persistent**: refresh-ul NU mai șterge informația — doar actualizează evenimentele cu același id și păstrează ligile aduse on-demand + piețele exotice; evenimentele duplicate sunt eliminate automat. Piețele de tip `*_lay` (prețuri de lay pe schimburi, ex. Betfair) sunt ascunse din afișare, fiind adesea artefacte fără lichiditate
- **Scor de încredere** (1–5★) pe fiecare value bet = edge + context care confirmă selecția
- Detectare value bets (probabilitate model > probabilitate casă)
- Detectare arbitraj (suma probabilităților < 100%)
- Bankroll management (Kelly fracționat) + istoric pariuri
- Dashboard web

## Instalare

```bash
cd C:\Users\eusun\sportsbet-app
pip install -r requirements.txt
```

Pune cheia API în `backend/config.json` la `api_key`.

## Pornire

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Sau dublează click pe `start.bat`.

Deschide **http://127.0.0.1:8000** în browser.

## Folosire

1. Click **Refresh cote** — descarcă cotele pentru EPL, NBA, tenis și darts
2. Tab **Value Bets** — unde modelul consideră că probabilitatea reală e mai mare decât cota casei (edge pozitiv)
3. Tab **Arbitraj** — combinații de pariuri cu profit garantat (trebuie jucate la casele indicate, cu mizele proporționale afișate)
4. Tab **Pariurile mele** — înregistrează miza (stake-ul sugerat se calculează cu Kelly) și marchează rezultatul

## Configurare (`backend/config.json`)

| Câmp | Descriere |
|------|-----------|
| `api_key` | Cheia de la the-odds-api |
| `regions` | Regiunea cotelor (`eu`, `uk`, `us`) |
| `markets` | Piețele (`h2h` = 1X2/winner, `totals` = peste/sub) |
| `sports_groups` | Sporturile monitorizate |
| `preferred_sports` | Ligile preferate per sport |
| `value_threshold_pct` | Pragul minim de edge (%) pentru value bet |
| `kelly_fraction` | Fracțiunea din Kelly pentru mize (25% = conservator) |

### Auto-refresh (`auto_refresh`)

| Câmp | Descriere |
|------|-----------|
| `enabled` | Refresh automat în fundal (fără să apeși butonul) |
| `interval_hours` | La câte ore se reîmprospătează cotele (6h = 12 req/zi ≈ 180/lună) |
| `refresh_on_startup` | Refresh la pornire dacă nu există cache |

Statusul (ultima/următoarea refresh, request-uri rămase, refresh-uri estimate) apare în dashboard; toggle-ul Auto ON/OFF e lângă butonul Refresh. Fiecare refresh complet = 1 request per sport activ.

### Chat AI (`chat`)

| Câmp | Descriere |
|------|-----------|
| `api_key` | Cheie opțională (dacă nu folosești providerii din opencode) |
| `base_url` | Endpoint-ul API (opțional, doar cu `api_key`) |
| `model` | Modelul (opțional, doar cu `api_key`) |
| `max_iterations` | Numărul maxim de tool calls per conversație |
| `persona` | Personalitatea AI: `microbist` (Miki, microbist + analist) sau implicit |

**Provideri automat:** dacă `api_key` e goală, aplicația citește singură config-ul opencode (`~/.config/opencode/opencode.json`) și folosește providerii compatibili OpenAI de acolo (ex. DeepSeek cu cheia din `deepseek-key`, Ollama local). Cei cu cheie au prioritate; dacă un provider pică, trece automat la următorul.

Chat-ul din tab-ul **Chat AI** poate: enumera value bets, arăta arbitraj, verifica contextul unei echipe, da statistici bankroll și reîmprospăta cotele — totul prin funcții reale din aplicație.

### Context (`context`)

| Câmp | Descriere |
|------|-----------|
| `enabled` | Activează/dezactivează analiza de context |
| `news_hl` | Limba știrilor (`en`, `de`, `ro`) |
| `news_cache_hours` | Cât timp rămân știrile în cache (evită refetch) |
| `news_lookups_per_scan` | Câte echipe sunt verificate per scan (max. 8) |
| `news_weight` | Cât de mult influențează știrile probabilitatea (0.10 = 10%) |
| `borderline_window_pct` | Intervalul de edge sub prag unde contextul decide |

## API

| Endpoint | Descriere |
|----------|-----------|
| `GET /api/refresh` | Reîmprospătează cotele (consumă 1 request/sport) |
| `GET /api/refresh/status` | Status auto-refresh: ultima/următoarea, request-uri rămase, estimare |
| `POST /api/refresh/auto` | Activează/dezactivează auto-refresh (`{"enabled": true}`) |
| `GET /api/odds` | Cotele din cache |
| `GET /api/value-bets` | Value bets detectate (cu context și încredere) |
| `GET /api/context?team=X` | Contextul (știri, scor) pentru o echipă |
| `GET /api/arbitrage` | Oportunități de arbitraj |
| `GET /api/bets` | Istoric pariuri |
| `POST /api/bets` | Adaugă pariu |
| `POST /api/bets/{id}/settle?won=true` | Soldează pariul |
| `GET /api/stats` | Statistici bankroll |
| `POST /api/chat` | Dialog cu AI (body: `{"messages": [...]}`), răspunde cu `reply` + `tools_used` |

## Note despre limita gratuită

Tier-ul gratuit oferă **500 request-uri/lună**. Fiecare `Refresh cote` consumă **1 request per sport** (4 la refresh complet). O scanare pe zi = ~120/lună, deci e suficient. Cotele rămân în cache (offline) până la următorul refresh.