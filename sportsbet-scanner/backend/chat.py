import json
import re
import time
from datetime import datetime, timezone

import requests

from value import find_value_bets, find_arbitrage
from context import extract_players, build_impact
from leagues import build_catalog, match_leagues, fetch_leagues, GROUPS, ALIASES
from websearch import web_search, fetch_page
from microbist import _pair_sim, _hours_apart

_CURRENT_SEASON = datetime.now().year

FOOTBALL_MARKET_KEYS = {
    "1x2": ["Match Winner"],
    "match winner": ["Match Winner"],
    "btts": ["Both Teams Score"],
    "ambele marcate": ["Both Teams Score"],
    "gg": ["Both Teams Score"],
    "ng": ["Both Teams Score"],
    "double chance": ["Double Chance"],
    "sansa dubla": ["Double Chance"],
    "draw no bet": ["Draw No Bet"],
    "fara egal": ["Draw No Bet"],
    "ht/ft": ["HT/FT Double"],
    "pauza/final": ["HT/FT Double"],
    "odd/even": ["Odd/Even"],
    "par/impar": ["Odd/Even"],
    "exact score": ["Exact Score"],
    "scor exact": ["Exact Score"],
    "over/under": ["Goals Over/Under"],
    "total": ["Goals Over/Under"],
    "goluri pauza": ["Goals Over/Under First Half"],
    "goals first half": ["Goals Over/Under First Half"],
    "corners": ["Total Corners", "Corners Over Under"],
    "cornere": ["Total Corners", "Corners Over Under"],
}

FOOTBALL_CORE_MARKETS = [
    "Match Winner", "Double Chance", "Draw No Bet", "Both Teams Score",
    "Goals Over/Under", "Goals Over/Under First Half", "HT/FT Double",
    "Total Corners", "Odd/Even", "Exact Score",
]

FOOTBALL_VALUE_FILTER = {
    "Goals Over/Under": {"Over 0.5", "Under 0.5", "Over 1.5", "Under 1.5",
                         "Over 2.5", "Under 2.5", "Over 3.5", "Under 3.5"},
    "Goals Over/Under First Half": {"Over 0.5", "Under 0.5", "Over 1.5", "Under 1.5",
                                    "Over 2.5", "Under 2.5"},
    "Total Corners": {"Over 7.5", "Under 7.5", "Over 8.5", "Under 8.5",
                      "Over 9.5", "Under 9.5", "Over 10.5", "Under 10.5"},
    "Corners Over Under": {"Over 7.5", "Under 7.5", "Over 8.5", "Under 8.5",
                           "Over 9.5", "Under 9.5", "Over 10.5", "Under 10.5"},
}

CHAT_TEXT = {
    "ro": {
        "ticket_header": "BILET SUGERIT", "ticket_selections": "selecții", "parlay": "bilet",
        "combined": "șansă combinată", "risk": "risc",
        "table_match": "Meci", "table_pick": "Selecție", "table_odds": "Cota",
        "table_edge": "Edge", "table_chance": "Șansă", "table_conf": "Înc.",
        "table_date": "Data", "why_picks": "De ce sunt alese:",
        "odds_word": "cota", "injuries": "accidentări / suspendări",
        "positive_news": "știri pozitive", "neutral_news": "știri neutre",
        "check_odds": "_Verifică cotele la casa de pariuri înainte de a juca. Joci responsabil._",
        "risk_note": "_Șansă combinată sub 50%: fiecare meci poate avea peste 50%, dar la un bilet multiplu șansele se înmulțesc._",
        "alternative": " Alternativă: **2 selecții → {pct}%** șansă combinată.",
        "no_ticket": "Nu am găsit suficiente value bets eligibile pentru a genera un bilet cu parametrii specificați.",
        "match_day": "MECIUL ZILEI", "table_detail": "Detaliu", "table_value": "Valoare",
        "table_selection": "Selecție", "table_confidence": "Încredere",
        "table_datetime": "Data și ora", "table_league": "Liga",
        "why_safe": "De ce îl aleg:",
        "prefetch": "[Meciuri VIITOARE aduse automat prin fetch_league; nu mai apela fetch_league pentru ele]",
    },
    "de": {
        "ticket_header": "TICKET-VORSCHLAG", "ticket_selections": "Auswahlen", "parlay": "Kombiwette",
        "combined": "kombinierte Gewinnchance", "risk": "Risiko",
        "table_match": "Spiel", "table_pick": "Auswahl", "table_odds": "Quote",
        "table_edge": "Edge", "table_chance": "Chance", "table_conf": "Vertrauen",
        "table_date": "Datum", "why_picks": "Warum diese Auswahl:",
        "odds_word": "Quote", "injuries": "Verletzungen / Sperren",
        "positive_news": "positive News", "neutral_news": "neutrale News",
        "check_odds": "_Prüfe die Quoten beim Buchmacher, bevor du spielst. Spiele verantwortungsvoll._",
        "risk_note": "_Kombinierte Gewinnchance unter 50 %: Jedes Spiel kann über 50 % liegen, aber bei einer Kombiwette werden die Chancen multipliziert._",
        "alternative": " Alternative: **2 Auswahlen → {pct}%** kombinierte Gewinnchance.",
        "no_ticket": "Ich habe nicht genug passende Value Bets gefunden, um ein Ticket mit diesen Parametern zu bauen.",
        "match_day": "SPIEL DES TAGES", "table_detail": "Detail", "table_value": "Wert",
        "table_selection": "Auswahl", "table_confidence": "Vertrauen",
        "table_datetime": "Datum und Uhrzeit", "table_league": "Liga",
        "why_safe": "Warum ich es wähle:",
        "prefetch": "[Kommende Spiele automatisch über fetch_league geladen; fetch_league dafür nicht erneut aufrufen]",
    },
    "en": {
        "ticket_header": "SUGGESTED TICKET", "ticket_selections": "selections", "parlay": "parlay",
        "combined": "combined win chance", "risk": "risk",
        "table_match": "Match", "table_pick": "Selection", "table_odds": "Odds",
        "table_edge": "Edge", "table_chance": "Chance", "table_conf": "Confidence",
        "table_date": "Date", "why_picks": "Why these picks:",
        "odds_word": "odds", "injuries": "injuries / suspensions",
        "positive_news": "positive news", "neutral_news": "neutral news",
        "check_odds": "_Check the odds at the bookmaker before betting. Play responsibly._",
        "risk_note": "_Combined win chance below 50%: each match can be above 50%, but in a parlay the chances multiply._",
        "alternative": " Alternative: **2 selections → {pct}%** combined win chance.",
        "no_ticket": "I did not find enough eligible value bets to build a ticket with those parameters.",
        "match_day": "MATCH OF THE DAY", "table_detail": "Detail", "table_value": "Value",
        "table_selection": "Selection", "table_confidence": "Confidence",
        "table_datetime": "Date and time", "table_league": "League",
        "why_safe": "Why I pick it:",
        "prefetch": "[Upcoming matches preloaded through fetch_league; do not call fetch_league again for them]",
    },
}

SPORT_LABELS = {
    "ro": {"soccer": "Fotbal", "basketball": "Baschet", "tennis": "Tenis", "mma": "MMA",
           "boxing": "Box", "icehockey": "Hochei", "americanfootball": "Fotbal american"},
    "de": {"soccer": "Fußball", "basketball": "Basketball", "tennis": "Tennis", "mma": "MMA",
           "boxing": "Boxen", "icehockey": "Eishockey", "americanfootball": "American Football"},
    "en": {"soccer": "Soccer", "basketball": "Basketball", "tennis": "Tennis", "mma": "MMA",
           "boxing": "Boxing", "icehockey": "Ice hockey", "americanfootball": "American football"},
}

LANG_INSTRUCTION = {
    "ro": "LIMBA RĂSPUNSULUI: română. Toate titlurile, etichetele de tabel, concluziile și avertismentele în română.",
    "de": "ANTWORTSPRACHE: Deutsch. Antworte ausschließlich auf Deutsch und in bundesdeutschem Hochdeutsch (keine Helvetismen: „Tickets“, nicht „Billette“; „Buchmacher/Wettanbieter“, nicht „Agentur“). Übersetze alle Überschriften, Tabellenlabels, Fazits und Warnungen. Tabellenkopf: Spiel | Auswahl | Quote | Edge | Chance | Vertrauen. Teamnamen bleiben wie in den Daten.",
    "en": "RESPONSE LANGUAGE: English. Answer only in English. Translate all headings, table labels, conclusions and warnings. Table header: Match | Selection | Odds | Edge | Chance | Confidence. Team names stay as in the data.",
}

SYSTEM_PROMPT = (
    "Ești asistentul analitic al unui scanner de cote sportive (fotbal, tenis, baschet, darts). "
    "Răspunde în limba utilizatorului, concis și onest. Nu promite profit garantat niciodată. "
    "Folosește tool-urile disponibile pentru date reale din aplicație: value bets, arbitraj, "
    "context echipe, statistici bankroll, refresh cote. Când utilizezi un tool, menționează scurt "
    "ce ai verificat. Recomandă jucat doar value bets cu încredere 4-5 stele. "
    "REGULI DE ONESTITATE ABSOLUTE: nu inventa NICIODATĂ scoruri, medii, cote, procente, "
    "accidentări, forme sau statistici. Orice cifră trebuie să provină dintr-un tool apelat în "
    "această conversație. Dacă nu ai date reale pentru o afirmație, spui explicit că nu ai date, "
    "nu ghicești. Separi întotdeauna ce e VERIFICAT (din tool) de părerea personală."
)

MICROBIST_PROMPT = (
    "Te cheamă Miki și ești un microbist pasionat din România, cu 20 de ani de suferință "
    "în tribună și pe canapea. Vorbești românește natural, cu entuziasm de suporter: folosești "
    "expresii de microbist (\"bă, aia e echipă!\", \"ne jucăm viața pe un corner\"), dar ești și "
    "un analist sportiv serios în fotbal, tenis, baschet și darts. Când analizezi un meci, "
    "vorbești despre formă, accidentări, atmosferă, motivare, dar te bazezi pe date reale din "
    "tool-uri, nu pe presimțiri. Reguli stricte: nu promiți niciodată profit garantat, nu "
    "recomanzi pariuri riscante, recomanzi doar value bets cu 4-5 stele și spui mereu să "
    "verifici cotele înainte de a juca. Când folosești un tool, spui pe scurt ce ai verificat. "
    "REGULI DE ONESTITATE ABSOLUTE (cele mai importante): "
    "1. INTERZIS să inventezi scoruri, medii de goluri, cote, procente, accidentări, forme, "
    "statistici sau meciuri. Dacă o cifră nu a venit dintr-un tool apelat în această conversație, "
    "nu o spui. "
    "2. Orice număr pe care îl menționezi trebuie să fie luat direct din rezultatul unui tool "
    "(get_match_patterns, get_value_bets, get_team_context, get_odds_summary, get_stats). "
    "3. Dacă nu ai date reale pentru un subiect, spui clar: \"aici n-am date verificate, "
    "nu pot să-ți spun\" — nu ghici, nu completa din memorie. "
    "4. Separi întotdeauna [VERIFICAT din tool] de părerea ta de microbist (etichetată ca atare). "
    "BILETE (parlay/multiplu, mai multe meciuri): apelează ÎNTÂI build_ticket - e INSTANT din cache, "
    "fără apeluri externe. NU folosi fetch_league sau get_market_odds ca să compui bilete; le folosești "
    "doar dacă userul cere explicit meciuri/piețe care nu sunt în cache. Prezinți biletul ca tabel "
    "(Meci | Selecție | Cota | Edge | Șansă | Încredere) + cota totală și avertismentul de verificare a cotelor. "
    "Șansa fiecărei selecții este model_prob (din tool), iar șansa biletului este produsul lor: "
    "la 3 selecții de 70% șansa combinată e ~34%, nu 70%. Nu numi un bilet 'sigur' dacă șansa "
    "combinată e sub 50%; spune clar că fiecare meci poate fi peste 50%, dar selecțiile se înmulțesc. "
    "RĂSPUNS CONCIS: maximum ~100-150 cuvinte de proză. Datele (value bets, cote, comparații de echipe/jucători, "
    "probabilități) le prezinți în TABELE MARKDOWN cu coloane clare (ex: Meci | Selecție | Cota | Edge | Încredere) — "
    "nu le descrii în paragrafe lungi. Proza scurtă o rezervi doar pentru verdict și avertismente. "
    "Fiecare value bet pe un rând de tabel. Folosește rânduri scurte; nu repeta în text ce e deja în tabel. "
    "METODĂ DE ANALIZĂ A UNUI MECI (în 3 pași, folosește analyze_match_deep): "
    "Pasul 1 - analizezi meciul și echipele (cote, formă, istoric H2H dacă există). "
    "Pasul 2 - analizezi contextul echipelor: accidentări, suspendări, jucători pe bancă, transferuri. "
    "Pasul 3 - te uiți la jucătorii cu evenimente (accidentați MAI ALES, suspendați, transferați) "
    "extrași din știri și îi iei în calcul la concluzie. Dacă lipsește un jucător cheie, spui clar "
    "ce impact are asupra șanselor. "
    "LEGI DE PE TOT GLOBUL: dacă ești întrebat de meciuri dintr-o țară/ligă care nu e în cache, "
    "cheamă MAI ÎNTÂI fetch_league cu numele ligii/țării înainte să răspunzi. Ai acces la 78 de ligi "
    "(toate țările la fotbal, NBA/WNBA, NFL, NHL, MLB, tenis ATP/WTA, MMA, box, cricket, rugby, golf). "
    "IMPORTANT — MECIURI VIITOARE: fetch_league (the-odds-api) aduce MECIURI VIITOARE CU COTE pentru ligile "
    "pe care le acoperă, inclusiv Swiss Super League (Elveția, campionatul elvețian), Bundesliga, EPL, Serie A, "
    "La Liga, Eredivisie, MLS, J League, Brazilian Série A etc. Dacă utilizatorul cere meciuri care urmează "
    "(nu de azi) dintr-o ligă acoperită, cheamă fetch_league — NU spune 'meciurile viitoare nu sunt disponibile'. "
    "Dacă fetch_league returnează 'Nicio ligă găsită', spui onest că liga respectivă (ex: România, juniori/U18/U20/U21) "
    "nu este disponibilă pe sursa de date și NU inventezi meciuri. "
    "API-FOOTBALL (plan GRATUIT, 100 req/zi, date reale): ai acces la fotbal real din TOATE țările lumii — ligi de "
    "seniori, juniori și tineret (U19/U18/U17/U20/U21) din orice țară, inclusiv România. Pe gratuit ai inclus și COTE "
    "din această sursă: football_odds aduce cote reale (1X2, șansă dublă, fără egal, BTTS/ambele marcate, pauză/final, "
    "par/impar, scor exact, CORNERE, total goluri, total goluri în PRIMA REPRIZĂ). Pe planul gratuit sunt vizibile "
    "DOAR meciurile de AZI din toată lumea (cote incluse); meciurile viitoare și sezoanele curente pe ligă nu sunt "
    "accesibile (premium) — dacă țara/liga nu joacă azi, spui onest 'nu joacă azi'. football_fixtures cu 'azi'/'today' "
    "returnează toate meciurile zilei. Dacă ești întrebat de meciuri/program/cote dintr-o țară sau ligă de juniori, cheamă football_leagues "
    "pentru identificare, apoi football_fixtures (meciuri) sau football_odds (cote, poți specifica market: corners, "
    "goluri pauza, btts, etc.). Pentru H2H folosești football_h2h. Când cineva vrea cornere sau goluri până la pauză "
    "la un meci din afara the-odds-api, folosești football_odds — acum există date reale. Folosește aceste tool-uri "
    "cu moderație (100 req/zi, plus limită pe minut): pentru cote la mai multe meciuri din aceeași ligă fă UN SINGUR "
    "apel football_odds pentru liga respectivă (nu repeta apeluri pentru aceeași ligă, nu apela football_odds în buclă). "
    "Dacă primești eroare de rate-limit, o spui scurt și nu mai insiști. Separi mereu ce e din football_* (real) "
    "de ce e din cotele the-odds-api. "
    "CĂUTARE WEB: ai tool-urile web_search (Bing, rezultate cu link-uri) și fetch_page (deschide un URL). "
    "Folosește-le pentru MECIURI VIITOARE / PROGRAM / calendar din ligi sau sporturi pe care sursele de cote NU le au — "
    "ex: darts (nu e în cele 78 de ligi), România Liga 1/SuperLiga (nu e acoperită de the-odds-api), ligi de juniori. "
    "Când userul cere meciuri viitoare dintr-o astfel de ligă/sport, caută pe web (ex: 'SuperLiga Romania 2026-2027 program "
    "meciuri etape', 'PDC darts calendar 2026 meciuri program') și, dacă trebuie, deschide un site de rezultate/program. "
    "REGULI WEB: NU inventa niciodată meciuri, scoruri sau cote — raportezi DOAR ce găsești; spui clar că datele sunt "
    "'din căutare web' (nu cote verificate din sursele noastre de cote) și că trebuie verificate la casa de pariuri; "
    "dacă web_search întoarce eroare, spui scurt că nu ai putut căuta pe net. "
    "MECIURI VIITOARE ELVETIA/ALTE LIGI ACOPERITE: pentru ligile din the-odds-api (ex: Swiss Super League/Elveția, "
    "Bundesliga, EPL, Serie A, La Liga) fetch_league se apelează automat din context — aduce meciuri VIITOARE cu cote. "
    "INFO MECI: pentru date despre un meci de azi (ora exactă, stadion, oraș, ARBITRU, ANTRENORI, "
    "prognoza rezultatului cu % câștigător și advice, comparație formă/atac/apărare, ultimele H2H, line-up-ul "
    "confirmat dacă există) folosești football_match. Dacă line-up-ul nu e încă anunțat, spui onest că apare "
    "cu ~1h înainte de meci. "
    "AFIȘARE 1X2: piața '1X2' (Match Winner) înseamnă 1 = gazde câștigă, X = egal, 2 = oaspeți câștigă — "
    "e standardul universal. Nu confunda cu '1X'/'X2' (șansă dublă). Când afișezi 1X2, pune întotdeauna "
    "eticheta explicit: '1 <Echipa Gazdă>', 'X Egal', '2 <Echipa Oaspete>' (ex: '1 SC Freiburg 2.09', "
    "'X Egal 3.85', '2 Werder Bremen 3.76'). Nu folosi doar numele echipei fără 1/X/2. "
    "VERDICT FINAL: la finalul răspunsului, după concluzie, adaugi pe ULTIMA linie exact formatul: "
    "[VERDICT] {\"win_pct\": <număr 0-100>, \"side\": \"<selecția recomandată/analizată>\", \"event\": \"<EchipaA vs EchipaB>\"} "
    "win_pct = probabilitatea de câștig a selecției analizate, luată DOAR din datele tool-ului "
    "(ex: model 38.65% → win_pct 38.65; restul e probabilitatea de pierdere). Nu inventa procente. "
    "Această linie e afișată ca un widget animat de Like/Dislike, deci nu descrii în proză ce pune widgetul. "
    "Folosește [VERDICT] DOAR când ai analizat un meci sau un bilet concret; NU îl adăuga la "
    "întrebări generale, saluturi, explicații sau liste de funcții — acolo nu există o selecție de analizat. "
    "EVIDENȚIERE CÂȘTIGĂTOR: când prezinți un meci și declari o echipă câștigătoare, înconjuri numele echipei "
    "cu << și >> (ex: <<Dinamo>> vs Steaua). Dacă e egal, pui ambele: <<Dinamo>> vs <<Steaua>>. "
    "Folosește doar la concluzie/verdict, nu în fiecare rând de tabel. "
    "PIEȚE DISPONIBILE: pe lângă 1X2 (h2h) ai cote pe: total goluri (totals), ambele marcate (btts), "
    "șansă dublă (double_chance), fără egal (draw_no_bet), pauză/final (ht_ft), par/impar (odd_even). "
    "Folosește get_market_odds pentru oricare dintre ele; piețele în afară de h2h/totals sunt aduse "
    "on-demand automat. Pe API-Football (football_odds) ai în plus: cornere, goluri până la pauză, "
    "scor exact, șansă dublă, fără egal."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_value_bets",
            "description": "Lista value bets detectate (sport, meci, selecție, cotă, edge %, încredere 1-5 stele, context echipe). ATENȚIE: recalculează cu context/știri - lent. Pentru BILETE folosește build_ticket.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_ticket",
            "description": "Construiește INSTANT un bilet (parlay/multiplu) din value bets deja calculate în cache local. FĂRĂ apeluri externe, răspunde rapid. FOLOSEȘTE-L ÎNTOTDEAUNA când userul cere un bilet / bilet de N meciuri / multiple selecții.",
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "description": "Câte selecții să aibă biletul (default 10, max 20)."},
                    "sport": {"type": "string", "description": "Opțional: filtrează o rubrică (soccer, basketball, boxing, mma, icehockey etc.)."},
                    "min_edge_pct": {"type": "number", "description": "Edge minim % per selecție (default pragul configurat)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_arbitrage",
            "description": "Oportunități de arbitraj: combinații de pariuri cu profit garantat, mizele proporționale și casele.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stats",
            "description": "Statistici bankroll: sold, profit, ROI, număr pariuri, win rate.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_team_context",
            "description": "Contextul unei echipe/jucător: scor știri (-1..+1, negativ = accidentări/suspendări), titluri de știri recente.",
            "parameters": {
                "type": "object",
                "properties": {"team": {"type": "string", "description": "Numele echipei sau jucătorului"}},
                "required": ["team"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "refresh_odds",
            "description": "Reîmprospătează cotele de la casele de pariuri. Consumă 1 request per sport din limita lunară.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_odds_summary",
            "description": "Rezumatul cotelor din cache: număr meciuri per sport și cele mai bune cote per meci.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_match_patterns",
            "description": "Analiză istorică a meciurilor dintre două echipe: frecvența scorurilor, pattern-uri repetate (același scor de mai multe ori), medii de goluri și lambdas Poisson estimate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_a": {"type": "string", "description": "Prima echipă"},
                    "team_b": {"type": "string", "description": "A doua echipă"},
                },
                "required": ["team_a", "team_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_match_deep",
            "description": "Analiză profundă a unui meci în 3 pași: 1) datele meciului și cele mai bune cote, 2) contextul și impactul ambelor echipe (accidentări, suspendări, jucători pe bancă, transferuri), 3) jucătorii cu evenimente extrași din știri. Folosește aceasta pentru a analiza orice meci complet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_a": {"type": "string", "description": "Prima echipă"},
                    "team_b": {"type": "string", "description": "A doua echipă"},
                },
                "required": ["team_a", "team_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_league",
            "description": "Aduce cotele pentru o ligă/țară la cerere (consumă 1-5 requesturi API). Exemple: 'elveția'/'schweiz'/'super league' (Swiss Super League), 'brazil', 'Serie A', 'Nations League', 'MLS', 'EFL Cup', 'NBA'. Folosește când te întreabă cineva de meciuri dintr-o țară/ligă care nu e deja în cache — aduce MECIURI VIITOARE CU COTE pentru ligile acoperite. Returnează meciurile aduse și requesturile rămase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "league": {"type": "string", "description": "Numele ligii sau țării (ex: 'elveția', 'romania', 'Brazil Serie A', 'J League', 'boxing')"},
                },
                "required": ["league"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_odds",
            "description": "Cotele pe o piață specifică pentru un meci. market poate fi: h2h (1X2), totals (total goluri), btts (ambele marcate), double_chance (șansă dublă), draw_no_bet (fără egal), ht_ft (pauză/final), odd_even (par/impar). Piețele în afară de h2h/totals sunt aduse on-demand (consumă 1 request) și apoi rămân în cache.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_a": {"type": "string", "description": "Prima echipă"},
                    "team_b": {"type": "string", "description": "A doua echipă"},
                    "market": {"type": "string", "description": "Cheia pieței: h2h, totals, btts, double_chance, draw_no_bet, ht_ft, odd_even"},
                },
                "required": ["team_a", "team_b", "market"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "football_leagues",
            "description": "Caută ligi de fotbal reale (toate țările, inclusiv România și ligile de juniori/tineret) în API-Football. Exemple: 'romania' → SuperLiga, Liga Elitelor U19/U18/U17; 'england' → Premier League, U21. Nu necesită cote, doar informații reale. Returnează ligile găsite (id, țară, tip).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nume țară sau ligă (ex: 'romania', 'superliga', 'U19', 'england')"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "football_fixtures",
            "description": "Aduce meciurile de AZI (program, forma) pentru o ligă/țară din API-Football. Exemple: 'romania' → meciurile din SuperLiga; 'SuperLiga'; 'U19 Romania'. Indică și liga găsită. NU oferă meciuri viitoare (sunt pe plan premium) și nici cote (cotele sunt la football_odds).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nume țară sau ligă (ex: 'romania', 'SuperLiga', 'Liga Elitelor U19')"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "football_h2h",
            "description": "Istoricul real de cap-la-cap (H2H) între două echipe de fotbal, din API-Football: ultimele meciuri directe cu scoruri, data, competiția. Folosește când ai nevoie de date reale H2H pentru o analiză (ex: Dinamo vs FCSB).",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_a": {"type": "string", "description": "Prima echipă (ex: 'Dinamo București')"},
                    "team_b": {"type": "string", "description": "A doua echipă (ex: 'FCSB')"},
                },
                "required": ["team_a", "team_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "football_odds",
            "description": "Aduce COTE REALE din API-Football pentru meciurile din orice ligă/țară (inclusiv România SuperLiga și ligile de juniori/tineret), incluse în planul gratuit. Exemple: 'romania', 'SuperLiga', 'U19 Romania', 'england', 'brasil'. Piețele disponibile: 1x2, btts (ambele marcate), double chance (șansă dublă), draw no bet (fără egal), ht/ft (pauză/final), odd/even (par/impar), exact score (scor exact), corners (cornere!), over/under (total goluri), goluri pauza (total goluri în prima repriză). Fără market returnează piețele principale. Când utilizatorul vrea cote la un meci dintr-o ligă care nu e în the-odds-api (ex: România, juniori), folosește ACEST tool — are cote și la cornere și goluri până la pauză.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nume țară sau ligă (ex: 'romania', 'SuperLiga', 'Liga Elitelor U19', 'brasil')"},
                    "market": {"type": "string", "description": "Opțional. Cheia pieței: 1x2, btts, double chance, draw no bet, ht/ft, odd/even, exact score, corners, over/under, goluri pauza. Implicit: piețele principale."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "football_match",
            "description": "Informații complete despre un meci de azi din API-Football (plan gratuit): data și ora exactă, stadion și oraș, arbitru, antrenorii ambelor echipe, status, prognoza rezultatului (câștigător %, advice, comparație formă/atac/apărare), ultimele H2H și line-up-ul confirmat (dacă a fost anunțat; altfel menționezi onest că apare cu ~1h înainte). Exemple: 'romania', 'SuperLiga', 'brasil', sau echipele: team_a='FCSB' team_b='Dinamo'. Folosește acest tool când utilizatorul întreabă cine arbitrează, cine antrenează, la ce oră / unde se joacă sau cine joacă (pronostic).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Opțional. Nume țară sau ligă (ex: 'romania', 'SuperLiga', 'england')."},
                    "team_a": {"type": "string", "description": "Opțional. Numele primei echipe (ex: 'FCSB')."},
                    "team_b": {"type": "string", "description": "Opțional. Numele celei de-a doua echipe (ex: 'Dinamo')."},
                    "fixture_id": {"type": "string", "description": "Opțional. ID-ul direct al meciului, dacă îl cunoști."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Caută pe internet informații reale și recente: program/calendar meciuri viitoare (orice sport, inclusiv darts, ligi neacoperite de sursele de cote, de ex. România Liga 1/SuperLiga), rezultate, știri, transferuri, accidentări. Returnează titluri, link-uri și fragmente. Folosește când utilizatorul cere meciuri/program din viitor pe care sursele de cote nu le au (ex: darts, România, ligi de juniori) sau informații actuale. NU prezenta informațiile de pe web ca și cum ar fi cote verificate — spui clar că sunt 'din căutare web'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Căutarea (ex: 'PDC darts calendar 2026 meciuri program', 'SuperLiga Romania 2026-2027 program meciuri etape')"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": "Deschide o pagină web (URL) și returnează textul ei (primele ~6000 de caractere). Folosește după web_search pentru a citi programul/datele de pe un site (ex: superliga.ro/meciuri, pdc.tv). Restricționat la http/https.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL-ul complet al paginii (http/https)"},
                },
                "required": ["url"],
            },
        },
    },
]


def _tool_schema(name, description, properties=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties or {}, "required": []},
        },
    }


class ChatService:
    def __init__(self, providers, storage, fetcher, context_engine, threshold=4.0,
                 max_iterations=6, borderline_window_pct=3.0, tools=None,
                 system_prompt=None, history_analyzer=None, football=None,
                 cached_value_bets=None):
        self.providers = providers
        self.storage = storage
        self.fetcher = fetcher
        self.context_engine = context_engine
        self.history_analyzer = history_analyzer
        self.football = football
        self.threshold = threshold
        self.max_iterations = max_iterations
        self.borderline_window_pct = borderline_window_pct
        self.tools = tools or TOOLS
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.cached_value_bets = cached_value_bets
        self._fb_league_cache = {}
        self._fb_fx_cache = {"date": None, "data": []}
        # providers that just failed (503/overload/quota) are moved to the back for a while,
        # so one struggling model does not slow down every single request
        self._provider_cooldown = {}
        self._provider_cooldown_s = 180

    def _ordered_providers(self):
        """Configured provider order, but recently failed ones are postponed (stable sort)."""
        now = time.time()
        return sorted(
            self.providers,
            key=lambda p: 0 if self._provider_cooldown.get(p.get("name"), 0) <= now else 1,
        )

    def _mark_failed(self, provider):
        self._provider_cooldown[provider.get("name")] = time.time() + self._provider_cooldown_s

    def _mark_ok(self, provider):
        self._provider_cooldown.pop(provider.get("name"), None)

    def _ticket_pool(self):
        """Value bets din cache-ul scanarii automate; fallback: recalcul rapid FARA context/știri."""
        if self.cached_value_bets:
            try:
                pool = self.cached_value_bets()
                if pool:
                    return list(pool)
            except Exception:
                pass
        results = []
        for group, events in self.storage.load_cache().items():
            if not isinstance(events, list):
                continue
            try:
                results.extend(find_value_bets(events, group, self.threshold))
            except Exception:
                continue
        return results

    def _build_ticket(self, args):
        try:
            count = max(1, min(int(args.get("count", 10) or 10), 20))
        except (TypeError, ValueError):
            count = 10
        sport = str(args.get("sport") or "").strip().lower()
        pool = self._ticket_pool()
        if sport:
            pool = [vb for vb in pool if str(vb.get("sport", "")).lower() == sport]
        try:
            min_edge = float(args.get("min_edge_pct") or 0) or float(self.threshold)
        except (TypeError, ValueError):
            min_edge = float(self.threshold)
        pool = [
            vb for vb in pool
            if isinstance(vb, dict)
            and vb.get("side")
            and float(vb.get("odds") or 0) > 1.01
            and float(vb.get("edge_pct") or 0) >= min_edge
        ]
        pool.sort(key=lambda vb: (vb.get("confidence", 0), vb.get("edge_pct", 0)), reverse=True)
        picks = pool[:count]
        legs = []
        total_odds = 1.0
        total_prob = 1.0
        for i, vb in enumerate(picks, 1):
            odds = float(vb.get("odds") or 1)
            edge = float(vb.get("edge_pct") or 0)
            true_p = (1.0 / odds) * (1.0 + edge / 100.0) if odds > 1.01 else 0.0
            total_prob *= true_p
            total_odds *= odds
            legs.append(
                {
                    "leg": i,
                    "match": f"{vb.get('home_team', '')} vs {vb.get('away_team', '')}",
                    "pick": vb.get("side", ""),
                    "odds": round(odds, 2),
                    "bookmaker": vb.get("bookmaker", ""),
                    "edge_pct": round(edge, 1),
                    "true_prob": round(true_p, 4),
                    "confidence": vb.get("confidence"),
                    "sport": vb.get("sport", ""),
                    "starts": vb.get("commence_time", ""),
                }
            )
        return {
            "legs_count": len(legs),
            "requested": count,
            "total_odds": round(total_odds, 2),
            "combined_prob": round(total_prob, 4),
            "legs": legs,
            "note": (
                f"Bilet generat instant din cache ({len(pool)} selecții eligibile, prag edge {min_edge}%). "
                "Cotele se pot schimba - verifică înainte de plasare."
            ),
        }

    def _dispatch(self, name, args):
        if name == "build_ticket":
            return self._build_ticket(args)
        if name == "get_value_bets":
            cache = self.storage.load_cache()
            results = []
            self.context_engine.begin_scan()
            for group, events in cache.items():
                results.extend(
                    find_value_bets(events, group, self.threshold,
                                    context_engine=self.context_engine,
                                    borderline_window_pct=self.borderline_window_pct,
                                    history_analyzer=self.history_analyzer)
                )
            return results
        if name == "get_arbitrage":
            cache = self.storage.load_cache()
            results = []
            for group, events in cache.items():
                for arb in find_arbitrage(events):
                    arb["sport"] = group
                    results.append(arb)
            return results
        if name == "get_stats":
            bets = self.storage.list_bets()
            initial = 1000.0
            balance = initial + sum(b.get("profit", 0) for b in bets if b["status"] != "open")
            balance -= sum(b["stake"] for b in bets if b["status"] == "open")
            settled = [b for b in bets if b["status"] != "open"]
            won = [b for b in settled if b["status"] == "won"]
            staked = sum(b["stake"] for b in settled)
            profit = sum(b.get("profit", 0) for b in settled)
            roi = (profit / staked * 100) if staked else 0.0
            return {
                "initial": initial,
                "balance": round(balance, 2),
                "profit": round(profit, 2),
                "total_bets": len(settled),
                "won": len(won),
                "lost": len(settled) - len(won),
                "win_rate_pct": round(len(won) / len(settled) * 100, 1) if settled else 0.0,
                "roi_pct": round(roi, 2),
            }
        if name == "get_team_context":
            return self.context_engine.get_team_context(args.get("team", ""))
        if name == "refresh_odds":
            return self._refresh()
        if name == "get_odds_summary":
            cache = self.storage.load_cache()
            summary = {}
            for group, events in cache.items():
                best_rows = []
                for ev in events[:10]:
                    top = None
                    for book in ev.get("bookmakers", []):
                        for m in book.get("markets", []):
                            if m.get("key") != "h2h":
                                continue
                            for o in m.get("outcomes", []):
                                if top is None or o["price"] > top["price"]:
                                    top = {"outcome": o["name"], "price": o["price"], "book": book.get("title")}
                    best_rows.append({"match": f"{ev.get('home_team')} vs {ev.get('away_team')}", "best": top})
                summary[group] = {"count": len(events), "matches": best_rows}
            return summary
        if name == "get_match_patterns":
            if not self.history_analyzer:
                return {"error": "Niciun istoric încărcat."}
            ta, tb = args.get("team_a", ""), args.get("team_b", "")
            if not ta or not tb:
                return {"error": "Specifică team_a și team_b."}
            return {
                "h2h": self.history_analyzer.h2h(ta, tb),
                "scoreline_frequency": self.history_analyzer.scoreline_frequency(ta, tb),
                "repeated_patterns": self.history_analyzer.repeated_patterns(ta, tb),
                "lambdas": self.history_analyzer.lambdas(ta, tb),
            }
        if name == "analyze_match_deep":
            ta, tb = args.get("team_a", ""), args.get("team_b", "")
            if not ta or not tb:
                return {"error": "Specifică team_a și team_b."}
            return self._deep_analysis(ta, tb)
        if name == "fetch_league":
            q = args.get("league", "")
            if not q:
                return {"error": "Specifică league (ex: 'Brazil Serie A')."}
            return self._fetch_league(q)
        if name == "get_market_odds":
            ta = args.get("team_a", "")
            tb = args.get("team_b", "")
            mk = args.get("market", "")
            if not ta or not tb or not mk:
                return {"error": "Specifică team_a, team_b și market."}
            return self._market_odds(ta, tb, mk)
        if name == "football_leagues":
            q = args.get("query", "")
            if not q:
                return {"error": "Specifică query (ex: 'romania')."}
            return self._football_leagues(q)
        if name == "football_fixtures":
            q = args.get("query", "")
            if not q:
                return {"error": "Specifică query (ex: 'romania')."}
            return self._football_fixtures(q)
        if name == "football_h2h":
            ta = args.get("team_a", "")
            tb = args.get("team_b", "")
            if not ta or not tb:
                return {"error": "Specifică team_a și team_b."}
            return self._football_h2h(ta, tb)
        if name == "football_odds":
            q = args.get("query", "")
            if not q:
                return {"error": "Specifică query (ex: 'romania')."}
            return self._football_odds(q, market=args.get("market"))
        if name == "football_match":
            return self._football_match(
                query=args.get("query"),
                team_a=args.get("team_a"),
                team_b=args.get("team_b"),
                fixture_id=args.get("fixture_id"),
            )
        if name == "web_search":
            q = args.get("query", "")
            if not q:
                return {"error": "Specifică query."}
            return self._web_search(q)
        if name == "fetch_page":
            url = args.get("url", "")
            if not url:
                return {"error": "Specifică url."}
            return self._fetch_page(url)
        return {"error": f"Tool necunoscut: {name}"}

    def _fetch_league(self, query):
        try:
            catalog = build_catalog(self.fetcher)
        except Exception as e:
            return {"error": f"Catalog fetch failed: {e}"}
        hits = match_leagues(catalog, query)
        if not hits:
            return {
                "error": f"Nicio ligă găsită pentru '{query}'.",
                "hits": [],
                "total_leagues": len(catalog),
            }
        return fetch_leagues(self.fetcher, self.storage, hits, cap=5)

    def _web_search(self, query):
        return web_search(query)

    def _fetch_page(self, url):
        return fetch_page(url)

    def _prefetch_leagues(self, text):
        if not text:
            return None
        low = text.lower()
        catalog = None
        fetched = []
        added_keys = set()
        for kw in ALIASES:
            if not kw or kw not in low:
                continue
            if catalog is None:
                try:
                    catalog = build_catalog(self.fetcher)
                except Exception:
                    return None
            hits = match_leagues(catalog, kw)
            cache = self.storage.load_cache()
            cache_keys = set()
            for evs in cache.values():
                for ev in evs:
                    if ev.get("sport_key"):
                        cache_keys.add(ev["sport_key"])
            for h in hits:
                if h["key"] in added_keys or h["key"] in cache_keys:
                    continue
                try:
                    res = fetch_leagues(self.fetcher, self.storage, [h], cap=1)
                except Exception:
                    continue
                if res.get("fetched"):
                    added_keys.add(h["key"])
                    fetched.append(
                        {
                            "key": h["key"],
                            "title": h["title"],
                            "matches": res["fetched"][0].get("matches"),
                            "remaining": res.get("remaining"),
                        }
                    )
            if len(fetched) >= 2:
                break
        if not fetched:
            return None
        return {"pre_fetched": fetched}

    def _has_market(self, event, market):
        for book in event.get("bookmakers", []):
            for m in book.get("markets", []):
                if m.get("key") == market:
                    return True
        return False

    @staticmethod
    def _merge_event_market(cache, ev_odds):
        if not ev_odds:
            return
        fetched = ev_odds[0] if isinstance(ev_odds, list) else ev_odds
        target_id = fetched.get("id")
        for group, events in cache.items():
            for ev in events:
                if ev.get("id") != target_id:
                    continue
                for fb in fetched.get("bookmakers", []):
                    cached_book = None
                    for cb in ev.setdefault("bookmakers", []):
                        if cb.get("key") == fb.get("key"):
                            cached_book = cb
                            break
                    if cached_book is None:
                        cached_book = {"key": fb.get("key"), "title": fb.get("title"), "markets": []}
                        ev["bookmakers"].append(cached_book)
                    cached_book.setdefault("markets", [])
                    for fm in fb.get("markets", []):
                        cached_book["markets"] = [m for m in cached_book["markets"] if m.get("key") != fm.get("key")]
                        cached_book["markets"].append(fm)
                return

    def _market_odds(self, team_a, team_b, market):
        market = market.strip().lower()
        if market in ("corner", "corners", "corner_kicks"):
            return {
                "error": "Piața de cornere nu este disponibilă pe sursa de date (the-odds-api).",
                "available": "h2h, totals, btts, double_chance, draw_no_bet, ht_ft, odd_even",
            }
        cache = self.storage.load_cache()
        ta, tb = team_a.strip().lower(), team_b.strip().lower()
        event = None
        sport_key = None
        for group, events in cache.items():
            for ev in events:
                home = (ev.get("home_team") or "").lower()
                away = (ev.get("away_team") or "").lower()
                if (ta in home and tb in away) or (tb in home and ta in away):
                    event = ev
                    sport_key = ev.get("sport_key") or group
                    break
            if event:
                break
        if not event:
            return {"error": f"Niciun meci '{team_a}' vs '{team_b}' în cache. Folosește fetch_league sau refresh întâi."}
        remaining = None
        if not self._has_market(event, market):
            try:
                ev_odds, headers = self.fetcher.get_event_odds(sport_key, event["id"], [market])
                self._merge_event_market(cache, ev_odds)
                self.storage.save_cache(cache)
                remaining = headers.get("remaining")
            except Exception as e:
                return {"error": f"Piața '{market}' indisponibilă pentru acest meci: {e}"}
        best = {}
        for book in event.get("bookmakers", []):
            for m in book.get("markets", []):
                if m.get("key") != market:
                    continue
                for o in m.get("outcomes", []):
                    key = f"{o.get('name','')} {o.get('point','')}".strip()
                    if key not in best or o["price"] < best[key]["price"]:
                        best[key] = {"price": o["price"], "bookmaker": book.get("title")}
        return {
            "event": f"{event.get('home_team')} vs {event.get('away_team')}",
            "sport": event.get("sport_group"),
            "market": market,
            "best_odds": best,
            "requests_remaining": remaining,
        }

    def _football_leagues(self, query):
        if not self.football:
            return {"error": "API-Football nu e configurat (nu există nicio instanță)."}
        try:
            data, remaining, errors = self.football.leagues(search=query)
            if not data and query.strip():
                data, remaining, errors = self.football.leagues(country=query)
        except Exception as e:
            return {"error": str(e)}
        out = []
        for item in data[:25]:
            lg = item.get("league", {}) or {}
            country = item.get("country", {}) or {}
            out.append({
                "id": lg.get("id"),
                "name": lg.get("name"),
                "type": lg.get("type"),
                "country": country.get("name"),
                "logo": country.get("flag"),
            })
        return {"query": query, "leagues": out, "requests_remaining": remaining}

    def _football_fixtures(self, query):
        if not self.football:
            return {"error": "API-Football nu e configurat (nu există nicio instanță)."}
        try:
            today = datetime.now().date().isoformat()
            rem = self.football.remaining_requests()
            fx_data = self._today_fixtures()
            q = (query or "").strip().lower()
            if q in ("", "azi", "today", "toate", "lume", "lumea"):
                matches = []
                for fx in fx_data:
                    teams = fx.get("teams", {}) or {}
                    home = teams.get("home", {}) or {}
                    away = teams.get("away", {}) or {}
                    lg = fx.get("league", {}) or {}
                    matches.append({
                        "league": lg.get("name"),
                        "country": lg.get("country"),
                        "date": fx.get("fixture", {}).get("date"),
                        "home": home.get("name"),
                        "away": away.get("name"),
                        "status": fx.get("fixture", {}).get("status", {}).get("short"),
                    })
                return {"scope": "toată lumea - meciurile de azi", "matches": matches[:30], "requests_remaining": rem}
            lg, name, country, _ = self._resolve_league(query)
            if not lg:
                return {"error": f"Nicio ligă găsită pentru '{query}'.", "requests_remaining": rem}
            fx_data = [f for f in fx_data if (f.get("league") or {}).get("id") == lg]
            matches = []
            for fx in fx_data:
                teams = fx.get("teams", {}) or {}
                goals = fx.get("goals", {}) or {}
                home = teams.get("home", {}) or {}
                away = teams.get("away", {}) or {}
                matches.append({
                    "league": name,
                    "country": country,
                    "date": fx.get("fixture", {}).get("date"),
                    "venue": fx.get("fixture", {}).get("venue", {}).get("name"),
                    "home": home.get("name"),
                    "away": away.get("name"),
                    "home_goals": goals.get("home"),
                    "away_goals": goals.get("away"),
                    "status": fx.get("fixture", {}).get("status", {}).get("short"),
                })
            return {"league": name, "country": country, "matches": matches, "requests_remaining": rem}
        except Exception as e:
            return {"error": str(e)}

    def _football_odds(self, query, market=None):
        if not self.football:
            return {"error": "API-Football nu e configurat (nu există nicio instanță)."}
        try:
            today = datetime.now().date().isoformat()
            rem = self.football.remaining_requests()
            lg, name, country, _ = self._resolve_league(query)
            if not lg:
                return {"error": f"Nicio ligă găsită pentru '{query}'.", "requests_remaining": rem}
            fx_data = [f for f in self._today_fixtures() if (f.get("league") or {}).get("id") == lg]
            if not fx_data:
                return {
                    "error": f"Nicio echipă din {name} nu joacă astăzi. Pe planul gratuit nu sunt vizibile meciurile viitoare.",
                    "requests_remaining": rem,
                }
            results = []
            for fx in fx_data[:2]:
                fid = (fx.get("fixture") or {}).get("id")
                teams = fx.get("teams", {}) or {}
                home = (teams.get("home") or {}).get("name")
                away = (teams.get("away") or {}).get("name")
                if not fid:
                    continue
                od, _, errors = self.football.odds_by_fixture(fid)
                time.sleep(1.2)
                if errors:
                    results.append({"match": f"{home} vs {away}", "note": str(errors)})
                    continue
                bets = {}
                for item in od:
                    for bm in item.get("bookmakers", []):
                        for bet in bm.get("bets", []):
                            nm = bet.get("name")
                            for v in bet.get("values", []):
                                key = f"{nm}: {v.get('value')}"
                                price = float(v.get("odd"))
                                if key not in bets or price > bets[key]["price"]:
                                    bets[key] = {"price": price, "book": bm.get("name")}
                filtered = self._filter_football_bets(bets, market)
                results.append({
                    "match": f"{home} vs {away}",
                    "date": fx.get("fixture", {}).get("date"),
                    "odds": filtered,
                })
            return {
                "league": name,
                "country": country,
                "market": market or "piețe principale",
                "matches": results,
                "requests_remaining": rem,
            }
        except Exception as e:
            return {"error": str(e)}

    def _football_match(self, query=None, team_a=None, team_b=None, fixture_id=None):
        if not self.football:
            return {"error": "API-Football nu e configurat (nu există nicio instanță)."}
        try:
            rem = self.football.remaining_requests()
            fx_data = self._today_fixtures()
            if fixture_id:
                matches = [f for f in fx_data if str((f.get("fixture") or {}).get("id")) == str(fixture_id)]
            elif query:
                lg, name, country, _ = self._resolve_league(query)
                if not lg:
                    return {"error": f"Nicio ligă găsită pentru '{query}'.", "requests_remaining": rem}
                matches = [f for f in fx_data if (f.get("league") or {}).get("id") == lg]
            elif team_a or team_b:
                a = (team_a or "").strip().lower()
                b = (team_b or "").strip().lower()

                def _hit(fx):
                    teams = fx.get("teams", {}) or {}
                    h = ((teams.get("home") or {}).get("name") or "").lower()
                    aw = ((teams.get("away") or {}).get("name") or "").lower()
                    return (a and (a in h or a in aw)) or (b and (b in h or b in aw))

                matches = [f for f in fx_data if _hit(f)]
            else:
                matches = fx_data
            if not matches:
                return {
                    "error": "Niciun meci de azi găsit pentru această selecție (pe planul gratuit nu sunt vizibile meciurile viitoare).",
                    "requests_remaining": rem,
                }
            cap = 2 if rem >= 12 else 1
            out = []
            for fx in matches[:cap]:
                fid = (fx.get("fixture") or {}).get("id")
                teams = fx.get("teams", {}) or {}
                home = teams.get("home") or {}
                away = teams.get("away") or {}
                fxi = fx.get("fixture", {}) or {}
                venue = fxi.get("venue", {}) or {}
                status = fxi.get("status", {}) or {}
                lg = fx.get("league", {}) or {}
                info = {
                    "fixture_id": fid,
                    "league": lg.get("name"),
                    "country": lg.get("country"),
                    "date": fxi.get("date"),
                    "status": status.get("long"),
                    "venue": venue.get("name"),
                    "city": venue.get("city"),
                    "referee": fxi.get("referee"),
                    "home": home.get("name"),
                    "away": away.get("name"),
                }
                if not fid:
                    out.append(info)
                    continue
                pred, _, perr = self.football.predictions(fid)
                time.sleep(1.2)
                if pred:
                    p = pred[0]
                    pr = p.get("predictions") or {}
                    comp = p.get("comparison") or {}
                    info["prediction"] = {
                        "winner": (pr.get("winner") or {}).get("name"),
                        "winner_comment": (pr.get("winner") or {}).get("comment"),
                        "advice": pr.get("advice"),
                        "percent": pr.get("percent"),
                        "goals": pr.get("goals"),
                    }
                    info["comparison"] = {k: comp.get(k) for k in ("form", "att", "def") if comp.get(k)}
                    h2h = p.get("h2h") or []
                    if h2h:
                        info["h2h_recent"] = [
                            {
                                "date": x.get("fixture", {}).get("date"),
                                "home": (x.get("teams", {}).get("home") or {}).get("name"),
                                "away": (x.get("teams", {}).get("away") or {}).get("name"),
                                "goals_home": (x.get("goals") or {}).get("home"),
                                "goals_away": (x.get("goals") or {}).get("away"),
                            }
                            for x in h2h[:5]
                        ]
                else:
                    info["prediction"] = {"note": f"predictions indisponibile: {perr}"}
                lin, _, lerr = self.football.lineups(fid)
                time.sleep(1.2)
                if lin:
                    lups = {}
                    for l in lin[:2]:
                        tname = (l.get("team") or {}).get("name")
                        lups[tname] = {
                            "formation": l.get("formation"),
                            "start_xi": [(p.get("player") or {}).get("name") for p in (l.get("startXI") or [])],
                        }
                    info["lineups"] = lups
                else:
                    info["lineups"] = {
                        "note": "Line-up-urile confirmate nu au fost încă anunțate (apar de obicei cu ~1h înainte de meci).",
                        "detail": str(lerr) if lerr else "",
                    }
                info["coach_home"] = "indisponibil pe planul gratuit (API-Football nu expune antrenorii)"
                info["coach_away"] = "indisponibil pe planul gratuit (API-Football nu expune antrenorii)"
                out.append(info)
            return {"matches": out, "requests_remaining": rem}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _filter_football_bets(bets, market):
        key = (market or "").strip().lower()
        wanted = FOOTBALL_MARKET_KEYS.get(key, FOOTBALL_CORE_MARKETS)
        out = {}
        for k, val in bets.items():
            nm = k.rsplit(":", 1)[0].strip()
            if nm not in wanted:
                continue
            v = k.rsplit(":", 1)[1].strip()
            allowed = FOOTBALL_VALUE_FILTER.get(nm)
            if allowed and v not in allowed:
                continue
            out[k] = val
        return out

    def _resolve_league(self, query):
        key = (query or "").strip().lower()
        if key in self._fb_league_cache:
            return self._fb_league_cache[key]
        data, remaining, errors = self.football.leagues(search=query)
        if not data and query.strip():
            data, remaining, errors = self.football.leagues(country=query)
        if not data:
            self._fb_league_cache[key] = (None, None, None, remaining)
            return self._fb_league_cache[key]
        lg = data[0].get("league", {}) or {}
        country = data[0].get("country", {}) or {}
        self._fb_league_cache[key] = (lg.get("id"), lg.get("name"), country.get("name"), remaining)
        return self._fb_league_cache[key]

    def _today_fixtures(self):
        today = datetime.now().date().isoformat()
        if self._fb_fx_cache["date"] != today:
            fx_data, _, _ = self.football.fixtures(date=today)
            self._fb_fx_cache["date"] = today
            self._fb_fx_cache["data"] = fx_data
        return self._fb_fx_cache["data"]

    def _football_h2h(self, team_a, team_b):
        if not self.football:
            return {"error": "API-Football nu e configurat (nu există nicio instanță)."}
        try:
            t1, _, _ = self.football.teams_by_name(team_a)
            t2, _, _ = self.football.teams_by_name(team_b)
            if not t1 or not t2:
                return {"error": f"Echipele nu au fost găsite (a: {team_a}, b: {team_b})."}
            id1 = t1[0].get("team", {}).get("id")
            id2 = t2[0].get("team", {}).get("id")
            data, remaining, errors = self.football.h2h(id1, id2)
        except Exception as e:
            return {"error": str(e)}
        meetings = []
        for fx in data[:15]:
            teams = fx.get("teams", {}) or {}
            goals = fx.get("goals", {}) or {}
            home = teams.get("home", {}) or {}
            away = teams.get("away", {}) or {}
            meetings.append({
                "date": fx.get("fixture", {}).get("date"),
                "league": fx.get("league", {}).get("name"),
                "home": home.get("name"),
                "away": away.get("name"),
                "goals": f"{goals.get('home')}-{goals.get('away')}",
            })
        return {"team_a": team_a, "team_b": team_b, "meetings": meetings, "requests_remaining": remaining}

    def _refresh(self):
        import json as _json
        from pathlib import Path

        with open(Path(__file__).parent / "config.json", encoding="utf-8") as f:
            cfg = _json.load(f)
        try:
            catalog = build_catalog(self.fetcher)
        except Exception:
            return {"error": "Catalog fetch failed."}
        by_group = {}
        for c in catalog:
            by_group.setdefault(c["group"], []).append(c)
        preferred = cfg.get("preferred_sports", {})
        events_by_sport = {}
        for g, pref_keys in preferred.items():
            cats = by_group.get(g, [])
            chosen_list = [c for c in cats if c["key"] in pref_keys]
            if not chosen_list:
                chosen_list = sorted(cats, key=lambda c: c.get("title", ""))[:1]
            group_events = []
            for c in chosen_list:
                try:
                    events, _ = self.fetcher.get_odds(c["key"])
                except Exception:
                    continue
                for ev in events:
                    ev["sport_group"] = g
                    ev["sport_title"] = c.get("title")
                group_events.extend(events)
            events_by_sport[g] = group_events
        events_by_sport = self.storage.merge_cache(events_by_sport)
        return {"refreshed": True, "sports": {g: len(v) for g, v in events_by_sport.items()}}

    _DSML_MARKER = r"(?:转DSML转|転DSML転|｜｜DSML｜｜|dsml|｜)"
    _DSML_INVOKE_RE = re.compile(
        r"<?" + _DSML_MARKER + r"\s*<?\s*invoke\s+name=\"([^\"]+)\"[^>]*>(.*?)</" + _DSML_MARKER + r"\s*<?\s*invoke>",
        re.S,
    )
    _DSML_PARAM_RE = re.compile(
        r"<?" + _DSML_MARKER + r"\s*<?\s*parameter\s+name=\"([^\"]+)\"[^>]*>(.*?)</" + _DSML_MARKER + r"\s*<?\s*parameter>",
        re.S,
    )
    _DSML_DETECT_RE = re.compile(r"<?" + _DSML_MARKER + r"\s*<?\s*(?:tool_calls|invoke|parameter)\b")

    def _parse_dsml_tools(self, text):
        tools = []
        for m in self._DSML_INVOKE_RE.finditer(text or ""):
            name = m.group(1)
            args = {}
            for pm in self._DSML_PARAM_RE.finditer(m.group(2)):
                args[pm.group(1)] = pm.group(2)
            tools.append({"name": name, "arguments": json.dumps(args, ensure_ascii=False)})
        return tools

    def _clean_dsml(self, text):
        t = text or ""
        t = re.sub(
            r"<?" + self._DSML_MARKER + r"\s*<?\s*tool_calls[^>]*>.*?</" + self._DSML_MARKER + r"\s*<?\s*tool_calls>",
            "", t, flags=re.S,
        )
        t = re.sub(
            r"<?" + self._DSML_MARKER + r"\s*<?\s*(?:invoke|parameter)[^>]*>.*?</" + self._DSML_MARKER + r"\s*<?\s*(?:invoke|parameter)>",
            "", t, flags=re.S,
        )
        return t.strip()

    def _call_model(self, provider, messages, tool_choice="auto"):
        url = f"{provider['base_url']}/chat/completions"
        base = (provider.get("base_url") or "").lower()
        # Gemini's OpenAI-compatible endpoint round-trips an `extra_content` blob on tool-call
        # messages; other providers reject unknown fields, so drop it when we fall back to them.
        if "googleapis.com" not in base:
            messages = [{k: v for k, v in m.items() if k != "extra_content"} for m in messages]
        body = {
            "model": provider["preferred_model"],
            "messages": messages,
            "tools": self.tools,
            "tool_choice": tool_choice,
            "temperature": 0.4,
        }
        headers = {"Content-Type": "application/json"}
        if provider.get("api_key"):
            headers["Authorization"] = f"Bearer {provider['api_key']}"
        timeout = 25 if ("127.0.0.1" in base or "localhost" in base) else 60
        resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _deep_analysis(self, team_a, team_b):
        cache = self.storage.load_cache()
        event = None
        sport_group = None
        now_iso = datetime.now(timezone.utc).isoformat()
        best_key = None
        for group, events in cache.items():
            if not isinstance(events, list):
                continue
            for ev in events:
                if not isinstance(ev, dict):
                    continue
                # Fuzzy names + nearest kickoff: "FC Internazionale Milano"
                # must find "Inter Milan", and the same teams on two dates must
                # not silently return the wrong fixture.
                sim = _pair_sim(team_a, team_b, ev.get("home_team"), ev.get("away_team"))
                if sim < 0.65:
                    continue
                proximity = -(_hours_apart(now_iso, ev.get("commence_time")) or 9999.0)
                key = (round(sim, 3), proximity)
                if best_key is None or key > best_key:
                    best_key = key
                    event = ev
                    sport_group = group

        if not event:
            return {"error": f"Niciun meci '{team_a}' vs '{team_b}' în cotele curente.", "hint": "Dă refresh cote dacă meciul lipsește."}

        home_name = event.get("home_team", team_a)
        away_name = event.get("away_team", team_b)

        home_ctx = self.context_engine.get_team_context(home_name)
        away_ctx = self.context_engine.get_team_context(away_name)

        all_headlines = (home_ctx.get("headlines") or []) + (away_ctx.get("headlines") or [])
        players = extract_players(all_headlines, exclude_terms=[home_name, away_name])

        best = {}
        for book in event.get("bookmakers", []):
            for m in book.get("markets", []):
                if m.get("key") != "h2h":
                    continue
                for o in m.get("outcomes", []):
                    if o["name"] not in best or o["price"] > best[o["name"]]["price"]:
                        best[o["name"]] = {"price": o["price"], "book": book.get("title")}

        vb = find_value_bets([event], sport_group or "soccer", self.threshold,
                             context_engine=self.context_engine,
                             borderline_window_pct=self.borderline_window_pct,
                             history_analyzer=self.history_analyzer)

        return {
            "match": {
                "home": home_name,
                "away": away_name,
                "commence_time": event.get("commence_time"),
                "sport": event.get("sport_title") or sport_group,
            },
            "best_odds": best,
            "team_impact": {
                home_name: {
                    "score": home_ctx.get("score"),
                    "impact": home_ctx.get("impact"),
                    "summary": home_ctx.get("impact_summary"),
                },
                away_name: {
                    "score": away_ctx.get("score"),
                    "impact": away_ctx.get("impact"),
                    "summary": away_ctx.get("impact_summary"),
                },
            },
            "players_with_events": players,
            "value_bets": vb,
        }

    def chat(self, user_messages, lang="ro"):
        # Prepare common variables
        lang = lang if lang in CHAT_TEXT else "ro"
        T = CHAT_TEXT[lang]
        last_content = ""
        if user_messages:
            last_content = (user_messages[-1].get("content", "") or "").lower()
        # Detect match of the day/week request
        match_day_phrases = [
            "meciul zilei", "meciul saptamanii", "match of the day", "match of the week",
            "spiel des tages", "spiel der woche",
        ]
        if any(phrase in last_content for phrase in match_day_phrases):
            # Determine sport: default soccer, but allow override
            sport = "soccer"
            if "tenis" in last_content or "tennis" in last_content:
                sport = "tennis"
            elif "baschet" in last_content or "basketball" in last_content:
                sport = "basketball"
            # Get value bets list
            if self.cached_value_bets:
                try:
                    pool = list(self.cached_value_bets())
                except Exception:
                    pool = self._ticket_pool()
            else:
                pool = self._ticket_pool()
            # Filter by sport if needed
            if sport:
                pool = [vb for vb in pool if isinstance(vb, dict) and vb.get("sport") == sport]
            # Sort by estimated true probability desc (pick the "surest" match)
            def vb_true_prob(vb):
                o = float(vb.get("odds", 0))
                if o <= 1.01:
                    return 0.0
                return (1.0 / o) * (1.0 + float(vb.get("edge_pct", 0)) / 100.0)
            pool.sort(key=vb_true_prob, reverse=True)
            if pool:
                vb = pool[0]
                home = vb.get("home_team", "")
                away = vb.get("away_team", "")
                odds = vb.get("odds", 0)
                edge = vb.get("edge_pct", 0)
                conf = vb.get("confidence", 0)
                # Get team contexts
                home_ctx = self.context_engine.get_team_context(home) if home else {}
                away_ctx = self.context_engine.get_team_context(away) if away else {}
                home_score = home_ctx.get("score", 0.0)
                away_score = away_ctx.get("score", 0.0)
                commence_raw = vb.get("commence_time", "") or ""
                match_dt = "N/A"
                if commence_raw:
                    try:
                        cr = commence_raw
                        if isinstance(cr, str) and cr.endswith("Z"):
                            cr = cr[:-1] + "+00:00"
                        match_dt = datetime.fromisoformat(cr).strftime("%d.%m.%Y %H:%M")
                    except Exception:
                        match_dt = str(commence_raw)
                sport_key = vb.get("sport") or vb.get("sport_group") or ""
                league = SPORT_LABELS[lang].get(sport_key, sport_key or "N/A")
                sl = (vb.get("side") or "").strip().lower()
                if sl in ("home", "away"):
                    pick_label = f"1 {home}" if sl == "home" else f"2 {away}"
                else:
                    pick_label = vb.get("side") or ""
                true_p = (1.0 / odds) * (1.0 + edge / 100.0) if odds > 1.01 else 0.0
                win_pct = min(99.0, true_p * 100.0)
                ec = "green" if edge >= 0 else "red"
                stars = "★" * max(0, min(5, int(conf or 0)))
                reason_parts = []
                if home_score != 0:
                    c = "red" if home_score < 0 else "green"
                    lbl = T["injuries"] if home_score < 0 else T["positive_news"]
                    reason_parts.append("__" + home + "__: ##" + c + ":" + lbl + "##")
                if away_score != 0:
                    c = "red" if away_score < 0 else "green"
                    lbl = T["injuries"] if away_score < 0 else T["positive_news"]
                    reason_parts.append("__" + away + "__: ##" + c + ":" + lbl + "##")
                if not reason_parts:
                    reason_parts.append(T["neutral_news"])
                hc = home_ctx.get("score", 0.0)
                ac = away_ctx.get("score", 0.0)
                if abs(hc) >= abs(ac):
                    head = (home_ctx.get("headlines") or [''])[0] if home_ctx.get("headlines") else ''
                else:
                    head = (away_ctx.get("headlines") or [''])[0] if away_ctx.get("headlines") else ''
                if head:
                    clean = head.replace("&nbsp;", " ").replace("\u00a0", " ")
                    while "  " in clean:
                        clean = clean.replace("  ", " ")
                    clean = clean.strip()[:70]
                    if clean:
                        reason_parts.append("*" + clean + "…*")
                reason = " · ".join(reason_parts)
                header = "## " + T["match_day"]
                table = (
                    "| " + T["table_detail"] + " | " + T["table_value"] + " |\n"
                    "|---|---|\n"
                    "| " + T["table_selection"] + " | " + pick_label + " |\n"
                    "| " + T["table_odds"] + " | **" + ("%.2f" % odds) + "** |\n"
                    "| Edge | ##" + ec + ":" + ("%+.1f%%" % edge) + "## |\n"
                    "| " + T["table_confidence"] + " | " + stars + " |\n"
                    "| " + T["table_datetime"] + " | " + match_dt + " |\n"
                    "| " + T["table_league"] + " | " + league + " |"
                )
                verdict_line = f"\n\n[VERDICT] {{\"win_pct\": {win_pct:.1f}, \"side\": \"{pick_label}\", \"event\": \"{home} vs {away}\"}}"
                reply = header + "\n\n**" + home + " vs " + away + "**\n\n" + table + "\n\n**" + T["why_safe"] + "**\n" + reason + verdict_line
                return {
                    "reply": reply,
                    "tools_used": ["get_value_bets", "get_team_context"],
                    "provider": "system",
                }

            # If no suitable match found, fall through to normal flow
        # Detect ticket request for quick response
        ticket_request = False
        ticket_count = 5  # default
        ticket_sport = ""
        if user_messages:
            # Look for keywords
            import re as _re
            ticket_word = r"bilet|ticket|parlay|kombi|kombiwette|schein|multiple|accumulator|wette|wetten"
            hard_word = r"bilet|ticket|parlay|kombi|kombiwette|schein|multiple|accumulator"
            soft_word = r"wette|wetten"
            has_hard = bool(_re.search(r"\b(?:" + hard_word + r")\b", last_content))
            has_soft = bool(_re.search(r"\b(?:" + soft_word + r")\b", last_content))
            has_make = bool(_re.search(r"\b(?:mach|mache|erstelle|erstellen|gib|gebe|baue|bauen|zusammenstellen|create|make|build|fa|fă)\b", last_content))
            has_number = bool(_re.search(r"\b\d{1,2}\b", last_content))
            if has_hard or (has_soft and (has_make or has_number)):
                ticket_request = True
                # Try to extract a number before/after keywords
                m = _re.search(r"(\d+)\s*(?:" + ticket_word + r")|(?:" + ticket_word + r")\s*(\d+)", last_content)
                if m:
                    num = m.group(1) or m.group(2)
                    if num:
                        try:
                            val = int(num)
                            if 1 <= val <= 20:
                                ticket_count = val
                        except ValueError:
                            pass
                # Additionally, pick any number in the message as count if not set by above (but within range)
                if ticket_count == 5:  # still default, try to find any number
                    nums = _re.findall(r"\b(\d{1,2})\b", last_content)
                    for n in nums:
                        try:
                            v = int(n)
                            if 1 <= v <= 20:
                                ticket_count = v
                                break
                        except ValueError:
                            pass
                # Optionally detect sport: simple mapping
                if "fotbal" in last_content or "soccer" in last_content or "fußball" in last_content or "fussball" in last_content:
                    ticket_sport = "soccer"
                elif "tenis" in last_content or "tennis" in last_content:
                    ticket_sport = "tennis"
                elif "baschet" in last_content or "basketball" in last_content:
                    ticket_sport = "basketball"
        messages = [{"role": "system", "content": self.system_prompt + "\n\n" + LANG_INSTRUCTION[lang]}]
        messages.extend(user_messages)
        if user_messages:
            try:
                pref = self._prefetch_leagues(user_messages[-1].get("content", "") or "")
            except Exception:
                pref = None
            if pref:
                messages.append(
                    {
                        "role": "user",
                        "content": T["prefetch"] + ": " + json.dumps(pref, ensure_ascii=False),
                    }
                )
        # If ticket request, build and return instantly
        if ticket_request:
            try:
                # Use _ticket_pool to get raw value bets (with context)
                if self.cached_value_bets:
                    try:
                        pool = list(self.cached_value_bets())
                    except Exception:
                        pool = self._ticket_pool()
                else:
                    pool = self._ticket_pool()
                # Filter by sport if needed
                if ticket_sport:
                    pool = [vb for vb in pool if isinstance(vb, dict) and vb.get("sport") == ticket_sport]
                # Compute true probability for each selection: implied * (1 + edge/100)
                def true_prob(vb):
                    odds = float(vb.get("odds", 0))
                    if odds <= 1.01:
                        return 0.0
                    implied = 1.0 / odds
                    edge = float(vb.get("edge_pct", 0))
                    return implied * (1.0 + edge / 100.0)
                # Filter out those with true probability too low (optional)
                pool = [vb for vb in pool if true_prob(vb) > 0.01]
                # Sort by true probability descending (higher chance first)
                pool.sort(key=true_prob, reverse=True)
                # Take requested count, but ensure at least 1
                count = max(1, min(ticket_count, len(pool)))
                selected = pool[:count]
                # Build legs for display with extra info
                legs = []
                total_true_prob = 1.0
                selection_details = []  # for explanations
                for vb in selected:
                    odds = float(vb.get("odds", 0))
                    edge = float(vb.get("edge_pct", 0))
                    implied = 1.0 / odds if odds > 1.01 else 0.0
                    true_p = implied * (1.0 + edge / 100.0) if odds > 1.01 else 0.0
                    total_true_prob *= true_p
                    home = vb.get('home_team', '')
                    away = vb.get('away_team', '')
                    commence_raw = vb.get('commence_time', '')
                    # Format date/time
                    match_dt = "N/A"
                    if commence_raw:
                        try:
                            # Handle ISO string with Z
                            if isinstance(commence_raw, str) and commence_raw.endswith('Z'):
                                commence_raw = commence_raw[:-1] + '+00:00'
                            dt = datetime.fromisoformat(commence_raw)
                            match_dt = dt.strftime('%d.%m.%Y %H:%M')
                        except Exception:
                            match_dt = str(commence_raw)
                    # Determine league/competition from sport field or fallback
                    league = vb.get('sport', '') or vb.get('sport_group', '') or 'N/A'
                    # Where to watch (generic)
                    where_watch = "Pe platformele ufficiale de streaming / la TV"
                    # Get team contexts for short explanation
                    home_ctx = self.context_engine.get_team_context(home) if home else {}
                    away_ctx = self.context_engine.get_team_context(away) if away else {}
                    home_score = home_ctx.get('score', 0.0)
                    away_score = away_ctx.get('score', 0.0)
                    home_head = (home_ctx.get('headlines') or [''])[0] if home_ctx.get('headlines') else ''
                    away_head = (away_ctx.get('headlines') or [''])[0] if away_ctx.get('headlines') else ''
                    sl = (vb.get("side") or "").strip().lower()
                    if sl in ("home", "away"):
                        pick_label = f"1 {home}" if sl == "home" else f"2 {away}"
                    else:
                        pick_label = vb.get("side") or ""
                    legs.append({
                        "match": f"{home} vs {away}",
                        "pick": pick_label,
                        "odds": odds,
                        "edge_pct": edge,
                        "confidence": vb.get("confidence", 0),
                        "true_prob": true_p,
                        "date": match_dt,
                        "league": league,
                        "home_score": home_score,
                        "away_score": away_score,
                        "home_head": home_head,
                        "away_head": away_head,
                    })
                # Format ticket as markdown table
                if legs:
                    lines = [
                        "| " + T["table_match"] + " | " + T["table_pick"] + " | " + T["table_odds"] + " | " + T["table_edge"] + " | " + T["table_chance"] + " | " + T["table_conf"] + " | " + T["table_date"] + " |",
                        "|------|----------|------|------|-------|------|------|",
                    ]
                    for leg in legs:
                        ec = "green" if leg['edge_pct'] >= 0 else "red"
                        stars = "★" * max(0, min(5, int(leg['confidence'] or 0)))
                        leg_pct = max(0, min(100, int(round((leg.get('true_prob') or 0) * 100))))
                        lines.append(
                            "| **" + leg['match'] + "** | " + leg['pick'] + " | **" + ("%.2f" % leg['odds']) + "** | ##" + ec + ":" + ("%+.1f%%" % leg['edge_pct']) + "## | **" + str(leg_pct) + "%** | " + stars + " | " + leg['date'] + " |"
                        )
                    table_md = "\n".join(lines)
                    win_pct = min(99.0, total_true_prob * 100.0)
                    risk_pct = max(1.0, 100.0 - win_pct)
                    verdict_line = f"\n\n[VERDICT] {{\"win_pct\": {win_pct:.1f}, \"side\": \"{T['parlay']}\", \"event\": \"{count} {T['ticket_selections']}\"}}"
                    reasons = []
                    for idx, leg in enumerate(legs, 1):
                        hm = leg['match'].split(' vs ')
                        home_name = hm[0] if len(hm) > 1 else leg['match']
                        away_name = hm[1] if len(hm) > 1 else ''
                        parts = []
                        if leg['home_score'] != 0:
                            c = "red" if leg['home_score'] < 0 else "green"
                            lbl = T["injuries"] if leg['home_score'] < 0 else T["positive_news"]
                            parts.append("__" + home_name + "__: ##" + c + ":" + lbl + "##")
                        if leg['away_score'] != 0:
                            c = "red" if leg['away_score'] < 0 else "green"
                            lbl = T["injuries"] if leg['away_score'] < 0 else T["positive_news"]
                            parts.append("__" + away_name + "__: ##" + c + ":" + lbl + "##")
                        if not parts:
                            parts.append(T["neutral_news"])
                        head = leg['home_head'] if abs(leg['home_score']) >= abs(leg['away_score']) else leg['away_head']
                        if head:
                            clean = head.replace('&nbsp;', ' ').replace('\u00a0', ' ')
                            while '  ' in clean:
                                clean = clean.replace('  ', ' ')
                            clean = clean.strip()[:70]
                            if clean:
                                parts.append("*" + clean + "…*")
                        ec = "green" if leg['edge_pct'] >= 0 else "red"
                        reasons.append(
                            str(idx) + ". **" + leg['match'] + "** → " + leg['pick']
                            + " · " + T["odds_word"] + " **" + ("%.2f" % leg['odds']) + "** · edge ##" + ec + ":" + ("%+.1f%%" % leg['edge_pct']) + "##\n   " + " · ".join(parts)
                        )
                    details_section = "\n".join(reasons)
                    header = "## " + T["ticket_header"]
                    sub = f"**{count} {T['ticket_selections']}{f' · {ticket_sport}' if ticket_sport else ''}** · {T['combined']} ##green:{win_pct:.0f}%## · {T['risk']} ##red:{risk_pct:.0f}%##"
                    note = T["check_odds"]
                    risk_note = ""
                    if win_pct < 50.0:
                        alt_prob = 1.0
                        for vb in selected[:2]:
                            alt_prob *= true_prob(vb)
                        risk_note = "\n\n" + T["risk_note"]
                        if count >= 3 and alt_prob > win_pct / 100.0:
                            risk_note += T["alternative"].format(pct=f"{alt_prob * 100:.0f}")
                    reply = header + "\n" + sub + "\n\n" + table_md + "\n\n**" + T["why_picks"] + "**\n" + details_section + "\n" + note + risk_note + verdict_line
                else:
                    reply = T["no_ticket"]
                return {
                    "reply": reply,
                    "tools_used": ["get_value_bets"],  # we used cached value bets
                    "provider": "system",
                }

            except Exception as e:
                # fallback to normal flow if something goes wrong
                pass
        last_error = None
        all_errors = []
        for provider in self._ordered_providers():
            tools_used = []
            seen_tool_calls = {}
            for _ in range(self.max_iterations):
                try:
                    data = self._call_model(provider, messages)
                except Exception as e:
                    err = f"[{provider['name']}] {type(e).__name__}: {e}"
                    all_errors.append(err)
                    last_error = err
                    self._mark_failed(provider)
                    time.sleep(0.5)
                    break
                msg = data["choices"][0]["message"]
                tool_calls = list(msg.get("tool_calls") or [])
                content = msg.get("content") or ""
                if not tool_calls and content and self._DSML_DETECT_RE.search(content):
                    parsed = self._parse_dsml_tools(content)
                    for i, t in enumerate(parsed):
                        tool_calls.append(
                            {"id": f"call_dsml_{i}", "type": "function", "function": {"name": t["name"], "arguments": t["arguments"]}}
                        )
                    msg = dict(msg)
                    msg["content"] = self._clean_dsml(content)
                if tool_calls:
                    messages.append(msg)
                    looped = False
                    for tc in tool_calls:
                        fn = tc["function"]
                        tools_used.append(fn["name"])
                        sig = fn["name"] + "|" + (fn.get("arguments") or "")
                        seen_tool_calls[sig] = seen_tool_calls.get(sig, 0) + 1
                        if seen_tool_calls[sig] >= 2:
                            looped = True
                        try:
                            args = json.loads(fn.get("arguments") or "{}")
                        except Exception:
                            args = {}
                        try:
                            result = self._dispatch(fn["name"], args)
                        except Exception as e:
                            result = {"error": f"Tool {fn['name']} a eșuat: {e}"}
                        messages.append(
                            {"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result, ensure_ascii=False)}
                        )
                    if looped:
                        break
                    continue
                self._mark_ok(provider)
                return {
                    "reply": self._clean_dsml(content) or (msg.get("reasoning_content") or "")[:400] or "Răspuns gol.",
                    "tools_used": tools_used,
                    "provider": provider["name"],
                }
            try:
                data = self._call_model(provider, messages, tool_choice="none")
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                if self._DSML_DETECT_RE.search(content):
                    dsml = self._parse_dsml_tools(content)
                    if dsml:
                        for i, t in enumerate(dsml):
                            tools_used.append(t["name"])
                            try:
                                args = json.loads(t["arguments"] or "{}")
                            except Exception:
                                args = {}
                            try:
                                result = self._dispatch(t["name"], args)
                            except Exception as e:
                                result = {"error": f"Tool {t['name']} a eșuat: {e}"}
                            messages.append(
                                {"role": "tool", "tool_call_id": f"call_dsml_f_{i}", "content": json.dumps(result, ensure_ascii=False)}
                            )
                        data = self._call_model(provider, messages, tool_choice="none")
                        msg = data["choices"][0]["message"]
                        content = msg.get("content") or ""
                self._mark_ok(provider)
                return {
                    "reply": self._clean_dsml(content) or (msg.get("reasoning_content") or "")[:400] or "Răspuns gol.",
                    "tools_used": tools_used,
                    "provider": provider["name"],
                }
            except Exception as e:
                all_errors.append(f"[{provider['name']}] final: {type(e).__name__}: {e}")
                last_error = all_errors[-1]
                self._mark_failed(provider)
            last_error = last_error or f"[{provider['name']}] fără răspuns"
        return {
            "reply": {
                "ro": f"Niciun provider AI nu a răspuns. Erori: {' | '.join(all_errors) or 'fără detalii'}",
                "de": f"Kein KI-Anbieter hat geantwortet. Fehler: {' | '.join(all_errors) or 'keine Details'}",
                "en": f"No AI provider responded. Errors: {' | '.join(all_errors) or 'no details'}",
            }[lang],
            "tools_used": [],
        }