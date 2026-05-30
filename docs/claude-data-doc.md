# Data Documentation

## Purpose

This file documents important findings about the data used in this project. Keep this updated as you discover new information about data schema, quality issues, business rules, and data quirks.

---

## Data Schema

### Dataset: [Dataset Name]

**Source**: [Where the data comes from]

**Update Frequency**: [How often data is updated]

**Date Range**: [Earliest to latest dates in dataset]

#### Column Descriptions

| Column Name | Data Type | Description | Expected Values/Range | Notes |
|------------|-----------|-------------|----------------------|-------|
| example_col | string | Brief description | Valid values or range | Any quirks or issues |
| date_col | datetime | Transaction date | 2020-01-01 to present | Format: YYYY-MM-DD |
| amount_col | float | Dollar amount | 0 to 1,000,000 | Can have nulls for pending |

---

## Data Quality Issues

### Missing Values

**Column: [column_name]**
- **Frequency**: X% of records
- **Pattern**: [When/why they occur]
- **Impact**: [How this affects analysis]
- **Handling**: [How we handle in pipeline]

**Example**:
```
Column: payment_amount
- Frequency: 5% of records
- Pattern: Missing for claims with status='Pending'
- Impact: Cannot calculate total revenue accurately
- Handling: Excluded from revenue calculations in CalculateMetrics task
```

### Data Inconsistencies

**Issue: [Brief description]**
- **Details**: [What's inconsistent]
- **Affected Records**: [How many/which records]
- **Resolution**: [How we handle this]

**Example**:
```
Issue: Date format inconsistency
- Details: Some dates are MM/DD/YYYY, others are YYYY-MM-DD
- Affected Records: ~10% of records before 2022-01-01
- Resolution: Standardized to YYYY-MM-DD in LoadData task using pd.to_datetime()
```

### Outliers

**Field: [field_name]**
- **Outlier Definition**: [What qualifies as outlier]
- **Frequency**: [How common]
- **Cause**: [Why they occur]
- **Treatment**: [What we do with them]

**Example**:
```
Field: transaction_amount
- Outlier Definition: Values > $100,000 or < -$10,000
- Frequency: 0.1% of transactions
- Cause: Bulk adjustments and refunds
- Treatment: Flagged but not removed; handled separately in analysis
```

---

## Business Rules

### Rule: [Rule Name]

**Description**: [What the rule is]

**Logic**: [How it's implemented]

**Applies To**: [Which data/records]

**Example**:
```
Rule: Claim Eligibility
Description: Claims are only eligible for payment if submitted within 90 days
Logic: (submission_date - service_date) <= 90 days
Applies To: All claims with status != 'Denied'
```

---

## Data Quirks and Edge Cases

### Quirk: [Brief description]

**Details**: [Full explanation]

**Why It Matters**: [Impact on analysis/processing]

**Example Code**: [How we handle it]

**Example**:
```
Quirk: Retroactive status changes
Details: Claims can have their status changed retroactively, creating multiple records with same claim_id but different effective dates
Why It Matters: Need to use effective_date to get point-in-time snapshots
Example Code: df.sort_values('effective_date').groupby('claim_id').last()
```

---

## Validation Rules

Document validation rules discovered during data exploration:

### [Validation Name]

**Rule**: [What we're validating]

**Expected**: [What should be true]

**Violation Handling**: [What happens if violated]

**Example**:
```
Validation: Date Sequence
Rule: service_date <= submission_date <= processed_date
Expected: All claims follow this sequence
Violation Handling: Flag records in data quality report, exclude from time-to-process calculations
```

---

## Important Findings

Document key insights that affect how we work with the data:

### Finding: [Brief title]

**Date Discovered**: YYYY-MM-DD

**Description**: [What was found]

**Implications**: [Why it matters]

**Action Taken**: [What we did about it]

**Example**:
```
Finding: Q4 2023 Data Gap
Date Discovered: 2024-01-15
Description: No claims data between 2023-10-15 and 2023-10-22 due to system migration
Implications: Cannot calculate complete Q4 2023 metrics; time series analysis has gap
Action Taken: Added note to Q4 reports; excluded week from trend analysis
```

---

## Column Value Distributions

Document important distributions for reference:

### [Column Name]

**Unique Values**: [Count or list if categorical]

**Distribution**: [Description or table]

**Example**:
```
claim_status
Unique Values: 5 values
Distribution:
- Approved: 65%
- Pending: 20%
- Denied: 10%
- Under Review: 4%
- Appealed: 1%
```

---

## Data Relationships

Document important relationships between fields:

### Relationship: [Brief description]

**Fields**: [Which fields are related]

**Type**: [One-to-one, one-to-many, etc.]

**Notes**: [Important details]

**Example**:
```
Relationship: Patient to Claims
Fields: patient_id -> claim_id
Type: One-to-many (one patient can have multiple claims)
Notes: Average 3.5 claims per patient; max observed is 47 claims
```

---

## Data Sources

### Source: [Source Name]

**Type**: [CSV, Database, API, etc.]

**Location**: [File path or connection string]

**Update Schedule**: [When/how data is refreshed]

**Contact**: [Who to ask about this data]

**Notes**: [Important details about this source]

---

## Change Log

Keep track of significant data changes:

### YYYY-MM-DD: [Change description]

**What Changed**: [Detailed description]

**Reason**: [Why it changed]

**Impact**: [What needs to be updated]

**Example**:
```
2024-01-15: Added new status code 'Partially Approved'
What Changed: New claim_status value introduced in source system
Reason: Business requirement to track partial approvals separately
Impact: Updated status mapping in LoadData task; added to dashboard filters
```

---

## Notes

- Keep this file updated as you discover new information
- Be specific and concrete - include examples
- Document both problems AND solutions
- Link to tasks/code where relevant
- Date your findings for context
