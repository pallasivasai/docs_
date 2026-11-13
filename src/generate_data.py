"""Generate a synthetic e-commerce orders dataset for the fictional company "ShopKart Lite".

Every number here is simulated - no real company or customer data is used.
Running the script again with the same SEED produces exactly the same file.

Story built into the data (the analysis has to discover it from the raw orders):
  * volume grows every month, but discounts get deeper over time
  * Fashion returns rise as discounts drive impulse buying
  * the customer mix shifts towards Tier 3 cities, where delivery costs more
  * more customers come from paid ads, which cost more each month and repeat less
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_MONTHS = 24                       # Jan 2024 .. Dec 2025
START = pd.Timestamp("2024-01-01")
BASE_ORDERS = 900                   # orders in the first month
GROWTH = 0.024                      # monthly order growth
REPEAT_SHARE = 0.38                 # share of orders placed by existing customers
OUT = Path(__file__).resolve().parents[1] / "data" / "orders.csv"

SEASON = {10: 1.35, 11: 1.30, 12: 1.10, 1: 0.90}   # festive-season boost

# mrp: typical price | sigma: price spread | cost: product cost as share of MRP
# ret: base return rate | disc: base discount | share: share of orders | drift: discount increase over 24 months
CATEGORIES = {
    "Electronics":    dict(mrp=6500, sigma=0.70, cost=0.78, ret=0.07, disc=0.08, share=0.20, drift=0.14),
    "Fashion":        dict(mrp=1400, sigma=0.50, cost=0.47, ret=0.15, disc=0.18, share=0.30, drift=0.12),
    "Home & Kitchen": dict(mrp=1800, sigma=0.60, cost=0.58, ret=0.06, disc=0.12, share=0.20, drift=0.05),
    "Beauty":         dict(mrp=650,  sigma=0.40, cost=0.38, ret=0.04, disc=0.12, share=0.15, drift=0.04),
    "Grocery":        dict(mrp=420,  sigma=0.40, cost=0.80, ret=0.02, disc=0.04, share=0.15, drift=0.01),
}
TIERS = ["Tier 1", "Tier 2", "Tier 3"]
TIER_SHIPPING = {"Tier 1": 45, "Tier 2": 70, "Tier 3": 110}   # rupees per delivery
REGIONS = ["North", "South", "East", "West"]
REGION_P = [0.28, 0.30, 0.14, 0.28]
CHANNELS = ["Organic", "Referral", "Paid Ads"]
LOYALTY = {"Organic": 1.0, "Referral": 1.4, "Paid Ads": 0.35}  # how likely a customer is to buy again


def main() -> None:
    rng = np.random.default_rng(SEED)
    params = pd.DataFrame(CATEGORIES).T
    cat_names = list(CATEGORIES)
    cat_p = params["share"].astype(float).to_numpy()

    # customer pool (grows every month)
    p_id = np.array([], dtype=int)
    p_ch = np.array([], dtype=object)
    p_ti = np.array([], dtype=object)
    p_re = np.array([], dtype=object)
    p_w = np.array([], dtype=float)
    next_id = 1
    frames = []

    for m in range(N_MONTHS):
        month_start = START + pd.DateOffset(months=m)
        t = m / (N_MONTHS - 1)                      # 0 -> 1 across the 24 months
        season = SEASON.get(month_start.month, 1.0)
        n = int(round(BASE_ORDERS * (1 + GROWTH) ** m * season * rng.normal(1, 0.03)))

        n_rep = int(rng.binomial(n, REPEAT_SHARE)) if len(p_id) else 0
        n_new = n - n_rep

        # --- returning customers (weighted by how loyal each customer is)
        if n_rep:
            idx = rng.choice(len(p_id), size=n_rep, p=p_w / p_w.sum())
        else:
            idx = np.array([], dtype=int)

        # --- new customers: more paid-ads and more Tier 3 as time goes on
        p_paid = 0.35 + 0.30 * t
        p_ref = 0.15
        ch_new = rng.choice(CHANNELS, size=n_new, p=[1 - p_paid - p_ref, p_ref, p_paid])
        p_t1 = 0.50 - 0.20 * t
        p_t3 = 0.17 + 0.20 * t
        ti_new = rng.choice(TIERS, size=n_new, p=[p_t1, 1 - p_t1 - p_t3, p_t3])
        re_new = rng.choice(REGIONS, size=n_new, p=REGION_P)
        id_new = np.arange(next_id, next_id + n_new)
        next_id += n_new
        w_new = np.array([LOYALTY[c] for c in ch_new]) * rng.lognormal(0, 0.4, n_new)
        cac = np.where(
            ch_new == "Paid Ads",
            (140 + 120 * t) * rng.lognormal(0, 0.15, n_new),   # ads get pricier every month
            np.where(ch_new == "Referral", 60.0, 0.0),
        )

        cust_id = np.concatenate([p_id[idx], id_new])
        channel = np.concatenate([p_ch[idx], ch_new])
        tier = np.concatenate([p_ti[idx], ti_new])
        region = np.concatenate([p_re[idx], re_new])
        acq_cost = np.concatenate([np.zeros(n_rep), cac])

        # --- order attributes
        cat = rng.choice(cat_names, size=n, p=cat_p)
        pr = params.loc[cat].reset_index(drop=True)
        mrp = rng.lognormal(np.log(pr["mrp"].astype(float)), pr["sigma"].astype(float))
        mrp = np.clip(np.round(mrp, -1), 99, None)

        festive = 0.05 if month_start.month in (10, 11) else 0.0
        disc = pr["disc"].astype(float) + pr["drift"].astype(float) * t + festive + rng.normal(0, 0.04, n)
        disc_pct = np.round(np.clip(disc, 0, 0.60) * 100 * 2) / 2     # nearest 0.5 percentage point
        selling = np.round(mrp * (1 - disc_pct / 100))

        qty = np.where(
            cat == "Grocery",
            rng.choice([1, 2, 3], size=n, p=[0.5, 0.3, 0.2]),
            rng.choice([1, 2, 3], size=n, p=[0.78, 0.17, 0.05]),
        )
        unit_cost = np.round(mrp * pr["cost"].astype(float) * rng.lognormal(0, 0.03, n))
        shipping = np.round(pd.Series(tier).map(TIER_SHIPPING).to_numpy() * rng.lognormal(0, 0.10, n))

        ret_rate = (
            pr["ret"].astype(float)
            * (1 + np.where(cat == "Fashion", 0.55, 0.15) * t)
            * np.where(tier == "Tier 3", 1.15, 1.0)
        )
        returned = (rng.random(n) < ret_rate).astype(int)

        days = rng.integers(0, month_start.days_in_month, n)
        dates = month_start + pd.to_timedelta(days, unit="D")

        frames.append(pd.DataFrame({
            "order_date": dates,
            "customer_id": cust_id,
            "acquisition_channel": channel,
            "region": region,
            "city_tier": tier,
            "category": cat,
            "mrp": mrp.astype(int),
            "discount_pct": disc_pct,
            "quantity": qty,
            "selling_price": selling.astype(int),
            "unit_cost": unit_cost.astype(int),
            "shipping_cost": shipping.astype(int),
            "acquisition_cost": np.round(acq_cost).astype(int),
            "returned": returned,
        }))

        # add this month's new customers to the pool
        p_id = np.concatenate([p_id, id_new])
        p_ch = np.concatenate([p_ch, ch_new])
        p_ti = np.concatenate([p_ti, ti_new])
        p_re = np.concatenate([p_re, re_new])
        p_w = np.concatenate([p_w, w_new])

    df = pd.concat(frames, ignore_index=True).sort_values("order_date", kind="stable").reset_index(drop=True)
    df.insert(0, "order_id", [f"ORD{i:06d}" for i in range(1, len(df) + 1)])
    df["customer_id"] = df["customer_id"].map(lambda i: f"C{i:05d}")
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df):,} orders from {df['customer_id'].nunique():,} customers to {OUT}")


if __name__ == "__main__":
    main()
