"""Create compact, scalable SVG charts after running generate_data.py and analyze.py."""
from pathlib import Path
import csv
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]; IMG=ROOT/"images"; RES=ROOT/"results"
def start(title,subtitle="Synthetic simulation only",height=500):
 return [f'<svg xmlns="http://www.w3.org/2000/svg" width="980" height="{height}" viewBox="0 0 980 {height}">','<rect width="100%" height="100%" fill="#fff"/>','<style>text{font-family:Arial,sans-serif;fill:#172033}.muted{fill:#667085}.grid{stroke:#e6eaf0}.blue{fill:#2563eb}.orange{fill:#f59e0b}.red{fill:#dc2626}.green{fill:#16a34a}</style>',f'<text x="42" y="48" font-size="25" font-weight="700">{title}</text>',f'<text x="42" y="76" class="muted" font-size="13">{subtitle}</text>']
def txt(p,x,y,s,size=13,anchor="start",weight="400",cls=""): p.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" class="{cls}">{s}</text>')
def save(name,p): p.append("</svg>"); (IMG/name).write_text("\n".join(p),encoding="utf-8")
with (RES/"monthly_activity.csv").open() as f: monthly=list(csv.DictReader(f))
p=start("Banking activity and suspicious test events","40,000 generated transfers across 12 synthetic months")
for k in range(5):
 y=120+67.5*k; p.append(f'<line x1="78" y1="{y}" x2="928" y2="{y}" class="grid"/>')
mx=max(int(r["transfers"]) for r in monthly)*1.12
for i,r in enumerate(monthly):
 x=86+i*70.83; v=int(r["transfers"]); q=int(r["flagged"])
 p.append(f'<rect x="{x}" y="{390-v/mx*270}" width="30" height="{v/mx*270}" rx="4" class="blue"/>')
 p.append(f'<rect x="{x+8}" y="{390-q/mx*270}" width="14" height="{q/mx*270}" rx="3" class="orange"/>')
 txt(p,x+15,414,r["month"][5:],11,"middle")
p += ['<rect x="690" y="98" width="12" height="12" class="blue"/>']; txt(p,710,109,"All transfers",12)
p += ['<rect x="825" y="98" width="12" height="12" class="orange"/>']; txt(p,845,109,"Flagged",12)
txt(p,42,470,"Planted labels, not confirmed real attacks.",12,cls="muted"); save("01_synthetic_activity.svg",p)
with (RES/"scenario_exposure.csv").open() as f: rows=list(csv.DictReader(f))
rows.sort(key=lambda r:int(r["attempts"])); p=start("Simulated suspicious-event categories","Generated labels; wrong-recipient may be user error")
mx=max(int(r["attempts"]) for r in rows)
for i,r in enumerate(rows):
 y=130+i*48; v=int(r["attempts"]); txt(p,270,y+19,r["scenario"],13,"end")
 p.append(f'<rect x="300" y="{y}" width="{600*v/mx}" height="25" rx="4" class="orange"/>'); txt(p,610+600*v/mx,y+18,str(v),12,weight="600")
save("02_attack_scenarios.svg",p)
rows.sort(key=lambda r:float(r["notional_inr"])); mx=max(float(r["notional_inr"]) for r in rows)
p=start("Notional value represented by suspicious scenarios","₹ lakh; not actual fraud loss, prevented loss or telemetry")
for i,r in enumerate(rows):
 y=130+i*48; v=float(r["notional_inr"]); txt(p,270,y+19,r["scenario"],13,"end")
 p.append(f'<rect x="300" y="{y}" width="{600*v/mx}" height="25" rx="4" class="blue"/>'); txt(p,610+600*v/mx,y+18,f"{v/100000:.2f}L",12,weight="600")
save("03_simulated_exposure.svg",p)
with (ROOT/"data"/"control_coverage.csv").open() as f: cov=list(csv.DictReader(f))
c=Counter(r["coverage_assessment"] for r in cov); p=start("Control coverage found in inspected code","Mapping is limited to repository files inspected")
for i,k in enumerate(["mitigates","partial","not_covered"]):
 x=130+i*280; color={"mitigates":"#16a34a","partial":"#f59e0b","not_covered":"#dc2626"}[k]
 p.append(f'<rect x="{x}" y="170" width="210" height="150" rx="14" fill="{color}"/>')
 txt(p,x+105,235,str(c[k]),48,"middle","700"); txt(p,x+105,275,k.replace("_"," "),17,"middle","600")
txt(p,490,400,"12 scenarios assessed",15,"middle",cls="muted"); save("04_control_coverage.svg",p)
with (RES/"control_test_results.csv").open() as f: tests=list(csv.DictReader(f))
p=start("Deterministic control-test fixtures","Expected fixture outcomes; not measured prevention efficacy",560)
for i,r in enumerate(tests):
 y=115+i*55; good=int(r["blocked_or_rejected_by_documented_control"]); gap=int(r["not_covered_or_unverified"])
 txt(p,320,y+20,r["test_case"],12,"end")
 p.append(f'<rect x="340" y="{y}" width="{good*.38}" height="25" rx="3" class="green"/>')
 p.append(f'<rect x="{340+good*.38}" y="{y}" width="{gap*.38}" height="25" rx="3" class="red"/>')
 txt(p,740,y+19,f"{good:,} / {good+gap:,}",12)
save("05_control_test_matrix.svg",p)
p=start("SAI Bank: 24-hour wrong-payment recovery","Conceptual flow described by the database procedure",400)
steps=[("Transfer","Atomic debit + credit"),("0–24 hours","Authenticate + ownership"),("Recovery","Lock both accounts"),("Deficit?","Freeze recipient"),("Future credits","Clear deficit")]
for i,(a,b) in enumerate(steps):
 x=28+i*190; p.append(f'<rect x="{x}" y="155" width="160" height="115" rx="12" fill="#f5f8ff" stroke="#2563eb" stroke-width="2"/>')
 txt(p,x+80,195,a,16,"middle","700"); txt(p,x+80,227,b,12,"middle")
 if i<4: p.append(f'<path d="M{x+162} 212 h24 m-8 -7 l8 7 -8 7" stroke="#344054" stroke-width="2" fill="none"/>')
txt(p,490,335,"Negative balance freeze can remain until future credits clear the deficit.",13,"middle",cls="muted")
save("06_24h_recovery_flow.svg",p)
print("Rendered 6 scalable SVG charts")
