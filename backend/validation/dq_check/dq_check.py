"""
Complete Data Quality Check and Transform for Golden Dataset
Raw → Golden Dataset
------------------------------------------------------

Features:
✔ Safe numeric comparison
✔ Safe date parsing
✔ Correct categorical cleaning
✔ Auto-removal of invalid rows
✔ Safe NaN handling
✔ Healthcare business rules (enhanced)
✔ Data masking for PII fields
✔ JSON report generation
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import os
import warnings
import hashlib
warnings.filterwarnings('ignore')


class ClaimsGoldenTransformer:
    """Transform raw dirty dataset to golden dataset"""
    
    def __init__(self):
        self.issues = {"critical": [], "errors": [], "warnings": []}
        self.fixes_applied = []
        self.stats = {}
        self.removed_rows = []
        
        # Metrics tracking
        self.metrics = {
            "duplicate_claim_ids": 0,
            "duplicate_rows": 0,
            "total_nulls_found": 0,
            "critical_nulls": 0,
            "invalid_claim_ids": 0,
            "invalid_dates": 0,
            "invalid_dates_removed": 0,
            "future_dates": 0,
            "very_old_dates": 0,
            "non_numeric_amounts": 0,
            "negative_amounts_fixed": 0,
            "categorical_typos_fixed": 0,
            "approved_without_amount": 0,
            "approved_amount_filled": 0,
            "approved_exceeds_claim_fixed": 0,
            "denied_without_reason_fixed": 0,
            "denied_amount_set_to_zero": 0,
            "pending_amount_filled": 0,
            "status_inferred_from_amounts": 0,
            "masked_patient_ids": 0,
            "masked_policy_ids": 0,
            "null_fixes": 0,
            "total_fixes": 0,
            "rows_removed": 0,
            "final_rows": 0,
            "data_completeness_pct": 0.0
        }

    def log_issue(self, severity, field, msg):
        """Log data quality issue"""
        if severity not in self.issues:
            severity = "warnings"
        self.issues[severity].append({"field": field, "message": msg})

    def log_fix(self, msg):
        """Log data transformation fix"""
        self.fixes_applied.append(msg)
        self.metrics["total_fixes"] += 1

    # ===================================================
    # PHASE 0: DATA MASKING (NEW)
    # ===================================================
    
    def mask_pii_fields(self, df):
        """Mask PII fields (Patient_ID, Policy_ID)"""
        print("\n" + "="*60)
        print("PHASE 0: DATA MASKING (PII PROTECTION)")
        print("="*60)
        
        def mask_id(value):
            """Mask ID using SHA-256 hash (first 8 chars)"""
            if pd.isna(value) or str(value).strip() == '':
                return value
            hashed = hashlib.sha256(str(value).encode()).hexdigest()
            return f"MASKED_{hashed[:8].upper()}"
        
        # Mask Patient_ID
        if 'Patient_ID' in df.columns:
            masked_count = df['Patient_ID'].notna().sum()
            df['Patient_ID'] = df['Patient_ID'].apply(mask_id)
            self.metrics["masked_patient_ids"] = masked_count
            self.log_fix(f"Masked {masked_count} Patient_IDs")
            print(f"✓ Masked {masked_count} Patient_IDs")
        
        # Mask Policy_ID
        if 'Policy_ID' in df.columns:
            masked_count = df['Policy_ID'].notna().sum()
            df['Policy_ID'] = df['Policy_ID'].apply(mask_id)
            self.metrics["masked_policy_ids"] = masked_count
            self.log_fix(f"Masked {masked_count} Policy_IDs")
            print(f"✓ Masked {masked_count} Policy_IDs")
        
        print(f"✓ PII masking complete")
        return df

    # ===================================================
    # PHASE 1: DUPLICATES
    # ===================================================
    
    def remove_duplicates(self, df):
        """Remove duplicate records"""
        print("\n" + "="*60)
        print("PHASE 1: DUPLICATE REMOVAL")
        print("="*60)
        
        initial_count = len(df)
        
        # Remove Claim_ID duplicates
        if 'Claim_ID' in df.columns:
            dupes = df['Claim_ID'].duplicated().sum()
            if dupes > 0:
                self.metrics["duplicate_claim_ids"] = dupes
                self.log_issue("critical", "Claim_ID", f"{dupes} duplicates removed")
                duplicated_ids = df[df['Claim_ID'].duplicated()]['Claim_ID'].tolist()
                self.removed_rows.extend(duplicated_ids)
                df = df.drop_duplicates(subset=['Claim_ID'], keep='first')
                self.log_fix(f"Removed {dupes} duplicate Claim_IDs")
                print(f"✓ Removed {dupes} duplicate Claim_IDs")
            else:
                print(f"✓ No duplicate Claim_IDs found")
        
        # Remove complete row duplicates
        row_dupes = df.duplicated().sum()
        if row_dupes > 0:
            self.metrics["duplicate_rows"] = row_dupes
            self.log_issue("warnings", "ROWS", f"{row_dupes} duplicate rows removed")
            df = df.drop_duplicates(keep='first')
            self.log_fix(f"Removed {row_dupes} duplicate rows")
            print(f"✓ Removed {row_dupes} duplicate rows")
        else:
            print(f"✓ No duplicate rows found")
        
        removed = initial_count - len(df)
        print(f"✓ Remaining rows: {len(df)} (removed {removed})")
        return df

    # ===================================================
    # PHASE 2: CRITICAL NULLS
    # ===================================================
    
    def remove_critical_nulls(self, df):
        """Remove rows with critical null values"""
        print("\n" + "="*60)
        print("PHASE 2: CRITICAL NULL REMOVAL")
        print("="*60)
        
        initial_count = len(df)
        critical_fields = ['Claim_ID', 'Patient_ID', 'Policy_ID']
        
        for field in critical_fields:
            if field in df.columns:
                null_mask = df[field].isnull()
                nulls = null_mask.sum()
                
                if nulls > 0:
                    self.metrics["critical_nulls"] += nulls
                    self.log_issue("critical", field, f"{nulls} critical nulls - rows removed")
                    
                    # Store removed IDs
                    if field == 'Claim_ID':
                        self.removed_rows.extend(df[null_mask].index.tolist())
                    
                    # Remove rows
                    df = df[~null_mask]
                    self.log_fix(f"Removed {nulls} rows with null {field}")
                    print(f"✓ Removed {nulls} rows with null {field}")
                else:
                    print(f"✓ No nulls in {field}")
        
        removed = initial_count - len(df)
        print(f"✓ Remaining rows: {len(df)} (removed {removed})")
        return df

    # ===================================================
    # PHASE 3: DATE VALIDATION & REMOVAL (FIXED)
    # ===================================================
    
    def clean_dates(self, df):
        """Parse dates, validate, and remove invalid ones"""
        print("\n" + "="*60)
        print("PHASE 3: DATE VALIDATION & CLEANING")
        print("="*60)
        
        initial_count = len(df)
        
        if 'Date_of_Service' in df.columns:
            # Safe date parsing
            def safe_parse_date(x):
                if pd.isna(x) or str(x).strip() in ['', 'None', 'nan']:
                    return pd.NaT
                
                for fmt in ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        parsed = pd.to_datetime(str(x), format=fmt)
                        return parsed
                    except:
                        continue
                return pd.NaT
            
            # Parse dates
            df['Date_of_Service'] = df['Date_of_Service'].apply(safe_parse_date)
            
            # Count invalid dates (nulls after parsing)
            invalid_dates = df['Date_of_Service'].isnull().sum()
            self.metrics["invalid_dates"] = invalid_dates
            
            # REMOVE invalid dates FIRST
            if invalid_dates > 0:
                self.log_issue("errors", "Date_of_Service", f"{invalid_dates} invalid dates - rows removed")
                df = df[df['Date_of_Service'].notna()]
                self.metrics["invalid_dates_removed"] = invalid_dates
                self.log_fix(f"Removed {invalid_dates} rows with invalid dates")
                print(f"✓ Removed {invalid_dates} rows with invalid dates")
            
            # Check and REMOVE future dates
            if df['Date_of_Service'].notna().any():
                future_mask = df['Date_of_Service'] > pd.Timestamp.now()
                future_dates = future_mask.sum()
                
                if future_dates > 0:
                    self.metrics["future_dates"] = future_dates
                    self.log_issue("errors", "Date_of_Service", f"{future_dates} future dates - rows removed")
                    
                    # Actually REMOVE future dates
                    df = df[~future_mask]
                    self.log_fix(f"Removed {future_dates} rows with future dates")
                    print(f"✓ Removed {future_dates} rows with future dates")
            
            # Check and REMOVE very old dates (before 2000)
            if df['Date_of_Service'].notna().any():
                old_mask = df['Date_of_Service'] < pd.Timestamp('2000-01-01')
                very_old = old_mask.sum()
                
                if very_old > 0:
                    self.metrics["very_old_dates"] = very_old
                    self.log_issue("warnings", "Date_of_Service", f"{very_old} dates before year 2000 - rows removed")
                    
                    # Actually REMOVE old dates
                    df = df[~old_mask]
                    self.log_fix(f"Removed {very_old} rows with dates before year 2000")
                    print(f"✓ Removed {very_old} rows with very old dates")
            
            # Standardize to YYYY-MM-DD (only for valid dates)
            if len(df) > 0:
                df['Date_of_Service'] = df['Date_of_Service'].dt.strftime('%Y-%m-%d')
                self.log_fix("Standardized dates to YYYY-MM-DD format")
                print(f"✓ Standardized dates to YYYY-MM-DD")
        
        removed = initial_count - len(df)
        print(f"✓ Remaining rows: {len(df)} (removed {removed})")
        return df

    # ===================================================
    # PHASE 4: NUMERIC CLEANING (NO REMOVAL)
    # ===================================================
    
    def clean_numeric(self, df):
        """Clean and fix numeric fields without removing rows"""
        print("\n" + "="*60)
        print("PHASE 4: NUMERIC CLEANING")
        print("="*60)
        
        def safe_to_float(val):
            """Safely convert to float"""
            if pd.isna(val):
                return np.nan
            if val in ["N/A", "none", "None", "", "unknown", "nan"]:
                return np.nan
            try:
                val_str = str(val).replace("$", "").replace(",", "").strip()
                return float(val_str)
            except:
                return np.nan
        
        for col in ['Claim_Amount', 'Approved_Amount']:
            if col in df.columns:
                # Convert to numeric
                original = df[col].copy()
                df[col] = df[col].apply(safe_to_float)
                
                # Count non-numeric
                non_numeric = (df[col].isna() & original.notna()).sum()
                if non_numeric > 0:
                    self.metrics["non_numeric_amounts"] += non_numeric
                    self.log_issue("errors", col, f"{non_numeric} non-numeric values set to NaN")
                    print(f"⚠ {col}: {non_numeric} non-numeric values → NaN")
                
                # Fix negatives to absolute value
                negative_mask = (df[col] < 0) & df[col].notna()
                negatives = negative_mask.sum()
                if negatives > 0:
                    self.metrics["negative_amounts_fixed"] += negatives
                    df.loc[negative_mask, col] = df.loc[negative_mask, col].abs()
                    self.log_fix(f"Fixed {negatives} negative values in {col}")
                    print(f"✓ {col}: Fixed {negatives} negative values")
                
                # Round to 2 decimals
                df[col] = df[col].round(2)
        
        self.log_fix("Numeric fields cleaned and rounded to 2 decimals")
        print(f"✓ Numeric cleaning complete")
        return df

    # ===================================================
    # PHASE 5: CATEGORICAL CLEANING
    # ===================================================
    
    def clean_categorical(self, df):
        """Clean and standardize categorical fields"""
        print("\n" + "="*60)
        print("PHASE 5: CATEGORICAL CLEANING")
        print("="*60)
        
        # Define typo fixes
        typo_fixes = {
            'Claim_Type': {
                'Cosmtic': 'Cosmetic',
                'Genral': 'General',
                'Emergncy': 'Emergency'
            },
            'Network_Status': {
                'Out-Network': 'Out-of-Network',
                'Out-Ntwk': 'Out-of-Network'
            },
            'Claim_Status': {
                'Approvd': 'Approved',
                'Pnding': 'Pending',
                'In Review': 'Pending'
            }
        }
        
        total_typos = 0
        
        for col in ['Claim_Type', 'Network_Status', 'Claim_Status', 'Error_Type']:
            if col in df.columns:
                # Standardize format
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.strip()
                    .str.title()
                    .replace({'None': np.nan, 'Nan': np.nan, '': np.nan})
                )
                
                # Fix known typos
                if col in typo_fixes:
                    typos_found = df[col].isin(typo_fixes[col].keys()).sum()
                    if typos_found > 0:
                        total_typos += typos_found
                        df[col] = df[col].replace(typo_fixes[col])
                        self.log_fix(f"Fixed {typos_found} typos in {col}")
                
                print(f"✓ {col}: Standardized format")
        
        if total_typos > 0:
            self.metrics["categorical_typos_fixed"] = total_typos
            print(f"✓ Fixed {total_typos} categorical typos")
        
        self.log_fix("Categorical fields normalized")
        return df

    # ===================================================
    # PHASE 6: BUSINESS RULES (ENHANCED & FIXED)
    # ===================================================
    
    def apply_business_rules(self, df):
        """Apply enhanced healthcare claims business rules"""
        print("\n" + "="*60)
        print("PHASE 6: BUSINESS RULES (ENHANCED)")
        print("="*60)
        
        # Rule 1: Infer missing Claim_Status from amounts and error types
        if 'Claim_Status' in df.columns and 'Claim_Amount' in df.columns and 'Approved_Amount' in df.columns:
            status_null = df['Claim_Status'].isna()
            
            if status_null.sum() > 0:
                print(f"  Inferring {status_null.sum()} missing Claim_Status values...")
                
                # Has both amounts and NO error -> Approved
                mask_approved = (
                    status_null & 
                    df['Claim_Amount'].notna() & 
                    df['Approved_Amount'].notna() & 
                    (df['Approved_Amount'] > 0) &
                    (df['Error_Type'].isna() | 
                     (df['Error_Type'].astype(str).str.strip().str.lower().isin(['', 'none', 'nan', 'unknown'])))
                )
                approved_count = mask_approved.sum()
                if approved_count > 0:
                    df.loc[mask_approved, 'Claim_Status'] = 'Approved'
                    self.metrics["status_inferred_from_amounts"] += approved_count
                    self.log_fix(f"Inferred {approved_count} claims as 'Approved' (has amounts, no errors)")
                    print(f"  ✓ Inferred {approved_count} as 'Approved'")
                
                # Has claim amount, has error (any error) -> Pending or Denied
                # Check if has denial reason -> Denied, else -> Pending
                if 'Denial_Reason' in df.columns:
                    mask_denied = (
                        status_null & 
                        df['Claim_Amount'].notna() & 
                        df['Error_Type'].notna() &
                        ~(df['Error_Type'].astype(str).str.strip().str.lower().isin(['', 'none', 'nan', 'unknown'])) &
                        df['Denial_Reason'].notna() &
                        ~(df['Denial_Reason'].astype(str).str.strip().str.lower().isin(['', 'n/a', 'none', 'nan']))
                    )
                    denied_count = mask_denied.sum()
                    if denied_count > 0:
                        df.loc[mask_denied, 'Claim_Status'] = 'Denied'
                        self.metrics["status_inferred_from_amounts"] += denied_count
                        self.log_fix(f"Inferred {denied_count} claims as 'Denied' (has error + denial reason)")
                        print(f"  ✓ Inferred {denied_count} as 'Denied'")
                
                # Has error but no denial reason -> Pending
                mask_pending = (
                    status_null & 
                    df['Claim_Amount'].notna() & 
                    df['Error_Type'].notna() &
                    ~(df['Error_Type'].astype(str).str.strip().str.lower().isin(['', 'none', 'nan', 'unknown']))
                )
                # Re-check to exclude already classified as denied
                if 'Denial_Reason' in df.columns:
                    mask_pending = mask_pending & (
                        df['Denial_Reason'].isna() | 
                        (df['Denial_Reason'].astype(str).str.strip().str.lower().isin(['', 'n/a', 'none', 'nan']))
                    )
                
                pending_count = mask_pending.sum()
                if pending_count > 0:
                    df.loc[mask_pending, 'Claim_Status'] = 'Pending'
                    self.metrics["status_inferred_from_amounts"] += pending_count
                    self.log_fix(f"Inferred {pending_count} claims as 'Pending' (has error, no denial reason)")
                    print(f"  ✓ Inferred {pending_count} as 'Pending'")
        
        # Rule 2: Claims with Error_Type should NOT be Approved
        if 'Claim_Status' in df.columns and 'Error_Type' in df.columns:
            has_error = (
                df['Error_Type'].notna() & 
                ~(df['Error_Type'].astype(str).str.strip().str.lower().isin(['', 'none', 'nan', 'unknown']))
            )
            wrongly_approved = has_error & df['Claim_Status'].str.contains('Approv', case=False, na=False)
            
            fixes = wrongly_approved.sum()
            if fixes > 0:
                # Change to Pending (conservative - needs review)
                df.loc[wrongly_approved, 'Claim_Status'] = 'Pending'
                self.log_fix(f"Changed {fixes} claims from 'Approved' to 'Pending' (has error type)")
                self.log_issue("errors", "Claim_Status", f"{fixes} approved claims have error types - changed to Pending")
                print(f"  ✓ Fixed {fixes} approved claims with errors → Changed to 'Pending'")
        
        # Rule 3: Denied claims must have Approved_Amount = 0
        if 'Claim_Status' in df.columns and 'Approved_Amount' in df.columns:
            denied_mask = df['Claim_Status'].str.contains('Denied', case=False, na=False)
            denied_has_amount = denied_mask & (df['Approved_Amount'].notna() & (df['Approved_Amount'] > 0))
            
            fixes = denied_has_amount.sum()
            if fixes > 0:
                df.loc[denied_has_amount, 'Approved_Amount'] = 0.0
                self.metrics["denied_amount_set_to_zero"] += fixes
                self.log_fix(f"Set {fixes} denied claims Approved_Amount to 0.0")
                print(f"  ✓ Set {fixes} denied claims Approved_Amount to 0.0")
            
            # Fill null approved amounts for denied claims
            denied_null_amount = denied_mask & df['Approved_Amount'].isna()
            fixes = denied_null_amount.sum()
            if fixes > 0:
                df.loc[denied_null_amount, 'Approved_Amount'] = 0.0
                self.metrics["denied_amount_set_to_zero"] += fixes
                self.log_fix(f"Filled {fixes} denied claims with Approved_Amount = 0.0")
                print(f"  ✓ Filled {fixes} denied claims with Approved_Amount = 0.0")
        
        # Rule 4: Denied claims must have denial reason
        if 'Claim_Status' in df.columns and 'Denial_Reason' in df.columns:
            denied_mask = df['Claim_Status'].str.contains('Denied', case=False, na=False)
            no_reason_mask = (
                denied_mask & 
                (df['Denial_Reason'].isna() | 
                 (df['Denial_Reason'].astype(str).str.strip().isin(['', 'nan', 'None', 'N/A'])))
            )
            
            fixes = no_reason_mask.sum()
            if fixes > 0:
                self.metrics["denied_without_reason_fixed"] = fixes
                df.loc[no_reason_mask, 'Denial_Reason'] = 'Reason Not Provided'
                self.log_fix(f"Filled {fixes} missing denial reasons")
                print(f"  ✓ Filled {fixes} missing denial reasons")
        
        # Rule 5: Pending claims - Only fill NULL Approved_Amount with 0.0 (FIXED)
        if 'Claim_Status' in df.columns and 'Approved_Amount' in df.columns:
            pending_mask = df['Claim_Status'].str.contains('Pending', case=False, na=False)
            
            # Only fill if Approved_Amount is NULL/NaN (don't overwrite existing values)
            pending_null_amount = pending_mask & df['Approved_Amount'].isna()
            
            fixes = pending_null_amount.sum()
            if fixes > 0:
                df.loc[pending_null_amount, 'Approved_Amount'] = 0.0
                self.metrics["pending_amount_filled"] = fixes
                self.log_fix(f"Filled {fixes} pending claims with NULL Approved_Amount → 0.0")
                print(f"  ✓ Filled {fixes} pending claims with NULL Approved_Amount → 0.0")
            
            # Count pending with existing amounts (should be preserved)
            pending_with_amount = pending_mask & df['Approved_Amount'].notna() & (df['Approved_Amount'] > 0)
            if pending_with_amount.sum() > 0:
                print(f"  ℹ {pending_with_amount.sum()} pending claims have existing Approved_Amount (preserved)")
        
        # Rule 6: Approved claims should have approved amount (only if no error)
        if 'Claim_Status' in df.columns and 'Approved_Amount' in df.columns and 'Claim_Amount' in df.columns:
            approved_mask = df['Claim_Status'].str.contains('Approv', case=False, na=False)
            
            # Only fill if no error type
            if 'Error_Type' in df.columns:
                no_error = (
                    df['Error_Type'].isna() | 
                    (df['Error_Type'].astype(str).str.strip().str.lower().isin(['', 'none', 'nan', 'unknown']))
                )
                no_amount = approved_mask & no_error & (df['Approved_Amount'].isna() | (df['Approved_Amount'] == 0))
            else:
                no_amount = approved_mask & (df['Approved_Amount'].isna() | (df['Approved_Amount'] == 0))
            
            fixes = no_amount.sum()
            if fixes > 0:
                # Fill with claim amount (conservative estimate)
                df.loc[no_amount, 'Approved_Amount'] = df.loc[no_amount, 'Claim_Amount']
                self.metrics["approved_amount_filled"] = fixes
                self.log_fix(f"Filled {fixes} approved claims Approved_Amount with Claim_Amount")
                print(f"  ✓ Filled {fixes} approved claims with Approved_Amount = Claim_Amount")
        
        # Rule 7: Approved amount shouldn't exceed claim amount
        if 'Claim_Amount' in df.columns and 'Approved_Amount' in df.columns:
            exceeds_mask = (
                (df['Approved_Amount'] > df['Claim_Amount']) & 
                df['Approved_Amount'].notna() & 
                df['Claim_Amount'].notna()
            )
            
            adjustments = exceeds_mask.sum()
            if adjustments > 0:
                self.metrics["approved_exceeds_claim_fixed"] = adjustments
                df.loc[exceeds_mask, 'Approved_Amount'] = df.loc[exceeds_mask, 'Claim_Amount']
                self.log_fix(f"Adjusted {adjustments} cases where approved > claim")
                print(f"  ✓ Fixed {adjustments} cases where approved > claim")
        
        print(f"✓ Business rules applied")
        return df

    # ===================================================
    # PHASE 7: FILL REMAINING NULLS
    # ===================================================
    
    def fill_nulls(self, df):
        """Fill remaining non-critical null values"""
        print("\n" + "="*60)
        print("PHASE 7: NULL FILLING")
        print("="*60)
        
        null_fills = 0
        
        # Fill text columns with "Unknown"
        text_cols = ['Claim_Type', 'Error_Type']
        for col in text_cols:
            if col in df.columns:
                nulls = df[col].isna().sum()
                if nulls > 0:
                    df[col].fillna('Unknown', inplace=True)
                    null_fills += nulls
                    print(f"✓ {col}: Filled {nulls} nulls with 'Unknown'")
        
        # Fill Denial_Reason for non-denied claims
        if 'Denial_Reason' in df.columns and 'Claim_Status' in df.columns:
            not_denied_mask = ~df['Claim_Status'].str.contains('Denied', case=False, na=False)
            null_mask = df['Denial_Reason'].isna()
            fill_mask = not_denied_mask & null_mask
            
            filled = fill_mask.sum()
            if filled > 0:
                df.loc[fill_mask, 'Denial_Reason'] = 'N/A'
                null_fills += filled
                print(f"✓ Denial_Reason: Filled {filled} nulls with 'N/A'")
        
        # Fill missing Claim_Status with 'Pending' (conservative)
        if 'Claim_Status' in df.columns:
            nulls = df['Claim_Status'].isna().sum()
            if nulls > 0:
                df['Claim_Status'].fillna('Pending', inplace=True)
                null_fills += nulls
                print(f"✓ Claim_Status: Filled {nulls} nulls with 'Pending'")
        
        if null_fills > 0:
            self.metrics["null_fixes"] = null_fills
            self.log_fix(f"Filled {null_fills} null values")
        
        print(f"✓ Null filling complete")
        return df

    # ===================================================
    # PHASE 8: ENSURE TARGET ROWS
    # ===================================================
    
    def ensure_target_rows(self, df, target=100):
        """Ensure exactly target rows (default 100)"""
        print("\n" + "="*60)
        print(f"PHASE 8: ENSURE {target} ROWS")
        print("="*60)
        
        current_rows = len(df)
        
        if current_rows > target:
            # Take first N rows
            df = df.head(target)
            removed = current_rows - target
            self.log_fix(f"Trimmed to {target} rows (removed {removed})")
            print(f"✓ Trimmed to {target} rows (removed {removed})")
        elif current_rows < target:
            shortage = target - current_rows
            print(f"⚠ Warning: Only {current_rows} valid rows (need {shortage} more)")
            self.log_issue("warnings", "ROWS", f"Only {current_rows} valid rows available")
        else:
            print(f"✓ Exactly {target} rows - perfect!")
        
        self.metrics["final_rows"] = len(df)
        return df

    # ===================================================
    # STATISTICS & EXPORT
    # ===================================================
    
    def calculate_stats(self, df, original_count, original_cols):
        """Calculate final statistics"""
        print("\n" + "="*60)
        print("CALCULATING STATISTICS")
        print("="*60)
        
        # Overall stats
        self.stats = {
            "original_rows": original_count,
            "final_rows": len(df),
            "removed_rows": original_count - len(df),
            "original_columns": original_cols,
            "final_columns": len(df.columns),
            "total_fixes": len(self.fixes_applied)
        }
        
        # Data completeness
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        self.stats["completeness_pct"] = round(
            ((total_cells - null_cells) / total_cells) * 100, 2
        )
        
        # Count remaining nulls
        self.metrics["total_nulls_found"] = int(null_cells)
        self.metrics["data_completeness_pct"] = self.stats["completeness_pct"]
        self.metrics["rows_removed"] = self.stats["removed_rows"]
        
        # Column-wise null counts
        self.stats["null_counts"] = {k: int(v) for k, v in df.isnull().sum().to_dict().items()}
        
        # Categorical distributions
        categorical_cols = ['Claim_Type', 'Network_Status', 'Claim_Status']
        for col in categorical_cols:
            if col in df.columns:
                self.stats[f"{col.lower()}_distribution"] = df[col].value_counts().to_dict()
        
        # Amount statistics
        if 'Claim_Amount' in df.columns:
            amounts = pd.to_numeric(df['Claim_Amount'], errors='coerce').dropna()
            if len(amounts) > 0:
                self.stats['claim_amount'] = {
                    "count": int(len(amounts)),
                    "total": round(float(amounts.sum()), 2),
                    "mean": round(float(amounts.mean()), 2),
                    "median": round(float(amounts.median()), 2),
                    "min": round(float(amounts.min()), 2),
                    "max": round(float(amounts.max()), 2)
                }
        
        if 'Approved_Amount' in df.columns:
            approved = pd.to_numeric(df['Approved_Amount'], errors='coerce').dropna()
            if len(approved) > 0:
                self.stats['approved_amount'] = {
                    "count": int(len(approved)),
                    "total": round(float(approved.sum()), 2),
                    "mean": round(float(approved.mean()), 2),
                    "median": round(float(approved.median()), 2),
                    "min": round(float(approved.min()), 2),
                    "max": round(float(approved.max()), 2)
                }
        
        print(f"✓ Final rows: {len(df)}")
        print(f"✓ Data completeness: {self.stats['completeness_pct']}%")
        print(f"✓ Total fixes: {self.stats['total_fixes']}")

    def save_outputs(self, df, output_csv, report_json="output/dq_report.json"):
        """Save golden dataset and comprehensive JSON report"""
        # Create output directory
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        os.makedirs(os.path.dirname(report_json), exist_ok=True)
        
        # Save dataset
        df.to_csv(output_csv, index=False)
        
        # Create comprehensive report
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "pipeline_version": "2.0.0 (with PII masking)",
                "input_file": "Synthetic_dataset.csv",
                "output_file": output_csv,
                "pii_masked": True
            },
            "transformation_summary": {
                "original_shape": {
                    "rows": self.stats["original_rows"],
                    "columns": self.stats["original_columns"]
                },
                "final_shape": {
                    "rows": self.stats["final_rows"],
                    "columns": self.stats["final_columns"]
                },
                "rows_removed": self.stats["removed_rows"],
                "data_completeness_pct": self.stats["completeness_pct"],
                "total_fixes_applied": self.stats["total_fixes"]
            },
            "data_quality_metrics": self.metrics,
            "issues_found": {
                "critical": self.issues["critical"],
                "errors": self.issues["errors"],
                "warnings": self.issues["warnings"],
                "total_issues": sum(len(v) for v in self.issues.values())
            },
            "fixes_applied": self.fixes_applied,
            "data_statistics": {
                "null_counts_by_column": self.stats.get("null_counts", {}),
                "categorical_distributions": {
                    "claim_type": self.stats.get("claim_type_distribution", {}),
                    "network_status": self.stats.get("network_status_distribution", {}),
                    "claim_status": self.stats.get("claim_status_distribution", {})
                },
                "amount_statistics": {
                    "claim_amount": self.stats.get("claim_amount", {}),
                    "approved_amount": self.stats.get("approved_amount", {})
                }
            }
        }
        
        with open(report_json, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        return output_csv, report_json

    # ===================================================
    # MAIN PIPELINE
    # ===================================================
    
    def run_full_pipeline(self, input_csv, output_csv, target_rows=100):
        """Execute complete transformation pipeline"""
        print("\n" + "="*70)
        print("DATA QUALITY & TRANSFORMATION PIPELINE")
        print("="*70)
        
        # Load
        print(f"\nLoading: {input_csv}")
        df = pd.read_csv(input_csv)
        original_count = len(df)
        original_cols = len(df.columns)
        print(f"✓ Loaded {original_count} rows × {original_cols} cols")
        print(f"✓ Target: {target_rows} clean rows")
        
        # Execute phases
        df = self.mask_pii_fields(df)          # NEW: Phase 0
        df = self.remove_duplicates(df)
        df = self.remove_critical_nulls(df)
        df = self.clean_dates(df)
        df = self.clean_numeric(df)
        df = self.clean_categorical(df)
        df = self.apply_business_rules(df)
        df = self.fill_nulls(df)
        df = self.ensure_target_rows(df, target_rows)
        
        # Calculate stats
        self.calculate_stats(df, original_count, original_cols)
        
        # Save outputs
        golden_file, report_file = self.save_outputs(df, output_csv)
        
        # Print summary
        print("\n" + "="*70)
        print("✅ TRANSFORMATION COMPLETE")
        print("="*70)
        print(f"✓ Golden Dataset: {golden_file}")
        print(f"✓ DQ Report JSON: {report_file}")
        print(f"✓ Final Rows: {len(df)}")
        print(f"✓ Rows Removed: {self.metrics['rows_removed']}")
        print(f"✓ Total Fixes: {self.metrics['total_fixes']}")
        print(f"✓ Data Completeness: {self.stats['completeness_pct']}%")
        print(f"✓ PII Masked: {self.metrics['masked_patient_ids']} Patient IDs, {self.metrics['masked_policy_ids']} Policy IDs")
        print(f"✓ Status Inferred: {self.metrics['status_inferred_from_amounts']}")
        print(f"✓ Denied Claims Amount Set to 0: {self.metrics['denied_amount_set_to_zero']}")
        print(f"✓ Approved Claims Amount Filled: {self.metrics['approved_amount_filled']}")
        print("="*70)
        
        # Show sample
        print("\nSample of Golden Dataset (first 5 rows):")
        print(df.head().to_string())
        print("\n✅ Pipeline Complete!\n")
        
        return df


# ===================================================
# MAIN EXECUTION
# ===================================================

def main():
    """Main execution"""
    
    # Paths
    input_csv = "../../../datasets/CLM_AI_UC_001/Synthetic_dataset.csv"
    output_csv = "../../../datasets/CLM_AI_UC_001/Golden_dataset.csv"
    
    # Check file exists
    if not os.path.exists(input_csv):
        print(f"✗ File not found: {input_csv}")
        print(f"  Expected location: {os.path.abspath(input_csv)}")
        return
    
    # Run transformation
    transformer = ClaimsGoldenTransformer()
    transformer.run_full_pipeline(input_csv, output_csv, target_rows=100)


if __name__ == "__main__":
    main()