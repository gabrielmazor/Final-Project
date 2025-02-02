import itertools
import pandas as pd
from group4.group4 import Group4
from group4.helpers.runner import run_a_tournament

# Define the grid of hyperparameters.
param_grid = {
    "expB": [1.0, 1.15, 1.3],
    "expC": [0.6, 0.7, 0.8],
    "tol_boulware": [0.05, 0.1, 0.15],
    "multiplier_boulware": [0.65, 0.75, 0.85],
    "multiplier_other": [0.35, 0.4, 0.45]
}

results = []

# Iterate over every combination in the grid.
for expB_val, expC_val, tol_val, mult_b_val, mult_o_val in itertools.product(
        param_grid["expB"],
        param_grid["expC"],
        param_grid["tol_boulware"],
        param_grid["multiplier_boulware"],
        param_grid["multiplier_other"]):
    
    scores = []
    
    # Set hyperparameters on the Group4 class.
    Group4.exp = expB_val
    Group4.expC = expC_val
    Group4.tol_boulware = tol_val
    Group4.multiplier_boulware = mult_b_val
    Group4.multiplier_other = mult_o_val

    # Run the tournament 5 times for this combination.
    for _ in range(5):
        df = run_a_tournament(Group4, small=True, debug=False)
        # Assume df is a DataFrame with a "strategy" column and a "score" column,
        # and that your agent is identified as "Group4".
        row = df[df["strategy"] == "Group4"]
        if not row.empty:
            score = row["score"].values[0]
            scores.append(score)
    
    avg_score = sum(scores) / len(scores) if scores else None
    results.append(((expB_val, expC_val, tol_val, mult_b_val, mult_o_val), avg_score))
    print(f"Tested: expB={expB_val}, expC={expC_val}, tol_boulware={tol_val}, multiplier_boulware={mult_b_val}, multiplier_other={mult_o_val} -> Avg Score: {avg_score}")

# Sort results by average score (highest first)
results_sorted = sorted(results, key=lambda x: x[1] if x[1] is not None else -999, reverse=True)

print("\nSorted Hyperparameter Combinations (best first):")
for params, avg in results_sorted:
    expB_val, expC_val, tol_val, mult_b_val, mult_o_val = params
    print(f"expB={expB_val}, expC={expC_val}, tol_boulware: {tol_val}, multiplier_boulware: {mult_b_val}, multiplier_other: {mult_o_val} -> Avg Score: {avg}")