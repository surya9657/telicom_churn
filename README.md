# Signal — Customer Churn Prediction System

A full-stack, production-style customer churn analytics platform. An admin can manage
customers, run real machine-learning churn predictions, track risk levels, and explore
churn statistics through an interactive dashboard.

**Stack:** FastAPI + SQLAlchemy + PostgreSQL on the backend, a trained scikit-learn
Random Forest model for predictions, and a vanilla HTML/CSS/JS + Chart.js frontend.

```
Frontend (HTML/CSS/JS) → FastAPI REST API → Service layer → SQLAlchemy ORM → PostgreSQL
                                          ↘ ML preprocessing → Random Forest → risk classification
```

---

## Project layout

```
ml/                     Offline ML pipeline (data, training, evaluation, saved model)
  data/                 Dataset + generator script
  model/                Trained artifacts (churn_model.pkl, metrics.json, ...)
  preprocess.py         Shared feature schema + ColumnTransformer
  train.py               End-to-end training pipeline
  evaluate.py            Metric computation (accuracy/precision/recall/F1/ROC-AUC)

backend/
  app/
    main.py             FastAPI app, CORS, startup, error handlers
    database.py         SQLAlchemy engine/session
    core/               Settings + JWT/password security
    models/             SQLAlchemy ORM models (users, customers, predictions)
    schemas/            Pydantic request/response schemas
    routers/            REST endpoints (auth, customers, predictions, dashboard, model)
    services/           Business logic (customer + prediction workflows)
    ml/                 Model loader + predictor (feature mapping, inference)
  tests/                pytest + FastAPI TestClient tests
  requirements.txt
  .env.example
  Dockerfile

frontend/
  *.html                8 pages: login, dashboard, customers, customer detail,
                         prediction, prediction history, high-risk, model performance
  css/style.css          Design system (tokens, components)
  js/                    auth.js (API client + auth), layout.js (shared nav shell),
                          charts.js (Chart.js factories), and one script per page

docker-compose.yml       PostgreSQL + FastAPI backend
```

---

## 1. Train the ML model (do this first)

The trained model is **not** committed to git (see `.gitignore`) — generate it locally:

```bash
cd ml
pip install -r ../backend/requirements.txt   # scikit-learn, pandas, numpy, joblib, etc.
python data/generate_dataset.py              # creates ml/data/telco_churn.csv
python train.py                              # trains + evaluates + saves artifacts
```

> **About the dataset:** this environment could not reach the internet to download the
> real IBM Telco Customer Churn dataset from Kaggle, so `generate_dataset.py` produces a
> synthetic dataset with the **exact same columns** and realistic churn-driving
> relationships (month-to-month contracts, low tenure, high monthly charges, electronic
> check payment, etc. all increase churn probability, matching the real dataset's known
> patterns). **If you have internet access**, download the real dataset ("Telco Customer
> Churn" by blastchar on Kaggle) and save it as `ml/data/telco_churn.csv` with the same
> column names — `train.py` doesn't care which source the CSV came from.

This produces:
- `ml/model/churn_model.pkl` — the trained Random Forest pipeline (preprocessing + classifier), used by the API
- `ml/model/preprocessing_pipeline.pkl` — the fitted ColumnTransformer, standalone
- `ml/model/churn_model_logreg.pkl` — Logistic Regression comparison model
- `ml/model/metrics.json` — evaluation metrics for both models, served at `/api/model/metrics`

Sample results from a training run in this environment (yours will vary slightly by seed/data):

| Metric | Random Forest | Logistic Regression |
|---|---|---|
| Accuracy | ~0.77 | ~0.74 |
| Precision | ~0.48 | ~0.45 |
| Recall | ~0.60 | ~0.74 |
| F1 Score | ~0.54 | ~0.56 |
| ROC-AUC | ~0.80 | ~0.81 |

## 2. Run PostgreSQL + backend

### Option A — Docker (recommended)

```bash
docker-compose up --build
```

This starts PostgreSQL on `localhost:5432` and the FastAPI backend on `localhost:8000`
(API docs at `http://localhost:8000/docs`). The `ml/` folder is mounted read-only into
the backend container so it always uses your locally trained model.

### Option B — Run locally

```bash
# 1. Start PostgreSQL yourself (or via `docker run postgres:16-alpine`) and create a database.
# 2. cd backend
cp .env.example .env        # edit DATABASE_URL / SECRET_KEY as needed
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On first startup the backend automatically creates all tables and a default admin user
(`admin` / `Admin123!` — override via `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD`
in `.env`).

## 3. Run the frontend

The frontend is static HTML/CSS/JS — no build step. Serve it with any static file server
so the browser's `fetch` calls aren't blocked by `file://` restrictions, e.g.:

```bash
cd frontend
python3 -m http.server 5500
# open http://localhost:5500/login.html
```

By default the frontend calls the API at `http://localhost:8000`. To point at a
different backend URL, set `window.CHURN_API_BASE_URL` in a small inline script tag
before `js/auth.js` loads on each page.

Log in with the default admin credentials, then:
1. **Customers** → add a customer manually or import a CSV
2. **Predict Churn** → enter/load a profile and get a real model-scored probability
3. **Dashboard** → see live stats and charts built from your PostgreSQL data
4. **High-Risk Customers** / **Prediction History** → drill into results
5. **Model Performance** → compare Random Forest vs. Logistic Regression

## 4. Run backend tests

Tests use an in-memory SQLite database (via dependency override) so they run without a
live Postgres instance, and they exercise the real trained model for predictions — run
`python ml/train.py` before running tests.

```bash
cd backend
pytest -v
```

---

## Design notes

- **Risk thresholds are configurable in one place**: `app/core/config.py`
  (`RISK_LOW_MAX` / `RISK_MEDIUM_MAX`), not scattered across the frontend.
- **Training and inference share identical preprocessing.** The saved model is a single
  scikit-learn `Pipeline` (ColumnTransformer + RandomForestClassifier); the API never
  re-implements feature engineering separately from training.
- **Predictions are real model output.** `model.predict()` / `model.predict_proba()` are
  the only source of churn probabilities — there are no hardcoded or random values.
- **CSV import never silently drops bad rows** — every row is validated with the same
  Pydantic schema used for the "Add Customer" form, and the summary reports imported /
  duplicate / failed counts with per-row error messages.
- **Errors never leak stack traces.** A global FastAPI exception handler returns a clean
  500 message and logs the real exception server-side.

## Security

- Passwords hashed with bcrypt (passlib)
- JWT bearer tokens (python-jose), verified on every protected route
- All configuration (DB credentials, JWT secret, model path) via environment variables —
  nothing hardcoded, `.env` is git-ignored
- CORS restricted to configured origins
- All database access goes through SQLAlchemy ORM (no raw SQL string concatenation)
