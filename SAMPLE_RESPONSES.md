# Sample System Responses

Three example answers from running the crew. Reports are in the `reports/` folder.

```bash
python run_crew.py "Your question here"
```

---

## Response 1

**Question:** Which products need reordering and which suppliers should be contacted?  
**Report:** `reports/products_needing_reordering.md`

**Answer:**

- **Laptop** — stock 10 (reorder at 20) → contact **TechSupplierA**
- **Keyboard** — stock 5 (reorder at 15) → contact **InputTech**

**Notes:** Follow `reorder_policy.txt`. Laptop has a stock-delay ticket and higher demand before back-to-school.

**Actions:** Reorder laptop and keyboard now. Watch laptop stock in Q3.

---

## Response 2

**Question:** Which products need reordering?  
**Report:** `reports/products_requiring_reorder.md`

**Answer:**

- **Laptop** and **Keyboard** need reordering (stock below reorder level).

**Suppliers:**

- Laptop → TechSupplierA  
- Keyboard → InputTech  

**Actions:** Reorder to about 40 laptops and 30 keyboards (2× reorder level). Watch for supplier delays.

---

## Response 3

**Question:** Which products need reordering?  
**Report:** `reports/products_requiring_reorder_report.md`

**Answer:**

| Product  | Stock | Reorder level | Supplier      |
|----------|-------|---------------|---------------|
| Laptop   | 10    | 20            | TechSupplierA |
| Keyboard | 5     | 15            | InputTech     |

**Actions:**

- Reorder Laptop from TechSupplierA (target ~40 units).
- Reorder Keyboard from InputTech (target ~30 units).
- Check open stock-delay ticket for Laptop.

---

## Source data

Answers use `data/inventory.csv` and files in `data/documents/` (policies, product notes, support tickets).
