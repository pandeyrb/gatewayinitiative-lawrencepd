# Charge Standardization Process

This document explains how raw police charge strings from Lawrence PD incident data are cleaned and standardized into consistent, analysis-ready charge names.

## Files

| File | Purpose |
|---|---|
| `clean_charges.ipynb` | Cleans the raw `Charges` column, extracts statutes, splits multi-charge rows into `charge_1 … charge_N` columns, and builds `unique_charges_reference_v3.csv` (checkpoint 13) |
| `standardize_charges.py` | Core pipeline module: 8-step normalization applied to individual charge strings |
| `standardize_charges.ipynb` | Applies the pipeline to every charge in checkpoint 13, collapses expanded columns into a single `standardized_charges` field, and saves checkpoint 14 |
| `add_misdemeanor_warrant_cols.ipynb` | Adds `is_misdemeanor` and `has_warrant` columns to checkpoint 14 and saves checkpoint 15 |

**Input:**  `data/charges/unique_charges_reference_v3.csv`
**Output:** `scripts/charges/unique_charges_standardized.csv`, `data/checkpoints/checkpoint14_standardized_charges.csv`, `data/checkpoints/checkpoint15_misdemeanor_warrant.csv`

---

## The 8-Step Pipeline

Each raw charge string passes through the following steps in order.

### Step 1 — Extract Warrant Type

Warrant prefix strings are stripped from the front of the charge and stored separately.

| Raw charge | Warrant type extracted | Remaining text |
|---|---|---|
| `warrant charges: bench warrant: trespass` | `bench_warrant` | `trespass` |
| `default warrant: license suspended, op mv with` | `default_warrant` | `license suspended, op mv with` |
| `drug, possess class a` | `none` | `drug, possess class a` |

Recognized prefixes: `bench warrant`, `standard warrant`, `default warrant`, `child in need`, `capias`.

---

### Step 2 — Strip Statute References

Massachusetts statute citations (chapter/section codes and CMR references) are removed because they are redundant with the charge name and inconsistently formatted.

| Before | After |
|---|---|
| `trespass c266 s120` | `trespass` |
| `use mv without authority c90 s24` | `use mv without authority` |
| `destruction of prop -$1200, malicious c 266` | `destruction of prop -$1200, malicious` |
| `drug, possess class a 94c s34` | `drug, possess class a` |
| `540 cmr s14.04 motor carrier safety violation` | `motor carrier safety violation` |

---

### Step 3 — Clean Text Artifacts

Trailing commas, extra whitespace, stray punctuation, and encoding artifacts (e.g. `©`, backticks, `]`) are removed and whitespace is normalized.

---

### Step 4 — Extract Offense Number

Repeat-offense suffixes are stripped from the charge and stored as a separate `offense_number` field.

| Raw (after step 3) | Offense number | Base charge |
|---|---|---|
| `oui liquor, 3rd offense` | `3rd` | `oui liquor` |
| `shoplifting by asportation, 2nd off` | `2nd` | `shoplifting by asportation` |
| `drug, possess class b, subsq. off.` | `subsequent` | `drug, possess class b` |
| `license suspended, op mv with` | `none` | `license suspended, op mv with` |

Recognized suffixes: `1st`, `2nd`, `3rd`, `4th` … `9th`, `subsq. off.`, `subs off (f)`, `subsq`.

---

### Step 5 — Canonical Alias Normalization

A curated lookup table maps truncated, misspelled, or variant forms to a single canonical charge name. These variants arose from database field-length limits and inconsistent data entry.

**Examples:**

| Original (raw entry) | Canonical (standardized) |
|---|---|
| `a&b on family / household member / intimate partne` | `a&b on family / household member` |
| `a&b on family / household` | `a&b on family / household member` |
| `a&b on ambulance` | `a&b on ambulance personnel` |
| `strangulation or` | `strangulation or suffocation` |
| `strangulation or suffocation, serious bodily injur` | `strangulation or suffocation, serious bodily injury` |
| `negligent operation of motor` | `negligent operation of motor vehicle` |
| `negligent operation of` | `negligent operation of motor vehicle` |
| `fugitive from justice on court` | `fugitive from justice on court warrant` |
| `fugitive from justice on court warrant c` | `fugitive from justice on court warrant` |
| `cocaine, trafficking in - over` | `cocaine, trafficking in - over 14 grams` |
| `any person trafficks fentanyl more` | `any person trafficks fentanyl more than 10 grams` |
| `trafficking class a: 28+` | `trafficking class a: 28+ grams` |
| `larceny over $250 by false` | `larceny over $250 by false pretense` |
| `larceny by check over $1200 & s30(1)` | `larceny by check over $1200` |
| `shoplifting by concealing` | `shoplifting by concealing mdse` |
| `credit card fraud < $1200 by merchant` | `credit card fraud under $1200` |
| `credit card fraud > $1200 by merchant` | `credit card fraud over $1200` |
| `destruction of prop +$1200, malicious c` | `destruction of prop +$1200, malicious` |
| `wit/juror/pol/court official` | `wit/juror/pol/court official, intimidate` |
| `tampering with evidence for use in an official pro` | `tampering with evidence` |
| `criminal harrassment (m)` | `criminal harassment` |
| `miscellaneous munic ordinance/bylaw viol` | `miscellaneous municipal ordinance/bylaw violation` |
| `ordinance violation` | `municipal by-law or ordinance violation` |
| `sex offender fail to` | `sex offender fail to register` |
| `abuse prevention order` | `abuse prevention order, violate` |
| `harassment prevention` | `harassment prevention order, violate` |
| `persons previously convicted of 1 violent crimes o` | `persons previously convicted of 1 violent crime` |
| `firearm, carry without` | `firearm, carry without license` |
| `unlawful carring of firearms` | `unlawful carrying of firearms` |
| `unlawful improper storage firearm` | `unlawful improper storage of firearm` |
| `in control of a large capacity weapon or large cap` | `in control of large capacity weapon` |
| `license suspended, op mv` | `license suspended, op mv with` |
| `registration suspended, op mv` | `registration suspended, op mv with` |
| `electronic device, use while operating` | `electronic device, use while operating mv` |
| `use of mobile telephone or device uner 18` | `use of mobile telephone or device under 18` |
| `dna database sample,refuse` | `dna database sample, refuse provide` |

---

### Step 6 — Categorize

Each canonical charge is assigned to one of the following categories using keyword matching:

| Category | Example charges |
|---|---|
| Assault/Battery | `a&b on family / household member`, `strangulation or suffocation` |
| Drug Offense | `drug, possess class a`, `cocaine, trafficking in - over 14 grams` |
| Firearm Offense | `firearm, carry without license`, `carrying a loaded firearm` |
| Motor Vehicle | `license suspended, op mv with`, `oui liquor`, `negligent operation of motor vehicle` |
| Theft/Larceny | `larceny over $1200 by single scheme`, `shoplifting by concealing mdse` |
| Fraud/Financial | `credit card fraud over $1200`, `identity fraud` |
| Robbery | `robbery`, `carjacking` |
| Violent Crime - Homicide | `murder`, `manslaughter` |
| Violent Crime - Kidnapping | `kidnapping` |
| Violent Crime - Repeat Offender | `persons previously convicted of 1 violent crime` |
| Breaking & Entering | `b&e nighttime for felony`, `home invasion` |
| Property Destruction | `destruction of prop -$1200, malicious`, `deface property` |
| Sex Offense | `rape`, `indecent a&b`, `sex offender fail to register` |
| Arson | `arson`, `burn motor vehicle` |
| Weapons | `dangerous weapon, carry`, `body armor, use in felony` |
| Protective Order Violation | `abuse prevention order, violate`, `harassment prevention order, violate` |
| Obstruction of Justice | `resisting arrest`, `tampering with evidence`, `witness, intimidate` |
| Fugitive/Warrant | `fugitive from justice on court warrant` |
| Conspiracy | `conspiracy to violate drug law` |
| Public Order | `disorderly conduct`, `trespass`, `criminal harassment` |
| Attempt | `attempt to commit crime` |
| Miscellaneous | anything not matched above |

---

### Step 7 — Classify as Felony / Misdemeanor / Either

Each charge is classified under Massachusetts law. Charges that escalate with repeat offenses are upgraded from `Misdemeanor` to `Either` when an offense number suffix (2nd, 3rd, subsequent, etc.) was extracted in step 4.

| Classification | Meaning |
|---|---|
| `Felony` | Always a felony under MA law |
| `Misdemeanor` | Always a misdemeanor under MA law |
| `Either` | Can be either depending on circumstances (amount, prior record, etc.) |

**Examples:**

| Canonical charge | Classification |
|---|---|
| `murder` | Felony |
| `trafficking class a: 28+ grams` | Felony |
| `a&b with dangerous weapon` | Felony |
| `larceny over $1200 by single scheme` | Felony |
| `identity fraud` | Felony |
| `oui liquor` (3rd offense or higher) | Felony |
| `trespass` | Misdemeanor |
| `disorderly conduct` | Misdemeanor |
| `drug, possess class a` | Misdemeanor |
| `shoplifting by concealing mdse` | Misdemeanor |
| `oui liquor` (1st or 2nd offense) | Misdemeanor |
| `firearm, carry without license` | Either |
| `fugitive from justice on court warrant` | Either |
| `criminal harassment` | Either |
| `conspiracy to violate drug law` | Either |

---

### Step 8 — Aggregate

Rows that share the same `base_charge` (after steps 1–5) are merged, summing their `count` values. When variants differ in category or charge class, the classification from the highest-count variant is used.

---

## End-to-End Examples

These examples show the full transformation from the raw database entry to the final standardized charge:

| Raw entry from database | Standardized charge | Category | Classification |
|---|---|---|---|
| `A&B ON FAMILY / HOUSEHOLD MEMBER / INTIMATE PARTNE` | `a&b on family / household member` | Assault/Battery | Misdemeanor |
| `STRANGULATION OR SUFFOCATION` | `strangulation or suffocation` | Assault/Battery | Felony |
| `USE MV WITHOUT AUTHORITY c90 S24` | `use mv without authority` | Motor Vehicle | Misdemeanor |
| `LARCENY UNDER $250 c266 S30` | `larceny under $250` | Theft/Larceny | Misdemeanor |
| `WITNESS, INTIMIDATE c268 S13B` | `witness, intimidate` | Obstruction of Justice | Felony |
| `FALSE NAME/SS# TO LAW ENFORCEMENT` | `false name/ss# to law enforcement` | Fraud/Financial | Misdemeanor |
| `THREAT TO COMMIT CRIME c275 S2` | `threat to commit crime` | Public Order | Either |
| `ASSAULT W/DANGEROUS WEAPON` | `assault w/dangerous weapon` | Assault/Battery | Felony |
| `KIDNAPPING` | `kidnapping` | Violent Crime - Kidnapping | Felony |
| `IDENTITY FRAUD` | `identity fraud` | Fraud/Financial | Felony |
| `warrant charges: bench warrant: trespass` | `trespass` | Public Order | Misdemeanor |
| `default warrant: license suspended, op mv with` | `license suspended, op mv with` | Motor Vehicle | Misdemeanor |
| `DRUG, POSSESS CLASS A c94C s34` | `drug, possess class a` | Drug Offense | Misdemeanor |
| `cocaine, trafficking in - over c94c s32e(b)` | `cocaine, trafficking in - over 14 grams` | Drug Offense | Felony |
| `DESTRUCTION OF PROP -$1200, MALICIOUS c 266` | `destruction of prop -$1200, malicious` | Property Destruction | Misdemeanor |
| `OUI LIQUOR, 3rd offense` | `oui liquor` (offense: 3rd) | Motor Vehicle | Felony |
| `SHOPLIFTING BY ASPORTATION, 2nd off` | `shoplifting by asportation` (offense: 2nd) | Theft/Larceny | Either |
