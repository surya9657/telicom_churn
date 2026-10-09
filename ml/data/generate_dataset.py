"""
generate_dataset.py

Generates a synthetic customer-churn dataset that follows the exact schema
of the well-known IBM Telco Customer Churn dataset. This script exists so the
ML pipeline is fully reproducible offline. If you have network access, you can
skip this script and instead download the real dataset from Kaggle
("Telco Customer Churn" by blastchar) and save it as ml/data/telco_churn.csv
with the same column names used below - train.py does not care which source
the file came from as long as the columns match.

Run:
    python generate_dataset.py
"""

import numpy as np
import pandas as pd

RANDOM_SEED = 42
N_CUSTOMERS = 5000


def generate_dataset(n: int = N_CUSTOMERS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    gender = rng.choice(["Male", "Female"], size=n)
    senior_citizen = rng.choice([0, 1], size=n, p=[0.84, 0.16])
    partner = rng.choice(["Yes", "No"], size=n, p=[0.48, 0.52])
    dependents = rng.choice(["Yes", "No"], size=n, p=[0.30, 0.70])

    tenure = rng.integers(0, 73, size=n)

    contract = rng.choice(
        ["Month-to-month", "One year", "Two year"], size=n, p=[0.55, 0.21, 0.24]
    )
    phone_service = rng.choice(["Yes", "No"], size=n, p=[0.90, 0.10])
    multiple_lines = np.array(
        [
            "No phone service" if ps == "No" else rng.choice(["Yes", "No"], p=[0.42, 0.58])
            for ps in phone_service
        ]
    )

    internet_service = rng.choice(
        ["DSL", "Fiber optic", "No"], size=n, p=[0.34, 0.44, 0.22]
    )

    def dependent_internet_feature(p_yes=0.35):
        out = []
        for svc in internet_service:
            if svc == "No":
                out.append("No internet service")
            else:
                out.append(rng.choice(["Yes", "No"], p=[p_yes, 1 - p_yes]))
        return np.array(out)

    online_security = dependent_internet_feature(0.30)
    online_backup = dependent_internet_feature(0.35)
    device_protection = dependent_internet_feature(0.35)
    tech_support = dependent_internet_feature(0.30)
    streaming_tv = dependent_internet_feature(0.40)
    streaming_movies = dependent_internet_feature(0.40)

    paperless_billing = rng.choice(["Yes", "No"], size=n, p=[0.59, 0.41])
    payment_method = rng.choice(
        [
            "Electronic check",
            "Mailed check",
            "Bank transfer (automatic)",
            "Credit card (automatic)",
        ],
        size=n,
        p=[0.34, 0.23, 0.22, 0.21],
    )

    # Base monthly charge grows with add-on services
    base_charge = rng.normal(20, 2, size=n)
    addon_cost = np.zeros(n)
    for arr, cost in [
        (online_security, 5.5),
        (online_backup, 5.0),
        (device_protection, 5.0),
        (tech_support, 5.5),
        (streaming_tv, 9.5),
        (streaming_movies, 9.5),
    ]:
        addon_cost += np.where(arr == "Yes", cost, 0)

    internet_cost = np.select(
        [internet_service == "DSL", internet_service == "Fiber optic", internet_service == "No"],
        [24.0, 45.0, 0.0],
    )
    phone_cost = np.where(phone_service == "Yes", 20.0, 0.0)

    monthly_charges = np.clip(
        base_charge + addon_cost + internet_cost + phone_cost + rng.normal(0, 3, size=n),
        18.0,
        120.0,
    ).round(2)

    total_charges = np.clip(monthly_charges * tenure + rng.normal(0, 20, size=n), 0, None).round(2)
    # New customers (tenure 0) commonly have an empty/blank TotalCharges field
    # in the real dataset - we replicate that data-quality quirk deliberately
    # so the preprocessing pipeline has something real to clean.
    total_charges_str = total_charges.astype(str)
    total_charges_str[tenure == 0] = " "

    customer_id = np.array([f"{rng.integers(1000,9999)}-{''.join(rng.choice(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 5))}" for _ in range(n)])

    # ---- Churn probability model (ground truth signal used to LABEL the
    # synthetic data - the ML model itself never sees this formula, it only
    # sees the columns above and learns the pattern from data, same as it
    # would with the real dataset). ----
    logit = (
        -1.6
        + np.where(contract == "Month-to-month", 1.35, 0.0)
        + np.where(contract == "One year", 0.15, 0.0)
        - np.where(contract == "Two year", 1.1, 0.0)
        + np.where(internet_service == "Fiber optic", 0.55, 0.0)
        - np.where(internet_service == "No", 0.35, 0.0)
        - 0.035 * tenure
        + 0.012 * (monthly_charges - 60)
        + np.where(paperless_billing == "Yes", 0.30, 0.0)
        + np.where(payment_method == "Electronic check", 0.45, 0.0)
        - np.where(tech_support == "Yes", 0.30, 0.0)
        - np.where(online_security == "Yes", 0.30, 0.0)
        + np.where(senior_citizen == 1, 0.25, 0.0)
        - np.where(partner == "Yes", 0.15, 0.0)
        - np.where(dependents == "Yes", 0.20, 0.0)
        + rng.normal(0, 0.55, size=n)
    )
    churn_prob = 1 / (1 + np.exp(-logit))
    churn = np.where(rng.random(n) < churn_prob, "Yes", "No")

    df = pd.DataFrame(
        {
            "customerID": customer_id,
            "gender": gender,
            "SeniorCitizen": senior_citizen,
            "Partner": partner,
            "Dependents": dependents,
            "tenure": tenure,
            "PhoneService": phone_service,
            "MultipleLines": multiple_lines,
            "InternetService": internet_service,
            "OnlineSecurity": online_security,
            "OnlineBackup": online_backup,
            "DeviceProtection": device_protection,
            "TechSupport": tech_support,
            "StreamingTV": streaming_tv,
            "StreamingMovies": streaming_movies,
            "Contract": contract,
            "PaperlessBilling": paperless_billing,
            "PaymentMethod": payment_method,
            "MonthlyCharges": monthly_charges,
            "TotalCharges": total_charges_str,
            "Churn": churn,
        }
    )
    return df


if __name__ == "__main__":
    dataset = generate_dataset()
    dataset.to_csv("telco_churn.csv", index=False)
    print(f"Saved {len(dataset)} rows to telco_churn.csv")
    print(dataset["Churn"].value_counts(normalize=True))
