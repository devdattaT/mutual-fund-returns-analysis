import os

import pandas as pd
import matplotlib.pyplot as plt

# Create the figure
fig, ax = plt.subplots(figsize=(16, 9))


fnds =[{'cd':'122639', 'name': 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth'}, 
           {'cd':'115676', 'name': 'SBI GOLD FUND REGULAR PLAN - GROWTH'},
           {'cd':'100822', 'name': 'UTI - NIFTY Index Fund- Regular Plan - Growth Option'},
           {'cd':'100377', 'name': 'Nippon India Growth Fund-Growth Plan-Growth Option'},
           {'cd':'106235', 'name': 'Nippon India Large Cap  Fund- Growth Plan -Growth Option'},
           {'cd':'105758', 'name': 'HDFC Mid-Cap Opportunities Fund - Growth Plan'},
           {'cd':'113177', 'name': 'Nippon India Small Cap Fund - Growth Plan - Growth Option'}           
           ]

for fund in fnds:
    print(f"Processing fund: {fund['name']} with code: {fund['cd']}")
    fileName = os.path.join('returns_data', f"{fund['cd']}_7year_returns.csv")
    #Load the CSV
    fundData = pd.read_csv(fileName)
    # Convert date column to datetime
    fundData["end_date"] = pd.to_datetime(fundData["end_date"], dayfirst=True, format="%Y-%m-%d")
    # Ensure data is sorted by date
    fundData = fundData.sort_values("end_date")
    # Plot the two funds
    ax.plot(
        fundData["end_date"],
        fundData["xirr"],
        label=fund['name'],
        linewidth=2
    )

# Formatting
ax.set_xlabel("7 Year SIP end Date")
ax.set_ylabel("XIRR (%)")
ax.set_title("Fund XIRR Comparison for 7 Year SIP")
ax.legend()
ax.grid(True)

# Put legend outside
ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.10),
    ncol=3,
    frameon=False
)

plt.tight_layout()

# Save to JPEG
fig.savefig(
    os.path.join('images', "fund_comparison_7yrs.jpg"),
    format="jpg",
    dpi=600,
    bbox_inches="tight"
)

plt.close(fig)