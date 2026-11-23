"""Delivery Delay Root-Cause Analysis - end-to-end pipeline.
Steps: 1 generate data -> 2 SQL analysis -> 3 driver model -> 4 dashboard -> 5 report."""
import numpy as np, pandas as pd, sqlite3, json, html, datetime as dt
rng = np.random.default_rng(42)
LOG = []
def log(s): LOG.append(f"- [x] {s}"); print(s)

# ---------- 1. DATA (synthetic, documented assumptions) ----------
N = 20000
zones = {"Koramangala":(3.0,.25),"Indiranagar":(3.2,.30),"Whitefield":(6.5,.45),
         "HSR Layout":(3.5,.20),"Electronic City":(7.0,.40),"Jayanagar":(4.0,.15),"Hebbal":(5.5,.35)}
zn = rng.choice(list(zones), N, p=[.2,.17,.14,.16,.09,.14,.10])
dist = np.array([max(.5, rng.normal(zones[z][0],1.2)) for z in zn])
cong = np.array([zones[z][1] for z in zn])
start = dt.datetime(2026,6,1)
ts = [start+dt.timedelta(days=int(d), minutes=int(m)) for d,m in zip(rng.integers(0,90,N),
      rng.choice(1440,N,p=np.repeat([.004,.006,.012,.03,.045,.05,.04,.035,.03,.025,.03,.045],120)/ (np.repeat([.004,.006,.012,.03,.045,.05,.04,.035,.03,.025,.03,.045],120).sum())))]
hour = np.array([t.hour for t in ts]); dow = np.array([t.weekday() for t in ts])
weather = rng.choice(["Clear","Rain","Heavy Rain"], N, p=[.62,.28,.10])
rest = rng.integers(1,121,N); rest_prep = rng.normal(16,5,120).clip(6,35)
prep = (rest_prep[rest-1] + rng.normal(0,3,N) + np.where(np.isin(hour,[13,14,20,21]),3,0)).clip(4,None)
rider = rng.integers(1,301,N); tenure = rng.gamma(2.2,5,300).clip(.5,48)[rider-1]
peak = np.isin(hour,[12,13,14,19,20,21,22]).astype(int)
wmult = pd.Series(weather).map({"Clear":1,"Rain":1.25,"Heavy Rain":1.65}).values
travel = dist*3.6*(1+cong)*wmult*(1+.18*peak)*(1.25-.25*np.minimum(tenure,24)/24) + rng.normal(0,2.5,N)
wait = rng.exponential(2,N)*(1+peak)
total = (prep+wait+travel.clip(2,None)).round(1)
promised = (32+4.6*dist).round(0)
breach = (total>promised).astype(int)
cancel = (rng.random(N) < (.012+.03*np.clip((total-promised)/15,0,3))).astype(int)
value = rng.lognormal(5.6,.5,N).round(0)
df = pd.DataFrame(dict(order_id=range(1,N+1),order_ts=ts,hour=hour,dow=dow,zone=zn,restaurant_id=rest,rider_id=rider,
    rider_tenure_m=tenure.round(1),distance_km=dist.round(2),weather=weather,order_value=value,prep_min=prep.round(1),
    wait_min=wait.round(1),travel_min=travel.clip(2,None).round(1),promised_min=promised,delivered_min=total,
    sla_breach=breach,cancelled=cancel))
# inject realistic mess, then clean (shows data-cleaning skill)
dirty = df.copy()
dirty.loc[rng.choice(N,300,replace=False),"weather"] = None
dirty.loc[rng.choice(N,150,replace=False),"zone"] = dirty["zone"].str.upper()
dirty = pd.concat([dirty, dirty.sample(120, random_state=1)])
dirty.to_csv("orders_raw.csv", index=False)
c = dirty.drop_duplicates("order_id").copy()
c["zone"] = c["zone"].str.title().replace({"Hsr Layout":"HSR Layout"})
c["weather"] = c["weather"].fillna("Unknown")
c = c[(c.delivered_min>0)&(c.distance_km>0)]
c.to_csv("orders_clean.csv", index=False)
log(f"Data generated ({N:,} orders), injected 300 nulls/150 case errors/120 duplicates, cleaned -> {len(c):,} rows")

# ---------- 2. SQL ANALYSIS ----------
con = sqlite3.connect(":memory:"); c.to_sql("orders",con,index=False)
Q = lambda s: pd.read_sql(s,con)
kpi = Q("""SELECT COUNT(*) orders, ROUND(100.0*AVG(sla_breach),1) breach_pct, ROUND(100.0*AVG(cancelled),2) cancel_pct,
 ROUND(AVG(delivered_min),1) avg_min, ROUND(SUM(CASE WHEN cancelled=1 THEN order_value END)) lost_rev, ROUND(SUM(order_value)) gmv FROM orders""").iloc[0]
by_zone = Q("SELECT zone label, ROUND(100.0*AVG(sla_breach),1) v, COUNT(*) n FROM orders GROUP BY zone ORDER BY v DESC")
by_hour = Q("SELECT hour label, ROUND(100.0*AVG(sla_breach),1) v FROM orders GROUP BY hour ORDER BY hour")
by_wx = Q("SELECT weather label, ROUND(100.0*AVG(sla_breach),1) v, COUNT(*) n FROM orders GROUP BY weather ORDER BY v DESC")
by_ten = Q("""SELECT CASE WHEN rider_tenure_m<3 THEN '1. <3 months' WHEN rider_tenure_m<12 THEN '2. 3-12 months' ELSE '3. 12+ months' END label,
 ROUND(100.0*AVG(sla_breach),1) v, COUNT(*) n FROM orders GROUP BY 1 ORDER BY 1""")
by_prep = Q("""SELECT CASE WHEN prep_min<12 THEN '1. <12 min' WHEN prep_min<20 THEN '2. 12-20 min' ELSE '3. 20+ min' END label,
 ROUND(100.0*AVG(sla_breach),1) v, COUNT(*) n FROM orders GROUP BY 1 ORDER BY 1""")
worst_rest = Q("""SELECT restaurant_id label, ROUND(100.0*AVG(sla_breach),1) v, COUNT(*) n FROM orders GROUP BY restaurant_id
 HAVING n>=100 ORDER BY v DESC LIMIT 8""")
combo = Q("""SELECT zone||' | '||weather label, ROUND(100.0*AVG(sla_breach),1) v, COUNT(*) n FROM orders
 WHERE hour IN (12,13,14,19,20,21,22) GROUP BY zone,weather HAVING n>=40 ORDER BY v DESC LIMIT 6""")
log("SQL analysis done: KPIs, zone, hour, weather, rider tenure, prep time, restaurants, peak x zone x weather")

# ---------- 3. DRIVER MODEL (OLS, standardised) ----------
X = pd.DataFrame({"Distance":c.distance_km,"Prep time":c.prep_min,"Rider tenure":c.rider_tenure_m,
  "Peak hour":c.hour.isin([12,13,14,19,20,21,22]).astype(int),"Rain":(c.weather=="Rain").astype(int),
  "Heavy rain":(c.weather=="Heavy Rain").astype(int)})
Z = (X-X.mean())/X.std(); y = (c.delivered_min-c.delivered_min.mean())/c.delivered_min.std()
A = np.c_[np.ones(len(Z)),Z.values]; beta = np.linalg.lstsq(A,y,rcond=None)[0][1:]
pred = A@np.linalg.lstsq(A,y,rcond=None)[0]; r2 = 1-((y-pred)**2).sum()/(y**2).sum()
drivers = pd.DataFrame({"label":X.columns,"v":np.abs(beta).round(3),"sign":np.sign(beta)}).sort_values("v",ascending=False)
log(f"Driver model fitted (standardised OLS, R2={r2:.2f}); top driver: {drivers.iloc[0].label}")

# ---------- 4. DASHBOARD ----------
def bars(title,d,unit="%",note=""):
    m = max(d.v.max(),1e-9)
    rows = "".join(f'<div class="r"><span>{html.escape(str(l))}</span><div class="b"><i style="width:{v/m*100:.0f}%"></i></div><b>{v}{unit}</b></div>' for l,v in zip(d.label,d.v))
    return f'<section><h3>{title}</h3><p class="n">{note}</p>{rows}</section>'
tw = by_ten.set_index("label").v; pw = by_wx.set_index("label").v
ins = [f"Weather is the biggest controllable lever (distance is fixed): SLA breach rises from {pw.get('Clear')}% (clear) to {pw.get('Heavy Rain')}% in heavy rain.",
 f"New riders (&lt;3 months) breach {tw.iloc[0]}% of orders versus {tw.iloc[2]}% for 12+ month riders.",
 f"Worst peak-hour hotspot: {combo.iloc[0].label} at {combo.iloc[0].v}% breach.",
 f"Top delay driver by standardised effect: {drivers.iloc[0].label}, then {drivers.iloc[1].label}.",
 f"Cancellations cost an estimated ₹{kpi.lost_rev:,.0f} ({kpi.lost_rev/kpi.gmv*100:.1f}% of GMV)."]
recs = ["Add surge rider incentives and dynamic ETA buffers for Rain/Heavy Rain in outer zones.",
 "Pair new riders with short-distance, low-congestion orders for their first 3 months.",
 "Renegotiate prep-time SLAs with the slowest restaurants; pause promos on them at peak.",
 "Pre-position riders in Whitefield, Electronic City and Hebbal before 12:00 and 19:00."]
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Delivery Delay Root-Cause Dashboard</title><style>
:root{{--bg:#f7f7f4;--card:#fff;--tx:#1d1d1b;--mu:#6b6b66;--ac:#0f766e;--bd:#e3e3dd;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#151514;--card:#1f1f1d;--tx:#f0f0ec;--mu:#a0a09a;--ac:#2dd4bf;--bd:#333330}}}}
body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 system-ui,sans-serif;padding:20px}}
h1{{margin:0 0 4px}}.sub{{color:var(--mu);margin:0 0 18px}}
.k{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px}}
.k div,section{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px}}
.k b{{display:block;font-size:24px;color:var(--ac)}}.k span{{color:var(--mu);font-size:13px}}
.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}}
h3{{margin:0 0 2px;font-size:16px}}.n{{color:var(--mu);font-size:12px;margin:0 0 8px}}
.r{{display:grid;grid-template-columns:130px 1fr 52px;gap:8px;align-items:center;font-size:13px;margin:4px 0}}
.b{{background:var(--bd);height:10px;border-radius:5px;overflow:hidden}}.b i{{display:block;height:100%;background:var(--ac)}}
.r b{{text-align:right}}li{{margin:6px 0}}</style></head><body>
<h1>Delivery Delay Root-Cause Dashboard</h1><p class="sub">{kpi.orders:,.0f} orders · Bengaluru · Jun–Aug 2026 · synthetic dataset</p>
<div class="k"><div><b>{kpi.breach_pct}%</b><span>SLA breach rate</span></div><div><b>{kpi.avg_min} min</b><span>Avg delivery time</span></div>
<div><b>{kpi.cancel_pct}%</b><span>Cancellation rate</span></div><div><b>₹{kpi.lost_rev/1e5:.1f} L</b><span>Revenue lost to cancels</span></div></div>
<div class="g">{bars("SLA breach by zone",by_zone)}{bars("SLA breach by weather",by_wx)}{bars("SLA breach by rider tenure",by_ten)}
{bars("SLA breach by restaurant prep time",by_prep)}{bars("SLA breach by hour of day",by_hour,note="Peaks at lunch and dinner")}
{bars("Peak-hour hotspots (zone | weather)",combo)}{bars("Delay drivers (standardised effect)",drivers[["label","v"]],"",f"OLS on delivery time, R² = {r2:.2f}")}
{bars("Slowest restaurants (restaurant ID)",worst_rest)}
<section><h3>Key insights</h3><ul>{''.join(f'<li>{i}</li>' for i in ins)}</ul></section>
<section><h3>Recommendations</h3><ul>{''.join(f'<li>{r}</li>' for r in recs)}</ul></section></div></body></html>"""
open("dashboard.html","w",encoding="utf-8").write(page)
log("Interactive-style HTML dashboard built (dashboard.html)")

# ---------- 5. REPORT + PROGRESS ----------
plain = lambda s: s.replace("&lt;","<")
open("INSIGHTS.md","w",encoding="utf-8").write("# Insights\n"+"\n".join("- "+plain(i) for i in ins)+"\n\n# Recommendations\n"+"\n".join("- "+r for r in recs)+"\n")
open("queries.sql","w").write("-- Core queries are embedded in run_project.py (section 2). Example:\nSELECT zone, ROUND(100.0*AVG(sla_breach),1) AS breach_pct, COUNT(*) n FROM orders GROUP BY zone ORDER BY breach_pct DESC;\n")
log("INSIGHTS.md + queries.sql written")
open("PROGRESS.md","w",encoding="utf-8").write("# Progress Log\nLast updated: "+dt.datetime.now().strftime("%Y-%m-%d %H:%M")+"\n\n"+"\n".join(LOG)+
 "\n\n## Remaining / optional\n- [ ] Swap synthetic data for a real Kaggle delivery dataset\n- [ ] Add Power BI / Tableau version\n- [ ] Add A/B test simulation for rain incentive\n")
print(kpi.to_dict()); print(ins)
