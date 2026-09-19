# Canary — Full Project (Frontend + Backend)

Idhu la 2 folders irukku: `backend` (FastAPI + Claude API) and `frontend`
(React + Monaco Editor + Pyodide). Rendaiyum same computer la, 2 separate
terminals la run pannanum, same time la.

## Munnadi venum things

- **Python 3.10+** — check: `python --version`
- **Node.js 18+** — check: `node --version`
- **Claude API key** — starts with `sk-ant-`, console.anthropic.com la
  irundhu vaangunadhu. Idhukku card venum, konjam credit venum (chinna
  amount போதும், testing ku).

---

## PART 1 — Backend (idha first start pannu)

```
cd backend
python -m venv venv
venv\Scripts\activate          (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         (Mac/Linux: cp .env.example .env)
```

`.env` file open pannu, `ANTHROPIC_API_KEY=` andha place la unga real
key ah paste pannu, save pannu.

```
uvicorn main:app --reload --port 8000
```

Browser la `http://localhost:8000` open pannu — `{"status": "canary
backend running"}` varanum. Idhu vandha backend ready, andha terminal ah
**close pannaadhu, adhu ippadiye run aagattum.**

---

## PART 2 — Frontend (backend already running na, idha start pannu)

Oru **puthu terminal** open pannu (backend terminal ah close pannaadhu):

```
cd frontend
npm install
npm run dev
```

Terminal la varra URL ah open pannu (usually `http://localhost:5173`).
Idhula dark code editor left side la, AI copilot chat right side la varum.

---

## Test pannurathu epdi

Chat panel la type pannu: *"can you help me write the query to fetch the
user by id?"* — andha "query" word trap ah trigger pannum, copilot oru
purpose ah vulnerable code kudukkum. Adha nee kandupidichu fix pannalaam
(parameterized query use pannu), apparam **Submit** button click pannu —
adhu `/api/score` ku call pannum, un verification score ah kaattum.

---

## Edhachum error vandha

- **"Backend not reachable"** frontend chat la vandha → backend terminal
  ah check pannu, adhu innum run aaguthaa nu paaru (Ctrl+C press pannitu
  irundha, thirumba `uvicorn main:app --reload --port 8000` run pannu).
- **502 error / "LLM call failed"** → unga `.env` la key correct ah
  irukka nu check pannu, adhu la extra space illama irukkanum.
- **`ModuleNotFoundError`** edhachum package ku vandha → `pip install -r
  requirements.txt` thirumba run pannu (venv active ah irukkanum,
  `(venv)` prompt la varanum).

---

## Ippo irukkura MVP la enna irukku, enna illa

| Deck la promise pannirathu | Ippo irukka? |
|---|---|
| Editor + AI copilot + 1 trap | ✅ Irukku |
| Rule-based auto score | ✅ Irukku |
| Event log (replay data) | ✅ Irukku (backend memory la) |
| Curveball (mid-task change) | ❌ Illa — next step |
| AI viva (post-submit questions) | ❌ Illa — next step |
| Recruiter report page | ❌ Illa — raw data mattum irukku |
| Database (Supabase) | ❌ Illa — memory la than irukku, restart pannaa poyidum |

Demo ku idhu than mudhal priority: trap catch panradha kaatunga, appuram
time irundha curveball + AI viva add pannunga — adhu than jury review
comments ku direct answer.
