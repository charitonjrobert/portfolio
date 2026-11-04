# Metaprompt — audit German și comutare limbă MicrobistBets

> Folosește acest prompt pentru a verifica și corecta limba germană în aplicația
> MicrobistBets. Scopul nu este doar „are chei DE”, ci ca utilizatorul german să nu vadă
> niciun text românesc sau englezesc rătăcit, iar comutarea limbii să actualizeze imediat
> tot ecranul.

---

## 1. Context

- Aplicație: `C:\Projects\sportsbet-app`
- Frontend: `dashboard/app.js` (vanilla JS, i18n în `I18N.ro/de/en` + `Object.assign`)
- Backend: `backend/*.py`; textele de analiză, limite și fixtures sunt localizate prin `lang`
- Limbi: RO, DE, EN. Germana trebuie să fie **bundesdeutsches Hochdeutsch**, nu elvețiană
  sau austriacă.
- Pornire:
  ```powershell
  cd C:\Projects\sportsbet-app\backend
  python -m uvicorn main:app --host 127.0.0.1 --port 8000
  ```
- Acces: link cu `?k=<ui.access_key>` din `backend/config.json`. Nu pune cheia în raport.

---

## 2. Reguli de calitate pentru germană

1. **Tot textul vizibil** este în germană: titluri, butoane, placeholder-e, tooltip-uri,
   mesaje de eroare, stări goale, tabele, verdict, loader, limite, wallet, raport.
2. **Fără românismi**: `Egal`, `Meci`, `Cotă`, `Pariu`, `Șansă`, `Încredere`, `Acasă`,
   `Meciuri`, `Asistent`, `Gata`, `rămase`, `se reînnoiește`, `fără limită`.
3. **Fără englezisme inutile**: `Match` → `Spiel`, `Odds` → `Quoten`, `Draw` →
   `Unentschieden`, `Win chance` → `Gewinnchance`. Termenii tehnici consacrați rămân:
   `Value Bet`, `Sharp`, `CLV`, `Edge`, `Live`, `Stream`, `NBA`.
4. **Tipografie germană**: ghilimele `„Text“`, nu `"Text"`; procent cu spațiu înainte de
   `%` în proză (`31 %`), fără spațiu în tabele compacte dacă designul cere asta.
5. **Dată și oră**: `de-DE`, 24h, `31.10.2026 18:30`, nu `10/31 6:30 PM`.
6. **Numere și bani**: virgulă decimală în germană (`70,00 Demo`, `3,08 %`). Cotele pot
   rămâne cu punct dacă sunt afișate ca piață internațională, dar fii consecvent.
7. **Gen și articole**: `der Sharp-Markt`, `den Sharp-Markt`, `die Quote`, `das Ticket`,
   `die Auswahl`, `der Einsatz`, `die Gewinnchance`, `das Risiko`.
8. **Plural**: `1 Auswahl`, `3 Auswahlen`; `1 Spiel`, `3 Spiele`; `1 Wette`, `3 Wetten`.
9. **Nu traduci numele echipelor, ligile proprii, știrile externe** — acestea rămân în
   limba sursă. Traduci doar eticheta din jurul lor.
10. **Chat**: răspunsul modelului și quick-path-urile (bilet, meciul zilei) trebuie să fie
    în limba selectată. Modelul primește `lang` și o instrucțiune explicită de limbă.

---

## 3. Metodă de verificare

### 3.1 Paritate chei

Rulează în browser:

```js
const keys = Object.keys(I18N.ro);
({
  de_missing: keys.filter(k => !(k in I18N.de)),
  en_missing: keys.filter(k => !(k in I18N.en)),
  de_extra: Object.keys(I18N.de).filter(k => !(k in I18N.ro)),
});
```

Rezultat așteptat: toate cele trei liste goale. Nu te opri aici: o cheie poate exista cu
text românesc.

### 3.2 Text românesc rătăcit

Caută în valorile DE caracterele `ăâîșțĂÂÎȘȚ` și cuvintele:
`meci`, `cotă`, `cote`, `pariu`, `bilet`, `șansă`, `încredere`, `egal`, `acasă`, `asistent`,
`rămase`, `reînnoiește`, `fără limită`, `Gata`.

Caută și în codul din afara obiectului `I18N` (funcții de randare) șiruri românești hardcodate.

### 3.3 Comutare limbă

Testează click pe `DE` / `EN` / `RO` **fără reload** și verifică:

- tab-urile, titlurile, butoanele, placeholder-ele;
- lista de meciuri, chips-urile de sport, notele;
- cardul de analiză deschis (probabilități, piață, value bets, motivul, știrile);
- wallet: sold, profit, pariuri, „keine Spiele beobachtet”;
- limits modal: nivel, cotă, „erneuert sich in”;
- chat: chips-urile și răspunsurile noi;
- raportul de meci, dacă e deschis.

Dacă o secțiune rămâne în limba veche, `setLang()` trebuie să re-randeze secțiunea
(nu doar `applyI18n()` pe elementele statice).

### 3.4 Date, numere, sporturi

- `fmtTime` / `fmtFull` folosesc `de-DE`, 24h.
- `fmtMoney` / `fmtNum` folosesc virgulă decimală.
- Chips-urile de sport: Fußball, Basketball, Tennis, Boxen, MMA, Eishockey — nu
  `soccer`, `boxing`, `icehockey`.
- Meciurile fără ligă afișează sportul tradus, nu grupul brut.

### 3.5 Backend

- `POST /api/chat` primește `lang` și îl transmite lui `ChatService.chat`.
- Quick-path bilet: header, tabel, „kombinierte Gewinnchance”, „Risiko”, notă, alternativă,
  verdict — toate în germană.
- Quick-path „Spiel des Tages”: tabel și „Warum ich es wähle” în germană.
- `POST /api/analyze` primește `lang` și întoarce `reasons`, `note`, `disclaimer` în germană.
- `/api/fixtures` notele sunt în germană; nu afișa excepții brute de rețea.
- `/api/limits` mesajele sunt în germană.

### 3.6 Chat general

Întrebare de control:

> „Antworte kurz auf Deutsch: Was kannst du mir bei Wetten zeigen?”

Răspunsul trebuie să fie în germană, fără `[VERDICT]` inventat pentru o întrebare generală.
Apoi:

> „Mach mir eine Wette mit 3 Spielen”

Trebuie să declanșeze biletul rapid, cu tabel german și widget 31 % / 69 %.

---

## 4. Defecte deja corectate (28 oct 2026)

- `setLang()` re-randează meciuri, analiză, wallet, bets, watch, limits, chat chips.
- `renderProbabilityBars` și tabelul de piață folosesc `Unentschieden`, nu `Egal`.
- `renderSports` traduce grupele de sport (`Fußball`, `Boxen` etc.).
- `fmtTime` / `fmtFull` folosesc `de-DE` și 24h.
- `fmtMoney` / `fmtNum` folosesc virgulă decimală.
- Quick-path bilet și „Spiel des Tages” localizate în RO/DE/EN.
- `/api/chat` primește `lang`; modelul are instrucțiune explicită de limbă.
- Notele football-data nu mai afișează excepții brute.
- Ghilimele germane `„…“`, `wallet.subtitle` → `Ergebnis`, `res.stars` → `Vertrauen`.
- `[VERDICT]` interzis pentru întrebări generale.

---

## 5. Rezidual cunoscut

- Știrile și numele ligilor din surse externe rămân în limba originală (engleză).
- Unele erori rare din `betting.py` / `main.py` (ex. „Pariul nu există”) pot fi încă în
  română; dacă apar în UI, localizează-le sau mapează-le în frontend.
- Istoricul vechi de chat rămâne în limba în care a fost scris; mesajele noi folosesc limba
  selectată.
- Cotele pot păstra punctul decimal ca convenție de piață; restul sumelor folosesc virgula.

---

## 6. Formatul raportului

1. Paritate chei (RO/DE/EN) și numărul de chei.
2. Tabel `cheie | text DE | problemă | fix`.
3. Teste de comutare limbă, cu capturi înainte/după.
4. Teste chat DE (general + bilet), cu răspuns brut și randat.
5. Riscuri reziduale și ce nu poate fi tradus (știri externe).
6. Capturi finale în germană, salvate în `screenshots/<data>-de/`.

Nu declara „totul e tradus” fără să fi verificat toate tab-urile și cel puțin o analiză,
un bilet și un mesaj de eroare.
