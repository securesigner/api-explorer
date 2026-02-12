import json
from collections import defaultdict

with open("data/apis.json") as f:
    apis = json.load(f)

cat_stats = defaultdict(
    lambda: {"total": 0, "pending_apikey": 0, "tested_apikey": 0, "total_apikey": 0}
)
for api in apis:
    cat = api["category"]
    cat_stats[cat]["total"] += 1
    if api["auth"] == "api-key":
        cat_stats[cat]["total_apikey"] += 1
        if api["status"] == "pending":
            cat_stats[cat]["pending_apikey"] += 1
        else:
            cat_stats[cat]["tested_apikey"] += 1

print("=== PENDING api-key APIs by Category ===")
print("Category                       Pending  Tested   Total  % Done")
print("-" * 70)
sorted_cats = sorted(cat_stats.items(), key=lambda x: -x[1]["pending_apikey"])
total_pending = 0
total_tested = 0
total_apikey = 0
for cat, stats in sorted_cats:
    if stats["total_apikey"] > 0:
        pct = stats["tested_apikey"] / stats["total_apikey"] * 100
        print(
            f"{cat:<30s} {stats['pending_apikey']:>8d} {stats['tested_apikey']:>8d} {stats['total_apikey']:>8d} {pct:>7.0f}%"
        )
        total_pending += stats["pending_apikey"]
        total_tested += stats["tested_apikey"]
        total_apikey += stats["total_apikey"]
print("-" * 70)
pct_total = total_tested / total_apikey * 100 if total_apikey > 0 else 0
print(
    f"{'TOTAL':<30s} {total_pending:>8d} {total_tested:>8d} {total_apikey:>8d} {pct_total:>7.0f}%"
)

print()
print("=== Categories CLOSEST to 100% api-key completion (fewest pending) ===")
close_cats = [
    (cat, s) for cat, s in cat_stats.items() if s["total_apikey"] > 0 and s["pending_apikey"] > 0
]
close_cats.sort(key=lambda x: x[1]["pending_apikey"])
for cat, stats in close_cats[:20]:
    pct = stats["tested_apikey"] / stats["total_apikey"] * 100
    print(
        f"  {cat:<30s} {stats['pending_apikey']} pending of {stats['total_apikey']} ({pct:.0f}% done)"
    )

print()
print("=== Categories 100% api-key complete ===")
done = [
    (cat, s) for cat, s in cat_stats.items() if s["total_apikey"] > 0 and s["pending_apikey"] == 0
]
done.sort(key=lambda x: x[0])
for cat, stats in done:
    print(f"  {cat:<30s} {stats['total_apikey']} api-key APIs all tested")
