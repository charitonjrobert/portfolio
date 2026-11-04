/* MicrobistBets front-end (vanilla, no external deps — works offline & on mobile) */
"use strict";

/* ------------------------------------------------------------------ i18n */
const I18N = {
  ro: {
    "app.tagline": "Pariuri pe înțelesul tuturor",
    "nav.home": "Acasă", "nav.matches": "Meciuri", "nav.mine": "Pariurile mele", "nav.assistant": "Asistent",
    "home.title": "Caută un meci și îți spun ce șanse are",
    "home.subtitle": "Scrie numele echipelor. Îți arăt probabilitățile calculate, cotele cele mai bune și ce spun știrile — pe scurt și pe românește.",
    "home.searchPlaceholder": "Ex: Arsenal, Real Madrid, Inter…",
    "home.analyzeBtn": "Analizează",
    "home.or": "sau",
    "home.recommendBtn": "Recomandă-mi un meci",
    "home.recommendHint": "Îți propun un meci doar când are avantaj real față de piața sharp. E rar — dacă nu găsesc nimic, îți spun sincer.",
    "matches.title": "Meciuri",
    "mfilter.all": "Toate", "mfilter.live": "🔴 Live", "mfilter.stream": "📺 Cu stream", "mfilter.odds": "Cu cote", "mfilter.upcoming": "Viitoare",
    "matches.subtitle": "Alege din lista de meciuri (inclusiv din zilele următoare). Dă click pe un meci pentru analiză.",
    "matches.today": "Azi", "matches.tomorrow": "Mâine", "matches.week": "7 zile", "matches.all": "Toate",
    "matches.searchPlaceholder": "Filtrează după echipă sau ligă…",
    "matches.btn": "Caută",
    "mine.title": "Pariurile mele",
    "assistant.badge": "microbist",
    "assistant.subtitle": "Întreabă-mă orice: meciuri, cote, echipe, cum stai cu bugetul.",
    "assistant.placeholder": "Scrie o întrebare…", "assistant.send": "Trimite",
    "limits.short": "Limite", "limits.title": "Cât mai am de folosit",
    "limits.intro": "Aplicația folosește câteva surse gratuite, fiecare cu limita ei. Aici vezi exact cât mai ai și când se reînnoiește.",
    "limits.check": "Verifică acum (consumă 1)",
    "footer.disclaimer": "Probabilitățile sunt estimări, nu certitudini. Joacă responsabil.",
    "loader.finding": "Caut meciul…", "loader.odds": "Citesc cotele…", "loader.news": "Verific știrile…", "loader.done": "Gata!",
    "res.probabilities": "Șanse calculate", "res.bestOdds": "Cele mai bune cote",
    "res.noProbabilities": "Pentru acest meci nu am cote 1X2 din care să calculez șansele.",
    "res.pnote.no_odds": "Casele de pariuri nu au publicat încă nicio cotă pentru acest meci.",
    "res.pnote.no_h2h_market": "Există cote, dar nu pe piața 1X2 (doar pe alte piețe).",
    "res.pnote.insufficient_market": "Cotele găsite nu sunt suficiente pentru o estimare stabilă.",
    "res.singleBook": "o singură casă",
    "res.valueBets": "Unde văd avantaj", "res.why": "De ce", "res.news": "Ce spun știrile",
    "res.players": "Nume apărute în știri", "res.stars": "încredere",
    "res.realProb": "probabilitate reală", "res.implied": "cota implică",
    "res.edge": "avantaj", "res.odds": "cotă", "res.analyzeDetail": "Analizează în detaliu", "res.another": "Încă unul",
    "res.market": "Piața (referință sharp)", "res.marketModel": "Modelul meu", "res.marketReal": "Piața",
    "res.edgeReal": "avantaj real", "res.edgeBest": "vs. cea mai bună cotă",
    "res.fromNews": "din știri",
    "res.newsMoved": "Știrile mută probabilitățile cu",
    "counter.title": "Contra-caz: ce ar putea schimba rezultatul",
    "counter.why": "De ce ar putea câștiga {team}",
    "counter.adjusted": "Șansă ajustată", "counter.model": "model", "counter.conf": "încredere",
    "counter.conf.none": "—", "counter.conf.low": "mică", "counter.conf.medium": "medie", "counter.conf.high": "mare",
    "counter.grounded": "Motive cu surse reale", "counter.ungrounded": "Doar context, fără surse",
    "counter.support": "cât de plauzibil e factorul",
    "counter.none": "Nu am găsit factori externi reali care să răstoarne balanța — deci nu inventez un contraargument.",
    "counter.evidence": "Surse",
    "counter.hint": "Procentele arată cât de PLAUZIBIL e fiecare factor, NU probabilitatea de câștig (care rămâne cea a modelului). \"Șansă ajustată\" = cât de credibilă devine surpriza dacă factorii se adeveresc. Titlurile sunt preluate automat din știri.",
    "counter.f.fav_bad_news": "Vești proaste la {team} (accidentări/suspendări/plecări)",
    "counter.f.underdog_good_news": "{team} are jucători importanți care revin",
    "counter.f.underdog_home": "{team} joacă acasă",
    "counter.f.draw_threat": "Egalul e o amenințare reală (meci strâns)",
    "counter.f.market_skeptic": "Piața sharp dă {team} mai mult decât modelul meu",
    "counter.f.thin_edge": "Favorita nu e clar superioară (avantaj subțire)",
    "res.sharpOdds": "cotă sharp", "res.fairOdds": "cotă corectă", "res.source": "sursă",
    "res.sharpMarket": "piață sharp", "res.consensus": "consensul caselor", "res.noMarket": "fără referință de piață",
    "res.noEdge": "Aici nu am informație în plus față de piață — deci niciun avantaj real. Prefer să ți-o spun direct.",
    "res.marketHint": "Avantajul se măsoară față de piața sharp (fără marjă), nu față de cea mai bună cotă — altfel orice cotă atipică pare „valoare\".",
    "wallet.clv": "CLV mediu", "wallet.clvPositive": "Pariuri cu CLV pozitiv",
    "wallet.clvHint": "CLV = cât de bună a fost cota ta față de cota de închidere a pieței sharp. Peste 0% înseamnă că ai bătut piața — cel mai bun semn că un sistem chiar funcționează.",
    "res.noOdds": "Fără cote", "res.past": "Atenție: meciul e deja încheiat — îți arăt doar cum arăta atunci.",
    "res.found": "Am găsit", "res.variants": "variante", "res.variantOne": "variantă",
    "empty.matches": "Niciun meci găsit aici. Încearcă „Toate\" sau altă căutare.",
    "empty.bets": "Nu ai încă pariuri salvate.",
    "mine.balance": "Buget", "mine.open": "Pariuri deschise", "mine.roi": "ROI", "mine.settled": "Încheiate",
    "mine.winRate": "Rată câștig",
    "mine.won": "Câștigat", "mine.lost": "Pierdut", "mine.pending": "În așteptare",
    "chat.thinking": "Miki se gândește…",
    "chat.verdict": "Verdict final", "chat.win": "câștig", "chat.lose": "pierdut",
    "tip.brand": { t: "MicrobistBets", d: "Aplicația ta de pariuri, pe înțelesul tuturor. Aduni cote din mai multe case și îți arăt unde probabilitatea reală e mai mare decât ce zice cota." },
    "tip.lang": { t: "Limbă", d: "Schimbă limba aplicației: română, germană sau engleză." },
    "tip.theme": { t: "Mod zi/noapte", d: "Comută între tema închisă (dark) și cea deschisă (light). Alegerea se ține minte." },
    "tip.limits": { t: "Limite", d: "Cât mai ai de folosit din sursele gratuite (cote, detalii meciuri, meciuri viitoare, asistent) și când se reînnoiesc." },
    "tip.tabHome": { t: "Acasă", d: "Caută un meci sau cere o recomandare. Aici vezi probabilitățile și motivele." },
    "tip.tabMatches": { t: "Meciuri", d: "Lista de meciuri (azi, mâine, 7 zile sau toate), cu filtre pe ligă și căutare. Click pe un meci = analiză." },
    "tip.tabMine": { t: "Pariurile mele", d: "Bugetul tău, pariurile în așteptare și rezultatele. Le poți marca câștigate sau pierdute." },
    "tip.tabAssistant": { t: "Asistent", d: "Chat cu Miki: întreabă în limbaj natural despre meciuri, cote, echipe." },
    "tip.search": { t: "Căutare", d: "Scrie numele unei echipe. Îți propun meciuri potrivite pe măsură ce scrii." },
    "tip.analyze": { t: "Analizează", d: "Ia meciul din cotele salvate și calculează probabilitățile (model Poisson + istoric), le compară cu cotele și adaugă contextul din știri. Nu consumă cereri plătite." },
    "tip.recommend": { t: "Recomandă-mi un meci", d: "Aleg un meci doar dacă are avantaj real față de piața sharp (probabilitate plauzibilă) — fără lozuri. E rar: dacă nu găsesc nimic cu avantaj real, îți spun sincer în loc să-ți inventez o ocazie." },
    "tip.day0": { t: "Azi", d: "Meciurile care se joacă azi." },
    "tip.day1": { t: "Mâine", d: "Meciurile de mâine." },
    "tip.day7": { t: "7 zile", d: "Următoarele șapte zile." },
    "tip.dayAll": { t: "Toate", d: "Tot ce am în date, oricât de departe în viitor." },
    "tip.loadMatches": { t: "Caută", d: "Reîncarcă lista cu filtrele alese." },
    "tip.miki": { t: "Miki — microbistul", d: "Asistentul tău. Vorbește simplu, fără termeni de specialitate, și recunoaște când nu știe." },
    "tip.chatInput": { t: "Scrie aici", d: "Întreabă orice despre meciuri, cote, echipe sau buget." },
    "tip.chatSend": { t: "Trimite", d: "Trimite întrebarea către Miki." },
    "tip.close": { t: "Închide", d: "Închide panoul." },
    "tip.limitsCheck": { t: "Verifică acum", d: "Citește starea reală a surselor. Consumă 1 cerere de status (foarte puțin), de asta nu se face automat." },
    "watch.title": "📺 Watch live", "watch.free": "Streamuri gratuite legale:",
    "watch.noFree": "Liga asta nu are stream gratuit legal — se vede doar pe broadcasterul oficial (DAZN/Sky etc.).",
    "watch.off": "Fără stream gratuit",
    "watch.openTab": "Deschide în tab nou", "watch.playerHint": "Player încorporat (stream oficial, când există)",
  },
  de: {
    "app.tagline": "Wetten, einfach erklärt",
    "nav.home": "Start", "nav.matches": "Spiele", "nav.mine": "Meine Wetten", "nav.assistant": "Assistent",
    "home.title": "Spiel suchen und Chancen sehen",
    "home.subtitle": "Gib die Teamnamen ein. Du bekommst berechnete Wahrscheinlichkeiten, die besten Quoten und die wichtigsten News — kurz und verständlich.",
    "home.searchPlaceholder": "z. B. Bayern, Real Madrid, Inter…",
    "home.analyzeBtn": "Analysieren",
    "home.or": "oder",
    "home.recommendBtn": "Empfiehl mir ein Spiel",
    "home.recommendHint": "Ich schlage ein Spiel nur vor, wenn es einen echten Vorteil gegenüber dem Sharp-Markt gibt. Das ist selten — wenn ich nichts finde, sage ich es ehrlich.",
    "matches.title": "Spiele",
    "mfilter.all": "Alle", "mfilter.live": "🔴 Live", "mfilter.stream": "📺 Mit Stream", "mfilter.odds": "Mit Quoten", "mfilter.upcoming": "Kommend",
    "matches.subtitle": "Wähle aus der Liste (auch kommende Tage). Klick auf ein Spiel für die Analyse.",
    "matches.today": "Heute", "matches.tomorrow": "Morgen", "matches.week": "7 Tage", "matches.all": "Alle",
    "matches.searchPlaceholder": "Nach Team oder Liga filtern…",
    "matches.btn": "Suchen",
    "mine.title": "Meine Wetten",
    "assistant.badge": "Fußballfan",
    "assistant.subtitle": "Frag mich alles: Spiele, Quoten, Teams, dein Budget.",
    "assistant.placeholder": "Frage schreiben…", "assistant.send": "Senden",
    "limits.short": "Limits", "limits.title": "Wie viel ich noch nutzen kann",
    "limits.intro": "Die App nutzt einige kostenlose Quellen, jede mit eigenem Limit. Hier siehst du, wie viel bleibt und wann es sich erneuert.",
    "limits.check": "Jetzt prüfen (verbraucht 1)",
    "footer.disclaimer": "Wahrscheinlichkeiten sind Schätzungen, keine Gewissheiten. Spiele verantwortungsvoll.",
    "loader.finding": "Spiel wird gesucht…", "loader.odds": "Quoten werden gelesen…", "loader.news": "News werden geprüft…", "loader.done": "Fertig!",
    "res.probabilities": "Berechnete Chancen", "res.bestOdds": "Beste Quoten",
    "res.noProbabilities": "Für dieses Spiel habe ich keine 1X2-Quoten, aus denen ich die Chancen berechnen kann.",
    "res.pnote.no_odds": "Die Buchmacher haben für dieses Spiel noch keine Quote veröffentlicht.",
    "res.pnote.no_h2h_market": "Es gibt Quoten, aber nicht für den 1X2-Markt (nur für andere Märkte).",
    "res.pnote.insufficient_market": "Die gefundenen Quoten reichen für eine stabile Schätzung nicht aus.",
    "res.singleBook": "nur ein Buchmacher",
    "res.valueBets": "Wo ich einen Vorteil sehe", "res.why": "Warum", "res.news": "Was die News sagen",
    "res.players": "Namen in den News", "res.stars": "Vertrauen",
    "res.realProb": "echte Wahrscheinlichkeit", "res.implied": "Quote impliziert",
    "res.edge": "Vorteil", "res.odds": "Quote", "res.analyzeDetail": "Genauer analysieren", "res.another": "Noch eines",
    "res.market": "Markt (Sharp-Referenz)", "res.marketModel": "Mein Modell", "res.marketReal": "Markt",
    "res.edgeReal": "echter Vorteil", "res.edgeBest": "vs. beste Quote",
    "res.fromNews": "aus den News",
    "res.newsMoved": "Die News verschieben die Wahrscheinlichkeiten um",
    "counter.title": "Gegenfall: Was das Ergebnis kippen könnte",
    "counter.why": "Warum {team} gewinnen könnte",
    "counter.adjusted": "Angepasste Chance", "counter.model": "Modell", "counter.conf": "Vertrauen",
    "counter.conf.none": "—", "counter.conf.low": "gering", "counter.conf.medium": "mittel", "counter.conf.high": "hoch",
    "counter.grounded": "Gründe mit echten Quellen", "counter.ungrounded": "Nur Kontext, keine Quellen",
    "counter.support": "wie plausibel der Faktor ist",
    "counter.none": "Ich habe keine echten externen Faktoren gefunden, die das Blatt wenden könnten — also erfinde ich kein Gegenargument.",
    "counter.evidence": "Quellen",
    "counter.hint": "Die Prozente zeigen, wie PLAUSIBEL jeder Faktor ist — NICHT die Gewinnwahrscheinlichkeit (die bleibt die des Modells). „Angepasste Chance“ = wie glaubwürdig die Überraschung wird, wenn die Faktoren eintreffen. Schlagzeilen werden automatisch aus den News übernommen.",
    "counter.f.fav_bad_news": "Schlechte Nachrichten bei {team} (Verletzungen/Sperren/Abgänge)",
    "counter.f.underdog_good_news": "{team} bekommt wichtige Spieler zurück",
    "counter.f.underdog_home": "{team} spielt zu Hause",
    "counter.f.draw_threat": "Das Remis ist eine echte Gefahr (enges Spiel)",
    "counter.f.market_skeptic": "Der Sharp-Markt gibt {team} mehr als mein Modell",
    "counter.f.thin_edge": "Der Favorit ist nicht klar überlegen (dünner Vorteil)",
    "res.sharpOdds": "Sharp-Quote", "res.fairOdds": "faire Quote", "res.source": "Quelle",
    "res.sharpMarket": "Sharp-Markt", "res.consensus": "Buchmacher-Konsens", "res.noMarket": "keine Marktreferenz",
    "res.noEdge": "Hier habe ich keine Zusatzinformation gegenüber dem Markt — also kein echter Vorteil. Das sage ich lieber direkt.",
    "res.marketHint": "Der Vorteil wird gegen den Sharp-Markt (ohne Marge) gemessen, nicht gegen die beste Quote — sonst wirkt jeder Ausreißer wie „Value“.",
    "wallet.clv": "CLV (Ø)", "wallet.clvPositive": "Wetten mit positivem CLV",
    "wallet.clvHint": "CLV = wie viel besser deine Quote war als die Schlussquote des Sharp-Markts. Über 0% heißt: du hast den Markt geschlagen — das beste Zeichen, dass ein System wirklich funktioniert.",
    "res.noOdds": "Ohne Quoten", "res.past": "Achtung: Das Spiel ist schon beendet — ich zeige nur, wie es damals aussah.",
    "res.found": "Gefunden", "res.variants": "Optionen", "res.variantOne": "Option",
    "empty.matches": "Keine Spiele gefunden. Versuche „Alle“ oder eine andere Suche.",
    "empty.bets": "Noch keine Wetten gespeichert.",
    "mine.balance": "Budget", "mine.open": "Offene Wetten", "mine.roi": "ROI", "mine.settled": "Beendet",
    "mine.winRate": "Trefferquote",
    "mine.won": "Gewonnen", "mine.lost": "Verloren", "mine.pending": "Ausstehend",
    "chat.thinking": "Miki überlegt…",
    "chat.verdict": "Endurteil", "chat.win": "Sieg", "chat.lose": "Niederlage",
    "tip.brand": { t: "MicrobistBets", d: "Deine Wett-App, einfach erklärt. Sie sammelt Quoten mehrerer Buchmacher und zeigt, wo die echte Wahrscheinlichkeit höher ist als die Quote." },
    "tip.lang": { t: "Sprache", d: "Sprache wechseln: Rumänisch, Deutsch oder Englisch." },
    "tip.theme": { t: "Hell/Dunkel", d: "Zwischen dunklem und hellem Design wechseln. Die Wahl bleibt gespeichert." },
    "tip.limits": { t: "Limits", d: "Wie viel du aus den kostenlosen Quellen noch nutzen kannst und wann sie sich erneuern." },
    "tip.tabHome": { t: "Start", d: "Spiel suchen oder Empfehlung anfordern. Hier siehst du Wahrscheinlichkeiten und Gründe." },
    "tip.tabMatches": { t: "Spiele", d: "Liste der Spiele (heute, morgen, 7 Tage, alle) mit Liga-Filtern und Suche. Klick = Analyse." },
    "tip.tabMine": { t: "Meine Wetten", d: "Budget, offene Wetten und Ergebnisse. Du kannst sie als gewonnen/verloren markieren." },
    "tip.tabAssistant": { t: "Assistent", d: "Chat mit Miki: frage natürlich nach Spielen, Quoten, Teams." },
    "tip.search": { t: "Suche", d: "Teamnamen eingeben. Passende Spiele werden während des Tippens vorgeschlagen." },
    "tip.analyze": { t: "Analysieren", d: "Nimmt das Spiel aus den gespeicherten Quoten und berechnet Wahrscheinlichkeiten (Poisson + Historie), vergleicht sie mit den Quoten und ergänzt News-Kontext. Verbraucht keine bezahlten Anfragen." },
    "tip.recommend": { t: "Empfiehl mir ein Spiel", d: "Ich wähle ein Spiel nur, wenn es einen echten Vorteil gegenüber dem Sharp-Markt gibt — keine Lotterien. Das ist selten: finde ich nichts mit echtem Vorteil, sage ich es ehrlich, statt dir eine Chance zu erfinden." },
    "tip.day0": { t: "Heute", d: "Spiele, die heute stattfinden." },
    "tip.day1": { t: "Morgen", d: "Morgige Spiele." },
    "tip.day7": { t: "7 Tage", d: "Die nächsten sieben Tage." },
    "tip.dayAll": { t: "Alle", d: "Alles, was ich habe, egal wie weit in der Zukunft." },
    "tip.loadMatches": { t: "Suchen", d: "Liste mit den gewählten Filtern neu laden." },
    "tip.miki": { t: "Miki — der Fußballfan", d: "Dein Assistent. Spricht einfach, ohne Fachjargon, und gibt zu, wenn er etwas nicht weiß." },
    "tip.chatInput": { t: "Hier schreiben", d: "Frage alles zu Spielen, Quoten, Teams oder Budget." },
    "tip.chatSend": { t: "Senden", d: "Die Frage an Miki senden." },
    "tip.close": { t: "Schließen", d: "Panel schließen." },
    "tip.limitsCheck": { t: "Jetzt prüfen", d: "Liest den echten Status der Quellen. Verbraucht 1 Status-Anfrage — darum nicht automatisch." },
    "watch.title": "📺 Live schauen", "watch.free": "Kostenlose legale Streams:",
    "watch.noFree": "Für diese Liga gibt es keinen kostenlosen legalen Stream — nur beim offiziellen Sender (DAZN/Sky usw.).",
    "watch.off": "Kein kostenloser Stream",
    "watch.openTab": "In neuem Tab öffnen", "watch.playerHint": "Eingebetteter Player (offizieller Stream, falls vorhanden)",
  },
  en: {
    "app.tagline": "Betting made simple",
    "nav.home": "Home", "nav.matches": "Matches", "nav.mine": "My bets", "nav.assistant": "Assistant",
    "home.title": "Look up a match and see its chances",
    "home.subtitle": "Type the team names. You get calculated probabilities, the best odds and what the news says — short and clear.",
    "home.searchPlaceholder": "e.g. Arsenal, Real Madrid, Inter…",
    "home.analyzeBtn": "Analyze",
    "home.or": "or",
    "home.recommendBtn": "Recommend me a match",
    "home.recommendHint": "I suggest a match only when it has a real edge over the sharp market. That's rare — if I find nothing, I'll tell you honestly.",
    "matches.title": "Matches",
    "mfilter.all": "All", "mfilter.live": "🔴 Live", "mfilter.stream": "📺 With stream", "mfilter.odds": "With odds", "mfilter.upcoming": "Upcoming",
    "matches.subtitle": "Pick from the list (including upcoming days). Click a match to analyze it.",
    "matches.today": "Today", "matches.tomorrow": "Tomorrow", "matches.week": "7 days", "matches.all": "All",
    "matches.searchPlaceholder": "Filter by team or league…",
    "matches.btn": "Search",
    "mine.title": "My bets",
    "assistant.badge": "football fan",
    "assistant.subtitle": "Ask me anything: matches, odds, teams, your budget.",
    "assistant.placeholder": "Type a question…", "assistant.send": "Send",
    "limits.short": "Limits", "limits.title": "How much I can still use",
    "limits.intro": "The app uses a few free sources, each with its own limit. Here you see what's left and when it resets.",
    "limits.check": "Check now (uses 1)",
    "footer.disclaimer": "Probabilities are estimates, not certainties. Bet responsibly.",
    "loader.finding": "Looking up the match…", "loader.odds": "Reading odds…", "loader.news": "Checking the news…", "loader.done": "Done!",
    "res.probabilities": "Calculated chances", "res.bestOdds": "Best odds",
    "res.noProbabilities": "I don't have 1X2 odds for this match, so I can't calculate the chances.",
    "res.pnote.no_odds": "Bookmakers haven't published any odds for this match yet.",
    "res.pnote.no_h2h_market": "Odds exist, but not for the 1X2 market (other markets only).",
    "res.pnote.insufficient_market": "The odds found are not enough for a stable estimate.",
    "res.singleBook": "single bookmaker",
    "res.valueBets": "Where I see an edge", "res.why": "Why", "res.news": "What the news says",
    "res.players": "Names in the news", "res.stars": "confidence",
    "res.realProb": "real probability", "res.implied": "odds imply",
    "res.edge": "edge", "res.odds": "odds", "res.analyzeDetail": "Analyze in detail", "res.another": "Another one",
    "res.market": "Market (sharp reference)", "res.marketModel": "My model", "res.marketReal": "Market",
    "res.edgeReal": "real edge", "res.edgeBest": "vs. best price",
    "res.fromNews": "from news",
    "res.newsMoved": "The news moves the probabilities by",
    "counter.title": "Counter-case: what could flip the result",
    "counter.why": "Why {team} could win",
    "counter.adjusted": "Adjusted chance", "counter.model": "model", "counter.conf": "confidence",
    "counter.conf.none": "—", "counter.conf.low": "low", "counter.conf.medium": "medium", "counter.conf.high": "high",
    "counter.grounded": "Grounded reasons", "counter.ungrounded": "Context only, no sources",
    "counter.support": "how plausible the factor is",
    "counter.none": "I found no real external factors that could flip the balance — so I won't invent a counter-argument.",
    "counter.evidence": "Sources",
    "counter.hint": "The percentages show how PLAUSIBLE each factor is, NOT the win probability (that stays the model's). \"Adjusted chance\" = how credible the upset becomes if those factors come true. Headlines are collected automatically from the news.",
    "counter.f.fav_bad_news": "Bad news for {team} (injuries/suspensions/departures)",
    "counter.f.underdog_good_news": "{team} gets key players back",
    "counter.f.underdog_home": "{team} plays at home",
    "counter.f.draw_threat": "The draw is a real threat (tight match)",
    "counter.f.market_skeptic": "The sharp market gives {team} more than my model",
    "counter.f.thin_edge": "The favourite isn't clearly superior (thin edge)",
    "res.sharpOdds": "sharp price", "res.fairOdds": "fair price", "res.source": "source",
    "res.sharpMarket": "sharp market", "res.consensus": "bookmaker consensus", "res.noMarket": "no market reference",
    "res.noEdge": "Here I have no extra information versus the market — so no real edge. I'd rather say it straight.",
    "res.marketHint": "The edge is measured against the sharp market (margin-free), not against the best price — otherwise any outlier price looks like \"value\".",
    "wallet.clv": "avg CLV", "wallet.clvPositive": "Bets with positive CLV",
    "wallet.clvHint": "CLV = how much better your price was than the sharp market's closing price. Above 0% means you beat the market — the best sign a system actually works.",
    "res.noOdds": "No odds", "res.past": "Careful: this match is already over — I'm showing how it looked then.",
    "res.found": "Found", "res.variants": "options", "res.variantOne": "option",
    "empty.matches": "No matches found here. Try „All\" or another search.",
    "empty.bets": "No saved bets yet.",
    "mine.balance": "Balance", "mine.open": "Open bets", "mine.roi": "ROI", "mine.settled": "Settled",
    "mine.winRate": "Win rate",
    "mine.won": "Won", "mine.lost": "Lost", "mine.pending": "Pending",
    "chat.thinking": "Miki is thinking…",
    "chat.verdict": "Final verdict", "chat.win": "win", "chat.lose": "lose",
    "tip.brand": { t: "MicrobistBets", d: "Your betting app, made simple. It gathers odds from several bookmakers and shows where the real probability beats the odds." },
    "tip.lang": { t: "Language", d: "Switch the app language: Romanian, German or English." },
    "tip.theme": { t: "Light/Dark", d: "Toggle between dark and light theme. Your choice is remembered." },
    "tip.limits": { t: "Limits", d: "How much is left of each free source and when it resets." },
    "tip.tabHome": { t: "Home", d: "Search a match or ask for a recommendation. Probabilities and reasons show up here." },
    "tip.tabMatches": { t: "Matches", d: "Match list (today, tomorrow, 7 days, all) with league filters and search. Click = analyze." },
    "tip.tabMine": { t: "My bets", d: "Your budget, open bets and results. Mark them won or lost." },
    "tip.tabAssistant": { t: "Assistant", d: "Chat with Miki: ask about matches, odds and teams in plain words." },
    "tip.search": { t: "Search", d: "Type a team name. Matching fixtures are suggested as you type." },
    "tip.analyze": { t: "Analyze", d: "Takes the match from saved odds and computes probabilities (Poisson + history), compares them with the odds and adds news context. Uses no paid requests." },
    "tip.recommend": { t: "Recommend me a match", d: "I only pick a match when it has a real edge over the sharp market (plausible probability) — no lottery tickets. That's rare: if I find nothing with a real edge, I'll tell you honestly instead of inventing an opportunity." },
    "tip.day0": { t: "Today", d: "Matches played today." },
    "tip.day1": { t: "Tomorrow", d: "Tomorrow's matches." },
    "tip.day7": { t: "7 days", d: "The next seven days." },
    "tip.dayAll": { t: "All", d: "Everything I have, no matter how far ahead." },
    "tip.loadMatches": { t: "Search", d: "Reload the list with the chosen filters." },
    "tip.miki": { t: "Miki — the football fan", d: "Your assistant. Talks plainly, no jargon, and admits when it doesn't know." },
    "tip.chatInput": { t: "Type here", d: "Ask anything about matches, odds, teams or budget." },
    "tip.chatSend": { t: "Send", d: "Send the question to Miki." },
    "tip.close": { t: "Close", d: "Close the panel." },
    "tip.limitsCheck": { t: "Check now", d: "Reads the real source status. Uses 1 status request — that's why it isn't automatic." },
    "watch.title": "📺 Watch live", "watch.free": "Free legal streams:",
    "watch.noFree": "No free legal stream for this league — only on the official broadcaster (DAZN/Sky etc.).",
    "watch.off": "No free stream",
    "watch.openTab": "Open in new tab", "watch.playerHint": "Embedded player (official stream, when available)",
  },
};

/* Extra explanatory tooltips for result cards / stats (Jay's request: explain on hover). */
const EXTRA_TIPS = {
  ro: {
    "tip.match": { t: "Meci", d: "Apasă pentru analiza completă: probabilități, cele mai bune cote, avantaj și ce spun știrile." },
    "tip.cardProb": { t: "Șanse calculate", d: "Ce crede modelul meu despre fiecare rezultat. Folosește cotele ca punct de plecare, istoricul direct dintre echipe și ajustează cu ce se întâmplă în știri. Cele trei procente se adună la 100%." },
    "tip.cardOdds": { t: "Cele mai bune cote", d: "Cea mai mare cotă găsită pentru fiecare rezultat, la casele de pariuri monitorizate. Cu cât cota e mai mare, cu atât primești mai mult la aceeași miză." },
    "tip.cardValue": { t: "Unde văd avantaj", d: "Compar probabilitatea mea cu ce spune cota. Dacă cred că șansa e mai mare decât o plătește cota, apare un avantaj pozitiv. Stelele = cât de solid pare semnalul (avantaj + context), NU probabilitatea de câștig." },
    "tip.cardMarket": { t: "Piața (referință sharp)", d: "Cât crede PIAȚA că e șansa fiecărui rezultat, fără marja casei. Referința e casa sharp (Pinnacle/bursă) sau, dacă lipsește, mediana mai multor case. Diferența față de modelul meu, măsurată față de ACEASTĂ referință, este avantajul REAL — nu față de cea mai bună cotă (care poate fi o excepție)." },
    "tip.cardWhy": { t: "De ce", d: "Explicația simplă a concluziei: avantajul calculat, golurile estimate și starea de spirit din știri, la fiecare pas." },
    "tip.cardCounter": { t: "Contra-caz", d: "Aici joc rolul avocatului diavolului: caut motive REALE (din știri și context) pentru care echipa mai slab cotată ar putea câștiga. Fiecare factor are un procent = cât de plauzibil e, NU probabilitatea de câștig. Dacă nu găsesc motive reale, o spun direct." },
    "tip.counterSupport": { t: "Cât de plauzibil", d: "Cât de solid e semnalul pentru ACEST factor (din știri/context) — nu șansa de câștig. +pp = cu câte puncte procentuale ar putea mișca șansa echipei mai slabe." },
    "tip.cardNews": { t: "Ce spun știrile", d: "Titluri recente despre fiecare echipă, transformate într-un scor: plus = vești bune (ex. jucător cheie apt), minus = vești proaste (accidentări, scandaluri)." },
    "tip.statCard": { t: "Bugetul tău", d: "Banii pe care i-ai pus deoparte pentru pariuri, câți sunt în joc acum și randamentul (ROI) pe pariurile încheiate." },
    "tip.clv": { t: "CLV (Closing Line Value)", d: "Cât de bună a fost cota ta față de cota de închidere a pieței sharp (Pinnacle/bursă), măsurată la fiecare pariu. Peste 0% = ai prins o cotă mai bună decât piața — cel mai bun semn că un sistem chiar are valoare. Se calculează doar pe pariurile încheiate pentru care am prins cota de închidere." },
    "tip.betCard": { t: "Pariu salvat", d: "Un pariu pe care l-ai salvat. Când se termină meciul, marchează-l câștigat sau pierdut ca să vezi evoluția bugetului." },
    "tip.disclaimer": { t: "Atenție", d: "Probabilitățile sunt estimări ale modelului, nu certitudini. Nicio metodă nu garantează câștigul." },
  },
  de: {
    "tip.match": { t: "Spiel", d: "Klick für die volle Analyse: Wahrscheinlichkeiten, beste Quoten, Vorteil und News." },
    "tip.cardProb": { t: "Berechnete Chancen", d: "Was mein Modell über jedes Ergebnis denkt: Quoten als Startpunkt, direkte Historie der Teams und News-Anpassung. Die drei Prozentwerte ergeben 100%." },
    "tip.cardOdds": { t: "Beste Quoten", d: "Die höchste gefundene Quote für jedes Ergebnis bei den überwachten Buchmachern. Höhere Quote = mehr Gewinn bei gleichem Einsatz." },
    "tip.cardValue": { t: "Wo ich einen Vorteil sehe", d: "Ich vergleiche meine Wahrscheinlichkeit mit der Quote. Ist meine Chance höher, als die Quote vergütet, entsteht ein Vorteil. Sterne = wie solide das Signal wirkt (Vorteil + Kontext), NICHT die Gewinnwahrscheinlichkeit." },
    "tip.cardMarket": { t: "Markt (Sharp-Referenz)", d: "Was der MARKT über die Chance jedes Ergebnisses denkt, ohne die Buchmacher-Marge. Referenz ist der Sharp-Buchmacher (Pinnacle/Börse) oder, falls keiner dabei ist, der Median mehrerer Buchmacher. Die Abweichung meines Modells von DIESER Referenz ist der ECHTE Vorteil — nicht gegenüber der besten Quote (die ein Ausreißer sein kann)." },
    "tip.cardWhy": { t: "Warum", d: "Die einfache Begründung: berechneter Vorteil, erwartete Tore und die Stimmung in den News." },
    "tip.cardCounter": { t: "Gegenfall", d: "Hier bin ich der Advocatus Diaboli: ich suche ECHTE Gründe (aus News und Kontext), warum das schwächer gehandelte Team gewinnen könnte. Jeder Faktor hat einen Prozentsatz = wie plausibel er ist, NICHT die Gewinnwahrscheinlichkeit. Finde ich keine echten Gründe, sage ich es direkt." },
    "tip.counterSupport": { t: "Wie plausibel", d: "Wie solide das Signal für DIESEN Faktor ist (aus News/Kontext) — nicht die Gewinnchance. +pp = um wie viele Prozentpunkte er die Chance des schwächeren Teams verschieben könnte." },
    "tip.cardNews": { t: "Was die News sagen", d: "Aktuelle Schlagzeilen zu jedem Team, in einen Score umgerechnet: plus = gute Nachrichten, minus = schlechte (Verletzungen, Skandale)." },
    "tip.statCard": { t: "Dein Budget", d: "Dein Wett-Budget, wie viel gerade im Spiel ist und die Rendite (ROI) der abgeschlossenen Wetten." },
    "tip.clv": { t: "CLV (Closing Line Value)", d: "Wie viel besser deine Quote war als die Schlussquote des Sharp-Markts (Pinnacle/Börse), pro Wette gemessen. Über 0% = du hast eine bessere Quote als der Markt erwischt — das beste Zeichen, dass ein System wirklich Wert hat. Wird nur für abgeschlossene Wetten berechnet, bei denen die Schlussquote erfasst wurde." },
    "tip.betCard": { t: "Gespeicherte Wette", d: "Eine Wette, die du gespeichert hast. Nach dem Spiel als gewonnen/verloren markieren, um den Verlauf zu sehen." },
    "tip.disclaimer": { t: "Hinweis", d: "Wahrscheinlichkeiten sind Modellschätzungen, keine Gewissheiten. Keine Methode garantiert einen Gewinn." },
  },
  en: {
    "tip.match": { t: "Match", d: "Tap for the full analysis: probabilities, best odds, edge and what the news says." },
    "tip.cardProb": { t: "Calculated chances", d: "What my model thinks about each outcome: odds as a starting point, the teams' head-to-head history and news adjustments. The three percentages add up to 100%." },
    "tip.cardOdds": { t: "Best odds", d: "The highest odds found for each outcome across the monitored bookmakers. Higher odds = more return for the same stake." },
    "tip.cardValue": { t: "Where I see an edge", d: "I compare my probability with what the odds imply. If my chance is higher than the odds pay for, that's a positive edge. Stars = how solid the signal looks (edge + context), NOT the win probability." },
    "tip.cardMarket": { t: "Market (sharp reference)", d: "What the MARKET thinks the chance of each outcome is, without the bookmaker margin. The reference is the sharp book (Pinnacle/exchange) or, if there is none, the median of several books. My model's difference from THIS reference is the REAL edge — not versus the best price (which can be an outlier)." },
    "tip.cardWhy": { t: "Why", d: "The plain-language reason: the calculated edge, expected goals and the mood from the news." },
    "tip.cardCounter": { t: "Counter-case", d: "Here I play devil's advocate: I look for REAL reasons (from the news and the context) why the weaker-priced team could win. Each factor has a percentage = how plausible it is, NOT the win probability. If I find no real reasons, I say so straight." },
    "tip.counterSupport": { t: "How plausible", d: "How solid the signal for THIS factor is (from news/context) — not the win chance. +pp = how many percentage points it could shift the weaker team's chance." },
    "tip.cardNews": { t: "What the news says", d: "Recent headlines about each team turned into a score: plus = good news, minus = bad news (injuries, scandals)." },
    "tip.statCard": { t: "Your budget", d: "The money you set aside for betting, how much is in play right now and the return (ROI) on settled bets." },
    "tip.clv": { t: "CLV (Closing Line Value)", d: "How much better your price was than the sharp market's closing price (Pinnacle/exchange), measured per bet. Above 0% = you got a better price than the market — the best sign a system really has value. Computed only for settled bets where the closing price was captured." },
    "tip.betCard": { t: "Saved bet", d: "A bet you saved. When the match ends, mark it won or lost to track your budget." },
    "tip.disclaimer": { t: "Careful", d: "Probabilities are model estimates, not certainties. No method guarantees a win." },
  },
};
Object.keys(EXTRA_TIPS).forEach((l) => Object.assign(I18N[l], EXTRA_TIPS[l]));

/* Cache-related strings (server + client caching, 13 Oct 2026). */
Object.assign(I18N.ro, {
  "loader.working": "Se încarcă…", "loader.doneOk": "Gata", "loader.doneFail": "Nu am găsit nimic", "loader.noMatch": "Meciul nu e în sursele mele de cote",
  "app.updating": "Se actualizează aplicația…",
  "team.title": "Meciuri pentru {q}",
  "team.count": "{n} meciuri găsite",
  "team.both": "cu ambele echipe",
  "team.others": "Meciuri cu {team}",
  "team.tap": "Apasă pe un meci pentru analiză.",
  "team.playing": "în desfășurare",
  "nf.title": "Nu am găsit acest meci",
  "nf.body": "„{q}“ nu apare în sursele mele de cote.",
  "nf.scope": "Caut doar în 10 ligi europene (Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie, Primeira Liga, Champions League, Europa League, Championship) plus NBA, Euroleague, NHL și tenis. Liga 1 din România nu e disponibilă în sursa de cote.",
  "nf.try": "Încearcă unul dintre meciurile de mai jos:",
  "alerts.title": "Alerte live",
  "alerts.empty": "Nicio alertă încă. Urmărește un meci (☆) sau pune un pariu ca să primești goluri și cartonașe.",
  "tip.alertBubble": { t: "Alerte", d: "Toate alertele se adună aici (goluri, cartonașe, pariuri închise). Se pot derula dacă sunt mai multe; numărul roșu arată câte sunt necitite." },
  "cache.from": "din cache local", "cache.age": "acum {n} min", "cache.expired": "meciuri expirate curățate",
  "cache.offline": "fără net — date salvate", "cache.refresh": "⟳ Reîmprospătează",
  "cache.clear": "🗑 Golește cache-ul", "cache.cleared": "Cache golit.",
  "matches.sparse": "Puține meciuri în acest interval — apasă „Toate\" pentru lista completă.",
  "limits.footballData": "⚽ Meciurile viitoare de fotbal (PL, Serie A, La Liga, Bundesliga, CL…) vin de la football-data.org, gratuit. Cotele pentru ele apar separat, când le publică casele.",
  "ios.title": "Instalează pe iPhone",
  "ios.body": "Apasă butonul Partajează (pătratul cu săgeată) de jos, apoi alege Adaugă pe ecranul principal. Se va deschide ca o aplicație normală, fără bara Safari.",
  "ios.dismiss": "Am înțeles",
  "tip.touchHint": "Pe telefon: ține apăsat pe un buton ca să vezi ce face; pe carduri e de ajuns un tap.",
  "home.needTwoTeams": "Scrie ambele echipe (ex. Arsenal vs Chelsea) sau alege un meci din listă.",
  "chat.q1": "Care sunt cele mai bune pariuri acum?",
  "chat.q2": "Cum stau cu bugetul?",
  "chat.q3": "Analizează meciul Arsenal vs Chelsea",
  "tip.cacheClear": { t: "Golește cache-ul", d: "Șterge datele păstrate local (meciuri, analize, limite) și pe cele de pe server, ca totul să fie luat proaspăt. Nu consumă cereri suplimentare decât la următoarea căutare." },
});
Object.assign(I18N.de, {
  "loader.working": "Lädt…", "loader.doneOk": "Fertig", "loader.doneFail": "Nichts gefunden", "loader.noMatch": "Spiel nicht in meinen Quotenquellen",
  "app.updating": "Die App wird aktualisiert…",
  "team.title": "Spiele für {q}",
  "team.count": "{n} Spiele gefunden",
  "team.both": "mit beiden Teams",
  "team.others": "Spiele mit {team}",
  "team.tap": "Tippe ein Spiel für die Analyse an.",
  "team.playing": "läuft",
  "nf.title": "Spiel nicht gefunden",
  "nf.body": "„{q}“ ist in meinen Quotenquellen nicht vorhanden.",
  "nf.scope": "Ich suche nur in 10 europäischen Ligen (Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie, Primeira Liga, Champions League, Europa League, Championship) sowie NBA, Euroleague, NHL und Tennis. Die rumänische Liga 1 ist in der Quotenquelle nicht verfügbar.",
  "nf.try": "Versuche eines dieser Spiele:",
  "alerts.title": "Live-Alerts",
  "alerts.empty": "Noch keine Alerts. Beobachte ein Spiel (☆) oder setze eine Wette.",
  "tip.alertBubble": { t: "Alerts", d: "Alle Alerts sammeln sich hier (Tore, Karten, abgerechnete Wetten). Bei mehreren scrollbar; die rote Zahl zeigt ungelesene." },
  "cache.from": "aus dem lokalen Cache", "cache.age": "vor {n} Min.", "cache.expired": "abgelaufene Spiele bereinigt",
  "cache.offline": "offline — gespeicherte Daten", "cache.refresh": "⟳ Neu laden",
  "cache.clear": "🗑 Cache leeren", "cache.cleared": "Cache geleert.",
  "matches.sparse": "Wenige Spiele in diesem Zeitraum — „Alle“ zeigt die volle Liste.",
  "limits.footballData": "⚽ Kommende Fußballspiele (PL, Serie A, La Liga, Bundesliga, CL…) kommen kostenlos von football-data.org. Die Quoten dafür erscheinen später, sobald die Buchmacher sie veröffentlichen.",
  "ios.title": "Auf dem iPhone installieren",
  "ios.body": "Tippe unten auf Teilen (Quadrat mit Pfeil) und wähle dann Zum Home-Bildschirm. Es öffnet sich wie eine normale App.",
  "ios.dismiss": "Verstanden",
  "tip.touchHint": "Am Handy: Halte einen Button gedrückt, um zu sehen, was er macht; auf Karten genügt ein Tipp.",
  "home.needTwoTeams": "Gib beide Teams ein (z. B. Arsenal vs Chelsea) oder wähle ein Spiel aus der Liste.",
  "chat.q1": "Welche Wetten sind gerade am besten?",
  "chat.q2": "Wie steht mein Budget?",
  "chat.q3": "Analysiere das Spiel Arsenal vs Chelsea",
  "tip.cacheClear": { t: "Cache leeren", d: "Löscht lokal gespeicherte Daten (Spiele, Analysen, Limits) und die Server-Caches, damit alles neu geladen wird." },
});
Object.assign(I18N.en, {
  "loader.working": "Loading…", "loader.doneOk": "Done", "loader.doneFail": "Nothing found", "loader.noMatch": "Match not in my odds sources",
  "app.updating": "Updating the app…",
  "team.title": "Matches for {q}",
  "team.count": "{n} matches found",
  "team.both": "with both teams",
  "team.others": "Matches with {team}",
  "team.tap": "Tap a match to analyze it.",
  "team.playing": "in play",
  "nf.title": "Match not found",
  "nf.body": "„{q}“ is not in my odds sources.",
  "nf.scope": "I only cover 10 European leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie, Primeira Liga, Champions League, Europa League, Championship) plus NBA, Euroleague, NHL and tennis. Romanian Liga 1 is not available in the odds source.",
  "nf.try": "Try one of these matches:",
  "alerts.title": "Live alerts",
  "alerts.empty": "No alerts yet. Watch a match (☆) or place a bet to get goals and cards.",
  "tip.alertBubble": { t: "Alerts", d: "Every alert collects here (goals, cards, settled bets). Scrollable when there are several; the red number shows unread ones." },
  "cache.from": "from local cache", "cache.age": "{n} min ago", "cache.expired": "expired matches cleaned",
  "cache.offline": "offline — saved data", "cache.refresh": "⟳ Refresh",
  "cache.clear": "🗑 Clear cache", "cache.cleared": "Cache cleared.",
  "matches.sparse": "Few matches in this window — tap „All\" for the full list.",
  "limits.footballData": "⚽ Upcoming football fixtures (PL, Serie A, La Liga, Bundesliga, CL…) come free from football-data.org. Their odds show up later, once bookmakers publish them.",
  "ios.title": "Install on your iPhone",
  "ios.body": "Tap Share (the square with an arrow) at the bottom, then choose Add to Home Screen. It opens like a normal app, without the Safari bar.",
  "ios.dismiss": "Got it",
  "tip.touchHint": "On a phone: press and hold a button to see what it does; on cards a single tap is enough.",
  "home.needTwoTeams": "Type both teams (e.g. Arsenal vs Chelsea) or pick a match from the list.",
  "chat.q1": "What are the best bets right now?",
  "chat.q2": "How is my budget?",
  "chat.q3": "Analyze the match Arsenal vs Chelsea",
  "tip.cacheClear": { t: "Clear cache", d: "Deletes data stored locally (matches, analyses, limits) plus the server caches, so everything is fetched fresh." },
});

/* Simulation wallet strings (demo money, real results). */
Object.assign(I18N.ro, {
  "nav.mine": "Portofel demo",
  "wallet.title": "Portofel demo",
  "wallet.subtitle": "Bani demo, rezultate reale. Pariez virtual pe meciuri și verific automat rezultatul din sursele reale.",
  "wallet.simulation": "SIMULARE · bani virtuali",
  "wallet.balance": "Sold demo",
  "wallet.currency": "demo",
  "wallet.startedWith": "Ai plecat de la",
  "wallet.profit": "Profit",
  "wallet.roi": "ROI",
  "wallet.winRate": "Rată câștig",
  "wallet.openBets": "Pariuri deschise",
  "wallet.player": "Jucător:",
  "wallet.checkResults": "⟳ Verifică rezultatele",
  "wallet.reset": "↺ Resetează la 100",
  "wallet.checking": "Verific rezultatele reale…",
  "wallet.settledN": "Am închis {n} pariuri cu rezultate reale.",
  "wallet.nothingSettled": "Nicio închidere acum — meciurile din pariuri nu s-au terminat încă.",
  "wallet.noBets": "Niciun pariu încă. Mergi la un meci și pune o miză demo.",
  "wallet.pending": "în așteptare",
  "wallet.won": "câștigat",
  "wallet.lost": "pierdut",
  "wallet.stake": "miză",
  "wallet.cancel": "anulează",
  "wallet.placeTitle": "Pune un pariu (demo)",
  "wallet.place": "Plasează pariul",
  "wallet.pickSide": "Alege un rezultat (1, X sau 2)",
  "wallet.pickStake": "Scrie o miză validă",
  "wallet.selected": "Ales",
  "wallet.recommended": "Recomandarea mea",
  "wallet.draw": "Egal",
  "tip.simBadge": { t: "Simulare", d: "Toate sumele sunt virtuale, bani demo. Rezultatele meciurilor sunt reale, luate din sursele oficiale." },
  "tip.wallet": { t: "Portofel demo", d: "Începi cu 100 demo. Pariezi virtual, rezultatul vine automat din scoruri reale, iar profitul/ROI-ul se calculează pe rezultate reale." },
  "tip.player": { t: "Jucător", d: "Numele portofelului. Fiecare nume are propriii bani demo, ca să nu se amestece pariurile între voi." },
  "tip.checkResults": { t: "Verifică rezultatele", d: "Trage scorurile reale (football-data.org + the-odds-api) și închide pariurile care s-au terminat. Se face și automat, la 30 de minute." },
  "tip.resetWallet": { t: "Resetează", d: "Șterge pariurile acestui jucător și readuce soldul la 100 demo." },
  "tip.betPanel": { t: "Pariu demo", d: "Alege rezultatul, scrie miza (sugestia e ~5% din sold) și plasează. Bani virtuali; rezultatul se închide automat cu scorul real." },
  "tip.stake": { t: "Miză", d: "Cât pariezi din banii demo. Ex.: 5 din 100. Nu poți paria mai mult decât ai." },
  "tip.placeBet": { t: "Plasează", d: "Confirmă pariul virtual. Se scade miza din portofel și așteptăm rezultatul real." },
  "tip.betRow": { t: "Pariul tău", d: "Meciul, ce ai ales, cota și miza. Când meciul se termină, apare scorul real și profitul (verde = câștig, roșu = pierdere)." },
});
Object.assign(I18N.de, {
  "nav.mine": "Meine Wetten",
  "wallet.title": "Demo-Wallet",
  "wallet.subtitle": "Demo-Geld, echte Ergebnisse. Ich wette virtuell und prüfe das Ergebnis automatisch aus echten Quellen.",
  "wallet.simulation": "SIMULATION · virtuelles Geld",
  "wallet.balance": "Guthaben (Demo)",
  "wallet.currency": "Demo",
  "wallet.startedWith": "Start",
  "wallet.profit": "Gewinn",
  "wallet.roi": "ROI",
  "wallet.winRate": "Trefferquote",
  "wallet.openBets": "Offene Wetten",
  "wallet.player": "Spieler:",
  "wallet.checkResults": "⟳ Ergebnisse prüfen",
  "wallet.reset": "↺ Auf 100 zurücksetzen",
  "wallet.checking": "Ich prüfe die echten Ergebnisse…",
  "wallet.settledN": "{n} Wetten mit echten Ergebnissen abgerechnet.",
  "wallet.nothingSettled": "Nichts abzurechnen — die Spiele laufen noch.",
  "wallet.noBets": "Noch keine Wette. Öffne ein Spiel und setze Demo-Geld.",
  "wallet.pending": "offen",
  "wallet.won": "gewonnen",
  "wallet.lost": "verloren",
  "wallet.stake": "Einsatz",
  "wallet.cancel": "stornieren",
  "wallet.placeTitle": "Wette platzieren (Demo)",
  "wallet.place": "Platzieren",
  "wallet.pickSide": "Ergebnis wählen (1, X oder 2)",
  "wallet.pickStake": "Gültigen Einsatz eingeben",
  "wallet.selected": "Gewählt",
  "wallet.recommended": "Mein Vorschlag",
  "wallet.draw": "Unentschieden",
  "tip.simBadge": { t: "Simulation", d: "Alle Beträge sind virtuell (Demo-Geld). Die Spielergebnisse sind echt und kommen aus offiziellen Quellen." },
  "tip.wallet": { t: "Demo-Wallet", d: "Du startest mit 100 Demo. Virtuell wetten, das Ergebnis kommt automatisch aus echten Scores, Gewinn/ROI werden auf echten Ergebnissen berechnet." },
  "tip.player": { t: "Spieler", d: "Name des Wallets. Jeder Name hat eigenes Demo-Guthaben, damit sich Wetten nicht mischen." },
  "tip.checkResults": { t: "Ergebnisse prüfen", d: "Holt echte Ergebnisse (football-data.org + the-odds-api) und rechnet beendete Wetten ab. Passiert auch automatisch alle 30 Minuten." },
  "tip.resetWallet": { t: "Zurücksetzen", d: "Löscht die Wetten dieses Spielers und setzt das Guthaben auf 100 Demo zurück." },
  "tip.betPanel": { t: "Demo-Wette", d: "Ergebnis wählen, Einsatz eingeben (Vorschlag ~5% des Guthabens) und platzieren. Virtuelles Geld; Abrechnung mit echtem Score." },
  "tip.stake": { t: "Einsatz", d: "Wie viel Demo-Geld du setzt. Z. B. 5 von 100. Mehr als das Guthaben geht nicht." },
  "tip.placeBet": { t: "Platzieren", d: "Wette bestätigen. Der Einsatz wird abgezogen, danach wird auf das echte Ergebnis gewartet." },
  "tip.betRow": { t: "Deine Wette", d: "Spiel, Auswahl, Quote und Einsatz. Nach Spielende erscheinen der echte Score und der Gewinn." },
});
Object.assign(I18N.en, {
  "nav.mine": "Demo wallet",
  "wallet.title": "Demo wallet",
  "wallet.subtitle": "Demo money, real results. I bet virtually and check the outcome automatically from real sources.",
  "wallet.simulation": "SIMULATION · virtual money",
  "wallet.balance": "Demo balance",
  "wallet.currency": "demo",
  "wallet.startedWith": "You started with",
  "wallet.profit": "Profit",
  "wallet.roi": "ROI",
  "wallet.winRate": "Win rate",
  "wallet.openBets": "Open bets",
  "wallet.player": "Player:",
  "wallet.checkResults": "⟳ Check results",
  "wallet.reset": "↺ Reset to 100",
  "wallet.checking": "Checking real results…",
  "wallet.settledN": "Settled {n} bets with real results.",
  "wallet.nothingSettled": "Nothing to settle yet — those matches are still running.",
  "wallet.noBets": "No bets yet. Open a match and place a demo stake.",
  "wallet.pending": "open",
  "wallet.won": "won",
  "wallet.lost": "lost",
  "wallet.stake": "stake",
  "wallet.cancel": "cancel",
  "wallet.placeTitle": "Place a bet (demo)",
  "wallet.place": "Place bet",
  "wallet.pickSide": "Pick an outcome (1, X or 2)",
  "wallet.pickStake": "Enter a valid stake",
  "wallet.selected": "Picked",
  "wallet.recommended": "My suggestion",
  "wallet.draw": "Draw",
  "tip.simBadge": { t: "Simulation", d: "All amounts are virtual (demo money). Match results are real, taken from official sources." },
  "tip.wallet": { t: "Demo wallet", d: "You start with 100 demo. Bet virtually, the outcome comes automatically from real scores, and profit/ROI are computed on real results." },
  "tip.player": { t: "Player", d: "Wallet name. Each name has its own demo money, so your bets don't mix." },
  "tip.checkResults": { t: "Check results", d: "Pulls real scores (football-data.org + the-odds-api) and settles finished bets. Also runs automatically every 30 minutes." },
  "tip.resetWallet": { t: "Reset", d: "Deletes this player's bets and puts the balance back to 100 demo." },
  "tip.betPanel": { t: "Demo bet", d: "Pick an outcome, type the stake (suggestion ~5% of balance) and place it. Virtual money; settled with the real score." },
  "tip.stake": { t: "Stake", d: "How much demo money you bet, e.g. 5 out of 100. You can't bet more than you hold." },
  "tip.placeBet": { t: "Place bet", d: "Confirm the virtual bet. The stake is deducted and we wait for the real result." },
  "tip.betRow": { t: "Your bet", d: "The match, your pick, odds and stake. After the match, the real score and profit appear." },
});

/* Live alerts + watchlist strings. */
Object.assign(I18N.ro, {
  "live.title": "LIVE",
  "live.matches": "meciuri",
  "live.waiting": "se actualizează…",
  "live.goal": "GOL",
  "live.card": "Cartonaș",
  "live.event": "Eveniment",
  "live.on": "Alerte pornite",
  "live.off": "Alerte oprite",
  "live.alertsOn": "Alerte pornite: primești goluri, cartonașe și sunet.",
  "live.alertsOff": "Alerte oprite.",
  "live.watch": "Urmărește",
  "live.watched": "Urmărit",
  "live.watchTitle": "Meciuri urmărite (primești alerte la goluri și cartonașe)",
  "live.watchedToast": "Adăugat la urmărite — primești alerte live.",
  "live.unwatched": "Scos din urmărite.",
  "live.remove": "Scoate",
  "live.noWatch": "Niciun meci urmărit. Apasă ☆ pe un meci ca să primești alerte.",
  "live.noEvents": "Niciun eveniment încă.",
  "matches.srcOdds": "cote reale",
  "matches.srcFixtures": "program",
  "limits.refreshOdds": "⟳ Aduc cote proaspete (~15 cereri)",
  "limits.refreshConfirm": "Aduc cote proaspete pentru toate ligile (fotbal, NBA, NHL, tenis)? Consumă ~15 cereri din 500 pe lună.",
  "limits.refreshing": "Aduc cote proaspete… poate dura până la un minut.",
  "limits.refreshed": "Gata: {n} cereri consumate, {left} rămase luna asta.",
  "tip.liveBar": { t: "Meciuri live", d: "Meciurile tale (urmărite sau pe care ai pariat) care se joacă acum, cu scor și minutul, actualizate o dată pe minut." },
  "tip.liveItem": { t: "Scor live", d: "Scorul și minutul vin de la API-Football, la un minut. Se actualizează doar cât timp ai un meci live, ca să nu consumăm degeaba." },
  "tip.alerts": { t: "Alerte", d: "Pornește/oprește alertele: la gol sau cartonaș primești mesaj în aplicație, sunet și vibrație. Dacă permiți notificările, îți apare și pe telefon." },
  "tip.watch": { t: "Urmărește meciul", d: "Pune meciul la urmărite (☆ → ★) ca să primești alerte live la goluri și cartonașe. Pariurile tale sunt urmărite automat." },
  "tip.watchRow": { t: "Meci urmărit", d: "Un meci pentru care primești alerte live. Poți scoate oricând cu ✕." },
  "tip.refreshOdds": { t: "Aduc cote proaspete", d: "Cere cote noi de la the-odds-api pentru toate ligile. Consumă ~15 din cele 500 de cereri lunare — de asta se face doar când apeși tu." },
});
Object.assign(I18N.de, {
  "live.title": "LIVE",
  "live.matches": "Spiele",
  "live.waiting": "wird aktualisiert…",
  "live.goal": "TOR",
  "live.card": "Karte",
  "live.event": "Ereignis",
  "live.on": "Alerts an",
  "live.off": "Alerts aus",
  "live.alertsOn": "Alerts an: Tore, Karten und Ton.",
  "live.alertsOff": "Alerts aus.",
  "live.watch": "Beobachten",
  "live.watched": "Beobachtet",
  "live.watchTitle": "Beobachtete Spiele (Alerts bei Toren und Karten)",
  "live.watchedToast": "Zur Beobachtung hinzugefügt — du bekommst Live-Alerts.",
  "live.unwatched": "Aus der Beobachtung entfernt.",
  "live.remove": "Entfernen",
  "live.noWatch": "Kein Spiel beobachtet. Tippe ☆ auf ein Spiel für Alerts.",
  "live.noEvents": "Noch keine Ereignisse.",
  "matches.srcOdds": "echte Quoten",
  "matches.srcFixtures": "Spielplan",
  "limits.refreshOdds": "⟳ Quoten aktualisieren (~15 Anfragen)",
  "limits.refreshConfirm": "Frische Quoten für alle Ligen laden (Fußball, NBA, NHL, Tennis)? Verbraucht ~15 der 500 monatlichen Anfragen.",
  "limits.refreshing": "Ich lade frische Quoten… kann bis zu einer Minute dauern.",
  "limits.refreshed": "Fertig: {n} Anfragen verbraucht, {left} diesen Monat übrig.",
  "tip.liveBar": { t: "Live-Spiele", d: "Deine Spiele (beobachtet oder mit Wette), die jetzt laufen — Score und Minute, jede Minute aktualisiert." },
  "tip.liveItem": { t: "Live-Score", d: "Score und Minute kommen von API-Football, im Minutentakt. Nur solange ein Spiel läuft, damit nichts unnötig verbraucht wird." },
  "tip.alerts": { t: "Alerts", d: "Alerts ein/aus: bei Tor oder Karte bekommst du Meldung, Ton und Vibration in der App. Mit erlaubten Benachrichtigungen auch am Handy." },
  "tip.watch": { t: "Spiel beobachten", d: "Spiel zur Beobachtung hinzufügen (☆ → ★) für Live-Alerts bei Toren und Karten. Deine Wetten werden automatisch beobachtet." },
  "tip.watchRow": { t: "Beobachtetes Spiel", d: "Ein Spiel, für das du Live-Alerts bekommst. Jederzeit mit ✕ entfernbar." },
  "tip.refreshOdds": { t: "Quoten aktualisieren", d: "Holt neue Quoten von the-odds-api für alle Ligen. Verbraucht ~15 der 500 Monatsanfragen — darum nur auf Knopfdruck." },
});
Object.assign(I18N.en, {
  "live.title": "LIVE",
  "live.matches": "matches",
  "live.waiting": "updating…",
  "live.goal": "GOAL",
  "live.card": "Card",
  "live.event": "Event",
  "live.on": "Alerts on",
  "live.off": "Alerts off",
  "live.alertsOn": "Alerts on: goals, cards and sound.",
  "live.alertsOff": "Alerts off.",
  "live.watch": "Watch",
  "live.watched": "Watching",
  "live.watchTitle": "Watched matches (alerts on goals and cards)",
  "live.watchedToast": "Added to your watchlist — live alerts on.",
  "live.unwatched": "Removed from watchlist.",
  "live.remove": "Remove",
  "live.noWatch": "No watched match yet. Tap ☆ on a match to get alerts.",
  "live.noEvents": "No events yet.",
  "matches.srcOdds": "real odds",
  "matches.srcFixtures": "fixtures",
  "limits.refreshOdds": "⟳ Fetch fresh odds (~15 requests)",
  "limits.refreshConfirm": "Fetch fresh odds for every league (football, NBA, NHL, tennis)? Consumes ~15 of the 500 monthly requests.",
  "limits.refreshing": "Fetching fresh odds… can take up to a minute.",
  "limits.refreshed": "Done: {n} requests used, {left} left this month.",
  "tip.liveBar": { t: "Live matches", d: "Your matches (watched or bet on) that are playing now, with score and minute, updated once a minute." },
  "tip.liveItem": { t: "Live score", d: "Score and minute come from API-Football, minute by minute. Only while a match is live, so nothing is wasted." },
  "tip.alerts": { t: "Alerts", d: "Turn alerts on/off: on a goal or card you get an in-app message, sound and vibration. With notifications allowed, also on your phone." },
  "tip.watch": { t: "Watch this match", d: "Add the match to your watchlist (☆ → ★) to get live goal and card alerts. Your bets are watched automatically." },
  "tip.watchRow": { t: "Watched match", d: "A match you get live alerts for. Remove it any time with ✕." },
  "tip.refreshOdds": { t: "Fetch fresh odds", d: "Asks the-odds-api for new odds across all leagues. Uses ~15 of the 500 monthly requests — that's why it's manual." },
});

/* ---------------------------------------------- report on a settled bet */
Object.assign(I18N.ro, {
  "tip.report": { t: "Raportul meciului", d: "Ce s-a întâmplat în meci: goluri, cartonașe, statistici și de ce s-a încheiat biletul așa. Se descarcă o singură dată per meci, apoi e salvat." },
  "report.title": "Raport meci",
  "report.loading": "Se încarcă raportul…",
  "report.error": "Nu am putut încărca raportul.",
  "report.match": "Meciul",
  "report.askMiki": "Întreabă-l pe Miki",
  "report.mikiAsk": "Explică-mi de ce biletul „{event}” ({outcome}) s-a încheiat așa și ce pot îmbunătăți la următorul.\n\nDate din raportul meciului:\n{details}",
  "report.won": "Bilet câștigat",
  "report.lost": "Bilet pierdut",
  "report.open": "Bilet în așteptare",
  "report.kickoff": "Start",
  "report.ended": "Final",
  "report.minute": "Minutul",
  "report.stoppage": "Prelungire",
  "report.league": "Competiție",
  "report.round": "Etapă",
  "report.venue": "Stadion",
  "report.referee": "Arbitru",
  "report.goals": "Goluri",
  "report.cards": "Cartonașe",
  "report.stats": "Statistici meci",
  "report.noEvents": "Fără evenimente înregistrate.",
  "report.why": "De ce s-a terminat așa",
  "report.improve": "Ce poți îmbunătăți",
  "report.noImprove": "Procesul a fost bun — nu am ce să-ți reproșez la biletul ăsta.",
  "report.mModel": "Modelul meu",
  "report.mMarket": "Piața",
  "report.mImplied": "Cota implică",
  "report.mEdge": "Avantaj",
  "report.mClv": "CLV",
  "report.mOdds": "Cota ta",
  "report.mSharp": "Cotă sharp",
  "report.source": "Sursă",
  "report.sourceStored": "scorul salvat",
  "report.nonFootball": "Pentru acest sport (non-fotbal) îți arăt doar scorul și analiza biletului, fără goluri și cartonașe.",
  "report.notFound": "Nu am detaliile meciului din sursa gratuită. Îți arăt scorul salvat și analiza biletului.",
  "report.assist": "pasă",
  "report.ownGoal": "autogol",
  "report.penalty": "penalty",
  "report.yellow": "galben",
  "report.red": "roșu",
  "report.v.won": "Bilet câștigat — analiza și rezultatul au fost în acord.",
  "report.v.won_lucky": "Câștigat, dar cu noroc: adversarul a dominat meciul.",
  "report.v.lost_bad_beat": "Pierdut la ghinion — echipa ta a dominat clar.",
  "report.v.lost_narrow": "Pierdut la limită (un gol diferență).",
  "report.v.lost_outplayed": "Pierdut pe merit — echipa ta a fost dominată.",
  "report.v.lost_upset": "Surpriză — favorita (peste 50%) nu a câștigat.",
  "report.v.lost": "Pierdut.",
  "report.f.low_edge": "Avantajul a fost mic (sub 3%). Alege bilete doar când avantajul real e mai mare.",
  "report.f.negative_clv": "Cota ta a fost mai slabă decât cota de închidere — ai pierdut valoare înainte de start.",
  "report.f.against_sharp": "Piața sharp era mult mai pesimistă decât cota ta.",
  "report.f.model_vs_market": "Modelul era mult mai optimist decât piața (peste 12 puncte) — verifică datele de intrare.",
  "report.f.few_chances": "Echipa aleasă a avut foarte puține șuturi pe poartă.",
  "report.f.many_cards": "Meci cu multe cartonașe — joc încâlcit, greu de prevăzut.",
  "report.r.dominated_but_lost": "A dominat (mai multe șuturi pe poartă) dar a pierdut — ghinion, nu eroare de analiză.",
  "report.r.outplayed": "A fost dominată de adversar.",
  "report.r.draw_killed": "Egalul a omorât biletul.",
  "report.r.beat_closing": "Ai bătut piața (CLV pozitiv) — procesul a fost bun, chiar dacă rezultatul nu a ținut.",
  "report.r.worse_than_closing": "Cota ta a fost mai slabă decât închiderea — de revizuit momentul plasării.",
  "report.stat.poss": "Posesie",
  "report.stat.shots": "Șuturi",
  "report.stat.sot": "Șuturi pe poartă",
  "report.stat.soff": "Șuturi pe lângă",
  "report.stat.blocked": "Șuturi blocate",
  "report.stat.inside": "Șuturi în careu",
  "report.stat.outside": "Șuturi din afara careului",
  "report.stat.corners": "Cornere",
  "report.stat.offside": "Offside",
  "report.stat.fouls": "Faulturi",
  "report.stat.yellow": "Cartonașe galbene",
  "report.stat.red": "Cartonașe roșii",
  "report.stat.saves": "Parade portar",
  "report.stat.passes": "Pase",
  "report.stat.passesAcc": "Pase reușite",
  "report.stat.passPct": "Precizia paselor",
});
Object.assign(I18N.de, {
  "tip.report": { t: "Spielbericht", d: "Was im Spiel passiert ist: Tore, Karten, Statistiken und warum die Wette so ausging. Wird einmal pro Spiel geladen und dann gespeichert." },
  "report.title": "Spielbericht",
  "report.loading": "Bericht wird geladen…",
  "report.error": "Der Bericht konnte nicht geladen werden.",
  "report.match": "Spiel",
  "report.askMiki": "Miki fragen",
  "report.mikiAsk": "Erklär mir, warum die Wette „{event}“ ({outcome}) so ausging und was ich beim nächsten Tipp besser machen kann.\n\nDaten aus dem Spielbericht:\n{details}",
  "report.won": "Wette gewonnen",
  "report.lost": "Wette verloren",
  "report.open": "Wette offen",
  "report.kickoff": "Anpfiff",
  "report.ended": "Ende",
  "report.minute": "Minute",
  "report.stoppage": "Nachspielzeit",
  "report.league": "Wettbewerb",
  "report.round": "Spieltag",
  "report.venue": "Stadion",
  "report.referee": "Schiedsrichter",
  "report.goals": "Tore",
  "report.cards": "Karten",
  "report.stats": "Spielstatistik",
  "report.noEvents": "Keine Ereignisse erfasst.",
  "report.why": "Warum es so ausging",
  "report.improve": "Was du verbessern kannst",
  "report.noImprove": "Der Prozess war gut — an dieser Wette gibt es nichts auszusetzen.",
  "report.mModel": "Mein Modell",
  "report.mMarket": "Markt",
  "report.mImplied": "Quote impliziert",
  "report.mEdge": "Vorteil",
  "report.mClv": "CLV",
  "report.mOdds": "Deine Quote",
  "report.mSharp": "Sharp-Quote",
  "report.source": "Quelle",
  "report.sourceStored": "gespeicherter Stand",
  "report.nonFootball": "Für diese Sportart (kein Fußball) zeige ich nur Ergebnis und Wettanalyse, ohne Tore und Karten.",
  "report.notFound": "Ich habe die Spieldetails nicht in der kostenlosen Quelle gefunden. Ich zeige das gespeicherte Ergebnis und die Wettanalyse.",
  "report.assist": "Vorlage",
  "report.ownGoal": "Eigentor",
  "report.penalty": "Elfmeter",
  "report.yellow": "Gelb",
  "report.red": "Rot",
  "report.v.won": "Gewonnen — Analyse und Ergebnis waren im Einklang.",
  "report.v.won_lucky": "Gewonnen, aber mit Glück: Der Gegner war überlegen.",
  "report.v.lost_bad_beat": "Unglücklich verloren — dein Team war klar überlegen.",
  "report.v.lost_narrow": "Knapp verloren (ein Tor Unterschied).",
  "report.v.lost_outplayed": "Verdient verloren — dein Team war unterlegen.",
  "report.v.lost_upset": "Überraschung — der Favorit (über 50 %) hat nicht gewonnen.",
  "report.v.lost": "Verloren.",
  "report.f.low_edge": "Der Vorteil war klein (unter 3 %). Nimm nur Wetten, wenn der echte Vorteil größer ist.",
  "report.f.negative_clv": "Deine Quote war schlechter als die Schlussquote — du hast vor dem Anpfiff Wert verloren.",
  "report.f.against_sharp": "Der Sharp-Markt war deutlich pessimistischer als deine Quote.",
  "report.f.model_vs_market": "Das Modell war viel optimistischer als der Markt (über 12 Punkte) — prüfe deine Eingaben.",
  "report.f.few_chances": "Das gewählte Team hatte sehr wenige Schüsse aufs Tor.",
  "report.f.many_cards": "Ein Spiel mit vielen Karten — zerfahren, schwer vorherzusagen.",
  "report.r.dominated_but_lost": "Überlegen (mehr Schüsse aufs Tor), aber verloren — Pech, kein Analysefehler.",
  "report.r.outplayed": "Wurde vom Gegner dominiert.",
  "report.r.draw_killed": "Das Unentschieden hat die Wette zerstört.",
  "report.r.beat_closing": "Du hast den Markt geschlagen (positives CLV) — der Prozess war gut, auch wenn das Ergebnis nicht hielt.",
  "report.r.worse_than_closing": "Deine Quote war schlechter als die Schlussquote — prüfe den Zeitpunkt der Platzierung.",
  "report.stat.poss": "Ballbesitz",
  "report.stat.shots": "Schüsse",
  "report.stat.sot": "Schüsse aufs Tor",
  "report.stat.soff": "Schüsse daneben",
  "report.stat.blocked": "Geblockte Schüsse",
  "report.stat.inside": "Schüsse im Strafraum",
  "report.stat.outside": "Schüsse außerhalb",
  "report.stat.corners": "Ecken",
  "report.stat.offside": "Abseits",
  "report.stat.fouls": "Fouls",
  "report.stat.yellow": "Gelbe Karten",
  "report.stat.red": "Rote Karten",
  "report.stat.saves": "Paraden",
  "report.stat.passes": "Pässe",
  "report.stat.passesAcc": "Angekommene Pässe",
  "report.stat.passPct": "Passgenauigkeit",
});
Object.assign(I18N.en, {
  "tip.report": { t: "Match report", d: "What happened in the match: goals, cards, stats and why the bet ended that way. Downloaded once per match, then cached." },
  "report.title": "Match report",
  "report.loading": "Loading report…",
  "report.error": "Could not load the report.",
  "report.match": "The match",
  "report.askMiki": "Ask Miki",
  "report.mikiAsk": "Explain why the bet \"{event}\" ({outcome}) ended that way and what I can improve on the next ticket.\n\nData from the match report:\n{details}",
  "report.won": "Bet won",
  "report.lost": "Bet lost",
  "report.open": "Bet pending",
  "report.kickoff": "Kick-off",
  "report.ended": "End",
  "report.minute": "Minute",
  "report.stoppage": "Stoppage",
  "report.league": "Competition",
  "report.round": "Round",
  "report.venue": "Venue",
  "report.referee": "Referee",
  "report.goals": "Goals",
  "report.cards": "Cards",
  "report.stats": "Match stats",
  "report.noEvents": "No events recorded.",
  "report.why": "Why it ended this way",
  "report.improve": "What you can improve",
  "report.noImprove": "The process was sound — nothing to fault on this bet.",
  "report.mModel": "My model",
  "report.mMarket": "Market",
  "report.mImplied": "Odds imply",
  "report.mEdge": "Edge",
  "report.mClv": "CLV",
  "report.mOdds": "Your odds",
  "report.mSharp": "Sharp odds",
  "report.source": "Source",
  "report.sourceStored": "stored score",
  "report.nonFootball": "For this sport (non-football) I can only show the score and the bet analysis, without goals and cards.",
  "report.notFound": "I could not find the match details in the free source. Here is the stored score and the bet analysis.",
  "report.assist": "assist",
  "report.ownGoal": "own goal",
  "report.penalty": "penalty",
  "report.yellow": "yellow",
  "report.red": "red",
  "report.v.won": "Won — analysis and result were aligned.",
  "report.v.won_lucky": "Won, but lucky: the opponent dominated.",
  "report.v.lost_bad_beat": "Unlucky loss — your team clearly dominated.",
  "report.v.lost_narrow": "Narrow loss (one goal in it).",
  "report.v.lost_outplayed": "Deserved loss — your team was outplayed.",
  "report.v.lost_upset": "Upset — the favourite (over 50%) did not win.",
  "report.v.lost": "Lost.",
  "report.f.low_edge": "The edge was small (under 3%). Only take bets when the real edge is bigger.",
  "report.f.negative_clv": "Your odds were worse than the closing price — you lost value before kick-off.",
  "report.f.against_sharp": "The sharp market was far more pessimistic than your odds.",
  "report.f.model_vs_market": "The model was far more optimistic than the market (over 12 points) — check your inputs.",
  "report.f.few_chances": "The chosen team had very few shots on target.",
  "report.f.many_cards": "A match with many cards — scrappy, hard to predict.",
  "report.r.dominated_but_lost": "Dominated (more shots on target) but lost — bad luck, not a bad read.",
  "report.r.outplayed": "Was outplayed by the opponent.",
  "report.r.draw_killed": "The draw killed the bet.",
  "report.r.beat_closing": "You beat the market (positive CLV) — the process was good even if the result did not hold.",
  "report.r.worse_than_closing": "Your odds were worse than closing — review when you placed it.",
  "report.stat.poss": "Possession",
  "report.stat.shots": "Shots",
  "report.stat.sot": "Shots on target",
  "report.stat.soff": "Shots off target",
  "report.stat.blocked": "Blocked shots",
  "report.stat.inside": "Shots inside box",
  "report.stat.outside": "Shots outside box",
  "report.stat.corners": "Corners",
  "report.stat.offside": "Offsides",
  "report.stat.fouls": "Fouls",
  "report.stat.yellow": "Yellow cards",
  "report.stat.red": "Red cards",
  "report.stat.saves": "Goalkeeper saves",
  "report.stat.passes": "Passes",
  "report.stat.passesAcc": "Accurate passes",
  "report.stat.passPct": "Pass accuracy",
});
Object.assign(I18N.ro, { "report.score": "Scor", "report.ht": "prima repriză" });
Object.assign(I18N.de, { "report.score": "Ergebnis", "report.ht": "1. Halbzeit" });
Object.assign(I18N.en, { "report.score": "Score", "report.ht": "first half" });

// match status on the fixtures card (finished games stay listed so you can still analyse them)
Object.assign(I18N.ro, { "match.live": "LIVE", "match.finished": "încheiat" });
Object.assign(I18N.de, { "match.live": "LIVE", "match.finished": "beendet" });
Object.assign(I18N.en, { "match.live": "LIVE", "match.finished": "finished" });

Object.assign(I18N.ro, {
  "limits.remaining": "rămase: <b>{n}</b> / {lim}",
  "limits.limitMonth": "limita: <b>{lim}</b> pe lună",
  "limits.limitDay": "limita: <b>{lim}</b> pe zi",
  "limits.limitMinute": "ritm: <b>{lim}</b> pe minut",
  "limits.noDaily": "fără limită zilnică",
  "limits.renewsIn": "se reînnoiește în {x}",
  "limits.level.green": "OK", "limits.level.yellow": "aproape", "limits.level.red": "epuizat", "limits.level.unknown": "necunoscut",
  "cache.local": "local", "cache.server": "server", "cache.events": "meciuri", "cache.upcoming": "viitoare",
  "sport.soccer": "Fotbal", "sport.basketball": "Baschet", "sport.tennis": "Tenis",
  "sport.mma": "MMA", "sport.boxing": "Box", "sport.icehockey": "Hochei",
  "sport.americanfootball": "Fotbal american", "sport.baseball": "Baseball",
  "sport.rugbyleague": "Rugby", "sport.cricket": "Cricket",
  "sport.aussierules": "Football australian", "sport.lacrosse": "Lacrosse", "sport.other": "Altele",
});
Object.assign(I18N.de, {
  "limits.remaining": "übrig: <b>{n}</b> / {lim}",
  "limits.limitMonth": "Limit: <b>{lim}</b> pro Monat",
  "limits.limitDay": "Limit: <b>{lim}</b> pro Tag",
  "limits.limitMinute": "Tempo: <b>{lim}</b> pro Minute",
  "limits.noDaily": "kein Tageslimit",
  "limits.renewsIn": "erneuert sich in {x}",
  "limits.level.green": "OK", "limits.level.yellow": "knapp", "limits.level.red": "erschöpft", "limits.level.unknown": "unbekannt",
  "cache.local": "lokal", "cache.server": "Server", "cache.events": "Spiele", "cache.upcoming": "kommend",
  "sport.soccer": "Fußball", "sport.basketball": "Basketball", "sport.tennis": "Tennis",
  "sport.mma": "MMA", "sport.boxing": "Boxen", "sport.icehockey": "Eishockey",
  "sport.americanfootball": "American Football", "sport.baseball": "Baseball",
  "sport.rugbyleague": "Rugby League", "sport.cricket": "Cricket",
  "sport.aussierules": "Australian Football", "sport.lacrosse": "Lacrosse", "sport.other": "Sonstiges",
});
Object.assign(I18N.en, {
  "limits.remaining": "remaining: <b>{n}</b> / {lim}",
  "limits.limitMonth": "limit: <b>{lim}</b> per month",
  "limits.limitDay": "limit: <b>{lim}</b> per day",
  "limits.limitMinute": "pace: <b>{lim}</b> per minute",
  "limits.noDaily": "no daily limit",
  "limits.renewsIn": "renews in {x}",
  "limits.level.green": "OK", "limits.level.yellow": "close", "limits.level.red": "exhausted", "limits.level.unknown": "unknown",
  "cache.local": "local", "cache.server": "server", "cache.events": "matches", "cache.upcoming": "upcoming",
  "sport.soccer": "Soccer", "sport.basketball": "Basketball", "sport.tennis": "Tennis",
  "sport.mma": "MMA", "sport.boxing": "Boxing", "sport.icehockey": "Ice hockey",
  "sport.americanfootball": "American football", "sport.baseball": "Baseball",
  "sport.rugbyleague": "Rugby league", "sport.cricket": "Cricket",
  "sport.aussierules": "Australian rules", "sport.lacrosse": "Lacrosse", "sport.other": "Other",
});

/* --------------------------------------------------------------- utilities */
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));
let lang = localStorage.getItem("mb_lang") || "ro";
const LANG_LABEL = { ro: "RO", de: "DE", en: "EN" };

function t(key, vars) {
  const entry = (I18N[lang] && I18N[lang][key]) || (I18N.ro && I18N.ro[key]) || key;
  if (entry && typeof entry === "object") return entry.t;
  let text = String(entry);
  if (vars) for (const k in vars) text = text.replaceAll("{" + k + "}", vars[k]);
  return text;
}
function tipOf(key) {
  const entry = (I18N[lang] && I18N[lang][key]) || (I18N.ro && I18N.ro[key]);
  if (entry && typeof entry === "object") return entry;
  return { t: t(key), d: "" };
}
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
/* Chat renderer: markdown tables, the ##green:32%## colour tags produced by the
   backend, <<winner>> highlighting and the [VERDICT] thumbs widget.
   Order matters: the raw text is escaped first, then only our own whitelisted
   tags are turned into HTML. Never inject model HTML directly. */
function inlineMd(raw) {
  let s = esc(raw);
  s = s.replace(/##(green|red|yellow|blue):(.+?)##/g, (m, c, v) => `<span class="pct pct-${c}">${v}</span>`);
  s = s.replace(/&lt;&lt;(.+?)&gt;&gt;/g, '<span class="winner">$1</span>');
  s = s.replace(/__(.+?)__/g, '<strong class="hl">$1</strong>');
  s = s.replace(/(^|[^_])_([^_\n]+)_(?!_)/g, "$1<em>$2</em>");
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>");
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  return s;
}
function mdCells(line) {
  return line.replace(/^\s*\|/, "").replace(/\|\s*$/, "").split("|").map((c) => inlineMd(c.trim()));
}
function mdToHtml(md) {
  const lines = String(md == null ? "" : md).replace(/\r/g, "").split("\n");
  let html = "", inList = false;
  const closeList = () => { if (inList) { html += "</ul>"; inList = false; } };
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const next = lines[i + 1];
    if (!line.trim()) { closeList(); continue; }
    if (line.includes("|") && next && /^\s*\|?[\s:|-]+\|?\s*$/.test(next) && next.includes("-")) {
      closeList();
      const head = mdCells(line);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        rows.push(mdCells(lines[i]));
        i++;
      }
      i--;
      html += `<div class="md-table-wrap"><table class="md-table"><thead><tr>${head.map((c) => `<th>${c}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
      continue;
    }
    const h = line.match(/^(#{1,4})\s+(.+)$/);
    if (h) { closeList(); html += `<h${h[1].length}>${inlineMd(h[2])}</h${h[1].length}>`; continue; }
    if (/^\s*[-*]\s+/.test(line)) {
      if (!inList) { html += "<ul>"; inList = true; }
      html += `<li>${inlineMd(line.replace(/^\s*[-*]\s+/, ""))}</li>`;
      continue;
    }
    if (/^\s*([-*_])\1{2,}\s*$/.test(line)) { closeList(); html += "<hr>"; continue; }
    closeList();
    html += `<p>${inlineMd(line)}</p>`;
  }
  closeList();
  return html;
}
function renderVerdict(v) {
  const raw = Number(v && v.win_pct);
  if (!isFinite(raw)) return "";
  const win = Math.max(0, Math.min(100, raw));
  const lose = 100 - win;
  const winTop = win >= lose;
  const side = esc((v && v.side) || "");
  const event = esc((v && v.event) || "");
  return `<div class="verdict">
    <div class="verdict-title">${esc(t("chat.verdict"))}</div>
    <div class="verdict-cards">
      <div class="v-card v-win ${winTop ? "top" : ""}">
        <div class="v-emoji">👍</div><div class="v-pct" data-val="${win}">0%</div>
        <div class="v-label">${esc(t("chat.win"))}</div>
      </div>
      <div class="v-card v-lose ${winTop ? "" : "top"}">
        <div class="v-emoji">👎</div><div class="v-pct" data-val="${lose}">0%</div>
        <div class="v-label">${esc(t("chat.lose"))}</div>
      </div>
    </div>
    <div class="v-note">${side}${event ? " · " + event : ""}</div>
  </div>`;
}
function animatePct(el) {
  const target = Math.max(0, Math.min(100, parseFloat(el.dataset.val) || 0));
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    el.textContent = Math.round(target) + "%";
    return;
  }
  let cur = 0;
  const step = Math.max(1, target / 30);
  const timer = setInterval(() => {
    cur = Math.min(target, cur + step);
    el.textContent = Math.round(cur) + "%";
    if (cur >= target) clearInterval(timer);
  }, 30);
}
function renderReply(text) {
  const raw = String(text == null ? "" : text);
  const m = raw.match(/\[VERDICT\]\s*(\{[\s\S]*\})\s*$/);
  let verdict = null;
  let body = raw;
  if (m) {
    try { verdict = JSON.parse(m[1]); } catch (err) { console.warn("VERDICT parse failed", err); }
    body = raw.replace(m[0], "");
  }
  if (!verdict) {
    const marker = body.indexOf("[VERDICT]");
    if (marker !== -1) body = body.slice(0, marker);
  }
  return mdToHtml(body.trim()) + (verdict ? renderVerdict(verdict) : "");
}
const LANG_LOCALE = { ro: "ro-RO", de: "de-DE", en: "en-GB" };
function localeOf() { return LANG_LOCALE[lang] || "ro-RO"; }
function sportLabel(g) {
  if (!g) return "";
  const key = "sport." + g;
  const val = t(key);
  return val === key ? String(g) : val;
}
function leagueLabel(m) {
  const lg = (m && m.league) || "";
  const sp = sportLabel(m && m.sport);
  if (!lg) return sp;
  const raw = String(lg).toLowerCase();
  if (["soccer", "basketball", "tennis", "mma", "boxing", "icehockey"].includes(raw)) return sportLabel(raw);
  return lg;
}
function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  const today = new Date(), tom = new Date(Date.now() + 864e5);
  const same = (a, b) => a.toDateString() === b.toDateString();
  const hm = d.toLocaleTimeString(localeOf(), { hour: "2-digit", minute: "2-digit" });
  if (same(d, today)) return hm;
  if (same(d, tom)) return t("matches.tomorrow") + " " + hm;
  return d.toLocaleDateString(localeOf(), { day: "2-digit", month: "2-digit" }) + " " + hm;
}
function sideLabel(vb) {
  if (vb.side === "draw") return "X";
  return vb.side === "home" ? vb.home_team : vb.away_team;
}
function toast(msg, ms, big) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.toggle("big", !!big);
  el.classList.remove("hidden");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add("hidden"), ms || 4200);
}

/* --------------------------------------------------------------- tooltips */
/* Mouse: hover. Touch: a single tap for info cards, LONG-PRESS for buttons
   (so a tap never both opens an explanation and triggers the action). */
const TT = $("#tooltip");
const TIP_LONGPRESS_MS = 500;
let tipAnchor = null, pressTimer = null, pressStart = null, suppressClick = false;

function tipTarget(node) { return node && node.closest ? node.closest("[data-tip]") : null; }
function isInteractiveEl(el) {
  if (!el) return false;
  if (el.matches && el.matches("button, a, input, select, textarea, [role='button']")) return true;
  return el.getAttribute("data-clickable") === "1";
}
function showTip(anchor, ev) {
  const key = anchor.getAttribute("data-tip");
  if (!key) return null;
  const info = tipOf(key);
  TT.innerHTML = `<span class="tt-title">${esc(info.t)}</span>${esc(info.d)}`;
  TT.classList.remove("hidden");
  positionTip(anchor, ev);
  return key;
}
function positionTip(anchor, ev) {
  const pad = 10;
  let x, y;
  if (ev && ev.touches && ev.touches[0]) { x = ev.touches[0].clientX; y = ev.touches[0].clientY; }
  else if (ev && ev.clientX) { x = ev.clientX; y = ev.clientY; }
  else { const r = anchor.getBoundingClientRect(); x = r.left + r.width / 2; y = r.bottom + 4; }
  const w = TT.offsetWidth || 260, h = TT.offsetHeight || 70;
  x = Math.min(Math.max(pad, x - w / 2), Math.max(pad, window.innerWidth - w - pad));
  y = Math.min(Math.max(pad, y + 14), Math.max(pad, window.innerHeight - h - pad));
  TT.style.left = x + "px";
  TT.style.top = y + "px";
}
function hideTip() { TT.classList.add("hidden"); tipAnchor = null; }

document.addEventListener("pointerover", (e) => {
  if (e.pointerType !== "mouse") return;
  const el = tipTarget(e.target);
  if (el) showTip(el, e);
});
document.addEventListener("pointerout", (e) => {
  if (e.pointerType !== "mouse") return;
  if (tipTarget(e.target)) TT.classList.add("hidden");
});
document.addEventListener("pointerdown", (e) => {
  const el = tipTarget(e.target);
  if (!el) { hideTip(); return; }
  if (e.pointerType === "mouse") return; // mouse users already have hover
  // info cards: tap shows the explanation (tap again hides it)
  if (el.getAttribute("data-tip-mode") === "tap" || !isInteractiveEl(el)) {
    if (tipAnchor === el) { hideTip(); return; }
    tipAnchor = el;
    showTip(el, e);
    return;
  }
  // interactive elements: long-press, so a normal tap keeps doing its job
  pressStart = { x: e.clientX, y: e.clientY, el };
  clearTimeout(pressTimer);
  pressTimer = setTimeout(() => {
    if (!pressStart) return;
    suppressClick = true;
    tipAnchor = pressStart.el;
    showTip(pressStart.el, { clientX: pressStart.x, clientY: pressStart.y });
    pressStart = null;
  }, TIP_LONGPRESS_MS);
});
document.addEventListener("pointermove", (e) => {
  if (!pressStart) return;
  if (Math.abs(e.clientX - pressStart.x) > 12 || Math.abs(e.clientY - pressStart.y) > 12) {
    clearTimeout(pressTimer);
    pressStart = null;
  }
});
function endPress() { clearTimeout(pressTimer); pressStart = null; }
document.addEventListener("pointerup", endPress);
document.addEventListener("pointercancel", endPress);
// after a long-press explainer, swallow the click so the action does not fire by accident
document.addEventListener("click", (e) => {
  if (suppressClick) { suppressClick = false; e.stopPropagation(); e.preventDefault(); }
}, true);
document.addEventListener("scroll", hideTip, true);

function maybeShowTouchHint() {
  const touch = (window.matchMedia && window.matchMedia("(hover: none)").matches) || "ontouchstart" in window;
  if (!touch || localStorage.getItem("mb_touch_hint") === "1") return;
  localStorage.setItem("mb_touch_hint", "1");
  setTimeout(() => toast(t("tip.touchHint")), 1600);
}

/* ------------------------------------------------------------------- i18n */
function applyI18n() {
  document.documentElement.lang = lang;
  $$("[data-i18n]").forEach((el) => { el.textContent = t(el.getAttribute("data-i18n")); });
  $$("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.getAttribute("data-i18n-ph")); });
  $("#langLabel").textContent = LANG_LABEL[lang] || "RO";
  renderLimitsPill();
}
function setLang(l) {
  if (!I18N[l]) l = "ro";
  lang = l;
  localStorage.setItem("mb_lang", l);
  $("#langMenu").classList.add("hidden");
  applyI18n();
  // Dynamic sections are built from t() at render time, so they must be
  // rebuilt too; otherwise German labels stay Romanian until a page reload.
  if (LAST_FIXTURES.length) loadFixtures();
  renderChatChips();
  maybeShowIosBanner();
  if (LAST_REPORT && !$("#reportOverlay").classList.contains("hidden")) renderReport(LAST_REPORT);
  if (LAST_ANALYSIS_ARGS) {
    runAnalysis(LAST_ANALYSIS_ARGS.home, LAST_ANALYSIS_ARGS.away,
      LAST_ANALYSIS_ARGS.eventId, LAST_ANALYSIS_ARGS.commenceTime);
  }
  loadWallet();
  loadBets();
  loadWatch();
  if (!$("#limitsOverlay").classList.contains("hidden")) { renderLimitsBody(); renderCacheInfo(); }
  fetchLimits(false);
}

/* ------------------------------------------------------------------ theme */
function applyTheme(th) {
  document.documentElement.setAttribute("data-theme", th);
  $("#themeBtn").textContent = th === "dark" ? "🌙" : "☀️";
  $("#themeBtn").setAttribute("data-theme-state", th);
  localStorage.setItem("mb_theme", th);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", th === "dark" ? "#1a1220" : "#fdf8f3");
}

/* ------------------------------------------------------------------ api */
/* Local cache (client side): repeated searches must not hit the server again.
   Entries expire by TTL; finished matches are pruned as they go. */
const CACHE_PREFIX = "mb_cache_v6:"; // bump this whenever the payload shape changes -> old client caches invalidate
const CACHE_TTL = { fixtures: 600, analyze: 1800, config: 43200, limits: 120, stats: 30, bets: 15 };
function ttlFor(path) {
  if (path.startsWith("/api/fixtures")) return CACHE_TTL.fixtures;
  if (path.startsWith("/api/analyze")) return CACHE_TTL.analyze;
  if (path.startsWith("/api/config")) return CACHE_TTL.config;
  if (path.startsWith("/api/limits")) return CACHE_TTL.limits;
  if (path.startsWith("/api/stats")) return CACHE_TTL.stats;
  if (path.startsWith("/api/bets")) return CACHE_TTL.bets;
  return 0; // chat / recommend / cache-status are never cached
}
function cacheKeyOf(path, opts) {
  const body = opts && opts.body ? String(opts.body) : "";
  return CACHE_PREFIX + path + (body ? "|" + body : "");
}
function cacheGet(key) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const e = JSON.parse(raw);
    if (!e || typeof e.ts !== "number") return null;
    return { data: e.data, age: (Date.now() - e.ts) / 1000 };
  } catch (err) { return null; }
}
function cacheSet(key, data) {
  try {
    localStorage.setItem(key, JSON.stringify({ ts: Date.now(), data }));
  } catch (err) {
    cachePrune(true); // out of space -> drop the oldest entries and retry once
    try { localStorage.setItem(key, JSON.stringify({ ts: Date.now(), data })); } catch (e2) { /* give up quietly */ }
  }
}
function isPast(iso) { const d = new Date(iso); return !isNaN(d) && d.getTime() < Date.now(); }
// expected running time per sport (minutes) — mirrors backend/microbist.py GROUP_DURATION_MIN
const MATCH_DURATION_MIN = { soccer: 115, basketball: 160, icehockey: 160, tennis: 240, mma: 190, boxing: 190, americanfootball: 210, baseball: 200, handball: 130 };
// keep a server-known "finished" as-is; otherwise derive upcoming/live/finished from the clock,
// so a payload served from the 10-minute cache still labels matches correctly as time passes
function refreshMatchStatus(m) {
  if (!m || m.status === "finished") return m;
  const ct = m.commence_time ? new Date(m.commence_time).getTime() : null;
  if (ct == null || isNaN(ct)) return m;
  const dur = (MATCH_DURATION_MIN[m.sport] || 160) * 60000;
  const now = Date.now();
  if (now >= ct + dur) m.status = "finished";
  else if (now >= ct) m.status = "live";
  else m.status = "upcoming";
  return m;
}
function sortFixtures(items) {
  const rank = { live: 0, upcoming: 1, finished: 2 };
  const key = (it) => (rank[it.status] != null ? rank[it.status] : 1);
  return items.slice().sort((a, b) => {
    const d = key(a) - key(b);
    if (d) return d;
    const ta = a.commence_time || "", tb = b.commence_time || "";
    return a.status === "finished" ? (ta < tb ? 1 : ta > tb ? -1 : 0) : (ta < tb ? -1 : ta > tb ? 1 : 0);
  });
}
function pruneFixturePayload(data) {
  if (!data || !Array.isArray(data.items)) return data;
  const before = data.items.length;
  // drop only what is well in the past (the server already trims at -3h); keep recent
  // finished matches so their badge + score stay visible
  const cutoff = Date.now() - 6 * 3600 * 1000;
  data.items = sortFixtures(data.items
    .filter((it) => { const t = it.commence_time ? new Date(it.commence_time).getTime() : NaN; return isNaN(t) || t > cutoff; })
    .map(refreshMatchStatus));
  data.count = data.items.length;
  if (before !== data.items.length) data.pruned_past = before - data.items.length;
  return data;
}
function cachePrune(hard) {
  const now = Date.now();
  const keys = [];
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k && k.startsWith(CACHE_PREFIX)) keys.push(k);
  }
  keys.forEach((k) => {
    const hit = cacheGet(k);
    const tooOld = !hit || (now - (now - hit.age * 1000)) > 24 * 3600 * 1000 || hit.age > 24 * 3600;
    if (tooOld) { localStorage.removeItem(k); return; }
    if (k.startsWith(CACHE_PREFIX + "/api/fixtures") && hit.data && Array.isArray(hit.data.items)) {
      const left = pruneFixturePayload(hit.data).items.length;
      if (!left) localStorage.removeItem(k);
      else if (hard) localStorage.setItem(k, JSON.stringify({ ts: Date.now() - hit.age * 1000, data: hit.data }));
    }
  });
}
function clearLocalCache() {
  const keys = [];
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k && k.startsWith(CACHE_PREFIX)) keys.push(k);
  }
  keys.forEach((k) => localStorage.removeItem(k));
  return keys.length;
}
async function api(path, opts, cfg) {
  cfg = cfg || {};
  const ttl = cfg.ttl != null ? cfg.ttl : ttlFor(path);
  const key = cacheKeyOf(path, opts);
  if (ttl > 0 && !cfg.force) {
    const hit = cacheGet(key);
    if (hit && hit.age <= ttl) {
      let data = hit.data;
      if (path.startsWith("/api/fixtures")) {
        data = pruneFixturePayload(data);
        if (!data.items.length) data = null; // nothing left in the future -> refetch
      }
      if (data) {
        data.__cache = { age: hit.age, fromCache: true, limit: ttl };
        return data;
      }
    }
  }
  try {
    const res = await fetch(path, opts);
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch (err) { data = { error: text.slice(0, 300) }; }
    if (ttl > 0 && !data.error) cacheSet(key, data);
    data.__cache = { age: 0, fromCache: false, limit: ttl };
    return data;
  } catch (err) {
    const hit = cacheGet(key);
    if (hit) {
      const data = path.startsWith("/api/fixtures") ? pruneFixturePayload(hit.data) : hit.data;
      data.__cache = { age: hit.age, fromCache: true, stale: true, offline: true, limit: ttl };
      return data;
    }
    return { error: String(err) };
  }
}

/* Auto-update: the server fingerprints the assets; when they change, the app reloads itself.
   This is how changes reach the client (and an installed PWA) without sending a new link. */
async function checkVersion() {
  try {
    const r = await fetch("/api/version", { cache: "no-store" });
    const d = await r.json();
    if (!d || !d.assets) return;
    const v = String(d.assets);
    const seen = localStorage.getItem("mb_asset_v");
    if (seen && seen !== v) {
      localStorage.setItem("mb_asset_v", v);
      toast(t("app.updating"), 5000);
      setTimeout(() => location.replace(location.pathname + "?u=" + Date.now()), 1200);
      return;
    }
    localStorage.setItem("mb_asset_v", v);
  } catch (err) { /* offline: keep working with what we have */ }
}

/* ------------------------------------------------- iOS: add to home screen */
function maybeShowIosBanner() {
  const el = $("#iosBanner");
  if (!el) return;
  const ua = navigator.userAgent || "";
  const isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const standalone = window.navigator.standalone === true || (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches);
  if (!isIOS || standalone) { el.classList.add("hidden"); return; }
  if (localStorage.getItem("mb_ios_banner_dismissed") === "1") return;
  el.innerHTML = `<span class="ico">📲</span>
    <span><b>${esc(t("ios.title"))}</b><br>${t("ios.body")}</span>
    <button id="iosClose" aria-label="${esc(t("ios.dismiss"))}">✕</button>`;
  el.classList.remove("hidden");
  const close = $("#iosClose");
  if (close) close.addEventListener("click", () => {
    localStorage.setItem("mb_ios_banner_dismissed", "1");
    el.classList.add("hidden");
  });
}

/* cache badge (shows when data came from the local cache + manual refresh) */
let LAST_ACTION = null;
function setAction(fn) { LAST_ACTION = fn; }
function showCacheBadge(data) {
  const el = $("#cacheBadge");
  const meta = data && data.__cache;
  if (!el) return;
  if (!meta || !meta.fromCache) { el.classList.add("hidden"); el.innerHTML = ""; return; }
  const age = Math.max(1, Math.round(meta.age / 60));
  const pruned = data.pruned_past ? ` · ${data.pruned_past} ${t("cache.expired")}` : "";
  el.innerHTML = `<span>${meta.offline ? "📴" : "📦"} ${esc(t(meta.offline ? "cache.offline" : "cache.from"))} · ${esc(t("cache.age", { n: age }))}${esc(pruned)}</span>
    <button class="btn small" id="cacheRefresh">${esc(t("cache.refresh"))}</button>`;
  el.classList.remove("hidden");
  const btn = $("#cacheRefresh");
  if (btn) btn.addEventListener("click", () => { if (LAST_ACTION) LAST_ACTION(true); });
}

/* ---------------------------------------------------------------- limits */
let LIMITS = null;
const DOT = { green: "🟢", yellow: "🟡", red: "🔴", unknown: "⚪" };
async function fetchLimits(live) {
  try {
    LIMITS = await api("/api/limits?lang=" + lang + (live ? "&live=1" : ""), null, { force: !!live });
  } catch (e) { LIMITS = null; }
  renderLimitsPill();
  if (!$("#limitsOverlay").classList.contains("hidden")) renderLimitsBody();
}
function localCacheCount() {
  let n = 0;
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k && k.startsWith(CACHE_PREFIX)) n++;
  }
  return n;
}
async function renderCacheInfo() {
  const el = $("#cacheInfo");
  if (!el) return;
  const s = await api("/api/cache/status", null, { force: true });
  const server = s && s.server ? s.server.entries : "—";
  const odds = (s && s.odds_cache) || {};
  el.innerHTML = `📦 ${esc(t("cache.local"))}: <b>${localCacheCount()}</b> · ${esc(t("cache.server"))}: <b>${server}</b> · ${esc(t("cache.events"))}: <b>${odds.events_upcoming != null ? odds.events_upcoming : "—"}</b> ${esc(t("cache.upcoming"))} / ${odds.events_total != null ? odds.events_total : "—"}`;
}
function renderLimitsPill() {
  if (!LIMITS) return;
  $("#limitsDot").textContent = DOT[LIMITS.overall] || "⚪";
  const short = $("#limitsShort");
  if (short) short.textContent = t("limits.short");
}
function renderLimitsBody() {
  const body = $("#limitsBody");
  if (!LIMITS) { body.innerHTML = ""; return; }
  const quota = (p) => {
    const lim = p.limit == null ? "—" : p.limit;
    if (p.remaining != null) return t("limits.remaining", { n: p.remaining, lim });
    if (p.kind === "monthly") return t("limits.limitMonth", { lim });
    if (p.kind === "daily") return t("limits.limitDay", { lim });
    if (p.kind === "minute") return t("limits.limitMinute", { lim });
    return t("limits.noDaily");
  };
  body.innerHTML = LIMITS.providers.map((p) => `
    <div class="provider">
      <div class="prow">
        <b>${esc(p.label)}</b>
        <span class="lvl ${esc(p.level)}">${DOT[p.level] || "⚪"} ${esc(t("limits.level." + p.level))}</span>
      </div>
      <div class="mini">${quota(p)}</div>
      ${p.resets_at ? `<div class="mini">${esc(t("limits.renewsIn", { x: p.resets_in_human || "" }))}</div>` : ""}
      <div class="msg">${esc(p.message || "")}</div>
      ${p.register_url ? `<div class="mini"><a href="${esc(p.register_url)}" target="_blank" rel="noopener">${esc(p.register_url)}</a></div>` : ""}
    </div>`).join("");
}

/* -------------------------------------------------------------- fixtures */
let LAST_FIXTURES = [], LAST_NOTES = [], LAST_FIXTURES_RESP = null, SPORT_FILTER = "", DAYS = "7";
let LAST_ANALYSIS_ARGS = null;
function sportName(g) {
  const map = { soccer: "⚽", basketball: "🏀", tennis: "🎾", mma: "🥊", boxing: "🥊", icehockey: "🏒", americanfootball: "🏈", baseball: "⚾", rugbyleague: "🏉", cricket: "🏏", aussierules: "🏉", lacrosse: "🥍", other: "🎯" };
  const key = "sport." + g;
  const label = t(key);
  return (map[g] || "🎯") + " " + (label === key ? g : label);
}
async function loadFixtures(force) {
  setAction(() => loadFixtures(true));
  $("#matchesList").innerHTML = `<div class="card empty">…</div>`;
  const q = encodeURIComponent($("#matchSearch").value.trim());
  const data = await api(`/api/fixtures?days=${DAYS}&q=${q}&lang=${lang}&limit=250`, null, { force: !!force });
  if (data.error && !(data.items || []).length) {
    $("#matchesList").innerHTML = `<div class="card empty">⚠️ ${esc(data.error)}</div>`;
    showCacheBadge(data);
    return;
  }
  LAST_FIXTURES = data.items || [];
  LAST_NOTES = data.notes || [];
  LAST_FIXTURES_RESP = data;
  if (LAST_FIXTURES.some((m) => matchStatus(m) === "live")) await loadLiveScores();
  renderSports(LAST_FIXTURES);
  renderMatches(LAST_FIXTURES, LAST_NOTES);
  showCacheBadge(data);
}
function renderSports(items) {
  const counts = {};
  items.forEach((it) => { counts[it.sport] = (counts[it.sport] || 0) + 1; });
  if (SPORT_FILTER && !counts[SPORT_FILTER]) SPORT_FILTER = ""; // the filter target disappeared after a reload
  const chips = [`<button class="chip ${SPORT_FILTER === "" ? "active" : ""}" data-sport="">${t("matches.all")}</button>`];
  Object.keys(counts).sort((a, b) => counts[b] - counts[a]).forEach((s) => {
    chips.push(`<button class="chip ${SPORT_FILTER === s ? "active" : ""}" data-sport="${esc(s)}">${esc(sportName(s))} (${counts[s]})</button>`);
  });
  $("#sportChips").innerHTML = chips.join("");
  $$("#sportChips .chip").forEach((b) => b.addEventListener("click", () => {
    SPORT_FILTER = b.getAttribute("data-sport");
    renderSports(LAST_FIXTURES);
    renderMatches(LAST_FIXTURES, LAST_NOTES);
  }));
}
/* status badge + score for a fixture card (finished games stay listed so they can still be analysed) */
function matchStatus(m) {
  return m && m.status ? m.status : "upcoming";
}
function matchHasScore(m) {
  return m && m.home_score != null && m.away_score != null;
}
function matchBadgeHtml(m) {
  const st = matchStatus(m);
  if (st === "live") return `<span class="st live">🔴 ${esc(t("match.live"))}</span>`;
  if (st === "finished") return `<span class="st finished">✅ ${esc(t("match.finished"))}</span>`;
  return "";
}
function matchTeamsHtml(m) {
  const min = m.live_minute ? ` <b class="mt-min">${m.live_minute}'</b>` : "";
  const score = matchHasScore(m) ? `<span class="mt-score">${m.home_score}–${m.away_score}${min}</span>` : "";
  return `<div class="teams"><span class="tn">${esc(m.home)} <span class="muted">–</span> ${esc(m.away)}</span>${score}</div>`;
}
/* --------- scoruri live (meciuri pornite) --------- */
let LIVE_SCORES = [];
function normTeam(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]/g, ""); }
function liveScoreFor(m) {
  const nh = normTeam(m.home), na = normTeam(m.away);
  if (!nh || !na) return null;
  for (const s of LIVE_SCORES) {
    const ih = normTeam(s.h), ia = normTeam(s.a);
    if (!ih || !ia) continue;
    if ((nh.includes(ih) || ih.includes(nh)) && (na.includes(ia) || ia.includes(na))) return s;
    if ((nh.includes(ia) || ia.includes(nh)) && (na.includes(ih) || ih.includes(na))) return { ...s, swapped: true };
  }
  return null;
}
function annotateLive(items) {
  for (const m of items) {
    if (matchStatus(m) === "live") {
      const s = liveScoreFor(m);
      if (s && s.hs != null && s.as != null) {
        m.home_score = s.swapped ? s.as : s.hs;
        m.away_score = s.swapped ? s.hs : s.as;
        m.live_minute = s.min;
      }
    }
  }
  return items;
}
async function loadLiveScores() {
  try {
    const d = await api("/api/livescores", null, { force: true });
    LIVE_SCORES = (d && d.items) || [];
  } catch (e) { /* scorurile live sunt bonus */ }
}
let MATCH_FILTER = "";
function renderMatches(items, notes) {
  let shown = SPORT_FILTER ? items.filter((i) => i.sport === SPORT_FILTER) : items;
  if (MATCH_FILTER === "live") shown = shown.filter((i) => matchStatus(i) === "live");
  else if (MATCH_FILTER === "upcoming") shown = shown.filter((i) => matchStatus(i) === "upcoming");
  else if (MATCH_FILTER === "odds") shown = shown.filter((i) => i.has_odds);
  else if (MATCH_FILTER === "stream") shown = shown.filter((i) => ((WATCH_CHANNELS[i.sport_key || ""]) || []).length > 0);
  annotateLive(shown);
  const sparse = shown.length > 0 && shown.length < 5 && DAYS !== "all";
  $("#matchesNotes").innerHTML = (sparse ? `<div>💡 ${esc(t("matches.sparse"))}</div>` : "")
    + (notes || []).map((n) => `<div>ℹ️ ${esc(n)}</div>`).join("");
  if (!shown.length) {
    $("#matchesList").innerHTML = `<div class="card empty">${esc(t("empty.matches"))}</div>`;
    return;
  }
  $("#matchesList").innerHTML = shown.map((m, i) => {
    const o = m.odds || {};
    const oddsHtml = m.has_odds
      ? `<div class="odds">
           <span class="odd" data-tip="tip.analyze">1 <b>${o.home != null ? o.home.toFixed(2) : "—"}</b></span>
           ${o.draw != null ? `<span class="odd">X <b>${o.draw.toFixed(2)}</b></span>` : ""}
           <span class="odd">2 <b>${o.away != null ? o.away.toFixed(2) : "—"}</b></span>
         </div>`
      : `<div class="odds"><span class="badge-src">${esc(t("res.noOdds"))}</span></div>`;
    const watched = isWatched(m.home, m.away);
    const st = matchStatus(m);
    const badge = matchBadgeHtml(m);
    const hasWatch = !!((WATCH_CHANNELS[m.sport_key || ""]) || []).length;
    const watchBtn = (st === "live" || st === "upcoming")
      ? `<span class="watchbtn ${hasWatch ? "has" : "off"}" data-watch="1" title="${hasWatch ? esc(t("watch.title")) : esc(t("watch.off"))}">📺</span>`
      : "";
    return `<div class="match st-${st}" data-idx="${i}" data-id="${esc(m.id || "")}" data-time="${esc(m.commence_time || "")}" data-home="${esc(m.home)}" data-away="${esc(m.away)}" data-tip="tip.match" data-clickable="1">
      <div class="row1">
        <span>${esc(leagueLabel(m))}</span>
        <span>${esc(fmtTime(m.commence_time))}${badge ? " · " + badge : ""}</span>
      </div>
      ${matchTeamsHtml(m)}
      ${oddsHtml}
      <div class="row1" style="margin-top:6px">
        <span class="badge-src ${m.has_odds ? "odds" : ""}">${m.source === "odds" ? esc(t("matches.srcOdds")) : esc(t("matches.srcFixtures"))}</span>
        ${watchBtn}
        <span class="star ${watched ? "on" : ""}" data-star="1" title="${esc(watched ? t("live.watched") : t("live.watch"))}">${watched ? "★" : "☆"}</span>
      </div>
    </div>`;
  }).join("");
  $$("#matchesList .match").forEach((el) => {
    el.addEventListener("click", () => {
      hideTip();
      switchTab("home");
      runAnalysis(el.getAttribute("data-home"), el.getAttribute("data-away"),
        el.getAttribute("data-id"), el.getAttribute("data-time"));
    });
    const star = el.querySelector(".star");
    if (star) star.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const item = shown[parseInt(el.getAttribute("data-idx"), 10)];
      if (item) toggleWatch(item);
    });
    const wb = el.querySelector(".watchbtn");
    if (wb) wb.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const item = shown[parseInt(el.getAttribute("data-idx"), 10)];
      if (item) openWatch(item);
    });
  });
}

/* --------------------------------------------------------------- analysis */
const LOAD_STEPS = ["loader.finding", "loader.odds", "loader.news"];
let LOADER_GEN = 0;
function startLoader() {
  const gen = ++LOADER_GEN;
  const box = $("#loaderSteps");
  const fill = $("#progressFill");
  const status = $("#loaderStatus");
  let i = 0, pct = 0;
  const paint = () => {
    box.innerHTML = LOAD_STEPS.map((k, n) =>
      `<div class="${n < i ? "done" : (n === i ? "now" : "")}">${n < i ? "✓" : (n === i ? "●" : "○")} ${esc(t(k))}</div>`).join("");
  };
  paint();
  if (status) status.textContent = t("loader.working");
  if (fill) { fill.className = ""; fill.style.width = "3%"; }
  const iv = setInterval(() => {
    if (gen !== LOADER_GEN) return;
    if (fill) { pct = Math.min(92, pct + (pct < 55 ? 8 : 3)); fill.style.width = pct + "%"; }
    if (i < LOAD_STEPS.length) { i++; paint(); }
  }, 520);
  const hide = (delay) => setTimeout(() => { if (gen === LOADER_GEN) $("#loader").classList.add("hidden"); }, delay);
  return {
    /* ok=true -> green 100% "done"; ok=false -> red "nothing found" */
    done(ok, label) {
      if (gen !== LOADER_GEN) return;
      clearInterval(iv);
      if (fill) { fill.className = ok ? "ok" : "fail"; fill.style.width = "100%"; }
      if (status) status.textContent = label || (ok ? "✓ " + t("loader.doneOk") : "✗ " + t("loader.doneFail"));
      box.innerHTML = LOAD_STEPS.map((k) => `<div class="${ok ? "done" : ""}">${ok ? "✓" : "·"} ${esc(t(k))}</div>`).join("");
      hide(ok ? 900 : 2200);
    },
    fail(label) { this.done(false, label); },
  };
}
function renderProbabilityBars(p, match) {
  const rows = [["1", match.home, p.home], ["X", t("wallet.draw"), p.draw], ["2", match.away, p.away]];
  return `<div class="probbars">` + rows.map(([k, name, v]) => {
    if (v == null) return "";
    const pct = Math.round(v * 100);
    return `<div class="probrow"><span>${k} · ${esc(name)}</span>
      <span class="bar"><i style="width:${pct}%"></i></span><span class="pct">${pct}%</span></div>`;
  }).join("") + `</div>`;
}
/* -------------------------------------------------- bet panel (analysis) */
let BET_CTX = null;
function suggestStake() {
  const bal = WALLET && WALLET.balance ? WALLET.balance : 100;
  return Math.max(1, Math.round(bal * 0.05 * 2) / 2); // ~5% of the demo wallet
}
function betPanelHtml(sides, note) {
  if (!sides.length) return "";
  return `<div class="card betpanel" data-tip="tip.betPanel">
    <h3>💰 ${esc(t("wallet.placeTitle"))}</h3>
    <div class="sidebtns">
      ${sides.map(([side, label, o]) => `<button class="side" data-side="${side}" data-odds="${o}">
        <span class="k">${side === "home" ? "1" : (side === "draw" ? "X" : "2")}</span> ${esc(label)} <b>${o}</b></button>`).join("")}
    </div>
    <div class="searchrow">
      <input id="stakeInput" type="number" min="0.5" step="0.5" value="${suggestStake()}" data-tip="tip.stake">
      <button id="placeBetBtn" class="btn primary" data-tip="tip.placeBet">${esc(t("wallet.place"))}</button>
    </div>
    <p class="mini" id="betHint">${esc(note || t("wallet.pickSide"))} · ${esc(t("wallet.balance"))}: ${fmtMoney(WALLET ? WALLET.balance : 0, t("wallet.currency"))}</p>
  </div>`;
}
function wireBetPanel(defaultSide) {
  let chosen = null;
  const sides = $$("#result .sidebtns .side");
  sides.forEach((btn) => {
    if (defaultSide && btn.getAttribute("data-side") === defaultSide) {
      btn.classList.add("active");
      chosen = { side: defaultSide, odds: parseFloat(btn.getAttribute("data-odds")) };
    }
    btn.addEventListener("click", () => {
      sides.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      chosen = { side: btn.getAttribute("data-side"), odds: parseFloat(btn.getAttribute("data-odds")) };
      const hint = $("#betHint");
      if (hint) hint.textContent = t("wallet.selected") + ": " + btn.textContent.replace(/\s+/g, " ").trim();
    });
  });
  const place = $("#placeBetBtn");
  if (!place) return;
  place.addEventListener("click", async () => {
    if (!chosen) { toast(t("wallet.pickSide")); return; }
    const stake = parseFloat($("#stakeInput").value);
    if (!stake || stake <= 0) { toast(t("wallet.pickStake")); return; }
    const ctx = BET_CTX || {};
    const sc = (ctx.by_side || {})[chosen.side] || {};
    const ok = await placeBet({
      event_id: ctx.event_id || "", home: ctx.home || "", away: ctx.away || "",
      side: chosen.side, odds: chosen.odds, stake,
      edge_pct: sc.edge_pct != null ? sc.edge_pct : (ctx.edge_pct || 0),
      bookmaker: sc.bookmaker || ctx.bookmaker || "",
      model_prob: sc.model_prob != null ? sc.model_prob : (ctx.model_prob || null),
    });
    if (ok) place.disabled = true;
  });
}

/* Devil's-advocate card: why the weaker-priced team could still win.
   `c` is the language-neutral payload from the backend (codes + numbers);
   all the wording is localised here so the three languages stay in sync. */
function counterHtml(c) {
  if (!c || !c.underdog) return "";
  const u = c.underdog;
  const conf = c.confidence || "low";
  const factors = c.factors || [];
  const title = `<h3>⚔️ ${esc(t("counter.title"))}</h3>`;
  if (!factors.length) {
    return `<div class="card counter" data-tip="tip.cardCounter">${title}
      <p class="hint">${esc(t("counter.none"))}</p></div>`;
  }
  const head = `${title}
    <p class="mini"><b>${esc(t("counter.why", { team: u.team }))}</b> — ${esc(t("counter.adjusted"))}:
      <b class="cf-bal">${c.balance_pct}%</b>
      <span class="muted">(${esc(t("counter.model"))} ${u.model_pct}%${c.delta_pp > 0 ? ` · +${c.delta_pp} pp` : ""})</span></p>`;
  const rows = factors.map((f) => {
    const label = t("counter.f." + f.code, { team: f.team || "" });
    const ev = (f.evidence || []).length
      ? `<div class="cf-ev"><span class="muted">${esc(t("counter.evidence"))}:</span> ${f.evidence.map((e) => `<span class="cf-src">${esc(e)}</span>`).join("")}</div>`
      : "";
    return `<div class="cfactor">
      <div class="cf-top"><span class="cf-badge">+${f.pp} pp</span> <b>${esc(label)}</b>
        <span class="cf-pct" data-tip="tip.counterSupport">${f.support_pct}%</span></div>
      ${ev}</div>`;
  }).join("");
  return `<div class="card counter" data-tip="tip.cardCounter">${head}
    <div class="cf-tag">${c.grounded ? "🟢" : "⚪"} ${esc(t("counter." + (c.grounded ? "grounded" : "ungrounded")))} · ${esc(t("counter.conf"))}: ${esc(t("counter.conf." + conf))}</div>
    <div class="cfactors">${rows}</div>
    <p class="hint">${esc(t("counter.hint"))}</p>
  </div>`;
}

function renderAnalysis(d) {
  const area = $("#result");
  if (d.error) {
    area.innerHTML = `<div class="card"><h2>⚠️</h2><p>${esc(d.error)}</p></div>`;
    return;
  }
  if (!d.found) {
    const m = d.match || {};
    const when = m.commence_time ? fmtTime(m.commence_time) : "";
    area.innerHTML = `<div class="card">
      <h2>${esc(m.home)} <span class="muted">–</span> ${esc(m.away)}</h2>
      ${m.league || when ? `<p class="muted">${esc(m.league || "")}${when ? " · " + esc(when) : ""}</p>` : ""}
      <div class="reason">${esc((d.reasons || [])[0] || "")}</div>
      ${d.note ? `<p class="hint">${esc(d.note)}</p>` : ""}
    </div>`;
    focusResult();
    return;
  }
  const m = d.match, p = d.probabilities || {};
  const hasProbs = ["home", "draw", "away"].some((s) => p[s] != null);
  const probNote = d.probabilities_note ? t("res.pnote." + d.probabilities_note) : "";
  const odds = d.best_odds || {};
  const vbs = d.value_bets || [];
  const mkt = d.market || null;
  const mktSides = (mkt && mkt.sides) || {};
  const mktLabel = !mkt ? "" :
    mkt.kind === "sharp" ? `${t("res.sharpMarket")}${mkt.bookmaker ? " · " + mkt.bookmaker : ""}` :
    mkt.kind === "consensus" ? (mkt.books === 1 ? t("res.singleBook") : `${t("res.consensus")}${mkt.books ? " (" + mkt.books + ")" : ""}`) : t("res.noMarket");
  const vbHtml = vbs.length ? vbs.map((vb) => `
    <div class="vbcard">
      <div class="prow"><b>${esc(sideLabel(vb))}</b><span class="stars">${"★".repeat(vb.confidence || 0)}${"☆".repeat(Math.max(0, 5 - (vb.confidence || 0)))}</span></div>
      <div class="mini">${esc(t("res.marketModel"))}: <b>${Math.round(vb.model_prob * 100)}%</b>
        · ${esc(t("res.marketReal"))}: <b>${Math.round((vb.market_prob || 0) * 100)}%</b>
        ${vb.market_source ? `<span class="muted">(${esc(vb.market_source)})</span>` : vb.market_books ? `<span class="muted">(${esc(t("res.consensus"))} ${vb.market_books})</span>` : ""}
      </div>
      <div class="mini">${esc(t("res.edgeReal"))}: <b style="color:var(--ok)">+${vb.edge_pct}%</b>
        · ${esc(t("res.odds"))}: <b>${vb.odds}</b> ${vb.bookmaker ? `<span class="muted">(${esc(vb.bookmaker)})</span>` : ""}
        ${vb.sharp_odds ? `· ${esc(t("res.sharpOdds"))}: <b>${vb.sharp_odds}</b>` : vb.fair_odds ? `· ${esc(t("res.fairOdds"))}: <b>${vb.fair_odds}</b>` : ""}
      </div>
      <div class="mini muted">${esc(t("res.edgeBest"))}: ${vb.edge_best_pct >= 0 ? "+" : ""}${vb.edge_best_pct}%</div>
      ${Math.abs(vb.news_shift_pct || 0) >= 0.3 ? `<div class="mini" style="color:var(--ok)">📰 ${esc(t("res.fromNews"))}: <b>${vb.news_shift_pct > 0 ? "+" : ""}${vb.news_shift_pct} pp</b></div>` : ""}
    </div>`).join("") : `<p class="hint">${esc(t("res.noEdge"))}</p>`;

  const marketHtml = mkt && Object.keys(mktSides).length ? `
    <div class="card" data-tip="tip.cardMarket">
      <h3>⚖️ ${esc(t("res.market"))} <span class="muted" style="font-weight:400;font-size:.8em">${esc(mktLabel)}</span></h3>
      <div class="mktrow mktrow-head"><span></span><span>${esc(t("res.marketModel"))}</span><span>${esc(t("res.marketReal"))}</span><span>${esc(t("res.edgeReal"))}</span></div>
      ${["home", "draw", "away"].map((s) => {
        const ms = mktSides[s];
        if (!ms) return "";
        const row = p[s] != null ? p[s] : null;
        const real = row != null ? (row - ms.prob) * 100 : null;
        const nm = s === "draw" ? t("wallet.draw") : (ms.name || (s === "home" ? m.home : m.away));
        return `<div class="mktrow">
          <span>${esc(nm)}</span>
          <span>${row != null ? Math.round(row * 100) + "%" : "—"}</span>
          <span>${Math.round(ms.prob * 100)}%</span>
          <span style="color:${real != null && real >= 0 ? "var(--ok)" : "var(--muted)"}">${real != null ? (real >= 0 ? "+" : "") + real.toFixed(1) + "%" : "—"}</span>
        </div>`;
      }).join("")}
      <p class="hint">${esc(t("res.marketHint"))}</p>
    </div>` : "";

  const ctx = d.context || {};
  const ctxBox = (team, obj) => {
    const heads = (obj && obj.headlines) || [];
    return `<div class="ctxbox"><h4>${esc(team)} ${obj && obj.score ? `<span class="stars">(${obj.score > 0 ? "+" : ""}${obj.score})</span>` : ""}</h4>
      ${obj && obj.impact_summary ? `<div>${esc(obj.impact_summary)}</div>` : ""}
      ${heads.length ? `<ul>${heads.slice(0, 4).map((h) => `<li>${esc(h)}</li>`).join("")}</ul>` : ""}</div>`;
  };

  const sides = [
    ["home", m.home, odds[m.home]],
    ["draw", t("wallet.draw"), odds.Draw],
    ["away", m.away, odds[m.away]],
  ].filter((row) => row[2] != null);
  // Which side did the news move, and by how much (percentage points)?
  const nw = d.news && d.news.shift_pct ? d.news.shift_pct : null;
  const newsLine = nw ? ["home", "draw", "away"]
    .filter((s) => nw[s] != null && Math.abs(nw[s]) >= 0.3)
    .map((s) => {
      const nm = s === "draw" ? t("wallet.draw") : (s === "home" ? m.home : m.away);
      return `${esc(nm)} ${nw[s] > 0 ? "+" : ""}${nw[s]} pp`;
    }).join(" · ") : "";
  // Per-side context so placing a bet stores the numbers of the side actually
  // chosen (model probability from the model, edge/bookmaker from a value bet).
  const sideCtx = {};
  ["home", "draw", "away"].forEach((s) => {
    sideCtx[s] = { model_prob: p[s] != null ? p[s] : null, edge_pct: 0, bookmaker: "" };
  });
  (vbs || []).forEach((vb) => {
    if (!sideCtx[vb.side]) return;
    if (vb.model_prob != null) sideCtx[vb.side].model_prob = vb.model_prob;
    if (vb.edge_pct != null) sideCtx[vb.side].edge_pct = vb.edge_pct;
    if (vb.bookmaker) sideCtx[vb.side].bookmaker = vb.bookmaker;
  });
  BET_CTX = { event_id: m.event_id, home: m.home, away: m.away,
    edge_pct: (vbs[0] ? vbs[0].edge_pct : 0), bookmaker: (vbs[0] ? vbs[0].bookmaker : ""),
    model_prob: (vbs[0] ? vbs[0].model_prob : null), by_side: sideCtx };
  area.innerHTML = `
    <div class="card">
      <h2>${esc(m.home)} <span class="muted">–</span> ${esc(m.away)}</h2>
      <p class="muted">${esc(leagueLabel(m))} · ${esc(fmtTime(m.commence_time))}</p>
      ${m.is_past ? `<div class="notice pastwarn">${esc(t("res.past"))}</div>` : ""}
      <h3 style="margin-top:10px" data-tip="tip.cardProb">📊 ${esc(t("res.probabilities"))}</h3>
      ${hasProbs ? renderProbabilityBars(p, m) : `<p class="hint">${esc(t("res.noProbabilities"))}</p>${probNote ? `<p class="mini muted">${esc(probNote)}</p>` : ""}`}
      <h3 style="margin-top:12px" data-tip="tip.cardOdds">💰 ${esc(t("res.bestOdds"))}</h3>
      <div class="oddsrow">
        ${Object.keys(odds).map((k) => `<span class="odd">${esc(k === "Draw" ? "X (" + t("wallet.draw") + ")" : k)} <b>${odds[k]}</b>${d.best_bookmakers && d.best_bookmakers[k] ? ` <span class="muted">${esc(d.best_bookmakers[k])}</span>` : ""}</span>`).join("") || `<span class="hint">—</span>`}
      </div>
    </div>
    ${marketHtml}
    ${betPanelHtml(sides)}
    <div class="card" data-tip="tip.cardValue">
      <h3>🎯 ${esc(t("res.valueBets"))}</h3>
      ${vbHtml}
    </div>
    <div class="card" data-tip="tip.cardWhy">
      <h3>💡 ${esc(t("res.why"))}</h3>
      <div class="reasons">${(d.reasons || []).map((r) => `<div class="reason">${esc(r)}</div>`).join("")}</div>
    </div>
    ${counterHtml(d.counter)}
    <div class="card" data-tip="tip.cardNews">
      <h3>📰 ${esc(t("res.news"))}</h3>
      ${newsLine ? `<p class="mini">${esc(t("res.newsMoved"))} <b>${newsLine}</b>.</p>` : ""}
      <div class="teamctx">${ctxBox(m.home, ctx.home)}${ctxBox(m.away, ctx.away)}</div>
      ${(d.players || []).length ? `<p class="hint">${esc(t("res.players"))}: ${d.players.slice(0, 8).map(esc).join(", ")}</p>` : ""}
    </div>
    <div class="card disclaimer" data-tip="tip.disclaimer">${esc(d.disclaimer || t("footer.disclaimer"))}</div>`;
  wireBetPanel();
  focusResult();
}

/* Team search: list every match of a team (live/upcoming) instead of guessing one. */
function matchRowHtml(m, idx) {
  const o = m.odds || {};
  const oddsHtml = m.has_odds
    ? `<div class="odds">
         <span class="odd">1 <b>${o.home != null ? o.home.toFixed(2) : "—"}</b></span>
         ${o.draw != null ? `<span class="odd">X <b>${o.draw.toFixed(2)}</b></span>` : ""}
         <span class="odd">2 <b>${o.away != null ? o.away.toFixed(2) : "—"}</b></span>
       </div>`
    : `<div class="odds"><span class="badge-src">${esc(t("res.noOdds"))}</span></div>`;
  const st = matchStatus(m);
  const badge = matchBadgeHtml(m);
  return `<div class="match st-${st}" data-idx="${idx}" data-tip="tip.match" data-clickable="1">
    <div class="row1">
      <span>${esc(m.league || m.sport)}</span>
      <span>${esc(fmtTime(m.commence_time))}${badge ? " · " + badge : ""}</span>
    </div>
    ${matchTeamsHtml(m)}
    ${oddsHtml}
  </div>`;
}
function wireMatchRows(scope, items) {
  $$(`${scope} .match`).forEach((el) => el.addEventListener("click", () => {
    const m = items[parseInt(el.getAttribute("data-idx"), 10)];
    if (m) { hideTip(); runAnalysis(m.home, m.away, m.id, m.commence_time); }
  }));
}
async function searchMatches(query) {
  const data = await api(`/api/fixtures?days=all&q=${encodeURIComponent(query)}&lang=${lang}&limit=200`);
  return data.items || [];
}
async function showTeamMatches(query) {
  const area = $("#result");
  const words = query.split(/\s+/).filter((w) => w.length >= 3);
  let items = await searchMatches(query);
  // two teams typed: prefer the matches that contain both
  let both = [];
  if (words.length >= 2) {
    both = items.filter((i) => words.every((w) => `${i.home} ${i.away}`.toLowerCase().includes(w.toLowerCase())));
    if (both.length) items = both;
  }
  if (items.length === 1) { runAnalysis(items[0].home, items[0].away, items[0].id, items[0].commence_time); return "analyzed"; }
  if (items.length > 1) {
    area.innerHTML = `<div class="card">
      <h2>🔎 ${esc(t("team.title", { q: query }))}</h2>
      <p class="muted">${esc(t("team.count", { n: items.length }))}${both.length ? " · " + esc(t("team.both")) : ""}</p>
      <p class="hint">${esc(t("team.tap"))}</p>
      <div class="matches-list" id="teamRows">${items.map((m, i) => matchRowHtml(m, i)).join("")}</div>
    </div>`;
    wireMatchRows("#teamRows", items);
    focusResult();
    return "listed";
  }
  // nothing for the whole phrase -> try each word separately so one team still helps
  if (words.length >= 2) {
    const per = [];
    for (const w of words) {
      const found = await searchMatches(w);
      if (found.length) per.push([w, found]);
    }
    if (per.length) {
      area.innerHTML = per.map(([w, list], k) => `<div class="card">
        <h2>🔎 ${esc(t("team.others", { team: w }))}</h2>
        <p class="muted">${esc(t("team.count", { n: list.length }))}</p>
        <div class="matches-list" id="teamRows${k}">${list.map((m, i) => matchRowHtml(m, i)).join("")}</div>
      </div>`).join("") + `<div class="card"><p class="hint">${esc(t("nf.scope"))}</p></div>`;
      per.forEach(([, list], k) => wireMatchRows(`#teamRows${k}`, list));
      focusResult();
      return "listed";
    }
  }
  await showNotFound(query);
  return "none";
}

/* Team search: list every match of a team (live/upcoming) instead of guessing one. */
async function showNotFound(query) {
  const area = $("#result");
  area.innerHTML = `<div class="card">
    <h2>🔍 ${esc(t("nf.title"))}</h2>
    <p class="muted">${esc(t("nf.body", { q: query }))}</p>
    <p class="hint">${esc(t("nf.scope"))}</p>
    <div id="nfSuggest" class="datechips"></div>
  </div>`;
  focusResult();
  try {
    const data = await api("/api/fixtures?days=7&limit=120");
    const withOdds = (data.items || []).filter((i) => i.has_odds);
    const picks = withOdds.sort(() => Math.random() - 0.5).slice(0, 4);
    const box = $("#nfSuggest");
    if (!box || !picks.length) return;
    box.innerHTML = `<div class="mini" style="width:100%">${esc(t("nf.try"))}</div>`
      + picks.map((m, i) => `<button class="chip" data-i="${i}">${esc(m.home)} – ${esc(m.away)}</button>`).join("");
    $$("#nfSuggest .chip").forEach((b) => b.addEventListener("click", () => {
      const m = picks[parseInt(b.getAttribute("data-i"), 10)];
      if (m) runAnalysis(m.home, m.away, m.id, m.commence_time);
    }));
  } catch (err) { /* suggestions are a bonus */ }
}
/* On a phone the keyboard hides everything below the fold: close it and show the answer. */
function focusResult() {
  try { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); } catch (err) {}
  const el = $("#result");
  if (el && el.children.length) {
    setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
  }
}

async function runAnalysis(home, away, eventId, commenceTime, force) {
  if (!home || !away) return;
  LAST_ANALYSIS_ARGS = { home, away, eventId, commenceTime };
  setAction(() => runAnalysis(home, away, eventId, commenceTime, true));
  $("#result").innerHTML = "";
  $("#loader").classList.remove("hidden");
  const L = startLoader();
  const url = "/api/analyze" + (force ? "?nocache=1" : "");
  const d = await api(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ home, away, event_id: eventId || null, commence_time: commenceTime || null, lang }),
  }, { force: !!force });
  L.done(!!d.found, d.found ? undefined : "✗ " + t("loader.noMatch"));
  renderAnalysis(d);
  showCacheBadge(d);
}

/* -------------------------------------------------------------- recommend */
let REC_SEEN = [];
function renderPick(d) {
  const area = $("#result");
  if (d.error) {
    area.innerHTML = `<div class="card"><h2>⚠️</h2><p>${esc(d.error)}</p></div>`;
    return;
  }
  if (!d.pick) {
    area.innerHTML = `<div class="card"><h2>🎲</h2><p>${esc(d.message || "")}</p></div>`;
    return;
  }
  const vb = d.pick;
  BET_CTX = { event_id: vb.event_id, home: vb.home_team, away: vb.away_team, edge_pct: vb.edge_pct,
    bookmaker: vb.bookmaker, model_prob: vb.model_prob,
    by_side: { [vb.side]: { model_prob: vb.model_prob, edge_pct: vb.edge_pct, bookmaker: vb.bookmaker } } };
  area.innerHTML = `
    <div class="card hero">
      <h2>🎲 ${esc(t("res.found"))}: ${esc(vb.home_team)} – ${esc(vb.away_team)}</h2>
      <p class="muted">${esc(fmtTime(vb.commence_time))} · ${esc(sportLabel(vb.sport))} ${d.count ? "· " + d.count + " " + esc(t(d.count === 1 ? "res.variantOne" : "res.variants")) : ""}</p>
      <div class="vbcard" style="margin-top:10px" data-tip="tip.cardValue">
        <div class="prow"><b>${esc(sideLabel(vb))}</b><span class="stars">${"★".repeat(vb.confidence || 0)}${"☆".repeat(Math.max(0, 5 - (vb.confidence || 0)))}</span></div>
        <div class="mini">${esc(t("res.marketModel"))}: <b>${Math.round(vb.model_prob * 100)}%</b>
          · ${esc(t("res.marketReal"))}: <b>${Math.round((vb.market_prob || 0) * 100)}%</b>
          ${vb.market_source ? `<span class="muted">(${esc(vb.market_source)})</span>` : vb.market_books ? `<span class="muted">(${esc(t("res.consensus"))} ${vb.market_books})</span>` : ""}
          · ${esc(t("res.edgeReal"))}: <b style="color:var(--ok)">+${vb.edge_pct}%</b></div>
        <div class="mini">${esc(t("res.odds"))}: <b>${vb.odds}</b>${vb.bookmaker ? ` <span class="muted">(${esc(vb.bookmaker)})</span>` : ""}
          ${vb.sharp_odds ? `· ${esc(t("res.sharpOdds"))}: <b>${vb.sharp_odds}</b>` : ""}</div>
        ${Math.abs(vb.news_shift_pct || 0) >= 0.3 ? `<div class="mini" style="color:var(--ok)">📰 ${esc(t("res.fromNews"))}: <b>${vb.news_shift_pct > 0 ? "+" : ""}${vb.news_shift_pct} pp</b></div>` : ""}
      </div>
      <p class="hint">${esc(d.message || "")}</p>
      <div class="searchrow">
        <button class="btn primary" id="pickAnalyze">🔍 ${esc(t("res.analyzeDetail"))}</button>
        <button class="btn" id="pickAnother">🎲 ${esc(t("res.another"))}</button>
      </div>
    </div>
    ${betPanelHtml([[vb.side, sideLabel(vb), vb.odds]], t("wallet.recommended"))}`;
  $("#pickAnalyze").addEventListener("click", () => runAnalysis(vb.home_team, vb.away_team, vb.event_id, vb.commence_time));
  $("#pickAnother").addEventListener("click", recommend);
  wireBetPanel(vb.side);
  focusResult();
}
async function recommend() {
  $("#result").innerHTML = "";
  $("#loader").classList.remove("hidden");
  const L = startLoader();
  const d = await api(`/api/recommend?lang=${lang}&exclude=${encodeURIComponent(REC_SEEN.join(","))}`);
  L.done(!!d.pick, d.pick ? undefined : "✗ " + t("loader.doneFail"));
  if (d.pick && d.pick.event_id) { REC_SEEN.push(d.pick.event_id); if (REC_SEEN.length > 40) REC_SEEN.shift(); }
  renderPick(d);
  showCacheBadge(d);
}

/* ------------------------------------------------------------- suggestions */
let sugTimer = null;
function bindSuggest(inputSel, onPick) {
  const input = $(inputSel);
  input.addEventListener("input", () => {
    clearTimeout(sugTimer);
    const q = input.value.trim();
    if (q.length < 2) { $("#homeSuggest").classList.add("hidden"); return; }
    sugTimer = setTimeout(async () => {
      const data = await api(`/api/fixtures?days=all&q=${encodeURIComponent(q)}&lang=${lang}&limit=6`);
      const box = $("#homeSuggest");
      if (!(data.items || []).length) { box.classList.add("hidden"); return; }
      box.innerHTML = data.items.map((m) => `<button data-home="${esc(m.home)}" data-away="${esc(m.away)}">${esc(m.home)} <span class="muted">–</span> ${esc(m.away)} <span class="muted">· ${esc(fmtTime(m.commence_time))}</span></button>`).join("");
      box.classList.remove("hidden");
      $$("#homeSuggest button").forEach((b) => b.addEventListener("click", () => {
        box.classList.add("hidden");
        input.value = "";
        onPick(b.getAttribute("data-home"), b.getAttribute("data-away"));
      }));
    }, 220);
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".suggest") && !e.target.closest(inputSel)) $("#homeSuggest").classList.add("hidden");
  });
}

/* --------------------------------------------------- wallet (demo money) */
let WALLET = null;
function walletPlayer() { return localStorage.getItem("mb_player") || "client"; }
function setWalletPlayer(name) {
  const clean = (name || "client").trim() || "client";
  localStorage.setItem("mb_player", clean);
  WALLET = null;
  loadWallet();
  loadBets();
}
function fmtNum(n, digits) {
  if (n == null || isNaN(Number(n))) return "—";
  const d = digits == null ? 2 : digits;
  return new Intl.NumberFormat(localeOf(), { minimumFractionDigits: d, maximumFractionDigits: d }).format(Number(n));
}
function fmtMoney(n, cur) {
  if (n == null) return "—";
  return fmtNum(n) + " " + (cur || "demo");
}
async function loadWallet() {
  WALLET = await api("/api/wallet?player=" + encodeURIComponent(walletPlayer()));
  if (WALLET.auto_settle && WALLET.auto_settle.settled_count) alertsFromSettled(WALLET.auto_settle.settled);
  const openFromBets = WALLET.open_count;
  $("#stats").innerHTML = `
    <div class="stat stat-big" data-tip="tip.wallet">
      <div class="k">${esc(t("wallet.balance"))}</div>
      <div class="v">${fmtMoney(WALLET.balance, t("wallet.currency"))}</div>
      <div class="mini">${esc(t("wallet.startedWith"))}: ${fmtMoney(WALLET.initial, t("wallet.currency"))}</div>
    </div>
    <div class="stat" data-tip="tip.statCard"><div class="k">${esc(t("wallet.profit"))}</div><div class="v">${fmtMoney(WALLET.profit, "")}</div></div>
    <div class="stat" data-tip="tip.statCard"><div class="k">${esc(t("wallet.roi"))}</div><div class="v">${WALLET.roi_pct}%</div></div>
    <div class="stat" data-tip="tip.statCard"><div class="k">${esc(t("wallet.winRate"))}</div><div class="v">${WALLET.settled_count ? Math.round(WALLET.won / WALLET.settled_count * 100) : 0}%</div></div>
    <div class="stat" data-tip="tip.clv"><div class="k">${esc(t("wallet.clv"))}</div><div class="v" style="color:${WALLET.clv_avg_pct == null ? "var(--muted)" : (WALLET.clv_avg_pct >= 0 ? "var(--ok)" : "var(--danger)")}">${WALLET.clv_avg_pct == null ? "—" : (WALLET.clv_avg_pct >= 0 ? "+" : "") + WALLET.clv_avg_pct + "%"}</div><div class="mini">${esc(t("wallet.clvPositive"))}: ${WALLET.clv_positive_pct == null ? "—" : WALLET.clv_positive_pct + "%"}</div></div>
    <div class="stat" data-tip="tip.statCard"><div class="k">${esc(t("wallet.openBets"))}</div><div class="v">${openFromBets}</div></div>`;
  const badge = $("#simBadge");
  if (badge) badge.classList.remove("hidden");
}
async function loadBets() {
  const data = await api("/api/wallet/bets?player=" + encodeURIComponent(walletPlayer()));
  const bets = data.bets || [];
  if (!bets.length) {
    $("#betsList").innerHTML = `<div class="card empty">${esc(t("wallet.noBets"))}</div>`;
    return;
  }
  $("#betsList").innerHTML = bets.map((b) => {
    const statusTxt = b.status === "open" ? "⏳ " + t("wallet.pending")
      : (b.status === "won" ? "✅ " + t("wallet.won") : "❌ " + t("wallet.lost"));
    const cls = b.status === "won" ? "won" : (b.status === "lost" ? "lost" : "");
    const clvBadge = b.clv_pct != null
      ? `<span class="${b.clv_pct > 0 ? "pos" : (b.clv_pct < 0 ? "neg" : "muted")}" data-tip="tip.clv">· CLV ${b.clv_pct > 0 ? "+" : ""}${b.clv_pct}%</span>`
      : (b.closing_odds ? `<span class="muted">· CLV ${b.closing_odds} (${esc(t("wallet.pending"))})</span>`
        : (b.sharp_odds ? `<span class="muted">· ${esc(t("res.sharpOdds"))} ${b.sharp_odds}</span>` : ""));
    const settled = b.status === "won" || b.status === "lost";
    return `<div class="match betrow ${cls}${settled ? " clickable" : ""}" ${settled ? `data-bet="${b.id}" data-tip="tip.report" data-clickable="1"` : `data-tip="tip.betRow"`}>
      <div class="row1"><span>${esc(b.event)}</span><span class="badge-src">${esc(statusTxt)}${b.result_score ? " · " + esc(b.result_score) : ""}</span></div>
      <div class="teams">${esc(b.outcome)} <span class="muted">@</span> ${b.odds} <span class="muted">· ${esc(t("wallet.stake"))} ${fmtNum(b.stake || 0)}</span>
        ${b.profit ? `<span class="${b.profit > 0 ? "pos" : "neg"}">· ${b.profit > 0 ? "+" : ""}${fmtNum(b.profit)}</span>` : ""}${clvBadge}</div>
      ${b.status === "open" ? `<div class="searchrow"><button class="btn small" data-cancel="${b.id}">✕ ${esc(t("wallet.cancel"))}</button></div>` : ""}
      ${settled ? `<div class="mini muted" style="margin-top:4px">📋 ${esc(t("report.title"))}</div>` : ""}
    </div>`;
  }).join("");
  $$("#betsList [data-cancel]").forEach((el) => el.addEventListener("click", async (e) => {
    e.stopPropagation();
    await api(`/api/wallet/bet/${el.getAttribute("data-cancel")}?lang=${lang}`, { method: "DELETE" });
    loadWallet(); loadBets();
  }));
  $$("#betsList [data-bet]").forEach((el) => el.addEventListener("click", (e) => {
    if (e.target.closest("[data-cancel]")) return;
    openReport(el.getAttribute("data-bet"));
  }));
}
async function placeBet(payload) {
  const d = await api("/api/wallet/bet", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(Object.assign({ player: walletPlayer(), lang }, payload)),
  });
  if (d.error) { toast("⚠️ " + d.error); return false; }
  toast("✅ " + d.message);
  loadWallet(); loadBets();
  return true;
}
async function settleNow() {
  $("#settleInfo").textContent = t("wallet.checking");
  const d = await api("/api/wallet/settle", { method: "POST" });
  const n = d.settled_count || 0;
  $("#settleInfo").textContent = n ? t("wallet.settledN", { n }) : t("wallet.nothingSettled");
  alertsFromSettled(d.settled);
  loadWallet(); loadBets();
}
function alertsFromSettled(list) {
  (list || []).forEach((s) => pushAlert({
    kind: s.won ? "won" : "lost",
    title: `${s.won ? "✅ " + t("wallet.won") : "❌ " + t("wallet.lost")}: ${s.event}`,
    body: `${s.outcome} · ${s.result || ""} · ${s.profit > 0 ? "+" : ""}${fmtNum(s.profit || 0)} ${t("wallet.currency")}`,
  }));
}
async function resetWallet() {
  const d = await api(`/api/wallet/reset?player=${encodeURIComponent(walletPlayer())}&lang=${lang}`, { method: "POST" });
  toast("↺ " + (d.note || ""));
  loadWallet(); loadBets();
}

/* -------------------------------------------- match report (settled bet) */
/* Tapping a settled bet opens a drawer with what happened in the match (goals,
   cards, stats, start/end) plus an honest read of why the bet won/lost and what
   to improve. Backend returns language-neutral codes; we translate them here. */
let LAST_REPORT = null;
const STAT_I18N = {
  "Ball Possession": "report.stat.poss", "Total Shots": "report.stat.shots",
  "Shots on Goal": "report.stat.sot", "Shots off Goal": "report.stat.soff",
  "Blocked Shots": "report.stat.blocked", "Shots insidebox": "report.stat.inside",
  "Shots outsidebox": "report.stat.outside", "Corner Kicks": "report.stat.corners",
  "Offsides": "report.stat.offside", "Fouls": "report.stat.fouls",
  "Yellow Cards": "report.stat.yellow", "Red Cards": "report.stat.red",
  "Goalkeeper Saves": "report.stat.saves", "Total passes": "report.stat.passes",
  "Passes accurate": "report.stat.passesAcc", "Total passes %": "report.stat.passPct",
};
function fmtFull(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d)) return "—";
  return d.toLocaleDateString(localeOf(), { day: "2-digit", month: "2-digit", year: "numeric" }) + " " +
    d.toLocaleTimeString(localeOf(), { hour: "2-digit", minute: "2-digit" });
}
function rpNum(v) {
  if (v == null || v === "") return null;
  const n = parseFloat(String(v).replace("%", ""));
  return isNaN(n) ? null : n;
}
function rpMinute(r) {
  if (r.minute == null) return "";
  return r.minute + (r.extra ? "+" + r.extra : "") + "'";
}
function rpKv(k, v) {
  return (v == null || v === "") ? "" : `<span class="k">${esc(k)}</span><span>${esc(v)}</span>`;
}
function rpGoal(g) {
  const det = (g.detail || "").toLowerCase();
  const tags = [];
  if (det.includes("own")) tags.push(t("report.ownGoal"));
  if (det.includes("penalty")) tags.push(t("report.penalty"));
  const who = esc(g.player || "?") + (g.assist ? ` <span class="muted">(${esc(t("report.assist"))}: ${esc(g.assist)})</span>` : "");
  return `<div class="rp-ev"><span class="m">${esc(rpMinute(g))}</span>
    <span class="who">⚽ ${who}${tags.length ? ` <span class="muted">· ${esc(tags.join(", "))}</span>` : ""}</span>
    <span class="muted">${esc(g.team || "")}</span></div>`;
}
function rpCard(c) {
  const det = (c.detail || "").toLowerCase();
  const red = det.includes("red") || det.includes("second");
  return `<div class="rp-ev"><span class="m">${esc(rpMinute(c))}</span>
    <span class="who">${red ? "🟥" : "🟨"} ${esc(c.player || "?")} <span class="muted">· ${esc(red ? t("report.red") : t("report.yellow"))}</span></span>
    <span class="muted">${esc(c.team || "")}</span></div>`;
}
function rpStat(s) {
  const h = rpNum(s.home), a = rpNum(s.away);
  if (h == null && a == null) return "";
  const tot = (h || 0) + (a || 0);
  const hp = tot ? Math.round((h || 0) / tot * 100) : 50;
  const key = STAT_I18N[s.type];
  const lbl = key ? t(key) : s.type;
  return `<div class="rp-stat">
    <span class="h">${esc(s.home == null ? "—" : s.home)}</span>
    <span class="lbl">${esc(lbl)}</span>
    <span class="a">${esc(s.away == null ? "—" : s.away)}</span>
    <span class="track"><i class="h" style="width:${hp}%"></i><i class="a" style="width:${100 - hp}%"></i></span>
  </div>`;
}
function rpMetrics(mt) {
  const out = [];
  const push = (k, v) => { if (v != null && v !== "") out.push(`<span>${esc(k)}: <b>${esc(v)}</b></span>`); };
  push(t("report.mModel"), mt.model_prob != null ? mt.model_prob + "%" : null);
  push(t("report.mMarket"), mt.market_prob != null ? mt.market_prob + "%" : null);
  push(t("report.mImplied"), mt.implied_prob != null ? mt.implied_prob + "%" : null);
  push(t("report.mEdge"), mt.edge_pct != null ? (mt.edge_pct > 0 ? "+" : "") + mt.edge_pct + "%" : null);
  push(t("report.mClv"), mt.clv_pct != null ? (mt.clv_pct > 0 ? "+" : "") + mt.clv_pct + "%" : null);
  push(t("report.mOdds"), mt.odds);
  push(t("report.mSharp"), mt.sharp_odds);
  return out.length ? `<div class="rp-metrics">${out.join("")}</div>` : "";
}
function renderReport(d) {
  const body = $("#reportBody");
  if (!d || d.error) { body.innerHTML = `<p class="mini">${esc((d && d.error) || t("report.error"))}</p>`; return; }
  const b = d.bet || {}, m = d.match || {}, a = d.analysis || {};
  const score = m.score || {}, teams = m.teams || {};
  const hasScore = score.home != null && score.away != null;
  const won = b.won;
  const statusTxt = b.status === "won" ? "✅ " + t("report.won")
    : b.status === "lost" ? "❌ " + t("report.lost") : "⏳ " + t("report.open");
  const ht = (score.ht_home != null && score.ht_away != null)
    ? `<span class="muted" style="font-size:.55em">(${score.ht_home}–${score.ht_away})</span>` : "";
  let html = `<div class="rp-head">
      <div class="t">${esc(teams.home || b.event || "")}</div>
      <div class="rp-score">${hasScore ? score.home + "–" + score.away : "–"} ${ht}</div>
      <div class="t right">${esc(teams.away || "")}</div>
    </div>
    <div class="rp-status ${won ? "won" : "lost"}">${esc(statusTxt)}</div>
    <div class="rp-when">${esc(b.outcome || "")} @ ${esc(b.odds)} · ${esc(t("wallet.stake"))} ${fmtNum(b.stake || 0)}${b.profit ? ` · <span class="${b.profit > 0 ? "pos" : "neg"}">${b.profit > 0 ? "+" : ""}${fmtNum(b.profit)}</span>` : ""}</div>`;

  if (m.found) {
    const minute = m.minute != null ? m.minute + (m.extra ? "+" + m.extra : "") + "'" : null;
    html += `<div class="rp-sec"><h4>🕒 ${esc(t("report.match"))}</h4><div class="rp-kv">
      ${rpKv(t("report.kickoff"), m.kickoff ? fmtFull(m.kickoff) : null)}
      ${rpKv(t("report.ended"), m.ended ? fmtFull(m.ended) : null)}
      ${rpKv(t("report.minute"), minute)}
      ${rpKv(t("report.stoppage"), m.extra ? "+" + m.extra + "'" : null)}
      ${rpKv(t("report.league"), m.league)}
      ${rpKv(t("report.round"), m.round)}
      ${rpKv(t("report.venue"), m.venue)}
      ${rpKv(t("report.referee"), m.referee)}
    </div></div>`;
    const goals = m.goals || [], cards = m.cards || [], stats = m.stats || [];
    if (goals.length) html += `<div class="rp-sec"><h4>⚽ ${esc(t("report.goals"))}</h4>${goals.map(rpGoal).join("")}</div>`;
    if (cards.length) html += `<div class="rp-sec"><h4>🟨 ${esc(t("report.cards"))}</h4>${cards.map(rpCard).join("")}</div>`;
    if (stats.length) html += `<div class="rp-sec"><h4>📊 ${esc(t("report.stats"))}</h4>${stats.map(rpStat).join("")}</div>`;
    else if (!goals.length && !cards.length) html += `<div class="rp-sec"><p class="mini">${esc(t("report.noEvents"))}</p></div>`;
  } else {
    const reason = (d.meta || {}).reason;
    html += `<div class="rp-sec"><p class="mini">${esc(reason === "not_football" ? t("report.nonFootball") : t("report.notFound"))}</p></div>`;
  }

  const verdict = a.verdict ? t("report.v." + a.verdict) : "";
  const readings = (a.readings || []).map((r) => t("report.r." + r));
  const flags = (a.flags || []).map((f) => t("report.f." + f));
  html += `<div class="rp-sec"><h4>🔎 ${esc(t("report.why"))}</h4>
    ${verdict ? `<div class="rp-verdict ${won ? "won" : "lost"}">${esc(verdict)}</div>` : ""}
    ${readings.length ? `<ul class="rp-list">${readings.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>` : ""}
    ${rpMetrics(a.metrics || {})}
  </div>`;
  html += `<div class="rp-sec"><h4>🎯 ${esc(t("report.improve"))}</h4>
    ${flags.length ? `<ul class="rp-list">${flags.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : `<p class="mini">${esc(t("report.noImprove"))}</p>`}
  </div>`;
  html += `<div class="rp-actions"><button class="btn primary" id="reportMiki">💬 ${esc(t("report.askMiki"))}</button></div>`;
  html += `<p class="rp-note">${esc(t("report.source"))}: ${esc(m.source === "api-football" ? "API-Football" : t("report.sourceStored"))}</p>`;
  body.innerHTML = html;
  const mk = $("#reportMiki");
  if (mk) mk.addEventListener("click", askMiki);
}
async function openReport(betId) {
  if (!betId) return;
  const ov = $("#reportOverlay");
  $("#reportBody").innerHTML = `<p class="mini">${esc(t("report.loading"))}</p>`;
  ov.classList.remove("hidden");
  try {
    const d = await api(`/api/wallet/bet/${betId}/report?lang=${lang}`);
    LAST_REPORT = d || null;
    renderReport(d);
  } catch (err) {
    $("#reportBody").innerHTML = `<p class="mini">${esc(t("report.error"))}</p>`;
  }
}
function closeReport() { $("#reportOverlay").classList.add("hidden"); }
/* Compact, grounded summary of the report, handed to the assistant so it answers
   from the real match facts instead of guessing (it uses no extra API request). */
function reportContext(d) {
  if (!d) return "";
  const m = d.match || {}, a = d.analysis || {};
  const s = m.score || {}, mt = a.metrics || {};
  const lines = [];
  if (s.home != null && s.away != null) {
    lines.push(`${t("report.score")}: ${m.teams.home} ${s.home}-${s.away} ${m.teams.away}` +
      (s.ht_home != null ? ` (${t("report.ht")} ${s.ht_home}-${s.ht_away})` : ""));
  }
  (m.goals || []).forEach((g) => lines.push(`${t("report.goals")}: ${rpMinute(g)} ${g.player} (${g.team})${g.assist ? ` [${t("report.assist")}: ${g.assist}]` : ""}`));
  (m.cards || []).forEach((c) => lines.push(`${t("report.cards")}: ${rpMinute(c)} ${c.player} (${c.team}) ${c.detail}`));
  lines.push(`${t("report.mModel")}: ${mt.model_prob != null ? mt.model_prob + "%" : "—"}, ${t("report.mMarket")}: ${mt.market_prob != null ? mt.market_prob + "%" : "—"}, ${t("report.mEdge")}: ${mt.edge_pct != null ? mt.edge_pct + "%" : "—"}, ${t("report.mClv")}: ${mt.clv_pct != null ? mt.clv_pct + "%" : "—"}`);
  if (a.verdict) lines.push(`${t("report.why")}: ${t("report.v." + a.verdict)}`);
  (a.readings || []).forEach((x) => lines.push("• " + t("report.r." + x)));
  (a.flags || []).forEach((x) => lines.push("⚠ " + t("report.f." + x)));
  return lines.join("\n");
}
function askMiki() {
  const b = (LAST_REPORT && LAST_REPORT.bet) || {};
  const q = t("report.mikiAsk", {
    event: b.event || "", outcome: b.outcome || "", details: reportContext(LAST_REPORT),
  });
  closeReport();
  switchTab("assistant");
  setTimeout(() => sendChat(q), 150);
}

/* ------------------------------------------------------------------ watch live */
const WATCH_CHANNELS = {
  "soccer_germany_dfb_pokal": [
    { label: "ARD (Das Erste)", hls: "https://daserste-live.ard-mcdn.de/daserste/live/hls/int/master.m3u8" },
    { label: "ZDF", hls: "https://zdf-hls-15.akamaized.net/hls/live/2016498/de/high/master.m3u8" },
  ],
  "soccer_germany_liga3": [
    { label: "ARD (Das Erste)", hls: "https://daserste-live.ard-mcdn.de/daserste/live/hls/int/master.m3u8" },
  ],
};
let WATCH_MATCH = null;
let WATCH_HLS = null;
let WATCH_CUR = null;
function playHls(url) {
  const v = $("#watchVideo");
  if (!v || !url) return;
  WATCH_CUR = url;
  if (WATCH_HLS) { try { WATCH_HLS.destroy(); } catch (e) {} WATCH_HLS = null; }
  $("#watchPlayerWrap").classList.remove("hidden");
  if (window.Hls && window.Hls.isSupported()) {
    WATCH_HLS = new window.Hls({ lowLatencyMode: true });
    WATCH_HLS.loadSource(url);
    WATCH_HLS.attachMedia(v);
    WATCH_HLS.on(window.Hls.Events.MANIFEST_PARSED, () => { v.play().catch(() => {}); });
  } else if (v.canPlayType("application/vnd.apple.mpegurl")) {
    v.src = url;
    v.play().catch(() => {});
  } else {
    v.src = url;
  }
}
function openWatch(m) {
  WATCH_MATCH = m;
  const key = m.sport_key || "";
  const channels = WATCH_CHANNELS[key] || [];
  $("#watchTitle").textContent = `📺 ${m.home} vs ${m.away}`;
  let html = "";
  if (channels.length) {
    html += `<p class="mini">${esc(t("watch.free"))}</p><div class="watch-links">`
      + channels.map((c, i) => `<button class="btn small" data-ch="${i}">▶ ${esc(c.label)}</button>`).join("")
      + `</div>`;
  } else {
    html += `<p class="mini">${esc(t("watch.noFree"))}</p>`;
  }
  $("#watchBody").innerHTML = html;
  $$("#watchBody [data-ch]").forEach((b) => b.addEventListener("click", () => {
    const c = channels[parseInt(b.getAttribute("data-ch"), 10)] || {};
    playHls(c.hls);
  }));
  $("#watchPlayerWrap").classList.add("hidden");
  $("#watchMini").classList.add("hidden");
  $("#watchOverlay").classList.remove("hidden");
}
function stopWatchVideo() {
  const v = $("#watchVideo");
  if (WATCH_HLS) { try { WATCH_HLS.destroy(); } catch (e) {} WATCH_HLS = null; }
  if (v) { try { v.pause(); } catch (e) {} v.removeAttribute("src"); try { v.load(); } catch (e) {} }
  WATCH_CUR = null;
}
function closeWatch() {
  $("#watchOverlay").classList.add("hidden");
  $("#watchMini").classList.add("hidden");
  restoreWatchPlayer();
  stopWatchVideo();
}
function restoreWatchPlayer() {
  const slot = $("#watchPlayerSlot");
  const wrap = $("#watchPlayerWrap");
  if (slot && wrap) slot.appendChild(wrap);
}
function watchMinimize() {
  const mini = $("#watchMini");
  mini.appendChild($("#watchPlayerWrap"));
  mini.classList.remove("hidden");
  $("#watchMiniLabel").textContent = WATCH_MATCH ? `📺 ${WATCH_MATCH.home} vs ${WATCH_MATCH.away}` : "📺";
  $("#watchOverlay").classList.add("hidden");
}
function watchRestore() {
  restoreWatchPlayer();
  $("#watchMini").classList.add("hidden");
  $("#watchOverlay").classList.remove("hidden");
}
function watchFullscreen() {
  const v = $("#watchVideo");
  if (v && v.requestFullscreen) { try { v.requestFullscreen(); } catch (e) {} }
}
function watchRestart() {
  if (WATCH_CUR) playHls(WATCH_CUR);
}

/* ------------------------------------------------------------------ chat */
const CHAT_HISTORY = [];
function renderChatChips() {
  const box = $("#chatSuggest");
  if (!box) return;
  box.innerHTML = ["chat.q1", "chat.q2", "chat.q3"].map((k) => {
    const q = t(k);
    return `<button class="chip" data-q="${esc(q)}">${esc(q)}</button>`;
  }).join("");
  $$("#chatSuggest .chip").forEach((b) => b.addEventListener("click", () => sendChat(b.getAttribute("data-q"))));
}
function addMsg(role, text) {
  const box = $("#chatMessages");
  const el = document.createElement("div");
  el.className = "msg " + role;
  if (role === "assistant") {
    el.innerHTML = renderReply(text);
    el.querySelectorAll(".v-pct").forEach(animatePct);
  } else {
    el.textContent = text;
  }
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
  return el;
}
async function sendChat(text) {
  if (!text) return;
  addMsg("user", text);
  CHAT_HISTORY.push({ role: "user", content: text });
  $("#chatInput").value = "";
  const ph = addMsg("assistant", t("chat.thinking"));
  const d = await api("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: CHAT_HISTORY.slice(-8), lang }),
  });
  ph.innerHTML = renderReply(d.reply || "…");
  ph.querySelectorAll(".v-pct").forEach(animatePct);
  CHAT_HISTORY.push({ role: "assistant", content: d.reply || "" });
  if (d.provider === "error") { $("#aiNotice").classList.remove("hidden"); $("#aiNotice").textContent = d.reply || ""; }
  fetchLimits(false);
}

/* ------------------------------------------------- live alerts + watchlist */
let WATCH = [];
let LIVE_TIMER = null;
let LIVE_EVENTS = [];
function alertsOn() { return localStorage.getItem("mb_alerts") !== "0"; }
function setAlerts(on) { localStorage.setItem("mb_alerts", on ? "1" : "0"); }
function normName(s) { return String(s || "").toLowerCase().replace(/[^a-z0-9]/g, ""); }
function isWatched(home, away) {
  const h = normName(home), a = normName(away);
  return WATCH.some((w) => {
    const wh = normName(w.home_team), wa = normName(w.away_team);
    return (h && wh && (h.includes(wh) || wh.includes(h))) && (a && wa && (a.includes(wa) || wa.includes(a)));
  });
}
async function loadWatch() {
  const d = await api("/api/watch?player=" + encodeURIComponent(walletPlayer()));
  WATCH = d.items || [];
  renderWatchPanel();
  return WATCH;
}
async function toggleWatch(item) {
  if (isWatched(item.home, item.away)) {
    const hit = WATCH.find((w) => normName(w.home_team) === normName(item.home) || normName(w.home_team).includes(normName(item.home)));
    if (hit) await api("/api/watch/" + hit.id, { method: "DELETE" });
    toast(t("live.unwatched"));
  } else {
    await api("/api/watch", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        player: walletPlayer(), event_id: item.id || item.event_id || "",
        home: item.home || item.home_team, away: item.away || item.away_team,
        sport: item.sport || "soccer", league: item.league || "",
        commence_time: item.commence_time || "",
      }),
    });
    toast(t("live.watchedToast"));
  }
  await loadWatch();
  if (LAST_FIXTURES.length) renderMatches(LAST_FIXTURES, LAST_NOTES);
  startLivePolling(true);
}
function renderWatchPanel() {
  const el = $("#watchList");
  if (!el) return;
  if (!WATCH.length) { el.innerHTML = `<div class="mini">${esc(t("live.noWatch"))}</div>`; return; }
  el.innerHTML = WATCH.map((w) => `
    <div class="watchrow" data-tip="tip.watchRow">
      <span>⭐ ${esc(w.home_team)} <span class="muted">–</span> ${esc(w.away_team)}</span>
      <span class="mini">${esc(fmtTime(w.commence_time))}</span>
      <button class="icon-btn" data-unwatch="${w.id}" title="${esc(t("live.remove"))}">✕</button>
    </div>`).join("");
  $$("#watchList [data-unwatch]").forEach((b) => b.addEventListener("click", async () => {
    await api("/api/watch/" + b.getAttribute("data-unwatch"), { method: "DELETE" });
    loadWatch();
    if (LAST_FIXTURES.length) renderMatches(LAST_FIXTURES, LAST_NOTES);
  }));
}
function beep(kind) {
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    const ctx = beep.ctx || (beep.ctx = new AC());
    if (ctx.state === "suspended") ctx.resume();
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "triangle";
    const t0 = ctx.currentTime;
    o.frequency.setValueAtTime(kind === "goal" ? 880 : 560, t0);
    if (kind === "goal") o.frequency.setValueAtTime(1245, t0 + 0.13);
    g.gain.setValueAtTime(0.09, t0);
    g.gain.exponentialRampToValueAtTime(0.0008, t0 + 0.42);
    o.connect(g); g.connect(ctx.destination);
    o.start(t0); o.stop(t0 + 0.45);
  } catch (err) { /* audio is a bonus, never a blocker */ }
}
function notifyEvent(ev) {
  const isGoal = ev.kind === "goal";
  const title = `${isGoal ? "⚽" : "🟨"} ${isGoal ? t("live.goal") : (ev.kind === "card" ? t("live.card") : t("live.event"))}: ${ev.home} ${ev.score} ${ev.away}`;
  const parts = [ev.player, ev.detail, ev.minute ? ev.minute + "'" : ""].filter(Boolean);
  LIVE_EVENTS.unshift(ev);
  LIVE_EVENTS = LIVE_EVENTS.slice(0, 8);
  if (alertsOn()) {
    beep(ev.kind);
    if (navigator.vibrate) { try { navigator.vibrate(isGoal ? [90, 60, 90] : 45); } catch (e) {} }
  }
  toast(title + (parts.length ? " — " + parts.join(" · ") : ""), 12000, true);
  pushAlert({ kind: ev.kind, title, body: parts.join(" · ") });
  if (alertsOn() && "Notification" in window && Notification.permission === "granted") {
    try {
      const n = new Notification(title, { body: parts.join(" · "), tag: "mb-" + isGoal + ev.home + ev.minute, icon: "/assets/icon-192.png" });
      n.onclick = () => window.focus();
    } catch (err) { /* ignore */ }
  }
  renderLiveEvents();
}
function renderLiveEvents() {
  const el = $("#liveEvents");
  if (!el) return;
  el.innerHTML = LIVE_EVENTS.length
    ? LIVE_EVENTS.map((ev) => `<div class="liveevent ${esc(ev.kind)}">
        <b>${ev.kind === "goal" ? "⚽" : "🟨"} ${esc(ev.minute || "")}'</b>
        <span>${esc(ev.home)} <b>${esc(ev.score)}</b> ${esc(ev.away)}</span>
        <span class="mini">${esc([ev.player, ev.detail].filter(Boolean).join(" · "))}</span>
      </div>`).join("")
    : `<div class="mini">${esc(t("live.noEvents"))}</div>`;
}

/* ------------------------------------------------- alert bubble (scrollable feed) */
const ALERTS_KEY = "mb_alerts_feed_v1";
let ALERTS = [];
let ALERT_UNREAD = 0;
function loadAlerts() {
  try { ALERTS = JSON.parse(localStorage.getItem(ALERTS_KEY) || "[]") || []; } catch (err) { ALERTS = []; }
  renderAlertFeed();
}
function saveAlerts() {
  try { localStorage.setItem(ALERTS_KEY, JSON.stringify(ALERTS.slice(0, 60))); } catch (err) { /* full quota */ }
}
function timeAgo(ts) {
  const s = Math.max(1, Math.round((Date.now() - ts) / 1000));
  if (s < 60) return s + "s";
  if (s < 3600) return Math.round(s / 60) + "m";
  return Math.round(s / 3600) + "h";
}
function pushAlert(entry) {
  ALERTS.unshift(Object.assign({ ts: Date.now() }, entry));
  ALERTS = ALERTS.slice(0, 60);
  saveAlerts();
  const panel = $("#alertPanel");
  if (panel && panel.classList.contains("hidden")) {
    ALERT_UNREAD += 1;
  } else if (panel) {
    ALERT_UNREAD = 0;
  }
  renderAlertFeed();
}
function renderAlertFeed() {
  const feed = $("#alertFeed");
  const count = $("#alertCount");
  if (count) {
    count.textContent = ALERT_UNREAD > 9 ? "9+" : String(ALERT_UNREAD);
    count.classList.toggle("hidden", ALERT_UNREAD === 0);
  }
  const bub = $("#alertBubble");
  if (bub) bub.classList.toggle("has-new", ALERT_UNREAD > 0);
  if (!feed) return;
  feed.innerHTML = ALERTS.length
    ? ALERTS.map((a) => `<div class="alertitem ${esc(a.kind || "info")}">
        <span class="aico">${a.kind === "goal" ? "⚽" : (a.kind === "card" ? "🟨" : (a.kind === "won" ? "✅" : (a.kind === "lost" ? "❌" : "🔔")))}</span>
        <span class="atext"><b>${esc(a.title)}</b>${a.body ? `<br><span class="mini">${esc(a.body)}</span>` : ""}</span>
        <span class="atime">${esc(timeAgo(a.ts))}</span>
      </div>`).join("")
    : `<div class="mini" style="padding:10px">${esc(t("alerts.empty"))}</div>`;
}
function toggleAlertPanel(force) {
  const panel = $("#alertPanel");
  if (!panel) return;
  const show = force != null ? force : panel.classList.contains("hidden");
  panel.classList.toggle("hidden", !show);
  if (show) { ALERT_UNREAD = 0; renderAlertFeed(); }
}
async function pollLive(force) {
  const d = await api(`/api/live?player=${encodeURIComponent(walletPlayer())}${force ? "&force=1" : ""}`);
  renderLiveBar(d);
  (d.events || []).forEach(notifyEvent);
  return d;
}
function renderLiveBar(d) {
  const el = $("#liveBar");
  if (!el) return;
  const live = ((d && d.fixtures) || []).filter((f) => f.found);
  if (!d || !d.active || !live.length) {
    if (!LIVE_EVENTS.length) { el.classList.add("hidden"); return; }
  }
  const rows = live.map((f) => `
    <div class="liveitem" data-tip="tip.liveItem">
      <span class="min">${f.minute != null ? f.minute + "'" : (f.status || "")}</span>
      <span class="lteams">${esc(f.home)} <b>${f.score.home} – ${f.score.away}</b> ${esc(f.away)}</span>
      <span class="badge-src">${esc(f.league_live || f.league || "")}</span>
    </div>`).join("");
  el.innerHTML = `
    <div class="liverow">
      <span class="livedot"></span>
      <b data-tip="tip.liveBar">${esc(t("live.title"))}</b>
      <span class="mini">${live.length} ${esc(t("live.matches"))}${d.polled === false && d.reason === "throttled" ? " · " + esc(t("live.waiting")) : ""}</span>
      <button id="alertsToggle" class="btn small" data-tip="tip.alerts">${alertsOn() ? "🔔 " + esc(t("live.on")) : "🔕 " + esc(t("live.off"))}</button>
    </div>
    ${rows}`;
  el.classList.remove("hidden");
  const tgl = $("#alertsToggle");
  if (tgl) tgl.addEventListener("click", toggleAlerts);
}
async function toggleAlerts() {
  const on = !alertsOn();
  setAlerts(on);
  if (on) {
    beep("card"); // also unlocks audio on iOS inside the user gesture
    if ("Notification" in window && Notification.permission === "default") {
      try { await Notification.requestPermission(); } catch (e) {}
    }
    toast(t("live.alertsOn"));
  } else {
    toast(t("live.alertsOff"));
  }
  startLivePolling(true);
}
async function startLivePolling(immediate) {
  clearInterval(LIVE_TIMER);
  try {
    const d = await pollLive(!!immediate);
    if (!d || !d.active) return; // nothing live -> no polling, no quota spent
    LIVE_TIMER = setInterval(() => pollLive(false).catch(() => {}), 60000);
  } catch (err) { /* ignore */ }
}
function switchTab(name) {
  $$(".tab").forEach((b) => b.classList.toggle("active", b.getAttribute("data-tab") === name));
  $$(".panel").forEach((p) => p.classList.toggle("active", p.id === "tab-" + name));
  if (name === "matches" && !LAST_FIXTURES.length) loadFixtures();
  if (name === "matches" && LAST_FIXTURES_RESP) showCacheBadge(LAST_FIXTURES_RESP);
  if (name === "mine") { loadWallet(); loadBets(); }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ------------------------------------------------------------------ init */
function init() {
  applyTheme(localStorage.getItem("mb_theme") || "dark");
  applyI18n();
  cachePrune();
  loadAlerts();
  maybeShowIosBanner();

  $("#langBtn").addEventListener("click", (e) => { e.stopPropagation(); $("#langMenu").classList.toggle("hidden"); });
  $$("#langMenu button").forEach((b) => b.addEventListener("click", () => setLang(b.getAttribute("data-lang"))));
  document.addEventListener("click", () => $("#langMenu").classList.add("hidden"));

  $("#themeBtn").addEventListener("click", () => {
    applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
  });

  $("#limitsPill").addEventListener("click", () => {
    $("#limitsOverlay").classList.remove("hidden");
    renderLimitsBody();
    renderCacheInfo();
  });
  $("#limitsClose").addEventListener("click", () => $("#limitsOverlay").classList.add("hidden"));
  $("#limitsOverlay").addEventListener("click", (e) => { if (e.target.id === "limitsOverlay") $("#limitsOverlay").classList.add("hidden"); });
  $("#reportClose").addEventListener("click", closeReport);
  $("#reportOverlay").addEventListener("click", (e) => { if (e.target.id === "reportOverlay") closeReport(); });
  $("#watchClose").addEventListener("click", closeWatch);
  $("#watchOverlay").addEventListener("click", (e) => { if (e.target.id === "watchOverlay") closeWatch(); });
  $("#watchMin").addEventListener("click", watchMinimize);
  $("#watchFull").addEventListener("click", watchFullscreen);
  $("#watchRestart").addEventListener("click", watchRestart);
  $("#watchMiniRestore").addEventListener("click", watchRestore);
  $("#watchMiniClose").addEventListener("click", () => { $("#watchMini").classList.add("hidden"); restoreWatchPlayer(); stopWatchVideo(); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (!$("#watchOverlay").classList.contains("hidden")) closeWatch();
      else if (!$("#reportOverlay").classList.contains("hidden")) closeReport();
    }
  });
  $("#limitsRefresh").addEventListener("click", async () => { await fetchLimits(true); renderLimitsBody(); toast("✓"); });
  $("#cacheClear").addEventListener("click", async () => {
    const n = clearLocalCache();
    await api("/api/cache/clear?scope=all", { method: "POST" }, { force: true });
    LAST_FIXTURES = [];
    $("#cacheBadge").classList.add("hidden");
    toast(t("cache.cleared") + " (" + n + ")");
    renderCacheInfo();
  });
  const alertToggle = $("#alertToggle");
  if (alertToggle) alertToggle.addEventListener("click", (e) => { e.stopPropagation(); toggleAlertPanel(); });
  const alertClose = $("#alertClose");
  if (alertClose) alertClose.addEventListener("click", (e) => { e.stopPropagation(); toggleAlertPanel(false); });
  const alertClear = $("#alertClear");
  if (alertClear) alertClear.addEventListener("click", (e) => {
    e.stopPropagation();
    ALERTS = []; ALERT_UNREAD = 0; saveAlerts(); renderAlertFeed();
  });

  $$(".tab").forEach((b) => b.addEventListener("click", () => switchTab(b.getAttribute("data-tab"))));
  $$("#matchFilters .chip").forEach((b) => b.addEventListener("click", () => {
    MATCH_FILTER = b.getAttribute("data-mfilter") || "";
    $$("#matchFilters .chip").forEach((x) => x.classList.toggle("active", x === b));
    if (LAST_FIXTURES.length) renderMatches(LAST_FIXTURES, LAST_NOTES);
  }));
  setInterval(async () => {
    if (!LAST_FIXTURES.some((m) => matchStatus(m) === "live")) return;
    await loadLiveScores();
    renderMatches(LAST_FIXTURES, LAST_NOTES);
  }, 120000);

  $("#btnAnalyze").addEventListener("click", async () => {
    const v = $("#homeSearch").value.trim();
    if (!v) { toast(t("home.searchPlaceholder")); return; }
    $("#result").innerHTML = "";
    $("#loader").classList.remove("hidden");
    const L = startLoader();
    try {
      const parts = v.split(/\s+vs\s+|\s+-\s+|\s+—\s+/i).map((p) => p.trim()).filter(Boolean);
      if (parts.length >= 2) {
        // two teams typed explicitly: exact fixture -> straight to the analysis,
        // otherwise show what we DO have for each of them
        const items = await searchMatches(parts[0]);
        const a = normName(parts[0]), b = normName(parts[1]);
        const exact = items.find((i) => {
          const h = normName(i.home), w = normName(i.away);
          return ((h.includes(a) || a.includes(h)) && (w.includes(b) || b.includes(w)))
            || ((h.includes(b) || b.includes(h)) && (w.includes(a) || a.includes(w)));
        });
        if (exact) { L.done(true); runAnalysis(exact.home, exact.away, exact.id, exact.commence_time); return; }
        const res = await showTeamMatches(v);
        if (res === "listed") L.done(true); else if (res === "none") L.fail();
        return;
      }
      // one team (or a name with several words): list ALL its matches, analyse it if there is only one
      const res = await showTeamMatches(v);
      if (res === "listed") L.done(true); else if (res === "none") L.fail();
    } catch (err) {
      L.fail();
      showNotFound(v);
    }
  });
  $("#homeSearch").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#btnAnalyze").click(); });
  $("#btnRecommend").addEventListener("click", recommend);

  $$("#dateChips button").forEach((b) => b.addEventListener("click", () => {
    $$("#dateChips button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    DAYS = b.getAttribute("data-days");
    loadFixtures();
  }));
  $("#btnMatches").addEventListener("click", loadFixtures);
  $("#matchSearch").addEventListener("keydown", (e) => { if (e.key === "Enter") loadFixtures(); });

  bindSuggest("#homeSearch", runAnalysis);

  renderChatChips();
  maybeShowTouchHint();
  $("#chatSend").addEventListener("click", () => sendChat($("#chatInput").value.trim()));
  $("#chatInput").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#chatSend").click(); });

  fetchLimits(false).then(() => { if (LIMITS && LIMITS.overall === "red") toast(LIMITS.providers.find((p) => p.level === "red")?.message || ""); });
  loadWallet().catch(() => {});
  const playerInput = $("#playerInput");
  if (playerInput) {
    playerInput.value = walletPlayer();
    playerInput.addEventListener("change", () => setWalletPlayer(playerInput.value));
  }
  const settleBtn = $("#settleBtn");
  if (settleBtn) settleBtn.addEventListener("click", settleNow);
  const resetBtn = $("#resetBtn");
  if (resetBtn) resetBtn.addEventListener("click", resetWallet);
  const refreshOdds = $("#refreshOdds");
  if (refreshOdds) refreshOdds.addEventListener("click", async () => {
    if (!window.confirm(t("limits.refreshConfirm"))) return;
    toast(t("limits.refreshing"), 15000);
    const d = await api("/api/refresh", null, { force: true });
    if (d.error) { toast("⚠️ " + d.error, 9000); return; }
    toast(t("limits.refreshed", { n: d.requests_used, left: d.requests_remaining }), 9000);
    fetchLimits(true);
    LAST_FIXTURES = [];
    loadFixtures(true);
  });
  loadWatch().catch(() => {});
  startLivePolling(false).catch(() => {});
  checkVersion();
  setInterval(checkVersion, 300000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) checkVersion(); });
  setInterval(() => { if (WATCH.length || LIVE_EVENTS.length) startLivePolling(false).catch(() => {}); }, 180000);
  setInterval(() => fetchLimits(false), 120000);
}

document.addEventListener("DOMContentLoaded", init);
