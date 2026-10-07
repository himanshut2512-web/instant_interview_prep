# instant_interview_prep

**InstantInterviewPrep** is an AI agent that turns **your resume + a job description + your years of experience + the
target company** into a complete, personalised interview prep kit. It researches how that company interviews on the
live web, finds the questions candidates actually reported, and builds five study dashboards with 50+ questions,
model answers, scenario walkthroughs and a scored MCQ quiz.

> React (Vite) frontend · Python (FastAPI) backend · Claude agent with live web research.
> Works fully offline in **demo mode** when no API key is configured, which makes it handy as a hackathon fallback.

## What you get

| Dashboard | What's inside |
|---|---|
| **Overview** | Fit summary, strengths and gaps, a ready-to-say "Tell me about yourself" pitch, interview rounds, what the company looks for, questions candidates reported, topic priority, study plan, research report and sources |
| **1. Crash Revision** | One revision sheet per topic: key concepts, explanation, code example, pitfalls, how it is tested, cheat sheet, likely questions |
| **2. Theoretical** | Level-wise (beginner / intermediate / advanced) and 🔥 hot questions, each with a model answer, the key points interviewers listen for, a delivery tip and follow-ups |
| **3. Practical** | Coding, SQL and hands-on problems with the approach, a complete solution, complexity and edge cases |
| **4. Scenario-based** | Real on-the-job situations with a step-by-step framework to tackle them, a model answer, what the interviewer looks for and mistakes to avoid |
| **5. Quiz** | MCQs with instant explanations (why each option is right or wrong), a score, accuracy by topic and attempt history |

Everything is dynamic: the content is generated from your inputs, and every dashboard has **Generate more** for fresh
questions (by level, topic and an optional focus). You can also:

- **Practice mode**: hide the model answers, type your own, and get it scored out of 10 with specific feedback
- **Drill mode**: go through any question bank one card at a time (Space to reveal, ← / → to move, M to mark
  mastered, R for review later), and flip the revision key concepts as flashcards
- **Track progress**: mark questions *mastered* or *review later*, mark topics revised, and see readiness meters
- **Export**: download the whole kit as Markdown, or open a print view to save it as a PDF
- Keep a history of prep kits, switch between light and dark themes, and use it on mobile

## How the agent works

```mermaid
flowchart LR
    A["Resume + JD + years of experience + company<br/>(+ optional notes and files)"] --> B[Parse & extract text]
    B --> C{Company research}
    C -->|Claude web_search + web_fetch| D[Research report + sources]
    C -.->|web search unavailable| C2[DuckDuckGo results + page extracts] --> D
    C -.->|no web access at all| C3[Claude's own knowledge, labelled as such] --> D
    D --> E["Blueprint: profile, company intel,<br/>topic plan, study plan"]
    E --> F1[Crash revision notes]
    E --> F2[Theory × 3 levels]
    E --> F3[Practical × 3 levels]
    E --> F4[Scenario × 3 levels]
    E --> F5[MCQs × 3 levels]
    F1 & F2 & F3 & F4 & F5 --> G[Dashboards fill in live]
```

1. **Parse** the resume, JD and any attachments (PDF, DOCX, TXT, MD). Claude reads scanned PDFs too.
2. **Research** with Claude's server-side web search and web fetch: interview experiences (Glassdoor, AmbitionBox,
   GeeksforGeeks, LeetCode Discuss, Reddit…), rounds, reported questions, culture and recent news. Every search,
   page read and progress note streams into the live agent log.
3. **Blueprint**: a structured-output call matches your resume to the JD and the research. It produces your strengths
   and gaps, your pitch, the interview rounds and a weighted topic plan.
4. **Generate in parallel**: revision notes plus theory, practical, scenario and quiz batches at each level. The level
   mix follows your experience (freshers get more fundamentals, seniors more advanced and leadership questions).
   Questions reported for the company are marked 🔥 with their source.
5. **Dashboards unlock as soon as each section is ready**, so you can start reading while the agent is still writing.

| Prep depth | Theory | Practical | Scenario | MCQs | Topics |
|---|---|---|---|---|---|
| Quick | 15 | 10 | 10 | 15 | 8 |
| Standard (default) | 24 | 15 | 15 | 25 | 10 |
| Deep | 36 | 21 | 21 | 36 | 14 |

## Quick start

**Prerequisites:** Python 3.10+, Node.js 20.19+ (or 22.12+). An [Anthropic API key](https://console.anthropic.com) is
needed for AI mode; without one the app runs in demo mode.

### Option A: one command (development)

```bash
./scripts/dev.sh          # macOS / Linux / Git Bash
.\scripts\dev.ps1         # Windows PowerShell
```

The script creates the virtualenv, installs dependencies and copies `backend/.env.example` to `backend/.env`. It then
starts the API on :8000 and the app on **http://localhost:5173**.

### Option B: step by step

```bash
# 1. backend
cd backend
python3 -m venv .venv                # Windows: python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                 # Windows: copy .env.example .env  -> then add ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000

# 2. frontend (second terminal)
cd frontend
npm install
npm run dev                          # open http://localhost:5173
```

### Single server (for demos and deployment)

```bash
cd frontend && npm run build                      # produces frontend/dist
cd ../backend && uvicorn app.main:app --port 8000 # serves the API and the app on http://localhost:8000
```

### Docker

```bash
ANTHROPIC_API_KEY=sk-ant-... docker compose up --build    # omit the key for demo mode
# open http://localhost:8000  (data persists in the prep-data volume)
```

## AI mode vs demo mode

| | AI mode (`ANTHROPIC_API_KEY` set) | Demo mode (no key) |
|---|---|---|
| Company research | Live web search and page reading, with sources | None (generic interview process, clearly labelled) |
| Questions and answers | Freshly generated for your resume, JD, company and experience | Picked from a built-in 13-topic knowledge base matched to your JD and resume |
| Hot questions | Questions reported online for the company + very common staples | Classic, frequently asked staples |
| Generate more | New content, with an optional focus | Unused knowledge-base content |
| Answer feedback | Claude grades your answer and rewrites an improved version | Keyword coverage scoring against the key points |
| Time for a standard kit | A few minutes, depending on model, effort and rate limits (sections appear progressively) | A few seconds |

The demo knowledge base covers Python, SQL, Statistics and A/B testing, Machine Learning, Deep Learning, NLP and GenAI,
Data Engineering, Cloud and MLOps, BI, DSA, System Design, Case Studies and Guesstimates, and Behavioural/HR.

## Configuration (`backend/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(empty)* | Enables AI mode |
| `PREP_CLAUDE_MODEL` | `claude-opus-5-5` | Model for research and generation (e.g. `claude-sonnet-5-5` for faster, cheaper runs) |
| `PREP_CLAUDE_EFFORT` | `medium` | Thinking effort for generation: `low` … `max` (lower is faster and cheaper) |
| `PREP_RESEARCH_EFFORT` | `medium` | Thinking effort for the research step |
| `PREP_ENABLE_WEB_SEARCH` | `true` | Use Claude's web search/fetch (falls back to DuckDuckGo automatically) |
| `PREP_ENABLE_FALLBACKS` | `true` | Server-side refusal fallbacks (a declined request is retried on a fallback model) |
| `PREP_MAX_CONCURRENCY` | `6` | Parallel Claude calls; lower it if you hit rate limits |
| `PREP_DEMO_MODE` | `false` | Force demo mode even with a key |
| `PREP_DEMO_STEP_DELAY` | `0.6` | Seconds between demo steps (so the agent timeline is visible) |
| `PREP_DATA_DIR` | `backend/data` | Where the SQLite database lives |
| `PREP_MAX_UPLOAD_MB` | `10` | Upload size limit per file |

The new-prep form also has a checkbox to run a single kit in demo mode when a key is set.

## API

| Method & path | Description |
|---|---|
| `GET /api/health` | Mode (ai/demo), model, web-search flag, counts per depth |
| `GET /api/sample` | Sample inputs (fictional candidate) for "Try a sample" |
| `POST /api/sessions` | Multipart form: `company`, `years_experience`, `resume_file` or `resume_text`, `jd_file` or `job_description`, optional `role`, `extra_notes`, `extra_files[]`, `depth`, `mode` |
| `GET /api/sessions` | List prep kits |
| `GET /api/sessions/{id}` | Full kit: content, progress, user state, quiz attempts |
| `GET /api/sessions/{id}/status` | Lightweight progress for polling (steps, live log, sources, ready sections) |
| `POST /api/sessions/{id}/generate` | `{section, count, level, topic, focus}`: generate more questions or a new revision topic |
| `POST /api/sessions/{id}/evaluate` | `{section, item_id, answer}`: score a practice answer |
| `PUT /api/sessions/{id}/state` | Mark a question mastered/review, or a topic revised |
| `POST /api/sessions/{id}/quiz-attempts` | Save a quiz score |
| `GET /api/sessions/{id}/export.md` | Download the whole kit as Markdown |
| `POST /api/sessions/{id}/retry` | Regenerate a kit |
| `DELETE /api/sessions/{id}` | Delete a kit |

Interactive API docs are served at `http://localhost:8000/docs`.

## Project structure

```
backend/
  app/
    main.py                 FastAPI routes (+ serves frontend/dist when built)
    agent/
      llm.py                Claude client: streaming, structured outputs, web research, refusal fallbacks
      research.py           live web research -> DuckDuckGo fallback -> model-knowledge fallback
      prompts.py, schemas.py  prompts and JSON schemas for every generation step
      pipeline.py           orchestration: research -> blueprint -> parallel generation -> top-up
      plan.py               depth targets, experience-based level mix, batching
      progress.py           live progress timeline, log and incremental results
      actions.py            generate-more and answer evaluation
      demo.py               offline demo agent (knowledge base + heuristic profile and feedback)
    knowledge_base/         13 offline topics (revision notes + questions at three levels)
    parsing.py, storage.py, models.py, export.py, samples.py
  tests/                    pytest suite (API, units, AI pipeline with a fake Claude client)
frontend/
  src/pages/                Landing, NewPrep, Workspace, Overview, Revision, QuestionBank, Quiz, History, PrintView
  src/components/           question cards, drill deck, practice panel, filters, agent progress, charts, dialogs…
  src/styles/               design tokens (light/dark, a colour identity per dashboard) and per-area stylesheets
  src/hooks/, src/lib/      session polling, scroll helpers, motion presets, progress and formatting helpers
scripts/                    dev.sh / dev.ps1
Dockerfile, docker-compose.yml
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest            # 55 tests; the AI pipeline is tested with a fake Claude client (no key or network needed)
```

## Demo script for the hackathon

1. Open the app and click **Try a live sample** on the landing page (or **Build my prep kit** to use your own resume
   and JD), then **Build my prep kit** on the form.
2. Show the **live agent log**: searches, pages read and sources appear as the agent researches the company.
3. Open **Overview** while the rest generates: the pitch, the gaps, the interview rounds and the topic priority (click
   a bar to jump to its revision notes).
4. **Theoretical**: filter *Advanced* + *Hot only*, turn on **Practice mode**, type an answer and show the AI feedback.
5. **Scenario-based**: walk through the step-by-step approach for one question.
6. **Quiz**: take a 5-question quiz, then show the score, accuracy by topic and the "Revise next" links.
7. **Generate more** on any dashboard, then **Export Markdown** / **Print**.

## Notes

- **Privacy:** everything is stored locally in SQLite (`backend/data/prep.db`). In AI mode, your resume, JD and notes
  are sent to the Anthropic API to generate the kit.
- **Research quality** depends on what has been publicly reported about the company. The agent is instructed never
  to attribute a question to a source that didn't contain it, and it labels research that comes from model knowledge.
- **Cost and time** scale with depth, model and effort. For faster, cheaper kits, use `PREP_CLAUDE_EFFORT=low` or
  `PREP_CLAUDE_MODEL=claude-sonnet-5-5`.
