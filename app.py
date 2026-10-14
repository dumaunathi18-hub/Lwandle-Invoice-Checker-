import csv
import io
import json
import os
from datetime import date
import streamlit as st

# ==========================================
# CONFIGURATION
# ==========================================
JSON_FILE_PATH = "suppliers_db.json"

st.set_page_config(
    page_title="Invoice Validation Checker", page_icon="📋", layout="centered"
)

st.title("📋 Invoice Validation Checker")
st.write(
    "Upload your CSV invoice file below to automatically check for bank account changes and duplicate invoice numbers."
)

# File uploader widget
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
  # Load JSON database
  db = {}
  if os.path.exists(JSON_FILE_PATH):
    try:
      with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
    except json.JSONDecodeError:
      db = {}

  current_date = date.today().strftime("%Y-%m-%d")
  required_columns = {"supplier_name", "invoice_number", "bank_account", "amount"}

  # Read uploaded CSV file buffer
  decoded_file = uploaded_file.read().decode("utf-8")
  reader = csv.DictReader(io.StringIO(decoded_file))

  # Validate columns
  if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
    st.error(
        f"Error: CSV file must contain columns: {list(required_columns)}"
    )
  else:
    st.subheader("Processing Results")
    success_count = 0
    failure_count = 0

    for row in reader:
      supplier = row.get("supplier_name", "").strip()
      invoice_num = row.get("invoice_number", "").strip()
      bank_acc = row.get("bank_account", "").strip()

      if not supplier or not invoice_num:
        continue

      if supplier not in db:
        db[supplier] = {"bank_account": None, "seen_invoices": []}

      sup_record = db[supplier]

      # Check 1: Bank-Account Change
      bank_changed = False
      if sup_record["bank_account"] is not None:
        if sup_record["bank_account"] != bank_acc:
          bank_changed = True
      else:
        sup_record["bank_account"] = bank_acc

      # Check 2: Duplicate Invoice Number
      is_duplicate = False
      if invoice_num in sup_record["seen_invoices"]:
        is_duplicate = True
      else:
        sup_record["seen_invoices"].append(invoice_num)

      # Evaluate and display results in the web UI
      if not bank_changed and not is_duplicate:
        success_count += 1
        letter_md = f"""
                **CONFIRMATION LETTER**  
                *Date:* {current_date}  
                *Supplier:* {supplier}  
                *Invoice Number:* {invoice_num}  

                This letter confirms that the invoice has passed all validation checks (Bank Account Verification and Duplicate Check).
                """
        st.success(letter_md)
      else:
        failure_count += 1
        issues = []
        if bank_changed:
          issues.append("changed bank details")
        if is_duplicate:
          issues.append("duplicate invoice number")

        issue_str = " and ".join(issues)
        st.error(
            f"ALERT: Supplier '{supplier}', Invoice '{invoice_num}' FAILED."
            f" Issue(s): {issue_str} detected."
        )

    # Save updated database
    with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
      json.dump(db, f, indent=4)

    st.info(
        f"Processing complete! Passed: {success_count} | Failed:"
        f" {failure_count}"
    )
