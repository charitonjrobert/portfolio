import requests, json

csv = """2025-12-26,Newcastle United,Liverpool,1,1
2025-10-04,Liverpool,Newcastle United,2,1
2025-05-10,Newcastle United,Liverpool,1,1
2025-01-25,Liverpool,Newcastle United,3,1
2024-10-15,Newcastle United,Liverpool,1,1
2024-08-20,Liverpool,Newcastle United,2,0
2024-04-02,Newcastle United,Liverpool,1,1
2024-01-11,Liverpool,Newcastle United,1,1
2025-09-14,Arsenal,Coventry City,3,0
2025-04-06,Coventry City,Arsenal,0,2
2025-02-22,Arsenal,Coventry City,3,0
2024-11-30,Coventry City,Arsenal,1,2
"""

r = requests.post("http://127.0.0.1:8000/api/history", json={"csv": csv}, timeout=30)
print("POST:", r.json())

r2 = requests.get("http://127.0.0.1:8000/api/history?team_a=Newcastle%20United&team_b=Liverpool", timeout=30)
data = r2.json()
print("H2H:", json.dumps(data.get("h2h"), ensure_ascii=False)[:300])
print("SCORELINE FREQ:", json.dumps(data.get("scoreline_frequency"), ensure_ascii=False))
print("REPEATED:", json.dumps(data.get("repeated_patterns"), ensure_ascii=False))
print("LAMBDAS:", json.dumps(data.get("lambdas")))