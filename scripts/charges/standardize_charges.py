"""
Standardize police charge entries from unique_charges_reference_v3.csv.

Pipeline:
  1. Extract warrant type prefix
  2. Strip statute references
  3. Clean text artifacts
  4. Extract offense number (subsequent, 2nd, 3rd, etc.)
  5. Normalize to canonical charge name (curated alias table)
  6. Categorize
  7. Classify as Felony / Misdemeanor / Either
  8. Aggregate rows with same base_charge, summing counts

Input:  data/charges/unique_charges_reference_v3.csv
Output: scripts/unique_charges_standardized.csv
"""

import csv
import re
import os
from collections import defaultdict

INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "charges", "unique_charges_reference_v3.csv")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "unique_charges_standardized.csv")

# ---------------------------------------------------------------------------
# Step 1: Warrant prefix extraction
# ---------------------------------------------------------------------------
# Order matters: longest/most specific prefixes first
WARRANT_PREFIXES = [
    ("warrant charges: default warrant:", "default_warrant"),
    ("warrant charges: standard warrant:", "standard_warrant"),
    ("warrant charges: bench warrant:", "bench_warrant"),
    ("warrant charges: child in need:", "child_in_need"),
    ("warrant charges: capias:", "capias"),
    ("default warrant:", "default_warrant"),
    ("standard warrant:", "standard_warrant"),
    ("bench warrant:", "bench_warrant"),
    ("child in need:", "child_in_need"),
]


def extract_warrant_type(charge):
    """Extract warrant type prefix and return (warrant_type, remaining_charge)."""
    charge_lower = charge.strip().lower()
    for prefix, wtype in WARRANT_PREFIXES:
        if charge_lower.startswith(prefix):
            remaining = charge_lower[len(prefix):].strip()
            return wtype, remaining
    return "none", charge_lower


# ---------------------------------------------------------------------------
# Step 2: Strip statute references
# ---------------------------------------------------------------------------
STATUTE_PATTERNS = [
    r'\b\d{3}\s*cmr\s*s?\s*[\d.]+\b',
    r'\bc\d+[a-z]?\s+s[\$i][a-z0-9]+\b',
    r'\s+c\d+[a-z]?\b(?!\s*s)',
    r'\s+\d{3}\b$',
    r'\(civ(?:il|l)?\)',
    r'\]\s*\(a\)',
    r'©',
    r'\s*\]',
    r'`$',
    r'\s+90\s*$',
]


def strip_statute_refs(charge):
    """Remove statute/CMR references from charge text."""
    for pattern in STATUTE_PATTERNS:
        charge = re.sub(pattern, '', charge)
    return charge.strip()


# ---------------------------------------------------------------------------
# Step 3: Clean up
# ---------------------------------------------------------------------------
def clean_charge(charge):
    """Normalize abbreviations and clean trailing artifacts."""
    charge = charge.rstrip(', ')
    charge = re.sub(r'\s+', ' ', charge).strip()
    return charge


# ---------------------------------------------------------------------------
# Step 4: Extract offense number
# ---------------------------------------------------------------------------
# Patterns ordered longest-first. Each tuple: (regex, offense_label).
# The regex should match from the point where the suffix starts to end of string.
OFFENSE_PATTERNS = [
    (r',?\s*subsq\.?\s*off\.?$', "subsequent"),
    (r',?\s*subs\s+off\s*\(f\)$', "subsequent"),
    (r',?\s*subsq\.?$', "subsequent"),
    (r',?\s*9th\s+offense$', "9th"),
    (r',?\s*8th\s+offense$', "8th"),
    (r',?\s*7th\s+offense$', "7th"),
    (r',?\s*6th\s+offense$', "6th"),
    (r',?\s*5th\s+offense$', "5th"),
    (r',?\s*4th\s+off(?:ense)?\.?$', "4th"),
    (r',?\s*3rd\s+off(?:ense)?\.?$', "3rd"),
    (r',?\s*2nd\s+off(?:ense)?\.?$', "2nd"),
    (r',?\s*(?:1st|ist)\s+of(?:f(?:ense)?\.?)?$', "1st"),
]


def extract_offense_number(charge):
    """Extract offense number suffix. Returns (offense_number, cleaned_charge)."""
    for pattern, label in OFFENSE_PATTERNS:
        m = re.search(pattern, charge, re.IGNORECASE)
        if m:
            cleaned = charge[:m.start()].strip().rstrip(',').strip()
            return label, cleaned
    return "none", charge


# ---------------------------------------------------------------------------
# Step 5: Canonical alias table
# ---------------------------------------------------------------------------
# Maps a base_charge (after steps 1-4) to its canonical form.
# Built by reviewing all 546 unique base_charges for truncations, typos,
# trailing artifacts, and semantic duplicates.
CANONICAL_ALIASES = {
    # --- A&B variants ---
    "a&b on family / household": "a&b on family / household member",
    "a&b on family / household member /": "a&b on family / household member",
    "a&b on family / household member / intimate": "a&b on family / household member",
    "a&b on family / household member / intimate partne": "a&b on family / household member",
    "a&b on ambulance": "a&b on ambulance personnel",
    "a&b with dangerous weapon 265 si5a": "a&b with dangerous weapon",
    "a&b in the presence of a po": "a&b in the presence of a police officer",
    "a&b to intimidate for": "a&b to intimidate",
    "assault on family /": "assault on family / household member",
    "assault on family / household member /": "assault on family / household member",
    "assault on ambulance": "assault on ambulance personnel",
    "assault w/dangerous": "assault w/dangerous weapon",
    "assault by means": "assault by means of dangerous weapon",

    # --- Drug variants ---
    "any person trafficks fentanyl more": "any person trafficks fentanyl more than 10 grams",
    "any person trafficks fentanyl more than": "any person trafficks fentanyl more than 10 grams",
    "cocaine, trafficking in -": "cocaine, trafficking in - over 14 grams",
    "cocaine, trafficking in - over": "cocaine, trafficking in - over 14 grams",
    "drug, distribute class d (effective": "drug, distribute class d",
    "drug, distribute class d (effective 1/5/8": "drug, distribute class d",
    "drug, possess to distrib": "drug, possess to distrib class unknown",
    "drug, possess to distrib class": "drug, possess to distrib class unknown",
    "drug, pos to distrib class b": "drug, possess to distrib class b",
    "drug, poss to dist class d": "drug, possess to distrib class d",
    "drug violation near": "drug violation near school/park",
    "heroin, being present where": "heroin, being present where kept",
    "heroin/morphine/opium": "heroin/morphine/opium, trafficking in",

    # --- Trafficking class truncations ---
    "trafficking class a: 100+": "trafficking class a: 100+ grams",
    "trafficking class a: 200+": "trafficking class a: 200+ grams",
    "trafficking class a: 28+": "trafficking class a: 28+ grams",
    "trafficking class b: 100+": "trafficking class b: 100+ grams",
    "trafficking class b: 200+": "trafficking class b: 200+ grams",
    "trafficking class b: 28+": "trafficking class b: 28+ grams",
    "trafficking in": "trafficking in (unspecified)",

    # --- Firearm variants ---
    "carrying a loaded firearm weapon": "carrying a loaded firearm",
    "firearm, carry without": "firearm, carry without license",
    "firearm, discharge within": "firearm, discharge within 500 ft of bldg",
    "firearm within 500 ft of": "firearm within 500 ft of dwelling",
    "firearm within 500 ft of dwelling (civl)": "firearm within 500 ft of dwelling",
    "firearm without fid card, possess c": "firearm without fid card, possess",
    "in control of a large capacity weapon or": "in control of large capacity weapon",
    "in control of a large capacity weapon or large cap": "in control of large capacity weapon",
    "unlawful carring of firearms": "unlawful carrying of firearms",
    "unlawful improper storage": "unlawful improper storage of firearm",
    "unlawful improper storage firearm": "unlawful improper storage of firearm",
    "unl possession ammo no fid": "unlawful possession ammo no fid",

    # --- Motor vehicle variants ---
    "license suspended, op mv": "license suspended, op mv with",
    "license revoked as hto": "license revoked as hto, operate mv with",
    "license, false application": "license, false application for mv",
    "license, false application for": "license, false application for mv",
    "license, false statement in applic for": "license, false statement in application for mv",
    "negligent operation of": "negligent operation of motor vehicle",
    "negligent operation of motor": "negligent operation of motor vehicle",
    "reckless operation of": "reckless operation of motor vehicle",
    "reckless operation of motor": "reckless operation of motor vehicle",
    "motor veh, malicious": "motor veh, malicious damage to",
    "motor veh, malicious damage": "motor veh, malicious damage to",
    "motor veh, malicious damage to c": "motor veh, malicious damage to",
    "motor veh, receive stolen c": "motor veh, receive stolen",
    "motor veh, taking &": "motor veh, taking & stealing parts",
    "registration suspended, op": "registration suspended, op mv with",
    "registration suspended, op mv": "registration suspended, op mv with",
    "registration sticker not": "registration sticker not displayed",
    "leave scene of property": "leave scene of property damage",
    "leave scene of personal injury & death": "leave scene of personal injury causing death",
    "oui liquor & serious injury &": "oui liquor & serious injury & reckless",
    "alcohol from open container": "alcohol from open container in mv",
    "alcohol from open container in mv": "alcohol from open container in mv, drink",
    "electronic device, use": "electronic device, use while operating mv",
    "electronic device, use while": "electronic device, use while operating mv",
    "electronic device, use while operating": "electronic device, use while operating mv",
    "electronic device, use while operating, mv": "electronic device, use while operating mv",
    "speeding in violation special": "speeding in violation special regulation",
    "operation of motor vehicle": "improper operation of mv",
    "operation of motor vehicle, improper": "improper operation of mv",
    "motor carrier safety violation 540 cmr": "motor carrier safety violation",
    "unlicensed operation of mv 90": "unlicensed operation of mv",
    "use of mobile telephone or device uner 18": "use of mobile telephone or device under 18",
    "lights violation": "lights violation, mv",
    "identify self, mv operator": "identify self, mv operator refuse",

    # --- Fugitive variants ---
    "fugitive from justice on": "fugitive from justice on court warrant",
    "fugitive from justice on court": "fugitive from justice on court warrant",
    "fugitive from justice on court warrant c": "fugitive from justice on court warrant",

    # --- Larceny / theft variants ---
    "larceny by check over $1200 &": "larceny by check over $1200",
    "larceny by check over $1200 & s30": "larceny by check over $1200",
    "larceny by check over $1200 & s30(1)": "larceny by check over $1200",
    "larceny by check under $1200 &": "larceny by check under $1200",
    "larceny by check under $1200 & s30": "larceny by check under $1200",
    "larceny by check under $1200 & s30(1)": "larceny by check under $1200",
    "larceny over $1200 by single": "larceny over $1200 by single scheme",
    "larceny over $250 by false": "larceny over $250 by false pretense",
    "larceny under $1200 by": "larceny under $1200 by single scheme",
    "larceny under $250 by false": "larceny under $250 by false pretense",
    "larceny from building stealing": "larceny from building",
    "shoplifting by concealing": "shoplifting by concealing mdse",
    "shoplifting by asportation, 2nd": "shoplifting by asportation",
    "shoplifting $250+ by": "shoplifting $250+ by asportation",
    "shoplifting of shopping": "shoplifting of shopping cart",
    "receive stolen property -": "receive stolen property -$1200",
    "receive stolen property +$1200, subsq": "receive stolen property +$1200",
    "receive stolen prop -$1200, subsq. off": "receive stolen prop -$1200",

    # --- Credit card variants ---
    "credit card fraud < $1200 by merchant )": "credit card fraud under $1200",
    "credit card fraud < $1200 by merchant": "credit card fraud under $1200",
    "credit card fraud > $1200 by merchant": "credit card fraud over $1200",
    "credit card fraud under": "credit card fraud under $1200",
    "credit card, receive lost": "credit card, receive stolen",
    "credit card, false statemnt to": "credit card, false statement",
    "credit card, improper use": "credit card, improper use under $1200",

    # --- Property destruction variants ---
    "destruction of prop +$1200, malicious c": "destruction of prop +$1200, malicious",
    "destruction of prop +$1200, wanton c": "destruction of prop +$1200, wanton",
    "destruction of prop -$1200, malicious c": "destruction of prop -$1200, malicious",
    "destruction of prop -$1200, wanton c": "destruction of prop -$1200, wanton",
    "defacement malicious": "defacement malicious wanton property",
    "defacement malicious wanton": "defacement malicious wanton property",
    "deface property (tagging)": "deface property",

    # --- Obstruction / justice variants ---
    "resisting arrest c": "resisting arrest",
    "wit/juror/pol/court": "wit/juror/pol/court official, intimidate",
    "wit/juror/pol/court official": "wit/juror/pol/court official, intimidate",
    "wit/juror/pol/crt official": "wit/juror/pol/crt official, intimidate",
    "tampering with evidence for use in an official pro": "tampering with evidence",
    "strangulation or": "strangulation or suffocation",
    "strangulation or suffocation, serious bodily injur": "strangulation or suffocation, serious bodily injury",
    "false statement under": "false statement under penalty of perjury",
    "false id info, arrst furni to": "false id info, arrst furni to law enf",
    "dna database sample,refuse": "dna database sample, refuse provide",
    "dna database sample,refuse provide": "dna database sample, refuse provide",
    "witness fail to appear in": "witness fail to appear",

    # --- Public order variants ---
    "disorderly conduct c": "disorderly conduct",
    "disturbing the peace c": "disturbing the peace",
    "trespass c": "trespass",
    "criminal harrassment (m)": "criminal harassment",
    "criminal harrassment (m) subs off (f)": "criminal harassment",
    "noisy and disorderly house": "noisy and disorderly house, keep",
    "reckless endangerment to": "reckless endangerment to children",
    "miscellaneous munic": "miscellaneous municipal ordinance/bylaw violation",
    "miscellaneous munic ordinance/bylaw": "miscellaneous municipal ordinance/bylaw violation",
    "miscellaneous munic ordinance/bylaw viol": "miscellaneous municipal ordinance/bylaw violation",
    "municipal by-law or": "municipal by-law or ordinance violation",
    "municipal by-law or ordinance viol": "municipal by-law or ordinance violation",
    "ordinance violation": "municipal by-law or ordinance violation",
    "ordinance/bylaw viol": "municipal by-law or ordinance violation",
    "railroad track, walk/ride": "railroad track, walk/ride on",

    # --- Sex offense variants ---
    "sex offender fail to": "sex offender fail to register",

    # --- B&E / burglary variants ---
    "burglarious instrument": "burglarious instrument, possess",

    # --- Persons previously convicted truncations ---
    "persons previously convicted of 1 violent": "persons previously convicted of 1 violent crime",
    "persons previously convicted of 1 violent crimes o": "persons previously convicted of 1 violent crime",
    "persons previously convicted of 2 violent crimes o": "persons previously convicted of 2 violent crimes",
    "persons previously convicted of 3 violent crimes o": "persons previously convicted of 3 violent crimes",

    # --- Protective order variants ---
    "abuse prevention order": "abuse prevention order, violate",
    "harassment prevention": "harassment prevention order, violate",

    # --- Parole/probation ---
    "parole/pardon": "parole/pardon, fail file",

    # --- Truncated license/register (from offense number extraction) ---
    "license": "license suspended, op mv with",
    "register": "registration suspended, op mv with",
    "operation of motor vehicle, improper": "improper operation of mv",
    "motor veh vin, remove/alter": "motor veh vin, remove/alter",

    # --- Miscellaneous truncations ---
    "window": "window obstructed/nontransparent",
    "violation": "violation (unspecified)",
    "dog, crop ear of": "animal, cruelty to",
    "dog/cat, motorist fail report injury to": "animal, fail report injury to",
    "notes, possess worthless/false": "notes, possess worthless",
    "conspiracy to violate drug": "conspiracy to violate drug law",

    # --- Warrant prefix not fully stripped ---
    "warrant charges: child in need: escape from dys": "escape from dys",
    "warrant charges: child in need: registration suspended, op mv": "registration suspended, op mv with",

    # --- Body armor fix (use in felony = felony-level) ---
    "body armor, use in felony": "body armor, use in felony",
}


def normalize_charge(charge):
    """Apply canonical alias table. Returns the canonical form."""
    return CANONICAL_ALIASES.get(charge, charge)


# ---------------------------------------------------------------------------
# Step 6: Category mapping
# ---------------------------------------------------------------------------
CATEGORY_RULES = [
    # Drug offenses (before general "possess" checks)
    (["drug,", "drug ", "heroin", "cocaine", "fentanyl", "trafficking class",
      "trafficking in", "marihuana", "methamphetamine",
      "drug violation", "drug paraphernalia", "counterfeit drug",
      "conspiracy to violate drug", "2012 traff over"],
     "Drug Offense"),

    # Firearm offenses
    (["firearm", "ammo", "ammunition", "loaded firearm", "fid card",
      "large capacity weapon", "large cap", "feeding device",
      "silencer", "shotgun", "machine gun", "unlawful carrying of firearms",
      "unlawful carring of firearms", "firearms, trafficking",
      "unlawful improper storage", "unlawful possession ammo"],
     "Firearm Offense"),

    # Motor vehicle (before assault since some have "mv")
    (["unlicensed operation", "license suspended", "license revoked",
      "registration suspended", "registration revoked",
      "unregistered motor", "uninsured mv", "oui ",
      "reckless operation", "negligent operation", "operating to endanger",
      "motor veh", "marked lanes", "speeding", "stop/yield",
      "stop for police", "leave scene", "attaching wrong",
      "number plate", "inspection/sticker", "defective equipment",
      "window obstructed", "lights violation", "signal, fail",
      "one way street", "right lane", "left lane",
      "turn, improper", "passing violation", "crosswalk",
      "license not in possession", "license class",
      "license restriction", "license, false",
      "license, exhibit", "license/regis",
      "identify self, mv", "identify self, refuse",
      "rmv document", "rmv signature", "rmv id card",
      "registration not in", "registration sticker",
      "equipment violation", "moped", "motorcycle equipment",
      "impeded operation", "improper operation of mv",
      "electronic device, use",
      "use mv without", "abandon mv", "hang onto mv",
      "alcohol from open container",
      "snow/rec veh", "child under 6 without carseat",
      "child 6-12 without seat belt", "seat belt",
      "school bus", "headlights", "brakes violation",
      "horn violation", "red/blue light", "height, operate mv",
      "state hway", "unsafe operation of mv",
      "motor carrier",
      "failure to display lic", "failure to obey traffic",
      "keep right for oncoming", "m/v homicide",
      "trespass with motor vehicle",
      "breakdown lane", "safety standards, mv",
      "yield at intersection",
      "use of mobile telephone"],
     "Motor Vehicle"),

    # Robbery (before assault)
    (["robbery", "carjacking", "assault to rob"],
     "Robbery"),

    # Murder/homicide (before assault)
    (["murder", "manslaughter", "homicide"],
     "Violent Crime - Homicide"),

    # Kidnapping
    (["kidnapping", "kidnap"],
     "Violent Crime - Kidnapping"),

    # Assault & battery
    (["a&b", "assault", "strangulation", "suffocation", "mayhem"],
     "Assault/Battery"),

    # Sex offenses
    (["sexual conduct", "prostitut", "solicit for",
      "lewdness", "indecent", "rape", "obscene matter",
      "sex offender", "lewd, wanton"],
     "Sex Offense"),

    # Arson
    (["arson", "burn motor", "burn personalty"],
     "Arson"),

    # Breaking & entering / burglary
    (["b&e", "home invasion", "burglary", "burglarious",
      "enter dwelling at night", "break into depository",
      "truck, b&e"],
     "Breaking & Entering"),

    # Property crimes - theft/larceny/shoplifting
    (["larceny", "shoplifting", "receive stolen prop",
      "receive stolen property", "receive false-traded",
      "thief, common", "motor veh, taking & stealing",
      "tools, larceny"],
     "Theft/Larceny"),

    # Property crimes - destruction/vandalism
    (["destruction of prop", "defacement", "deface property",
      "trespass notice, vandalize", "building, vandalize"],
     "Property Destruction"),

    # Fraud & financial crimes
    (["credit card", "check, utter", "check, forgery",
      "identity fraud", "false id info", "forgery of document",
      "utter false", "counterfeit note", "false pretense",
      "false name/ss#", "insurance claim, false",
      "innkeeper, defraud", "restaurant, defraud",
      "trade secret", "notes, possess worthless",
      "note, forgery of bank", "credit card, false"],
     "Fraud/Financial"),

    # Weapons (non-firearm)
    (["dangerous weapon", "knife over", "body armor"],
     "Weapons"),

    # Protective orders
    (["abuse prevention order", "harassment prevention order"],
     "Protective Order Violation"),

    # Obstruction / interference with justice
    (["wit/juror", "witness,", "witness fail", "juror,",
      "juror fail", "police officer, interfere",
      "police officer, impersonate", "disguise to obstruct",
      "accessory after", "accessory before", "tampering with evidence",
      "resist arrest", "resisting arrest",
      "crime report, false", "false statement",
      "penalty of perjury", "contempt",
      "dna database", "recognizance, fail",
      "probation supervision", "parole/pardon",
      "prisoner, deliver", "correctional institution",
      "escape from", "firefighter, interfere",
      "emergency vehicle", "police horse",
      "extortion"],
     "Obstruction of Justice"),

    # Fugitive
    (["fugitive from justice", "fugitive, fail bring"],
     "Fugitive/Warrant"),

    # Conspiracy (general, not drug-specific)
    (["conspiracy"],
     "Conspiracy"),

    # Public order / nuisance
    (["disorderly conduct", "trespass", "disturbing the peace",
      "drinking in public", "threat to commit crime",
      "noisy and disorderly", "miscellaneous muni",
      "municipal by-law", "ordinance", "intimidate",
      "criminal harassment", "stalking",
      "reckless endangerment", "affray",
      "liquor, person under 21", "liquor to person under 21",
      "park regulation", "school, disturb",
      "fire call box", "fireworks",
      "trash, litter", "dumpster",
      "hunt/fish", "marine fish", "fish propagation",
      "dog", "animal", "taxi fare",
      "tramp", "nightwalker", "accost/annoy",
      "telephone", "bomb threat",
      "contribute to delinquency",
      "railroad track", "miscellaneous statutory",
      "hypodermic", "threat /dangerous"],
     "Public Order"),

    # Attempt to commit crime (generic)
    (["attempt to commit crime"],
     "Attempt"),

    # Violent crime - repeat offender
    (["persons previously convicted"],
     "Violent Crime - Repeat Offender"),

    # Remaining motor vehicle (truncated license entries)
    (["license,", "register, subsq"],
     "Motor Vehicle"),

    # Catch-all drug
    (["person traffick"],
     "Drug Offense"),

    # Violation (unspecified)
    (["violation (unspecified)"],
     "Miscellaneous"),
]


def categorize_charge(base_charge):
    """Assign a category to a base charge using keyword matching."""
    charge = base_charge.lower()
    for keywords, category in CATEGORY_RULES:
        for kw in keywords:
            if kw in charge:
                return category
    return "Miscellaneous"


# ---------------------------------------------------------------------------
# Step 7: Felony / Misdemeanor classification
# ---------------------------------------------------------------------------
CHARGE_CLASS_RULES = [
    # ---- ALWAYS FELONY ----

    # Drug trafficking (all classes, all weights)
    (["trafficking class", "trafficks fentanyl", "trafficking in",
      "2012 traff over"], "Felony"),
    # Drug distribution / possess-to-distribute class A/B/C
    (["drug, distribute class a", "drug, distribute class b",
      "drug, distribute class c",
      "drug, possess to distrib class a", "drug, possess to distrib class b",
      "drug, possess to distrib class c",
      "cocaine, distribute", "cocaine, possess to distribute",
      "heroin/morphine/opium, trafficking"], "Felony"),
    # Drug violation near school/park (enhancement)
    (["drug violation near school", "drug violation near",
      "drug violation 100'"], "Felony"),

    # Firearms - serious
    (["carrying a loaded firearm", "firearm use in felony",
      "large capacity weapon", "large cap",
      "feeding device, possess large",
      "firearms, trafficking", "machine gun", "silencer",
      "shotgun, possess sawed", "unlawful carrying of firearms",
      "unlawful carring of firearms",
      "firearm, larceny of",
      "in control of large capacity"], "Felony"),

    # Motor vehicle - felony level
    (["m/v homicide", "motor veh, larceny of"], "Felony"),
    # OUI 3rd+ offense
    (["oui liquor, 3rd", "oui liquor, 4th", "oui liquor, 5th",
      "oui liquor, 6th", "oui liquor, 7th", "oui liquor, 8th",
      "oui liquor, 9th",
      "oui liquor or .08%, 3rd", "oui liquor or .08%, 4th",
      "oui liquor or .08%, 5th", "oui liquor or .08%, 9th",
      "oui drugs, 3rd", "oui drugs, 4th", "oui drugs, 5th"], "Felony"),

    # Robbery (all forms)
    (["robbery", "carjacking", "assault to rob"], "Felony"),

    # Murder / manslaughter / homicide
    (["murder", "manslaughter", "homicide"], "Felony"),

    # Kidnapping
    (["kidnapping", "kidnap"], "Felony"),

    # Assault - felony level
    (["a&b with dangerous weapon", "assault w/dangerous weapon",
      "a&b on police officer", "a&b on +60/disabled",
      "a&b on child with substantial", "a&b : serious bodily",
      "a&b on ambulance", "a&b on correction officer",
      "a&b on public employee",
      "assault to murder", "assault to commit felony",
      "strangulation", "suffocation", "mayhem",
      "assault by means", "assault in dwelling, armed",
      "a&b : on a child", "a&b : pregnant"], "Felony"),

    # Sex offenses - felony level
    (["rape", "indecent a&b", "obscene matter to minor"], "Felony"),

    # Arson
    (["arson", "burn motor", "burn personalty"], "Felony"),

    # B&E / burglary - felony level
    (["b&e nighttime for felony", "b&e daytime for felony",
      "home invasion", "burglary", "enter dwelling at night",
      "break into depository", "truck, b&e for felony"], "Felony"),

    # Larceny / theft - felony level (over $1200)
    (["larceny over $1200", "larceny over $250 by false",
      "larceny by check over $1200",
      "receive stolen property +$1200", "receive stolen prop +$1200",
      "receive false-traded property +$1200",
      "shoplifting $250+ by"], "Felony"),

    # Property destruction - felony level (over $1200)
    (["destruction of prop +$1200"], "Felony"),

    # Fraud - felony level
    (["identity fraud", "check, utter false", "check, forgery",
      "forgery of document", "credit card fraud over $1200",
      "credit card, forge or utter",
      "credit card, improper use over $1200"], "Felony"),

    # Obstruction - felony level
    (["wit/juror/pol/court official, intimidate",
      "wit/juror/pol/crt official",
      "witness, retaliate", "witness, intimidate",
      "juror, intimidate",
      "accessory after", "accessory before",
      "tampering with evidence"], "Felony"),

    # Stalking
    (["stalking"], "Felony"),

    # Bomb threat
    (["bomb threat"], "Felony"),

    # Persons previously convicted
    (["persons previously convicted"], "Felony"),

    # Property damage to intimidate
    (["property damage to intimidate"], "Felony"),

    # Counterfeit notes (with intent)
    (["counterfeit note"], "Felony"),

    # Body armor in felony
    (["body armor, use in felony"], "Felony"),

    # Dangerous weapon on school grounds
    (["dangerous weapon on school"], "Felony"),

    # Trade secret
    (["trade secret"], "Felony"),

    # Utter false instrument
    (["utter false instrument"], "Felony"),

    # Motor vehicle in felony
    (["motor veh in felony"], "Felony"),

    # Drug possess to distrib (unspecified class - conservative)
    (["drug, possess to distrib class unknown"], "Felony"),
    (["drug, possess to distrib"], "Felony"),
    (["drug violation"], "Felony"),
    (["drug, larceny"], "Felony"),
    (["drug, obtain by fraud"], "Felony"),

    # Criminal harassment subsequent = felony
    (["criminal harassment"], "Either"),

    # ---- EITHER (can be felony or misdemeanor) ----

    # Firearm carry/possess without license
    (["firearm, carry without", "firearm without fid card",
      "firearm w/defaced no."], "Either"),

    # Drug - conspiracy (depends on underlying)
    (["conspiracy to violate drug"], "Either"),

    # Motor vehicle - receive stolen (depends on value)
    (["motor veh, receive stolen"], "Either"),
    # Motor vehicle - malicious damage (depends on value)
    (["motor veh, malicious damage"], "Either"),

    # Larceny from building/person (depends on value)
    (["larceny from building", "larceny from person"], "Either"),

    # Defacement (depends on damage)
    (["defacement"], "Either"),

    # Dangerous weapon carry
    (["dangerous weapon, carry"], "Either"),

    # Conspiracy (general)
    (["conspiracy"], "Either"),

    # Fugitive (depends on underlying)
    (["fugitive from justice", "fugitive, fail bring"], "Either"),

    # Attempt (depends on underlying)
    (["attempt to commit crime"], "Either"),

    # Threat to commit crime
    (["threat to commit crime"], "Either"),

    # Leave scene of personal injury
    (["leave scene of personal injury"], "Either"),

    # Reckless endangerment
    (["reckless endangerment"], "Either"),

    # Abuse prevention order violate
    (["abuse prevention order, violate"], "Either"),

    # Receive stolen property (unspecified amount)
    (["receive stolen property"], "Either"),

    # Shoplifting (depends on amount and priors) - 2nd/3rd
    (["shoplifting by asportation", "shoplifting by concealing mdse"], "Misdemeanor"),

    # Sexual conduct for fee (misdemeanor unless minor involved)
    (["sexual conduct for fee"], "Misdemeanor"),

    # ---- MISDEMEANOR ----

    # Drug possession (simple, all classes)
    (["drug, possess class", "heroin, possess", "marihuana, possess",
      "heroin, being present where kept",
      "drug paraphernalia", "counterfeit drug"], "Misdemeanor"),
    # Drug distribute class D/E (lower classes)
    (["drug, distribute class d", "drug, distribute class e",
      "drug, possess to distrib class d", "drug, possess to distrib class e",
      "counterfeit drug, distribute"], "Misdemeanor"),

    # Firearm - misdemeanor level
    (["ammo", "ammunition", "unlawful improper storage",
      "unlawful possession ammo",
      "firearm serial no., deface",
      "firearm, discharge within", "firearm in vehicle, leave",
      "firearm within 500 ft"], "Misdemeanor"),

    # Motor vehicle - all remaining MV offenses are misdemeanor
    (["unlicensed operation", "license suspended", "license revoked",
      "registration suspended", "registration revoked",
      "unregistered motor", "uninsured mv",
      "oui liquor", "oui drugs",
      "reckless operation", "negligent operation", "operating to endanger",
      "speeding", "stop/yield", "stop for police", "marked lanes",
      "leave scene of property damage",
      "attaching wrong", "number plate", "inspection/sticker",
      "defective equipment", "window obstructed", "lights violation",
      "signal, fail", "one way street", "right lane", "left lane",
      "turn, improper", "passing violation", "crosswalk",
      "license not in possession", "license class", "license restriction",
      "license, false", "license, exhibit", "license/regis",
      "identify self", "rmv document", "rmv signature", "rmv id card",
      "registration not in", "registration sticker",
      "equipment violation", "moped", "motorcycle equipment",
      "impeded operation", "improper operation",
      "electronic device, use",
      "use mv without", "abandon mv", "hang onto mv",
      "alcohol from open container",
      "snow/rec veh", "child under 6", "child 6-12", "seat belt",
      "school bus", "headlights", "brakes violation",
      "horn violation", "red/blue light", "height, operate mv",
      "state hway", "unsafe operation", "motor carrier",
      "failure to display", "failure to obey",
      "keep right for oncoming", "breakdown lane",
      "safety standards, mv", "yield at intersection",
      "trespass with motor vehicle",
      "use of mobile telephone",
      "motor veh vin, remove"], "Misdemeanor"),

    # Simple assault / a&b
    (["a&b domestic", "a&b on family", "a&b in the presence",
      "a&b to collect loan", "assault on family",
      "a&b to intimidate",
      "a&b", "assault"], "Misdemeanor"),

    # Sex offenses - misdemeanor
    (["lewdness", "indecent exposure", "prostitut", "solicit for",
      "lewd, wanton", "accost/annoy",
      "sex offender fail to"], "Misdemeanor"),

    # B&E for misdemeanor
    (["b&e for misdemeanor", "burglarious instrument"], "Misdemeanor"),

    # Theft - misdemeanor level
    (["larceny under $1200", "larceny under $250",
      "larceny by check under",
      "receive stolen property -$1200", "receive stolen prop -$1200",
      "shoplifting", "thief, common",
      "motor veh, taking & stealing", "tools, larceny"], "Misdemeanor"),

    # Property destruction - misdemeanor
    (["destruction of prop -$1200", "deface property",
      "trespass notice, vandalize", "building, vandalize"], "Misdemeanor"),

    # Fraud - misdemeanor
    (["false id info", "credit card fraud under $1200",
      "credit card, improper use under",
      "credit card, larceny of", "credit card, receive stolen",
      "credit card, false",
      "false name/ss#", "insurance claim, false",
      "innkeeper, defraud", "restaurant, defraud",
      "notes, possess worthless", "note, forgery of bank",
      "false pretense"], "Misdemeanor"),

    # Weapons - misdemeanor
    (["knife over", "body armor"], "Misdemeanor"),

    # Protective orders
    (["harassment prevention order"], "Misdemeanor"),

    # Obstruction - misdemeanor
    (["resist arrest", "resisting arrest",
      "crime report, false", "false statement",
      "penalty of perjury", "contempt",
      "dna database", "recognizance, fail",
      "probation supervision", "parole/pardon",
      "prisoner, deliver", "correctional institution",
      "escape from", "firefighter, interfere",
      "emergency vehicle", "police horse",
      "juror fail to attend", "witness fail to appear",
      "police officer, interfere", "police officer, impersonate",
      "disguise to obstruct",
      "extortion"], "Misdemeanor"),

    # Public order - misdemeanor
    (["disorderly conduct", "trespass", "disturbing the peace",
      "drinking in public", "noisy and disorderly",
      "miscellaneous muni", "municipal by-law", "ordinance",
      "criminal harassment", "affray",
      "liquor, person under 21", "liquor to person under 21",
      "park regulation", "school, disturb",
      "fire call box", "fireworks",
      "trash, litter", "dumpster",
      "hunt/fish", "marine fish", "fish propagation",
      "dog", "animal", "taxi fare",
      "tramp", "nightwalker",
      "telephone", "railroad track",
      "miscellaneous statutory", "hypodermic",
      "threat /dangerous",
      "contribute to delinquency", "intimidate"], "Misdemeanor"),

    # Remaining motor vehicle (truncated license entries)
    (["license,", "register, subsq"], "Misdemeanor"),

    # Violation (generic)
    (["violation"], "Misdemeanor"),
]


def classify_charge(base_charge, offense_number="none"):
    """Classify a charge as Felony, Misdemeanor, or Either under MA law."""
    charge = base_charge.lower()

    has_subsq = offense_number not in ("none", "1st")

    for keywords, classification in CHARGE_CLASS_RULES:
        for kw in keywords:
            if kw in charge:
                if has_subsq and classification == "Misdemeanor":
                    return "Either"
                return classification

    return "Unknown"


# ---------------------------------------------------------------------------
# Step 8: Aggregate
# ---------------------------------------------------------------------------
def aggregate_rows(rows):
    """Group rows by base_charge, summing counts.

    For category and charge_class, use the value associated with the
    highest count (i.e., the most common variant wins).
    """
    groups = defaultdict(lambda: {"total_count": 0, "variants": []})
    for r in rows:
        key = r["base_charge"]
        count = int(r["count"])
        groups[key]["total_count"] += count
        groups[key]["variants"].append((count, r["category"], r["charge_class"]))

    result = []
    for base_charge, info in groups.items():
        # Pick category/charge_class from the variant with highest count
        best = max(info["variants"], key=lambda x: x[0])
        result.append({
            "base_charge": base_charge,
            "total_count": info["total_count"],
            "category": best[1],
            "charge_class": best[2],
        })
    result.sort(key=lambda x: -x["total_count"])
    return result


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def process_charges():
    """Read input CSV, standardize charges, aggregate, write output CSV."""
    rows = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            original = row["charge"].strip()
            count = row["count"].strip()

            if not original:
                continue

            # Step 1: Extract warrant type
            warrant_type, remaining = extract_warrant_type(original)

            # Step 2: Strip statute references
            cleaned = strip_statute_refs(remaining)

            # Step 3: Clean up
            base_charge = clean_charge(cleaned)

            # Step 4: Extract offense number
            offense_number, base_charge = extract_offense_number(base_charge)

            # Step 5: Normalize to canonical form
            base_charge = normalize_charge(base_charge)

            # Step 6: Categorize
            category = categorize_charge(base_charge)

            # Step 7: Classify as Felony/Misdemeanor
            charge_class = classify_charge(base_charge, offense_number)

            rows.append({
                "base_charge": base_charge,
                "count": count,
                "category": category,
                "charge_class": charge_class,
            })

    # Step 8: Aggregate
    aggregated = aggregate_rows(rows)

    # Write output
    fieldnames = ["base_charge", "total_count", "category", "charge_class"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(aggregated)

    print(f"Input rows: {len(rows)}")
    print(f"Aggregated to: {len(aggregated)} unique charges -> {OUTPUT_FILE}")

    # Print category summary
    cat_counts = defaultdict(int)
    for r in aggregated:
        cat_counts[r["category"]] += 1
    print("\nCategory distribution (unique charges):")
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}")

    # Print charge class summary
    cc_counts = defaultdict(int)
    for r in aggregated:
        cc_counts[r["charge_class"]] += 1
    print("\nCharge class distribution:")
    for cc, cnt in sorted(cc_counts.items(), key=lambda x: -x[1]):
        print(f"  {cc}: {cnt}")

    # List any Unknown classifications
    unknowns = [r for r in aggregated if r["charge_class"] == "Unknown"]
    if unknowns:
        print(f"\n{len(unknowns)} charges with Unknown classification:")
        for r in unknowns:
            print(f"  {r['base_charge']} (count: {r['total_count']})")

    # List any Miscellaneous categories
    misc = [r for r in aggregated if r["category"] == "Miscellaneous"]
    if misc:
        print(f"\n{len(misc)} charges with Miscellaneous category:")
        for r in misc:
            print(f"  {r['base_charge']} (count: {r['total_count']})")


if __name__ == "__main__":
    process_charges()
