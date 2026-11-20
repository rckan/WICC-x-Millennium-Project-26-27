# The Impact of Agentic AI on Service-Based Industries

**WICC x Millennium Project, Spring 2027**

> **Research question:** To what extent is the rise of agentic AI disrupting traditional service-based industries, and how is this transformation affecting consumer behavior, business performance, and employment?

## Repo map

| Folder | What goes here |
|---|---|
| [`docs/`](docs/) | Proposal, research questions, timeline, team roles |
| [`research/themes/`](research/themes/) | One working doc per key area of exploration (findings → synthesis) |
| [`research/sources.md`](research/sources.md) | Master bibliography: every source we cite, logged once |
| [`research/notes/`](research/notes/) | Reading notes on individual reports/articles (copy `_template.md`) |
| [`case-studies/`](case-studies/) | Industry deep dives: incumbent vs. AI-agent alternative (copy `_template.md`) |
| [`analysis/`](analysis/) | Data, notebooks, figures, and the traditional-vs-AI comparison framework |
| [`analysis/financials/`](analysis/financials/) | Stock prices, fundamentals, and earnings commentary for companies in each sector |
| [`presentation/`](presentation/) | Slide outline, speaker notes, final assets |

## Workflow

1. **Find a source** → add a row to [`research/sources.md`](research/sources.md) with an ID (e.g. `S01`).
2. **Read it** → copy [`research/notes/_template.md`](research/notes/_template.md) to `research/notes/S01-short-name.md`.
3. **Pull out findings** → paste key claims (with source ID) into the matching file in `research/themes/`.
4. **Industry evidence** → build out a case study in `case-studies/`.
5. **Numbers** → stock and financial analysis in `analysis/financials/`; raw data in `analysis/data/raw/`, notebooks in `analysis/notebooks/`, charts in `analysis/figures/`.
6. **Synthesize** → each theme's "So what?" section feeds [`presentation/outline.md`](presentation/outline.md).

## Conventions

- Every factual claim carries a source ID, e.g. `[S04]`. No ID, no slide.
- File names: lowercase, hyphenated (`booking-com-earnings-q3.md`).
- Mark unfinished thoughts with `TODO:` so `grep -r TODO` shows outstanding work.
- One branch per person or per workstream; merge to `main` via PR.
