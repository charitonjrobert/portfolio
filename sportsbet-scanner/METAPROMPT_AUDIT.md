# Metaprompt — audit, optimizare și corectare MicrobistBets

> Document de lucru pentru agentul care preia aplicația. Include diagnoza deja confirmată,
> inventarul problemelor și contractul de livrare. Nu re-descoperi ce este marcat ca verificat;
> confirmă pe cod și pe aplicația rulantă, apoi corectează.

## 0. Status implementare (28 oct 2026)

Aplicate și testate pe aplicația rulantă:

- **F1-F3** — renderer chat nou: `[VERDICT]` + widget animat, `##green/##red`, `<<winner>>`,
  `__team__`, italic, tabele Markdown reale. Verificat cu răspuns real de bilet: 76% / 67% / 61%
  per selecție, widget 31% / 69%, fără markup brut.
- **F9** — `commence_time` trimis de frontend, potrivire fuzzy + dată în `_find_event` și
  `_deep_analysis`, deduplicare fixtures. `Venezia FC vs FC Internazionale Milano` găsește
  acum `Venezia vs Inter Milan` (12% / 16% / 73%); lista nu mai are duplicate detectabile.
- **F10** — o singură casă sănătoasă este acceptată pentru analiza afișată; value bets rămân
  stricte. NBA `Washington Wizards vs Charlotte Hornets` afișează 44% / 56% și „o singură casă”.
- **F11** — `probabilities_note` + empty-state clar. Meciurile fără cote 1X2 arată mesaj, nu
  secțiune goală; meciurile programate dar fără cote publicate au explicație.
- **F13** — biletul afișează șansa fiecărei selecții, „șansă combinată”, notă sub 50% și
  alternativă de 2 selecții.

Backup înainte de modificări: `C:\Projects\sportsbet-backups\sportsbet-20261028_0613.tar.gz`.
Capturi pentru client: `C:\Projects\sportsbet-app\screenshots\2026-10-28\`.

Audit german separat: `METAPROMPT_I18N_DE.md` (365 chei RO/DE/EN, comutare limbă,
quick-path bilet german, date/numere germane, capturi în `screenshots/2026-10-28-de/`).

Rămase de făcut: F4 (fallback verdict), F5 (procent numeric loader), F6 (istoric chat),
F7 (verificare stare meci terminat), F8 (value bets auto), F12 (sursă externă pentru meciurile
fără cote). Residual: circa 16 duplicate greu de distins prin nume (similitudine 0.5) și
64 de carduri football-data fără cote în fereastra curentă; acestea din urmă afișează mesaj
clar, dar nu au procente.

---

## 1. Rol și obiectiv

Ești un agent senior full-stack (FastAPI + JavaScript vanilla) cu experiență de QA, UX și
securitate web. Lucrezi pe aplicația **MicrobistBets / SportsBet Value Scanner** din
`C:\Projects\sportsbet-app`.

Obiective, în ordine:

1. **Corectare P0** — repară cele două regresii semnalate de client: analiza din chat nu mai
   afișează procentele la final (widgetul de verdict, procentele colorate, evidențierea
   câștigătorului) și analiza detaliată nu arată procente pentru fiecare meci (nume, duplicate,
   prag de case, empty-state).
2. **Audit complet** — verifică frontendul, backendul, contractele API, cache-ul, i18n,
   securitatea și limitele surselor gratuite. Găsește ce lipsește sau s-a pierdut la rescrieri.
3. **Optimizare** — reduce latența, consumul de tokeni/API și greutatea payload-urilor, fără
   a schimba comportamentul funcțional.
4. **Îmbunătățire** — UX mobil/PWA, accesibilitate, claritatea procentelor și a stării
   meciurilor (live / încheiat), istoricul conversațiilor.
5. **Raport** — livrabil scurt, cu dovezi `fișier:linie`, severitate, impact și test.

Nu face refactor general. Fiecare schimbare trebuie să aibă un motiv, un test și un risc
enumerat.

---

## 2. Contextul aplicației

- **Director de lucru:** `C:\Projects\sportsbet-app` (copia de dezvoltare).
- **Original (nu îl edita):** `C:\Users\eusun\sportsbet-app`.
- **Stack:** backend Python 3.11 + FastAPI/uvicorn; dashboard vanilla JS, fără build step;
  SQLite `backend/bets.db`; cache JSON în `backend/`; PWA instalabilă.
- **Fișiere mari:** `dashboard/app.js` ~2718 linii, `backend/chat.py` ~1644 linii,
  `backend/microbist.py` ~1488 linii. Nu le citi integral; folosește `grep` + feliile relevante.
- **Pornire:**
  ```powershell
  cd C:\Projects\sportsbet-app\backend
  python -m uvicorn main:app --host 127.0.0.1 --port 8000
  ```
  sau `start_sportsbet.bat`. **Python nu face hot-reload** — după orice editare repornește
  serverul și verifică `/api/version`.
- **Acces:** aplicația are `AccessGate`; linkul clientului cere `?k=<ui.access_key>` din
  `backend/config.json`. Nu afișa cheia în raport, log sau captură de ecran.
- **Limbi:** RO (implicit), DE, EN. Orice text nou trebuie tradus în toate cele trei.
- **Surse cu cotă gratuită:**
  - the-odds-api: 500 requesturi/lună; 1 request/sport/refresh.
  - API-Football: 100 requesturi/zi; unele date sunt premium.
  - Știri: cache 12h; nu refetch inutil.
- **Regulă de cost:** testele nu au voie să ardă quota. Folosește cache-ul existent,
  `?nocache=0`, și rulează refresh doar dacă testul o cere explicit.

---

## 3. Reclamația clientului și diagnoza confirmată

### 3.1 Reclamațiile

Reclamația 1:

> „La analyze nu mai arată în procent când termină.”

Interpretări posibile: (a) procentele din analiză nu mai apar la final; (b) meciul s-a
terminat și nu se mai afișează procentul; (c) loader-ul nu afișează procentul de finalizare.

Reclamația 2 (clarificare de la client):

> „Analyse Details sau completa îți arată în procent care e posibil să câștige.”
>
> „Da acuma merge, da nu la fiecare meci.”

Adică: analiza detaliată trebuie să afișeze procentul de câștig, dar pentru unele meciuri
secțiunea „Șanse calculate” rămâne goală sau analiza nu găsește meciul.

### 3.2 Concluzia pentru reclamația 1

**Cauza principală este (a), o regresie de randare în frontend.** Backendul calculează și
trimite în continuare procentele; dashboardul rescris în jurul datei **15 octombrie** a
înlocuit vechiul `renderReply()` / `mdToHtml()` cu `mdLite()`, care nu mai știe să interpreteze:

- linia finală `[VERDICT] {...}` (widgetul animat câștig/pierdut);
- marcajul inline `##green:32%##` / `##red:68%##`;
- evidențierea câștigătorului `<<Echipa>>`;
- marcajul `__Echipa__` și italicul `*text*`;
- tabelele Markdown (acum sunt turtite în bullet-uri).

Clientul vede marcaj brut, de exemplu:

```text
**3 selecții** · șansă câștig ##green:32%## · risc ##red:68%##
...
[VERDICT] {"win_pct": 32.0, "side": "parlay", "event": "3 selecții"}
```

Aceasta explică exact formularea „nu mai arată în procent”: procentele există în text,
dar sunt înconjurate de markup și nu mai sunt randate vizual.

### 3.3 Dovezi verificate pentru reclamația 1

| Dovadă | Locație | Ce arată |
|---|---|---|
| Promptul cere widget | `backend/chat.py:142-149` | Ultima linie trebuie să fie `[VERDICT] {"win_pct": ...}`; textul spune explicit că este afișat ca widget Like/Dislike. |
| Backendul emite marcaj | `backend/chat.py:1506`, `:1538`, `:1345` | `build_ticket` și „meciul zilei” produc `##green:...##`, `##red:...##` și `[VERDICT]`. |
| Frontendul nu parsează | `dashboard/app.js:906-923` | `mdLite()` doar escapează, bold, heading, bullet și newline. Nu are `##`, `<<>>`, `__`, tabel sau `[VERDICT]`. |
| Randarea reply-ului | `dashboard/app.js:2320-2341` | `ph.innerHTML = mdLite(d.reply || "…")`; nu există `renderReply()`. |
| Regresia e documentată | `memories/2026-08-20.md:10-11` | Widgetul exista și fusese reparat (JSON parsat din textul brut înainte de escape). |
| Implementarea veche | `C:\Users\eusun\sportsbet-backups\sportsbet-2026-08-20\dashboard\app.js:339-384` | `renderVerdict()`, `animatePct()`, `renderReply()` — referință de design, nu copia direct. |
| CSS vechi | backup `dashboard/style.css:370-410` | `.verdict`, `.v-card`, `.v-pct`, `.v-win`, `.v-lose`, animație thumbs. |
| Dovadă din date reale | `backend/bets.db`, tabela `chats` | Conversații din 14-15 oct conțin literal `##green:32%##`, `__FC Bayern München__`, `<<FC Barcelona Bàsquet>>`, `[VERDICT] {...}`. |

### 3.4 Ce NU este cauza pentru reclamația 1

- **Nu este finalul meciului.** `/api/analyze` returnează `probabilities` și pentru meciuri
  trecute (`is_past`), iar cardul de meci are badge „încheiat”. Verifică totuși afișarea
  stării, pentru ipoteza (b).
- **Nu sunt probabilitățile din backend.** `backend/microbist.py` construiește
  `probabilities` din `predict_1x2()` și le returnează; frontendul le randează în
  `renderAnalysis()`.
- **Nu este cache-ul clientului.** `checkVersion()` compară `/api/version` și reîncarcă
  assets-urile; problema se reproduce și cu cache curat.

---

### 3.5 Reclamația 2 — procente lipsă la unele meciuri (confirmat)

Testat pe aplicația rulantă și pe cache-ul din 28 oct 2026. **Nu este o singură cauză.**
Sunt patru cauze suprapuse, plus un empty-state nedescris în UI.

#### Date măsurate

- `GET /api/fixtures?days=7`: **221 carduri**, 132 cu cote, 89 fără.
- 87 carduri vin din football-data.org fără cote; 2 carduri din odds cache nu au niciun bookmaker.
- **39 din 87** au un geamăn în lista de odds, la aceeași oră — același meci apare de două ori:
  o dată cu cote, o dată fără.
- Potrivirea strictă din `_find_event`: **58 din 87** de carduri football-data nu găsesc
  niciun eveniment în cache; **3** găsesc evenimentul din altă zi (meciuri diferite, aceleași echipe).
- `market_sides()` întoarce `None` pentru:
  - baschet **23/49**, box **24/26**, MMA **17/18**, fotbal **4/197**, hochei **0/8**.
  - **16** evenimente au zero bookmakers; restul au cel puțin o casă cu cote h2h sănătoase.
- După relaxarea la o singură casă: rămân **16** evenimente fără nicio cotă; restul de **52**
  pot primi probabilități.

#### Cauze

**R1. Fixtures duplicate, fără deduplicare.**
`microbist.py` adaugă întâi meciurile din cache-ul de cote, apoi meciurile football-data.org
(`microbist.py:732-809`), fără să le unească. Același meci apare ca două carduri. Clientul
poate apăsa cardul fără cote și primește „casele încă nu au publicat cote”, deși cardul geamăn
are cote și probabilități.

**R2. `_find_event` și `_deep_analysis` prea stricte și fără dată.**
`microbist.py:878-895` compară doar substring-uri normalizate de nume și **ignoră data**.
`chat.py:1179-1196` (`_deep_analysis`) face aceeași potrivire naivă `ta in home and tb in away`,
fără dată și fără `event_id` — deci și analiza din chat pică pe aceleași nume diferite.
Exemple reale:
- `Venezia FC vs FC Internazionale Milano` nu găsește `Venezia vs Inter Milan`;
- `FC Bayern München vs Borussia Dortmund` nu găsește `Bayern Munich vs Borussia Dortmund`;
- `1. FC Union Berlin vs 1. FC Köln` (1 nov) găsește meciul din 27 oct — probabilități de la
  alt meci.

`AnalyzeIn` (`microbist.py:871-876`) nu primește `commence_time`, iar frontendul trimite doar
`home`, `away`, `event_id` (`app.js:1857`). Pentru cardurile football-data, `event_id` este
`fd-...`, nu id-ul din odds cache, deci căderea pe nume este garantată.

**R3. O singură casă de pariuri = zero probabilități.**
`market_sides()` cere `min_consensus_books=1`, dar `consensus_probs()` forțează
`max(2, min_books)` (`sharp.py:83`). Dacă a doua casă are cote de lay/artefact și este
filtrată, rămâne una singură și referința devine goală. `predict_1x2()` returnează `None`
(`models.py:93-95`). Așa se pierd NBA, MMA și 4 meciuri de fotbal.

**R4. Evenimente cu zero bookmakers.**
Există evenimente în cache cu `bookmakers: []` (ex. box din 31 dec 2026). Nu există nicio
cotă 1X2 din care să calculăm; `found:true`, dar `probabilities:null`. Nu se poate afișa un
procent onest fără altă sursă (API-Football predictions, web verificat) — trebuie spus clar.

**R5. UI afișează titlul „Șanse calculate” cu corp gol.**
`app.js:1710-1711` randează mereu `<h3>📊 Șanse calculate</h3>` și `renderProbabilityBars(p)`;
dacă `p` este `{}`, toate rândurile sunt `null` și nu apare nimic. Clientul vede o secțiune
goală, fără explicație.

#### Dovezi din API-ul rulant

| Cerere | Rezultat |
|---|---|
| `Venezia FC vs FC Internazionale Milano` | `found:false`, `probabilities:null`, mesaj „cotele nu sunt publicate” |
| `Venezia vs Inter Milan` | `found:true`, `probabilities:{home:0.1175, draw:0.1567, away:0.7258}` |
| `Washington Wizards vs Charlotte Hornets` | `found:true`, `probabilities:null` (o singură casă) |
| `Manel Kape vs Joshua Van` | `found:true`, `probabilities:null` (o singură casă) |
| `Daniel Dubois vs Agit Kabayel` | `found:true`, `probabilities:null` (zero bookmakers) |

Concluzie: nu este vorba despre „unele sporturi nu au procente” sau despre finalul meciului.
Este o combinație de potrivire de nume, duplicate de fixtures, prag prea dur la numărul de
case și lipsa unui mesaj clar când datele chiar nu există.

---

## 4. Inventar: ce lipsește sau este expus

Marchează fiecare punct cu `confirmat`, `neverificat` sau `nu se aplică`. Nu presupune.

### P0 — vizibil pentru client

1. **Widgetul `[VERDICT]`** — absent complet din `dashboard/app.js`. Procentele de câștig
   și pierdere nu mai sunt afișate vizual.
2. **Procentele colorate** — `##green:32%##`, `##red:68%##`, `##green:+3.6%##` apar brut.
3. **Evidențierea câștigătorului** — `<<Echipa>>` apare cu parantezele la vedere.
4. **Textul evidențiat** — `__Echipa__` apare cu underscore-uri.
5. **Tabelele Markdown** — sunt transformate în „• celula — celula — celula”; pierd
   coloanele, barele de procent și lizibilitatea pe mobil.
6. **Verdict lipsă de la model** — dacă modelul uită linia `[VERDICT]`, clientul nu vede
   niciun procent. Nu există plasă de siguranță în backend.
7. **Fixtures duplicate** — același meci apare cu cote și fără cote; cardul fără cote nu
   produce probabilități. 39 de duplicate măsurate în fereastra de 7 zile.
8. **Potrivire de nume prea strictă** — `_find_event` ignoră data și nu tratează aliasuri
   (`FC Internazionale Milano` vs `Inter Milan`, `Bayern München` vs `Bayern Munich`).
   58/87 de carduri football-data nu își găsesc meciul; 3 găsesc meciul din altă zi.
9. **Pragul de 2 case** — o singură casă sănătoasă produce `probabilities:null` pentru NBA,
   MMA și o parte din fotbal. `min_consensus_books=1` este ignorat de `max(2, ...)`.
10. **Zero bookmakers** — evenimentele fără nicio cotă 1X2 arată `found:true` cu procente
    lipsă, fără explicație în UI.
11. **Empty-state „Șanse calculate”** — titlul apare cu corp gol când `probabilities` e
    `null`; clientul crede că analiza e stricată.

### P1 — funcționalitate și UX

7. **Istoricul chatului** — `GET /api/chat/history` există (`backend/main.py:687`) și
   conversațiile sunt salvate în SQLite, dar frontendul nu îl încarcă. La reload, clientul
   pierde analizele.
8. **Loader fără procent numeric** — bara se umple, dar nu afișează `NN%`; la final scrie
   doar „Gata”. Dacă reclamația clientului era despre loader, aici este rezolvarea.
9. **Starea meciului** — verifică badge-urile „LIVE” / „încheiat”, scorul final, minutul
   live și faptul că un meci terminat rămâne analizabil. Nu afișa `'` dacă nu există minut.
10. **`/api/value-bets/auto`** — endpointul există (`backend/main.py:437`) dar frontendul nu
    îl consumă; indicatorul „scanning” și lista automată nu sunt vizibile.
11. **Traduceri** — verdictul și orice text nou trebuie să aibă chei RO/DE/EN.
12. **Semantica șansei pe bilet** — un bilet de 3 selecții poate afișa 31% combinat
    (76% × 67% × 61%), deși fiecare meci e peste 50%. Clientul poate citi cifra ca pe o
    contradicție. Tabelul trebuie să arate șansa fiecărei selecții și să eticheteze clar
    „șansă combinată”, cu explicație când e sub 50%.

### P2 — performanță și mentenanță

12. **Latența analizei în chat** — măsoară: număr de tool calls, timp per provider, cache
    hit/miss. Elimină apelurile duplicate și respectă `max_iterations`.
13. **Payload și DOM** — nu re-randa tot chatul la fiecare mesaj; limitează istoricul trimis
    la model; păstrează `slice(-8)` sau justifică altă valoare.
14. **Cache** — verifică TTL-urile (`CACHE_TTL` în `app.js`, `cache_ttl_hours` în config),
    invalidarea la schimbarea formei payload-ului și comportamentul offline.
15. **Accesibilitate** — contrast pe procente, `aria-live` pe verdict, focus după analiză,
    navigare cu tastatura, `prefers-reduced-motion`.

### P3 — securitate și operare

16. **XSS** — orice text venit de la model trebuie escapeat înainte de `innerHTML`; parserul
    de markup nu are voie să accepte HTML arbitrar.
17. **Chei API** — `backend/config.json` conține chei în clar. Nu le loga, nu le returna în
    API și nu le pune în capturi. Verifică `/api/config` și `/api/debug/providers`.
18. **Access gate** — nu dezactiva `AccessGate` pentru teste; folosește cheia din config.
19. **Logging** — loghează parse failures pentru `[VERDICT]` și markup necunoscut, fără a
    loga conținutul sensibil.

---

## 5. Protocol de lucru obligatoriu

### Pasul 0 — protecție

- Creează un backup înainte de orice editare:
  ```powershell
  $ts = Get-Date -Format "yyyyMMdd_HHmm"
  New-Item -ItemType Directory -Force C:\Projects\sportsbet-backups | Out-Null
  Compress-Archive -Path C:\Projects\sportsbet-app -DestinationPath "C:\Projects\sportsbet-backups\sportsbet-$ts.zip"
  ```
- Nu șterge backup-uri și nu edita originalul din `C:\Users\eusun\sportsbet-app`.
- Verifică dacă serverul rulează și pe ce port; nu omorî alte procese Python.

### Pasul 1 — reproducere

- Deschide aplicația cu cheia de acces.
- Trimite în chat exact: `Analizează meciul FC Barcelona Bàsquet vs Olympiacos`.
- Salvează răspunsul brut (`/api/chat`) și o captură „before”.
- Confirmă prezența literală a `[VERDICT]`, `##green:`, `<<`, `__` în bubble.
- Verifică și fluxul `Analizează` din tab-ul Acasă: procentele din card trebuie să fie
  vizibile; dacă nu sunt, este altă problemă și o documentezi separat.

### Pasul 2 — test care pică

- Scrie un test minim pentru parser (Node sau Playwright) cu intrări:
  ```text
  [VERDICT] {"win_pct": 32.0, "side": "parlay", "event": "3 selecții"}
  ##green:32%## · ##red:68%##
  <<Dinamo>> vs Steaua
  __FC Bayern München__: ##red:accidentări / suspendări##
  | Meci | Cotă | Edge |
  |---|---|---|
  | A vs B | 1.85 | ##green:+3.2%## |
  ```
- Testul trebuie să eșueze pe codul actual și să treacă după fix.

### Pasul 3 — schimbare minimă

- Un fix = un diff mic, cu scop clar. Nu amesteca redenumiri, formatări și feature-uri.
- Păstrează contractul API și schema SQLite. Dacă e nevoie de schimbare de contract,
  cere aprobare și oferă variantă backward-compatible.
- Respectă stilul existent: vanilla JS, fără dependențe noi dacă se poate, funcții mici.

### Pasul 4 — verificare

- Repornește serverul; confirmă că `/api/version` s-a schimbat.
- Hard reload (sau link cu `?u=<timestamp>`); verifică pe desktop și viewport mobil.
- Rulează matricea de test din secțiunea 7.
- Compară capturi „before/after”.

### Pasul 5 — raport

- Livrează raportul în formatul din secțiunea 8, în română.
- Include ce ai schimbat, ce ai testat, ce risc rămâne și ce ai lăsat intenționat.

---

## 6. Fixuri cerute și criterii de acceptare

### F1. Widget verdict (P0)

- Extrage `[VERDICT]` din **textul brut**, înainte de orice `escape`/markdown:
  regex tolerant la spații și newline, JSON.parse în `try/catch`.
- Elimină linia din textul afișat; nu lăsa JSON brut în bubble.
- Afișează două carduri: 👍 `win_pct` / 👎 `100 - win_pct`, cu animație de numărare
  (respectă `prefers-reduced-motion`).
- Clamp `0..100`; dacă JSON-ul e invalid, nu inventa procente — afișează textul fără widget
  și loghează eroarea în consolă.
- Afișează `side` și `event` sub carduri, cu escape.
- Chei i18n: verdict, câștig, pierdut, în toate cele trei limbi.
- Test: 0%, 50%, 100%, `win_pct` lipsă, JSON invalid, text cu acolade în `event`.

### F2. Parser inline sigur (P0)

Ordinea obligatorie:

1. separă verdictul din textul brut;
2. escapează HTML;
3. aplică markupul pe textul escapizat;
4. randază în DOM.

Suport minim:

- `##green:...##`, `##red:...##`, `##yellow:...##` → `<span class="pct pct-ok|pct-bad|pct-warn">`;
- `<<Echipa>>` → `<span class="winner">Echipa</span>` (inclusiv forma escapizată
  `&lt;&lt;...&gt;&gt;`);
- `__Echipa__` → `<strong class="hl">`;
- `**bold**`, `*italic*`, `` `code` ``;
- tabele Markdown cu header, aliniere și scroll orizontal pe mobil;
- heading-uri `## Titlu`, liste `-`/`*`, linii orizontale.

Interzis: `innerHTML` cu text needomesticit, `eval`, regex care acceptă `<script>`.
Test XSS: `Analizează <img src=x onerror=alert(1)>` nu execută nimic.

### F3. Tabele Markdown (P0/P1)

- Păstrează coloanele; nu turti în bullet-uri.
- Înveliș cu `overflow-x:auto` pe mobil.
- Pentru coloanele numerice cu `%` sau `edge`, opțional bară vizuală, fără a rupe textul.
- Tabelele din `build_ticket` trebuie să arate ca tabel, nu ca listă.

### F4. Plasă de siguranță pentru verdict (P1)

- În `backend/chat.py`, când ultimul răspuns a folosit `analyze_match_deep` sau
  `get_value_bets` și nu conține `[VERDICT]`, calculează verdictul **doar din datele
  tool-ului** (ex. `model_prob` / `win_pct` deja existent) și adaugă linia.
- Nu inventa probabilități; dacă datele lipsesc, nu adăuga nimic.
- Marchează intern sursa (`fallback`) pentru debug; nu o afișa clientului.
- Test: model care răspunde fără verdict → widgetul apare cu procentul tool-ului.

### F5. Loader cu procent numeric (P1)

- Afișează `NN%` lângă bară, sincronizat cu `progressFill`.
- La final: `100% · Gata!` (sau echivalentul i18n).
- La eșec: oprește la procentul curent și afișează mesajul clar.
- Test: analiză reușită, analiză fără meci, refresh eșuat.

### F6. Istoric chat (P1)

- La deschiderea tab-ului Asistent, încarcă `GET /api/chat/history?limit=50` și randează
  mesajele cu același `renderReply`.
- Buton „Șterge istoricul” → `DELETE /api/chat/history`, cu confirmare.
- Nu duplica mesajele sesiunii curente; după reload, istoricul trebuie să apară o singură dată.

### F7. Stare meci și procente (P1)

- Confirmă că un meci `finished` are badge „încheiat”, scor final și rămâne analizabil.
- Nu afișa minut live după final; nu afișa `'` fără valoare.
- În analiza unui meci trecut, păstrează procentele modelului și afișează avertismentul
  `res.past`.
- Test: meci live, meci terminat, meci viitor, meci fără cote.

### F8. Indicator value bets auto (P2, opțional)

- Consumă `/api/value-bets/auto` pentru badge „scanning” și listă, doar dacă timpul permite.
- Nu bloca restul fixurilor pentru acest punct.

### F9. Deduplicare fixtures + potrivire meci (P0)

**Frontend:**

- Adaugă `commence_time` în body-ul lui `/api/analyze` (`app.js:1857`) și în semnătura
  `runAnalysis(home, away, eventId, commenceTime, force)`.
- Toți callerii care au un item de fixture îl transmit: căutare, listă de meciuri, recomandare,
  value bets. Pentru value bets, `event_id` rămâne potrivirea exactă.

**Backend:**

- `AnalyzeIn` primește `commence_time: Optional[str] = None`.
- Extrage un matcher comun (ex. `find_cached_event(home, away, sport, event_id, commence_time)`)
  și folosește-l în `microbist._find_event` **și** în `chat._deep_analysis`.
- `_find_event(home, away, sport, event_id=None, commence_time=None)`:
  1. dacă `event_id` se potrivește exact, îl returnează;
  2. altfel construiește candidați după nume fuzzy, nu doar substring:
     - normalizează diacriticele și tokenii;
     - ignoră prefixe/sufixe de club (`FC`, `CF`, `SC`, `AC`, `SSC`, `Club`, `de`, `del`);
     - tratează aliasuri frecvente (`Inter` ↔ `Internazionale`, `München` ↔ `Munich`,
       `Atlético` ↔ `Atletico`, `Borussia` etc.);
     - folosește `difflib.SequenceMatcher` sau overlap de tokeni cu prag configurabil;
  3. dacă `commence_time` există, cere diferență de cel mult **36h** față de kickoff;
     alege candidatul cu diferența minimă;
  4. niciodată nu returna un meci la mai mult de 36h distanță;
  5. dacă există mai mulți candidați ambigui, preferă cel cu `bookmakers` h2h și loghează.
- Deduplică lista din `/api/fixtures` înainte de a o returna:
  - cheie = tokeni de echipe normalizați + kickoff rotunjit la ±90 min;
  - dacă există pereche football-data + odds, păstrează itemul cu cote, dar păstrează
    `source` original într-un câmp `sources`;
  - nu elimina meciurile care chiar nu au pereche.
- Test obligatoriu:
  - `Venezia FC vs FC Internazionale Milano` și `Venezia vs Inter Milan` trebuie să
    returneze același `event_id` și aceleași probabilități;
  - `1. FC Union Berlin vs 1. FC Köln` din 1 nov nu are voie să returneze meciul din 27 oct;
  - lista de fixtures nu mai conține două carduri pentru același meci la aceeași oră.
- Invalidează cache-ul de fixtures după schimbarea structurii (TTL scurt sau cheie nouă),
  altfel lista veche cu duplicate rămâne servită până expiră.

### F10. O singură casă de pariuri (P0)

- `consensus_probs()`: pragul devine `max(1, int(min_books))` (`sharp.py:83`).
- `reference(event)` păstrează implicit `min_consensus_books=3` pentru value bets — o singură
  casă nu are voie să genereze „edge”.
- Pentru analiza afișată, `market_sides()` poate folosi o singură casă; marchează răspunsul
  cu `books: 1` și `kind: "consensus"` (sau `single`), iar UI afișează „o singură casă”.
- În `microbist.analyze`, `market_block` poate folosi `sharp.reference(event, min_consensus_books=1)`
  pentru afișare; `find_value_bets` rămâne strict.
- Acceptare: `Washington Wizards vs Charlotte Hornets`, `Manel Kape vs Joshua Van` și
  `Liverpool vs Manchester United` returnează probabilități home/away (draw opțional) și
  bara 1/X/2 (X lipsește la sporturile cu două rezultate).

### F11. Zero cote și empty-state clar (P0/P1)

- Backend: când `predict_1x2()` returnează `None`, adaugă în răspuns:
  - `probabilities: null`;
  - `probabilities_note`: motiv (`no_odds`, `no_h2h_market`, `single_book_unsupported`,
    `sport_not_supported`);
  - `odds_status`: `none`, `totals_only`, `partial`.
- UI: dacă `probabilities` lipsește sau toate valorile sunt `null`:
  - nu mai randa titlul „Șanse calculate” cu corp gol;
  - afișează un card scurt: „Nu am cote 1X2 pentru acest meci” + motivul + ce poate face
    clientul (refresh, alt meci, revină mai târziu);
  - dacă există `market.sides`, afișează procentele pieței etichetate „Piața (fără model)”,
    nu le prezenta ca probabilitate a modelului.
- Opțional, doar la cerere explicită de analiză: încearcă aducerea ligii on-demand
  (`fetch_league`) dacă meciul e într-o ligă acoperită și nu are cote. Limitează la 1 request
  per ligă / 6h și nu rula în scanările de fundal.
- Acceptare: `Daniel Dubois vs Agit Kabayel` afișează mesaj clar, nu secțiune goală;
  niciun card cu `has_odds:false` nu mai pare „analiză stricată”.
- La orice schimbare de payload: bump `analyze|v2` → `analyze|v3` în `microbist.py:1196`
  și `CACHE_PREFIX` în `app.js:1071`, altfel clienții primesc răspunsuri vechi fără noile
  câmpuri.

### F12. Sursă externă pentru procente (P2, opțional)

- Doar dacă F9-F11 nu acoperă destule meciuri: pentru fotbalul de azi fără cote, folosește
  `football_match` / API-Football `predictions` și afișează procentele ca sursă externă,
  clar etichetate, cu fallback onest dacă lipsește.
- Nu înlocui modelul de cote cu predicția externă; o afișezi separat.
- Consumă 1 request/meci; respectă limita de 100/zi.

### F13. Semantica șansei pe bilet (P1)

**Problema:** biletul de 3 selecții a afișat „șansă câștig 31% · risc 69%”. Fiecare
selecție avea peste 50% (aproximativ 76%, 67%, 61%), dar produsul lor este ~31%. Matematica
este corectă; prezentarea induce confuzie.

**Cerințe:**

- Tabelul biletului are coloană separată **Șansă** pentru fiecare selecție (model_prob).
- Linia de sumar folosește eticheta **„șansă combinată”**, nu „șansă câștig” ambiguu.
- Dacă șansa combinată este sub 50%, adaugă o notă scurtă: fiecare meci poate fi peste
  50%, dar la parlay șansele se înmulțesc. Oferă alternativa cu 2 selecții și procentul ei.
- Nu numi biletul „sigur” când șansa combinată e sub 50%.
- `build_ticket` returnează `true_prob` per selecție și `combined_prob` pentru bilet.
- Pentru cereri de tip „sigure / foarte probabile”, sortează după `true_prob` descendent
  și, opțional, filtrează selecțiile sub 60%. Nu promite peste 51% pentru 3 selecții dacă
  datele nu permit.
- Test: bilet 3 selecții cu 76%/67%/61% → tabel arată cele trei valori, sumarul arată
  ~31% combinat, nota explică înmulțirea și oferă alternativa de 2 selecții.

---

## 7. Matrice de test

Rulează în RO, DE, EN. Pentru fiecare caz, notează rezultatul și captura.

| # | Acțiune | Rezultat așteptat |
|---|---|---|
| 1 | Chat: `Analizează meciul FC Barcelona Bàsquet vs Olympiacos` | Widget cu două procente care însumează 100; fără `[VERDICT]` brut; fără `##`/`<<`/`__`. |
| 2 | Chat: `Fa-mi un bilet cu 3 selecții din cele mai sigure value bets de azi` | Tabel real; „șansă câștig 32%” colorat; „risc 68%” colorat; widget la final. |
| 3 | Chat: `Da-mi top 3 value bets, doar numele` | Procente și cote lizibile; fără markup brut. |
| 4 | Chat DE: `Welcher Tipp bei diesem Spiel gibt value und ist über 50% wahrscheinlich` | Text în germană; verdict tradus; procente corecte. |
| 5 | Chat EN: `Analyze the match Arsenal vs Chelsea` | Text în engleză; verdict tradus. |
| 6 | Chat cu `<img src=x onerror=alert(1)>` | Niciun dialog; text afișat literal. |
| 7 | Analiză din tab-ul Acasă | Bară de probabilități 1/X/2, cote, value bets, procente vizibile. |
| 8 | Loader la analiză | Procent numeric crește până la 100%; „Gata”. |
| 9 | Reload pagină | Istoricul chatului apare; analizele nu se pierd. |
| 10 | Meci terminat în listă | Badge „încheiat”, scor final, analiză disponibilă. |
| 11 | Meci live | Badge LIVE, minut și scor; fără erori după final. |
| 12 | Mobil 390×844 | Tabelele au scroll orizontal; widgetul nu iese din ecran; butoanele sunt apăsabile. |
| 13 | Offline / cache stale | Aplicația afișează datele din cache și mesajul de offline, fără crash. |
| 14 | Provider AI picat | Eroare clară în chat, nu buclă infinită; restul aplicației funcționează. |
| 15 | Fixtures 7 zile | Niciun meci nu apare de două ori la aceeași oră; cardurile păstrează sursa cu cote. |
| 16 | `Venezia FC vs FC Internazionale Milano` | Găsește meciul; aceleași probabilități ca `Venezia vs Inter Milan`: 11.75% / 15.67% / 72.58%. |
| 17 | `1. FC Union Berlin vs 1. FC Köln` (1 nov) | Returnează meciul din 1 nov, nu pe cel din 27 oct; data din răspuns coincide. |
| 18 | `Washington Wizards vs Charlotte Hornets` | Procent 1/2 afișat, etichetă „o singură casă”; fără edge inventat. |
| 19 | `Manel Kape vs Joshua Van` | Procent 1/2 afișat din singura casă disponibilă. |
| 20 | `Daniel Dubois vs Agit Kabayel` | Mesaj clar „fără cote 1X2”; fără titlu gol „Șanse calculate”. |
| 21 | Meci fără cote din football-data | Fie găsește geamănul cu cote, fie afișează mesajul clar; niciodată probabilități de la alt meci. |
| 22 | Chat: `fa-mi un bilet cu 3 meciuri` | Tabel cu coloana „Șansă” per selecție; sumar „șansă combinată”; dacă e sub 50%, nota explică înmulțirea și oferă alternativa de 2 selecții. |
| 23 | Chat: `bilet cu 3 meciuri foarte probabile` | Selecțiile sunt sortate după șansa modelului; fiecare peste 50% dacă există în cache; biletul nu este numit „sigur” când combinatul e sub 50%. |

---

## 8. Formatul raportului final

Livrează în română, fără laudă și fără filler:

1. **Rezumat executiv** — 5 rânduri: ce era rupt, ce ai reparat, ce rămâne.
2. **Tabel constatări** — `severitate | fișier:linie | dovadă | impact | fix`.
3. **Schimbări aplicate** — fișier, motiv, diff scurt (max. 15 linii per fișier).
4. **Dovezi de test** — tabelul din secțiunea 7, cu `pass/fail` și capturi.
5. **Riscuri reziduale** — ce nu ai putut verifica, ce depinde de provideri/quota.
6. **Următorii pași** — maxim 5, prioritizați.

Nu raporta „totul funcționează” fără dovadă. Nu ascunde un test picat.

---

## 9. Guardrails

- Nu modifica promptul astfel încât să elimine contractul `[VERDICT]`; dimpotrivă, păstrează-l
  și adaugă plasa de siguranță.
- Nu schimba endpointuri, nume de câmpuri API sau schema DB fără aprobare.
- Nu adăuga framework sau bundler; dashboardul rămâne vanilla.
- Nu atinge `C:\Users\eusun\sportsbet-app`.
- Nu rula refresh de cote sau interogări API-Football în buclă pentru teste.
- Nu afișa chei API, tokeni sau conținut din `config.json` în raport.
- Nu șterge fișiere, cache-uri sau backup-uri fără confirmare explicită.
- Dacă un fix depășește 2 fișiere, împarte-l în pași și raportează între pași.

---

## 10. Definiția „gata”

- Clientul vede procentele la finalul analizei, colorate și animate, în toate cele trei limbi.
- Fiecare card cu cote produce procente de câștig; fiecare card fără cote afișează un motiv clar.
- Nu mai există fixtures duplicate și nicio analiză nu returnează probabilitățile altui meci.
- Nu mai apare niciun `[VERDICT]`, `##green:`, `##red:`, `<<`, `__` în interfață.
- Tabelele Markdown sunt lizibile pe mobil.
- Verdictul apare și când modelul uită să îl emită, dacă tool-ul are date.
- Biletele afișează șansa fiecărei selecții și șansa combinată; sub 50% au explicație clară.
- Loader-ul afișează procent numeric până la 100%.
- Istoricul chatului supraviețuiește reload-ului.
- Matricea de test este completă, cu dovezi.
- Backup creat, server repornit, `/api/version` verificat.
