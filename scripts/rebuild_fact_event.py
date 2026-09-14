"""
rebuild_fact_event.py
------------------------
Phase 3 correction: full rebuild of fact_event using a genuinely
complete Jan-Dec 2026 calendar source (gowod.app), after discovering
our original scrape (roxupdates.com) was missing Q1 2026 entirely plus
several second-editions later in the year (Cape Town x2, Beijing x2,
Nice x2, Stockholm x2, Helsinki x2, Washington DC x2), and missing new
cities entirely (Cairo, Melbourne, Kuala Lumpur, Perth, Athens, etc.)

Excludes "Youngstars" child events (ages 8-15) -- these always co-locate
with an adult event in the same city/weekend and would double-count a
single market decision if treated as a separate event row.
"""

import re
import unicodedata
import pandas as pd
from datetime import date, datetime, timezone

RAW_PATH = "gowod_calendar.txt"
OUTPUT_PATH = "hyrox_events_rebuilt.csv"
OLD_STATUS_PATH = "fact_events.csv"  # to preserve finer status where we already had it

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}

# All known cities, multi-word ones listed as full phrases.
# Checked longest-first so "SALT LAKE CITY" matches before any partial word collision.
KNOWN_CITIES = [
    "SALT LAKE CITY", "CAPE TOWN", "HONG KONG", "LAS VEGAS", "NEW YORK",
    "MEXICO CITY", "RIO DE JANEIRO", "KUALA LUMPUR", "SAO PAULO",
    "WASHINGTON DC", "MIAMI BEACH", "ST GALLEN",
    "BRISBANE","ROTTERDAM","COLOGNE","MALAGA","WARSAW","MONTERREY","PARIS",
    "CARDIFF","LISBOA","HELSINKI","BARCELONA","HEERENVEEN","OTTAWA","INCHEON",
    "PUEBLA","SHANGHAI","LYON","BERLIN","RIMINI","JOHANNESBURG","RIGA",
    "BUENOS AIRES","STOCKHOLM","JAKARTA","SYDNEY","HANGZHOU","DELHI","CHENGDU",
    "ISTANBUL","CHIBA","SHENZHEN","ACAPULCO","TENERIFE","BEIJING","MAASTRICHT",
    "MUMBAI","IZMIR","ROME","OSLO","BORDEAUX","KARLSRUHE","TORONTO","BOSTON",
    "GENEVA","GDANSK","VALENCIA","TAMPA","BIRMINGHAM","HAMBURG","NICE","DUBLIN",
    "DUSSELDORF","DENVER","SEOUL","DALLAS","POZNAN","GUANGZHOU","UTRECHT",
    "LONDON","ANAHEIM","MILAN","FRANKFURT","NASHVILLE","GENT","VANCOUVER",
    "SANYA","AUCKLAND","PHOENIX","OSAKA","TURIN","VIENNA","GUADALAJARA",
    "BILBAO","KATOWICE","FORTALEZA","TAIPEI","GLASGOW","COPENHAGEN","CANCUN",
    "TOULOUSE","BANGKOK","HOUSTON","MECHELEN","SINGAPORE","BOLOGNA","BENGALURU",
    "WUHAN","PERTH","ATHENS","CAIRO","MELBOURNE","MANCHESTER","AMSTERDAM",
]
# Sort longest first (by word count, then char length) so multi-word cities win
KNOWN_CITIES = sorted(KNOWN_CITIES, key=lambda c: (-len(c.split()), -len(c)))

# Correct display form matching (or extending) dim_city.city_name conventions,
# including proper accents for the join to work against existing rows.
CITY_DISPLAY = {
    "SALT LAKE CITY": "Salt Lake City", "CAPE TOWN": "Cape Town", "HONG KONG": "Hong Kong",
    "LAS VEGAS": "Las Vegas", "NEW YORK": "New York City", "MEXICO CITY": "Mexico City",
    "RIO DE JANEIRO": "Rio de Janeiro", "KUALA LUMPUR": "Kuala Lumpur", "SAO PAULO": "São Paulo",
    "WASHINGTON DC": "Washington DC", "MIAMI BEACH": "Miami Beach", "ST GALLEN": "St. Gallen",
    "BRISBANE": "Brisbane", "ROTTERDAM": "Rotterdam", "COLOGNE": "Cologne", "MALAGA": "Malaga",
    "WARSAW": "Warsaw", "MONTERREY": "Monterrey", "PARIS": "Paris", "CARDIFF": "Cardiff",
    "LISBOA": "Lisbon", "HELSINKI": "Helsinki", "BARCELONA": "Barcelona", "HEERENVEEN": "Heerenveen",
    "OTTAWA": "Ottawa", "INCHEON": "Incheon", "PUEBLA": "Puebla", "SHANGHAI": "Shanghai",
    "LYON": "Lyon", "BERLIN": "Berlin", "RIMINI": "Rimini", "JOHANNESBURG": "Johannesburg",
    "RIGA": "Riga", "BUENOS AIRES": "Buenos Aires", "STOCKHOLM": "Stockholm", "JAKARTA": "Jakarta",
    "SYDNEY": "Sydney", "HANGZHOU": "Hangzhou", "DELHI": "New Delhi", "CHENGDU": "Chengdu",
    "ISTANBUL": "Istanbul", "CHIBA": "Chiba", "SHENZHEN": "Shenzhen", "ACAPULCO": "Acapulco",
    "TENERIFE": "Santa Cruz de Tenerife", "BEIJING": "Beijing", "MAASTRICHT": "Maastricht",
    "MUMBAI": "Mumbai", "IZMIR": "İzmir", "ROME": "Rome", "OSLO": "Oslo", "BORDEAUX": "Bordeaux",
    "KARLSRUHE": "Karlsruhe", "TORONTO": "Toronto", "BOSTON": "Boston", "GENEVA": "Geneva",
    "GDANSK": "Gdańsk", "VALENCIA": "Valencia", "TAMPA": "Tampa", "BIRMINGHAM": "Birmingham",
    "HAMBURG": "Hamburg", "NICE": "Nice", "DUBLIN": "Dublin", "DUSSELDORF": "Düsseldorf",
    "DENVER": "Denver", "SEOUL": "Seoul", "DALLAS": "Dallas", "POZNAN": "Poznań",
    "GUANGZHOU": "Guangzhou", "UTRECHT": "Utrecht", "LONDON": "London", "ANAHEIM": "Anaheim",
    "MILAN": "Milan", "FRANKFURT": "Frankfurt", "NASHVILLE": "Nashville", "GENT": "Gent",
    "VANCOUVER": "Vancouver", "SANYA": "Sanya", "AUCKLAND": "Auckland", "PHOENIX": "Phoenix",
    "OSAKA": "Osaka", "TURIN": "Turin", "VIENNA": "Vienna", "GUADALAJARA": "Guadalajara",
    "BILBAO": "Bilbao", "KATOWICE": "Katowice", "FORTALEZA": "Fortaleza", "TAIPEI": "Taipei",
    "GLASGOW": "Glasgow", "COPENHAGEN": "Copenhagen", "CANCUN": "Cancún", "TOULOUSE": "Toulouse",
    "BANGKOK": "Bangkok", "HOUSTON": "Houston", "MECHELEN": "Mechelen", "SINGAPORE": "Singapore",
    "BOLOGNA": "Bologna", "BENGALURU": "Bengaluru", "WUHAN": "Wuhan", "PERTH": "Perth",
    "ATHENS": "Athens", "CAIRO": "Cairo", "MELBOURNE": "Melbourne", "MANCHESTER": "Manchester",
    "AMSTERDAM": "Amsterdam",
}

# country/region for cities NOT already in dim_city (the original 72 already have this;
# these are the ~29 newly-discovered cities)
NEW_CITY_COUNTRY_REGION = {
    "St. Gallen": ("Switzerland", "Europe"), "Manchester": ("United Kingdom", "Europe"),
    "Amsterdam": ("Netherlands", "Europe"), "Auckland": ("New Zealand", "APAC"),
    "Phoenix": ("USA", "North America"), "Osaka": ("Japan", "APAC"), "Turin": ("Italy", "Europe"),
    "Vienna": ("Austria", "Europe"), "Guadalajara": ("Mexico", "North America"),
    "Bilbao": ("Spain", "Europe"), "Las Vegas": ("USA", "North America"),
    "Katowice": ("Poland", "Europe"), "Fortaleza": ("Brazil", "South America"),
    "Taipei": ("Taiwan", "APAC"), "Glasgow": ("United Kingdom", "Europe"),
    "Copenhagen": ("Denmark", "Europe"), "Cancún": ("Mexico", "North America"),
    "Toulouse": ("France", "Europe"), "Houston": ("USA", "North America"),
    "Mechelen": ("Belgium", "Europe"), "Singapore": ("Singapore", "APAC"),
    "Miami Beach": ("USA", "North America"), "Bologna": ("Italy", "Europe"),
    "Bengaluru": ("India", "APAC"), "Wuhan": ("China", "APAC"), "Perth": ("Australia", "APAC"),
    "Athens": ("Greece", "Europe"), "Cairo": ("Egypt", "Africa"),
    "Kuala Lumpur": ("Malaysia", "APAC"), "Melbourne": ("Australia", "APAC"),
}

def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def find_city(event_name: str):
    name_norm = strip_accents(event_name).upper()
    name_norm = re.sub(r"\s+\d+$", "", name_norm)  # drop trailing " 2" duplicate-marker
    for city_key in KNOWN_CITIES:
        pattern = r"\b" + re.escape(city_key) + r"\b"
        if re.search(pattern, name_norm):
            return CITY_DISPLAY[city_key]
    return None

def parse_dates(date_str: str, year=2026):
    date_str = date_str.replace("–", "-").strip()
    m = re.match(
        r"(?P<mon1>\w{3})\s+(?P<day1>\d{1,2})"
        r"(?:-(?P<day2same>\d{1,2}))?"
        r"(?:-(?P<mon2>\w{3})\s+(?P<day2>\d{1,2}))?$",
        date_str
    )
    if not m:
        return None, None
    d = m.groupdict()
    mon1 = MONTHS[d["mon1"]]
    if d["mon2"]:
        start = date(year, mon1, int(d["day1"]))
        end = date(year, MONTHS[d["mon2"]], int(d["day2"]))
    elif d["day2same"]:
        start = date(year, mon1, int(d["day1"]))
        end = date(year, mon1, int(d["day2same"]))
    else:
        start = date(year, mon1, int(d["day1"]))
        end = start
    return start, end

# Load old status data to preserve finer registration_status where we already had it
old_status_lookup = {}
try:
    old_df = pd.read_csv(OLD_STATUS_PATH, na_values=["NULL"])
    for _, row in old_df.iterrows():
        key = (row["city_name"], pd.to_datetime(row["date_id"], format="%Y%m%d").month)
        old_status_lookup[key] = row["registration_status"]
except FileNotFoundError:
    print("Old fact_events.csv not found -- skipping status reconciliation, will use derived status only.")

rows = []
skipped = []
new_cities_needed = {}

with open(RAW_PATH, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or "|" not in line:
            continue
        name, date_str = [x.strip() for x in line.split("|")]
        if "YOUNGSTARS" in name.upper():
            continue  # exclude child events -- co-located with adult event, not a separate market decision

        city = find_city(name)
        if city is None:
            skipped.append(name)
            continue

        start, end = parse_dates(date_str)
        if start is None:
            skipped.append(f"{name} (date parse failed: {date_str})")
            continue

        if city in NEW_CITY_COUNTRY_REGION:
            new_cities_needed[city] = NEW_CITY_COUNTRY_REGION[city]

        today = datetime.now(timezone.utc).date()
        derived_status = "Past" if start < today else "Scheduled"
        status = old_status_lookup.get((city, start.month), derived_status)

        rows.append({
            "brand_name": "HYROX", "city": city, "event_name_raw": name,
            "start_date": start, "end_date": end,
            "registration_status": status,
            "sold_out_flag": status == "Sold Out",
            "source_note": "gowod.app full-season calendar, retrieved via Claude web_fetch",
        })

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_PATH, index=False)

print(f"Parsed {len(df)} events. Skipped {len(skipped)}:")
for s in skipped:
    print(f"  - {s}")
print(f"\nNew cities requiring a dim_city insert ({len(new_cities_needed)}):")
for c, (country, region) in sorted(new_cities_needed.items()):
    print(f"  {c}: {country}, {region}")
print(f"\nStatus breakdown:\n{df['registration_status'].value_counts()}")
print(f"\nEvents per city (top 10 by count -- these are the real multi-city/saturated markets):")
print(df["city"].value_counts().head(10))