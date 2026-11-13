"""Why did ShopKart Lite's profit fall while sales kept growing?

Usage (from the project root):
    python src/generate_data.py     # creates data/orders.csv (only needed once)
    python src/analysis.py          # creates images/*.png and results/*

Everything is computed from data/orders.csv. Nothing in the README is typed in by hand:
the numbers there are copied from results/key_metrics.json.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "orders.csv"
IMG = ROOT / "images"
RES = ROOT / "results"
IMG.mkdir(exist_ok=True)
RES.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------
# Business rules and what-if assumptions (change these and re-run to test ideas)
# ----------------------------------------------------------------------------
WRITE_OFF = 0.30            # share of a returned product that cannot be resold
A_CAP_PCT = 20              # A: maximum discount allowed ...
A_CATEGORIES = ["Electronics", "Fashion"]   # ... in these categories
A_ORDERS_LOST_PER_PP = 0.012  # A: each 1 pp of discount removed loses 1.2% of those orders
B_RETURN_CUT = 0.25         # B: Fashion returns fall by a quarter (size guide + QC photos)
C_FEE = 49                  # C: delivery fee on small orders (rupees)
C_LIMIT = 499               # C: "small order" = below this order value (rupees)
C_TIERS = ["Tier 2", "Tier 3"]
C_ORDERS_LOST = 0.12        # C: 12% of the affected orders are not placed
D_REPEAT_LIFT_PP = 3        # D: 3 more of every 100 paid-ads customers buy again within 90 days
# B and D need a programme to be run. Their gain is shown BEFORE that programme's cost,
# so the number doubles as a budget ceiling: the programme must cost less than this per year.

LAKH = 100_000
BLUE, ORANGE, RED, GREEN, GRAY = "#2563eb", "#f97316", "#dc2626", "#16a34a", "#6b7280"
YEAR_COLORS = {2024: "#93c5fd", 2025: BLUE}

# the rupee sign is missing from some fonts; fall back to "Rs" so charts never show an empty box
_has_rupee = font_manager.findfont("DejaVu Sans") and 0x20B9 in font_manager.get_font(
    font_manager.findfont("DejaVu Sans")).get_charmap()
CUR = "₹" if _has_rupee else "Rs "

sns.set_theme(style="whitegrid", rc={
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 12, "figure.dpi": 100,
    "axes.grid.axis": "y",
})


def save(fig, name):
    fig.savefig(IMG / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------------
# 1. Load data and build the money columns
# ----------------------------------------------------------------------------
df = pd.read_csv(DATA, parse_dates=["order_date"])
df["year"] = df["order_date"].dt.year
df["month"] = df["order_date"].dt.to_period("M")

returned = df["returned"] == 1
df["mrp_value"] = df["mrp"] * df["quantity"]
df["sales_value"] = df["selling_price"] * df["quantity"]
df["discount_value"] = df["mrp_value"] - df["sales_value"]
df["refund"] = np.where(returned, df["sales_value"], 0)
df["net_revenue"] = df["sales_value"] - df["refund"]
df["cogs"] = np.where(returned, WRITE_OFF, 1.0) * df["unit_cost"] * df["quantity"]
df["shipping_total"] = df["shipping_cost"] * np.where(returned, 2, 1)   # forward + return trip
df["contribution"] = df["net_revenue"] - df["cogs"] - df["shipping_total"]   # profit before ad/referral cost
df["profit"] = df["contribution"] - df["acquisition_cost"]
# profit lost because this order was returned (0 for orders that were kept)
df["return_loss"] = np.where(
    returned, df["sales_value"] - (1 - WRITE_OFF) * df["unit_cost"] * df["quantity"] + df["shipping_cost"], 0)

d24, d25 = df[df["year"] == 2024], df[df["year"] == 2025]


def summarize(d):
    return pd.Series({
        "orders": len(d),
        "customers": d["customer_id"].nunique(),
        "net_revenue": d["net_revenue"].sum(),
        "profit": d["profit"].sum(),
        "profit_margin_pct": 100 * d["profit"].sum() / d["net_revenue"].sum(),
        "avg_discount_pct": 100 * d["discount_value"].sum() / d["mrp_value"].sum(),
        "return_rate_pct": 100 * d["returned"].mean(),
        "delivery_pct_of_net_revenue": 100 * d["shipping_total"].sum() / d["net_revenue"].sum(),
        "acquisition_cost": d["acquisition_cost"].sum(),
        "tier3_share_of_orders_pct": 100 * (d["city_tier"] == "Tier 3").mean(),
    })


yearly = pd.DataFrame({2024: summarize(d24), 2025: summarize(d25)}).T
yearly.index.name = "year"

# ----------------------------------------------------------------------------
# 2. Category view
# ----------------------------------------------------------------------------
cat_order = ["Electronics", "Fashion", "Home & Kitchen", "Beauty", "Grocery"]


def by_category(d):
    g = d.groupby("category")
    return pd.DataFrame({
        "orders": g.size(),
        "avg_discount_pct": 100 * g["discount_value"].sum() / g["mrp_value"].sum(),
        "return_rate_pct": 100 * g["returned"].mean(),
        "contribution": g["contribution"].sum(),
        "contribution_margin_pct": 100 * g["contribution"].sum() / g["net_revenue"].sum(),
        "profit_lost_to_returns": g["return_loss"].sum(),
    }).loc[cat_order]


cat24, cat25 = by_category(d24), by_category(d25)
pd.concat({"2024": cat24, "2025": cat25}, names=["year"]).round(2).to_csv(RES / "category_summary.csv")

# share of 2025 Electronics orders sold below product cost
elec25 = d25[d25["category"] == "Electronics"]
below_cost_pct = 100 * (elec25["selling_price"] < elec25["unit_cost"]).mean()

# ----------------------------------------------------------------------------
# 3. Delivery cost by city tier x order value
# ----------------------------------------------------------------------------
bucket_labels = [f"< {CUR}500", f"{CUR}500-999", f"{CUR}1,000-1,999", f"{CUR}2,000+"]
d25 = d25.assign(bucket=pd.cut(d25["sales_value"], [0, 500, 1000, 2000, np.inf], labels=bucket_labels, right=False))
ship_heat = (
    d25.groupby(["city_tier", "bucket"], observed=True)
    .apply(lambda g: 100 * g["shipping_cost"].sum() / g["sales_value"].sum(), include_groups=False)
    .unstack()
)
small_t3_orders_share = 100 * ((d25["city_tier"] == "Tier 3") & (d25["sales_value"] < 500)).mean()

# ----------------------------------------------------------------------------
# 4. Customer acquisition: CAC vs what a customer is worth in the first 90 days
# ----------------------------------------------------------------------------
first = df.groupby("customer_id")["order_date"].min().rename("first_date")
df = df.join(first, on="customer_id")
df["days_since_first"] = (df["order_date"] - df["first_date"]).dt.days
chan_of = df.groupby("customer_id")["acquisition_channel"].first()

# new-customer mix and ad cost per year (a customer belongs to the year of their first order)
new_cust = pd.DataFrame({"first": first, "channel": chan_of})
for yr in (2024, 2025):
    nc = new_cust[new_cust["first"].dt.year == yr]
    yearly.loc[yr, "new_customers"] = len(nc)
    yearly.loc[yr, "paid_ads_share_of_new_customers_pct"] = 100 * (nc["channel"] == "Paid Ads").mean()
    paid_first = df[(df["acquisition_channel"] == "Paid Ads") & (df["acquisition_cost"] > 0) & (df["year"] == yr)]
    yearly.loc[yr, "avg_paid_ads_cac"] = paid_first["acquisition_cost"].mean()
yearly.round(2).to_csv(RES / "yearly_summary.csv")


def cohort_table(start, end, window):
    ids = first[(first >= start) & (first <= end)].index
    sub = df[df["customer_id"].isin(ids) & (df["days_since_first"] < window)]
    per = sub.groupby("customer_id").agg(
        contribution=("contribution", "sum"), orders=("order_id", "count"), cac=("acquisition_cost", "sum"))
    per["channel"] = chan_of.loc[per.index]
    out = per.groupby("channel").agg(
        customers=("orders", "size"), cac=("cac", "mean"),
        contribution=("contribution", "mean"), repeat_rate=("orders", lambda s: 100 * (s > 1).mean()))
    out["net_value"] = out["contribution"] - out["cac"]
    return out.loc[["Organic", "Referral", "Paid Ads"]]


# customers acquired Jan-Sep 2025 all have a full 90-day window before the data ends on 31 Dec 2025
c90 = cohort_table("2025-01-01", "2025-09-30", 90)
c90.round(2).to_csv(RES / "channel_economics_90d.csv")
# sensitivity: a longer 180-day window, for customers acquired Jan-Jun 2025
c180 = cohort_table("2025-01-01", "2025-06-30", 180)
n_paid_2025 = int(((first >= "2025-01-01") & (first <= "2025-12-31") & (chan_of == "Paid Ads")).sum())

# ----------------------------------------------------------------------------
# 5. What-if scenarios on the 2025 orders
# ----------------------------------------------------------------------------
base_profit = d25["profit"].sum()

def discount_cap_gain(orders_lost_per_pp):
    """A. cap discounts in Electronics and Fashion: higher price on the orders we keep, some orders lost."""
    m = d25["category"].isin(A_CATEGORIES) & (d25["discount_pct"] > A_CAP_PCT)
    excess = (d25["discount_pct"] - A_CAP_PCT).where(m, 0)
    keep = (1 - orders_lost_per_pp * excess).clip(lower=0)
    new_price = np.round(d25["mrp"] * (1 - A_CAP_PCT / 100))
    price_gain = np.where(d25["returned"] == 0, (new_price - d25["selling_price"]) * d25["quantity"], 0)
    return float((keep * (d25["contribution"] + price_gain) - d25["contribution"])[m].sum())


gain_A = discount_cap_gain(A_ORDERS_LOST_PER_PP)
sens_A = {f"{100 * e:.1f}%": round(discount_cap_gain(e)) for e in (0.006, 0.012, 0.020)}

# B. cut Fashion returns (gross gain: the programme itself must cost less than this to pay off)
gain_B = B_RETURN_CUT * float(d25.loc[d25["category"] == "Fashion", "return_loss"].sum())

# C. delivery fee on small Tier 2/3 orders
m = d25["city_tier"].isin(C_TIERS) & (d25["sales_value"] < C_LIMIT)
gain_C = float(((1 - C_ORDERS_LOST) * (d25["contribution"] + C_FEE) - d25["contribution"])[m].sum())

# D. win-back journeys: more paid-ads customers place a second order within 90 days
paid_repeat_orders = df[(df["acquisition_channel"] == "Paid Ads") & (df["year"] == 2025) & (df["days_since_first"] > 0)]
repeat_order_margin = float(paid_repeat_orders["contribution"].mean())
gain_D = D_REPEAT_LIFT_PP / 100 * n_paid_2025 * repeat_order_margin

scen = pd.DataFrame({
    "lever": [
        f"A. Cap discounts at {A_CAP_PCT}% (Electronics, Fashion)",
        f"B. Cut Fashion returns by {B_RETURN_CUT:.0%}",
        f"C. {CUR}{C_FEE} delivery fee on orders under {CUR}{C_LIMIT} (Tier 2/3)",
        f"D. Win-back journeys for paid-ads customers (+{D_REPEAT_LIFT_PP} pp repeat)",
    ],
    "profit_gain": [gain_A, gain_B, gain_C, gain_D],
})
total_gain = float(scen["profit_gain"].sum())
scen.loc[len(scen)] = ["All four together", total_gain]
scen["profit_gain_lakh"] = scen["profit_gain"] / LAKH
scen.round(0).to_csv(RES / "scenario_impact.csv", index=False)

# ----------------------------------------------------------------------------
# 6. Charts
# ----------------------------------------------------------------------------
y24, y25 = yearly.loc[2024], yearly.loc[2025]
rev_growth = 100 * (y25["net_revenue"] / y24["net_revenue"] - 1)
profit_change = 100 * (y25["profit"] / y24["profit"] - 1)

# --- Chart 1: revenue up, profit down
monthly = df.groupby("month").agg(net_revenue=("net_revenue", "sum"), profit=("profit", "sum"))
x = monthly.index.to_timestamp()
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7.4), sharex=True)
a1.fill_between(x, monthly["net_revenue"] / LAKH, color=BLUE, alpha=0.15)
a1.plot(x, monthly["net_revenue"] / LAKH, color=BLUE, lw=2.2)
a1.set_ylabel(f"Net revenue ({CUR} lakh)")
a2.bar(x, monthly["profit"] / LAKH, width=22, color=[GREEN if v >= 0 else RED for v in monthly["profit"]])
a2.axhline(0, color="black", lw=0.8)
a2.set_ylabel(f"Profit ({CUR} lakh)")
a2.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
for ax, col, xpos, ha in ((a1, "net_revenue", 0.02, "left"), (a2, "profit", 0.98, "right")):
    ax.axvline(pd.Timestamp("2024-12-16"), color=GRAY, ls="--", lw=1)
    ax.text(xpos, 0.95, f"2024: {CUR}{y24[col] / LAKH:,.0f} lakh    2025: {CUR}{y25[col] / LAKH:,.0f} lakh",
            transform=ax.transAxes, fontsize=10.5, fontweight="bold", va="top", ha=ha)
fig.suptitle(f"Net revenue grew {rev_growth:.0f}% in 2025, yet profit fell {abs(profit_change):.0f}%", fontsize=14, fontweight="bold", y=0.98)
fig.tight_layout(rect=(0, 0, 1, 0.96))
save(fig, "01_revenue_vs_profit.png")

# --- Chart 2: profit bridge 2024 -> 2025
delta_cat = (cat25["contribution"] - cat24["contribution"]) / LAKH
delta_acq = -(y25["acquisition_cost"] - y24["acquisition_cost"]) / LAKH
bridge_steps = [("2024\nprofit", y24["profit"] / LAKH, "total")]
bridge_steps += [(c.replace(" & ", " &\n"), delta_cat[c], "delta") for c in cat_order]
bridge_steps += [("Ad & referral\ncost", delta_acq, "delta"), ("2025\nprofit", y25["profit"] / LAKH, "total")]
fig, ax = plt.subplots(figsize=(10, 5.4))
running = 0.0
for i, (label, val, kind) in enumerate(bridge_steps):
    if kind == "total":
        bottom, height, color, running = 0, val, BLUE, val
    else:
        bottom, height = min(running, running + val), abs(val)
        color = GREEN if val >= 0 else RED
        running += val
    ax.bar(i, height, bottom=bottom, color=color, width=0.62)
    top = bottom + height
    txt = f"{CUR}{val:.1f}" if kind == "total" else f"{'+' if val >= 0 else '-'}{CUR}{abs(val):.1f}"
    ax.text(i, top + 0.5, txt, ha="center", fontsize=10, fontweight="bold")
ax.set_xticks(range(len(bridge_steps)))
ax.set_xticklabels([s[0] for s in bridge_steps], fontsize=9)
ax.set_ylabel(f"{CUR} lakh")
ax.axhline(0, color="black", lw=0.8)
ax.set_ylim(min(0, ax.get_ylim()[0]), ax.get_ylim()[1] + 2)
ax.set_title(f"Profit fell {CUR}{abs(y25['profit'] - y24['profit']) / LAKH:.0f} lakh, mostly from Electronics (-{CUR}{abs(delta_cat['Electronics']):.0f} lakh) "
             f"and ad & referral cost (-{CUR}{abs(delta_acq):.0f} lakh)", loc="left", fontsize=12)
save(fig, "02_profit_bridge_2024_to_2025.png")

# --- Chart 3: where each Rs 100 of list-price sales went in 2025
tot = d25["mrp_value"].sum()
steps = [
    ("List-price\nsales", tot, "total"),
    ("Discounts", -d25["discount_value"].sum(), "cost"),
    ("Refunds\n(returns)", -d25["refund"].sum(), "cost"),
    ("Net\nrevenue", d25["net_revenue"].sum(), "total"),
    ("Product\ncost", -d25["cogs"].sum(), "cost"),
    ("Delivery", -d25["shipping_total"].sum(), "cost"),
    ("Ad & referral\ncost", -d25["acquisition_cost"].sum(), "cost"),
    ("Profit", d25["profit"].sum(), "total"),
]
fig, ax = plt.subplots(figsize=(10, 5.6))
running = 0.0
for i, (label, val, kind) in enumerate(steps):
    v = 100 * val / tot
    if kind == "total":
        bottom, height = 0, v
        color = (GREEN if v >= 0 else RED) if label == "Profit" else BLUE
        running = v
    else:
        bottom, height = running + v, -v
        color = ORANGE
        running += v
    ax.bar(i, height, bottom=bottom, color=color, width=0.62)
    ypos = bottom + height + 1.2
    ax.text(i, ypos, f"{CUR}{abs(v):.1f}" if kind == "total" else f"-{CUR}{abs(v):.1f}",
            ha="center", fontsize=10, fontweight="bold")
ax.set_xticks(range(len(steps)))
ax.set_xticklabels([s[0] for s in steps], fontsize=9)
ax.set_ylabel(f"{CUR} per 100 of list-price sales")
ax.set_ylim(0, 112)
ax.set_title(f"Of every {CUR}100 sold at list price in 2025, only {CUR}{100 * y25['profit'] / tot:.1f} stayed as profit", loc="left", fontsize=13)
save(fig, "03_where_the_money_goes_2025.png")

# --- Chart 3: discounts and margin by category
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.8))
w = 0.38
xi = np.arange(len(cat_order))
for ax, col, title, fmt in (
    (a1, "avg_discount_pct", "Average discount (% of list price)", "{:.0f}%"),
    (a2, "contribution_margin_pct", "Margin before ad cost (% of net revenue)", "{:.0f}%"),
):
    for k, (yr, tab) in enumerate(((2024, cat24), (2025, cat25))):
        bars = ax.bar(xi + (k - 0.5) * w, tab[col], w, color=YEAR_COLORS[yr], label=str(yr))
        ax.bar_label(bars, labels=[fmt.format(v) for v in tab[col]], fontsize=8, padding=2)
    ax.set_xticks(xi)
    ax.set_xticklabels([c.replace(" & ", " &\n") for c in cat_order], fontsize=9)
    ax.set_title(title, loc="left")
    ax.axhline(0, color="black", lw=0.8)
a1.legend(frameon=False)
fig.suptitle(f"Deeper discounts pushed Electronics into a loss ({cat25.loc['Electronics', 'contribution_margin_pct']:.0f}% margin) and cut Fashion margin "
             f"from {cat24.loc['Fashion', 'contribution_margin_pct']:.0f}% to {cat25.loc['Fashion', 'contribution_margin_pct']:.0f}%",
             fontsize=13, fontweight="bold", x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "04_discounts_and_margin_by_category.png")

# --- Chart 4: returns
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))
for k, (yr, tab) in enumerate(((2024, cat24), (2025, cat25))):
    bars = a1.bar(xi + (k - 0.5) * w, tab["return_rate_pct"], w, color=YEAR_COLORS[yr], label=str(yr))
    a1.bar_label(bars, labels=[f"{v:.0f}%" for v in tab["return_rate_pct"]], fontsize=8, padding=2)
a1.set_xticks(xi)
a1.set_xticklabels([c.replace(" & ", " &\n") for c in cat_order], fontsize=9)
a1.set_title("Return rate (% of orders)", loc="left")
a1.legend(frameon=False)
lost = (cat25["profit_lost_to_returns"] / LAKH).sort_values()
bars = a2.barh(lost.index, lost.values, color=[RED if c == "Fashion" else GRAY for c in lost.index])
a2.bar_label(bars, labels=[f"{CUR}{v:.1f} lakh" for v in lost.values], fontsize=9, padding=3)
a2.set_title(f"Profit lost to returns, 2025 ({CUR} lakh)", loc="left")
a2.set_xlim(0, lost.max() * 1.25)
a2.grid(axis="x", visible=True)
a2.grid(axis="y", visible=False)
fig.suptitle(f"Fashion returns rose to {cat25.loc['Fashion', 'return_rate_pct']:.0f}% and cost {CUR}{cat25.loc['Fashion', 'profit_lost_to_returns'] / LAKH:.0f} lakh of profit",
             fontsize=13, fontweight="bold", x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "05_returns.png")

# --- Chart 5: delivery cost heatmap
fig, ax = plt.subplots(figsize=(8.6, 4.2))
sns.heatmap(ship_heat, annot=True, fmt=".0f", cmap="YlOrRd", cbar=False, linewidths=2, linecolor="white",
            annot_kws={"fontsize": 12, "fontweight": "bold"}, ax=ax)
for t in ax.texts:
    t.set_text(t.get_text() + "%")
ax.set_xlabel("Order value")
ax.set_ylabel("")
ax.tick_params(axis="x", labelrotation=0)
ax.tick_params(axis="y", labelrotation=0)
ax.set_title(f"Delivery cost as % of order value (2025): small Tier 3 orders cost {ship_heat.iloc[-1, 0]:.0f}%", loc="left", fontsize=12)
save(fig, "06_delivery_cost_by_tier_and_order_value.png")

# --- Chart 6: paid ads vs organic customers
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))
chs = list(c90.index)
colors = [BLUE, GREEN, ORANGE]
bars = a1.bar(chs, c90["repeat_rate"], color=colors, width=0.55)
a1.bar_label(bars, labels=[f"{v:.0f}%" for v in c90["repeat_rate"]], fontsize=10, padding=2)
a1.set_title("Customers who buy again within 90 days", loc="left")
a1.set_ylim(0, c90["repeat_rate"].max() * 1.25)
xc = np.arange(len(chs))
b1 = a2.bar(xc - 0.19, c90["cac"], 0.38, color=GRAY, label="Cost to acquire (CAC)")
b2 = a2.bar(xc + 0.19, c90["contribution"], 0.38, color=GREEN, label="Margin earned in first 90 days")
a2.bar_label(b1, labels=[f"{CUR}{v:,.0f}" for v in c90["cac"]], fontsize=9, padding=2)
a2.bar_label(b2, labels=[f"{CUR}{v:,.0f}" for v in c90["contribution"]], fontsize=9, padding=2)
a2.set_xticks(xc)
a2.set_xticklabels(chs)
a2.axhline(0, color="black", lw=0.8)
a2.set_title(f"Per customer ({CUR}), acquired Jan-Sep 2025", loc="left")
a2.set_ylim(0, c90["contribution"].max() * 1.18)
a2.legend(frameon=False, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
fig.suptitle(f"Paid-ads customers barely pay back: {CUR}{c90.loc['Paid Ads', 'net_value']:,.0f} net in 90 days vs {CUR}{c90.loc['Organic', 'net_value']:,.0f} for organic",
             fontsize=13, fontweight="bold", x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "07_paid_ads_vs_organic.png")

# --- Chart 7: what the four fixes are worth
fig, ax = plt.subplots(figsize=(10, 4.8))
labels = scen["lever"].tolist()
vals = scen["profit_gain_lakh"].tolist()
cols = [BLUE] * 4 + ["#0f172a"]
yy = np.arange(len(labels))[::-1]
bars = ax.barh(yy, vals, color=cols, height=0.6)
ax.bar_label(bars, labels=[f"+{CUR}{v:.1f} lakh" for v in vals], fontsize=10, fontweight="bold", padding=4)
ax.set_yticks(yy)
ax.set_yticklabels(labels, fontsize=9.5)
ax.set_xlim(0, max(vals) * 1.22)
ax.set_xlabel(f"Estimated extra profit per year ({CUR} lakh)")
ax.set_title(f"Four fixes could lift 2025 profit from {CUR}{base_profit / LAKH:.0f} lakh to about {CUR}{(base_profit + total_gain) / LAKH:.0f} lakh",
             loc="left", fontsize=13)
ax.grid(axis="x", visible=True)
ax.grid(axis="y", visible=False)
fig.text(0.01, -0.06, "Gains for B and D are before the cost of running those programmes, so each also works as a yearly budget ceiling.",
         fontsize=9, color=GRAY)
save(fig, "08_expected_impact_of_fixes.png")

# ----------------------------------------------------------------------------
# 7. Key metrics for the README
# ----------------------------------------------------------------------------
metrics = {
    "orders_total": int(len(df)),
    "customers_total": int(df["customer_id"].nunique()),
    "revenue_growth_pct": float(rev_growth),
    "profit_change_pct": float(profit_change),
    "yearly": {str(int(y)): {k: float(v) for k, v in yearly.loc[y].items()} for y in (2024, 2025)},
    "category_2024": cat24.round(2).to_dict("index"),
    "category_2025": cat25.round(2).to_dict("index"),
    "electronics_orders_below_cost_pct_2025": float(below_cost_pct),
    "delivery_cost_pct_of_value_2025": ship_heat.round(1).to_dict("index"),
    "small_tier3_orders_share_pct": float(small_t3_orders_share),
    "channel_90d": c90.round(2).to_dict("index"),
    "channel_180d": c180.round(2).to_dict("index"),
    "paid_customers_acquired_2025": n_paid_2025,
    "profit_change_by_source_lakh": {**{c: round(float(delta_cat[c]), 2) for c in cat_order}, "Ad & referral cost": round(float(delta_acq), 2)},
    "paid_repeat_order_margin": round(repeat_order_margin, 2),
    "discount_cap_sensitivity": sens_A,
    "baseline_profit_2025": float(base_profit),
    "scenarios": {r.lever: round(float(r.profit_gain)) for r in scen.itertuples()},
    "profit_after_all_fixes": float(base_profit + total_gain),
    "margin_after_all_fixes_pct": float(100 * (base_profit + total_gain) / d25["net_revenue"].sum()),
}
(RES / "key_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
print(json.dumps(metrics, indent=2, ensure_ascii=False))
