# 🍬 Nassau Candy - Profitability Dashboard

A Streamlit dashboard for Nassau Candy Distributor's product line profitability and margin performance analysis.
# To See
[https://lmn6ttsxkmebemz44ng9qj.streamlit.app/](https://2df42t6xv6cfzzjh3dapnu.streamlit.app/#product-level-margin-leaderboard)

---


## 📌 Project Overview
A complete end-to-end profitability analysis of Nassau Candy Distributor's product lines.
This project identifies high-margin products, underperforming divisions, cost risks,
and profit concentration patterns using Python & data visualization.

---

## 🎯 Objectives
- Analyze product-level and division-level profitability
- Calculate 5 key financial KPIs across all product lines
- Identify top profit-generating products using Pareto analysis
- Flag low-margin and high-margin products for business action
- Build an interactive Streamlit dashboard

---

## 🔑 KPIs Calculated
| KPI | Formula |
|-----|---------|
| Gross Margin (%) | Gross Profit ÷ Sales × 100 |
| Profit per Unit | Gross Profit ÷ Units |
| Revenue Contribution | Product Sales ÷ Total Sales × 100 |
| Profit Contribution | Product Profit ÷ Total Profit × 100 |
| Margin Volatility | Std Dev of monthly Gross Margin % per product |

---

## 🛠️ Tools & Technologies
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=flat)
![Seaborn](https://img.shields.io/badge/Seaborn-4c9be8?style=flat)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
---

## 📂 Project Structure
```
Nassau-Candy-Analysis/
│
├── Nassau_Candy_Profitability_Analysis.ipynb   # Main notebook
├── data/
│   └── nassau_candy.csv                        # Input dataset
└── README.md
```

---

## 📊 Analysis Sections
1. **Data Cleaning & Validation** — Handle missing values, date formatting, duplicates
2. **KPI Calculation** — 5 profitability metrics at row and product level
3. **Product-Level Analysis** — Top 10 products by profit, quadrant scatter plot
4. **Division Dashboard** — Revenue vs Profit comparison, margin distribution
5. **Pareto Analysis** — 80/20 profit concentration, top 5 product dependency
6. **Cost vs Margin Diagnostics** — Risk flags (🔴 Low / 🟡 Average / 🟢 High margin)
7. **Streamlit Dashboard** — Interactive visualizations

---
## 👤 Author
**Tridev** — Data Analyst
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?logo=linkedin)](https://www.linkedin.com/in/tridev-pal-74575a379/)
[![GitHub](https://img.shields.io/badge/GitHub-black?logo=github)](https://github.com/danem47531-byte)

