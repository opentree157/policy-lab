"""Static dataset catalog — seeded once on startup."""

DATASETS = [
    {
        "id": "acs-housing-2023",
        "name": "American Housing Survey (ACS)",
        "slug": "acs-housing",
        "description": (
            "U.S. Census Bureau American Community Survey housing cost data. "
            "Covers rental/ownership costs, cost burden rates, and affordability "
            "metrics at state and county levels."
        ),
        "source": "U.S. Census Bureau",
        "category": "housing",
        "size_bytes": 2_840_000_000,
        "row_count": 3_200_000,
        "columns": [
            "state_fips", "county_fips", "year", "tenure", "gross_rent",
            "household_income", "cost_burden", "severe_burden", "bedrooms",
            "unit_type", "year_built", "vehicles_available",
        ],
        "schema_info": {
            "cost_burden": "Boolean — gross rent > 30% of monthly household income",
            "severe_burden": "Boolean — gross rent > 50% of monthly household income",
        },
        "tags": ["housing", "affordability", "census", "state-level", "county-level"],
        "years_available": list(range(2010, 2024)),
        "geographic_level": "county",
    },
    {
        "id": "bls-unemployment-2024",
        "name": "BLS Current Population Survey",
        "slug": "bls-unemployment",
        "description": (
            "Bureau of Labor Statistics monthly unemployment data by industry sector, "
            "occupation, age, education level, and state. Includes U-3 (official) "
            "and U-6 (broad) unemployment measures."
        ),
        "source": "Bureau of Labor Statistics",
        "category": "labor",
        "size_bytes": 890_000_000,
        "row_count": 14_500_000,
        "columns": [
            "year", "month", "state", "industry_sector", "occupation_group",
            "age_group", "education_level", "u3_rate", "u6_rate",
            "labor_force_participation", "employment_level",
        ],
        "schema_info": {
            "u3_rate": "Official unemployment rate (seasonally adjusted)",
            "u6_rate": "Broad unemployment including marginally attached workers",
        },
        "tags": ["labor", "unemployment", "workforce", "bls", "monthly"],
        "years_available": list(range(2000, 2025)),
        "geographic_level": "state",
    },
    {
        "id": "census-demographics-2020",
        "name": "Decennial Census Demographic Profile",
        "slug": "census-demographics",
        "description": (
            "Full population counts from the 2020 U.S. Decennial Census with "
            "demographic breakdowns by age, race, ethnicity, household type, "
            "and geographic unit down to the census tract."
        ),
        "source": "U.S. Census Bureau",
        "category": "demographics",
        "size_bytes": 12_400_000_000,
        "row_count": 74_000_000,
        "columns": [
            "geoid", "state", "county", "tract", "total_population",
            "age_under18", "age_18to64", "age_65plus", "white_alone",
            "black_alone", "hispanic", "asian_alone", "median_age",
            "avg_household_size", "total_households",
        ],
        "schema_info": {
            "geoid": "11-digit FIPS code (state+county+tract)",
        },
        "tags": ["demographics", "census", "population", "age", "race", "tract-level"],
        "years_available": [2010, 2020],
        "geographic_level": "tract",
    },
    {
        "id": "cms-medicare-2022",
        "name": "CMS Medicare Geographic Variation",
        "slug": "cms-medicare",
        "description": (
            "Centers for Medicare & Medicaid Services geographic variation in "
            "spending, utilization, and quality measures by state and hospital "
            "referral region. Captures regional disparities in healthcare costs."
        ),
        "source": "Centers for Medicare & Medicaid Services",
        "category": "healthcare",
        "size_bytes": 340_000_000,
        "row_count": 5_800_000,
        "columns": [
            "state", "hrr_code", "year", "total_spending_per_beneficiary",
            "inpatient_spending", "outpatient_spending", "physician_spending",
            "snf_spending", "readmission_rate", "preventable_admissions",
            "patient_satisfaction_score",
        ],
        "schema_info": {
            "hrr_code": "Hospital Referral Region code (306 regions nationwide)",
        },
        "tags": ["healthcare", "medicare", "spending", "cms", "regional"],
        "years_available": list(range(2015, 2023)),
        "geographic_level": "state",
    },
    {
        "id": "mit-elections-2020",
        "name": "MIT Election Lab Presidential Returns",
        "slug": "mit-elections",
        "description": (
            "County-level U.S. presidential election returns compiled by the "
            "MIT Election Data + Science Lab. Includes vote totals, turnout, "
            "and demographic correlates for every county from 2000–2020."
        ),
        "source": "MIT Election Data + Science Lab",
        "category": "elections",
        "size_bytes": 45_000_000,
        "row_count": 18_000,
        "columns": [
            "year", "state", "county_fips", "county_name", "party",
            "candidatevotes", "totalvotes", "turnout_rate",
            "pct_college", "median_income", "pct_white",
        ],
        "schema_info": {
            "turnout_rate": "votes cast / voting-age population",
        },
        "tags": ["elections", "voting", "county-level", "political-science"],
        "years_available": [2000, 2004, 2008, 2012, 2016, 2020],
        "geographic_level": "county",
    },
    {
        "id": "world-bank-climate-2023",
        "name": "World Bank Climate & Development Indicators",
        "slug": "world-bank-climate",
        "description": (
            "World Bank Development Indicators merged with climate vulnerability "
            "scores. Covers 217 countries with GDP, CO₂ emissions, temperature "
            "anomaly, energy mix, and climate risk index."
        ),
        "source": "World Bank / Notre Dame Global Adaptation Initiative",
        "category": "climate",
        "size_bytes": 78_000_000,
        "row_count": 6_500,
        "columns": [
            "country_code", "country_name", "year", "gdp_per_capita",
            "co2_per_capita", "renewable_energy_pct", "temperature_anomaly_c",
            "nd_gain_score", "climate_vulnerability", "fossil_fuel_pct",
            "forest_area_pct",
        ],
        "schema_info": {
            "nd_gain_score": "Notre Dame Global Adaptation Initiative score (0–100)",
            "temperature_anomaly_c": "Deviation from 1951–1980 baseline (°C)",
        },
        "tags": ["climate", "international", "gdp", "emissions", "world-bank"],
        "years_available": list(range(1990, 2024)),
        "geographic_level": "national",
    },
    {
        "id": "hud-fair-market-rent-2024",
        "name": "HUD Fair Market Rents",
        "slug": "hud-fmr",
        "description": (
            "HUD-published Fair Market Rents (FMRs) used to determine Section 8 "
            "housing voucher payment standards. Annual estimates of 40th percentile "
            "gross rents for standard quality units by bedroom size and metro area."
        ),
        "source": "U.S. Dept. of Housing and Urban Development",
        "category": "housing",
        "size_bytes": 12_000_000,
        "row_count": 530_000,
        "columns": [
            "fips_code", "metro_area", "state", "year",
            "fmr_0br", "fmr_1br", "fmr_2br", "fmr_3br", "fmr_4br",
            "median_income", "income_limit_80pct",
        ],
        "schema_info": {
            "fmr_2br": "40th percentile gross rent for 2-bedroom unit",
            "income_limit_80pct": "80% of Area Median Income threshold",
        },
        "tags": ["housing", "rent", "hud", "vouchers", "metro-area"],
        "years_available": list(range(2000, 2025)),
        "geographic_level": "county",
    },
]


ANALYSIS_TEMPLATES = {
    "housing_affordability": {
        "label": "Housing Affordability Analysis",
        "description": "Compute cost burden rates by income quintile, state, and year.",
        "compatible_datasets": ["acs-housing", "hud-fmr"],
        "parameters": {
            "states": {
                "type": "multiselect",
                "label": "States to include",
                "options": [
                    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
                    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
                    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
                    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
                    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
                ],
                "default": ["CA", "NY", "TX", "FL", "IL", "OH", "PA", "WA", "CO", "GA"],
            },
            "year_start": {"type": "integer", "label": "Start Year", "default": 2015, "min": 2010, "max": 2022},
            "year_end": {"type": "integer", "label": "End Year", "default": 2023, "min": 2011, "max": 2023},
            "income_quintile": {"type": "select", "label": "Focus Quintile", "options": ["all", "Q1", "Q2", "Q3", "Q4", "Q5"], "default": "all"},
        },
    },
    "labor_trends": {
        "label": "Labor Market Trends",
        "description": "Analyze unemployment rates by sector, geography, and demographic group.",
        "compatible_datasets": ["bls-unemployment"],
        "parameters": {
            "sectors": {
                "type": "multiselect",
                "label": "Industry Sectors",
                "options": ["Manufacturing", "Services", "Government", "Technology", "Healthcare", "Construction", "Retail", "Finance"],
                "default": ["Manufacturing", "Services", "Technology", "Healthcare"],
            },
            "year_start": {"type": "integer", "label": "Start Year", "default": 2010, "min": 2000, "max": 2023},
            "year_end": {"type": "integer", "label": "End Year", "default": 2024, "min": 2001, "max": 2024},
            "measure": {"type": "select", "label": "Unemployment Measure", "options": ["u3", "u6", "both"], "default": "u3"},
        },
    },
    "census_demographics": {
        "label": "Census Demographic Profile",
        "description": "Analyze population distribution, age structure, and demographic shifts.",
        "compatible_datasets": ["census-demographics"],
        "parameters": {
            "states": {
                "type": "multiselect",
                "label": "States",
                "options": [
                    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
                    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
                    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
                    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
                    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
                ],
                "default": ["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI"],
            },
            "breakdown": {
                "type": "select",
                "label": "Primary Breakdown",
                "options": ["age", "race_ethnicity", "household_type"],
                "default": "age",
            },
        },
    },
    "world_bank_indicators": {
        "label": "World Bank Development & Climate Indicators",
        "description": (
            "Live data from the World Bank Open Data API. "
            "GDP per capita, CO₂ emissions, renewable energy share, and inequality "
            "for up to 20 countries over any date range."
        ),
        "compatible_datasets": ["world-bank-climate"],
        "live_data": True,
        "parameters": {
            "countries": {
                "type": "multiselect",
                "label": "Countries (ISO-3 codes)",
                "options": [
                    "USA", "CHN", "DEU", "GBR", "FRA", "JPN", "IND", "BRA",
                    "CAN", "AUS", "KOR", "MEX", "IDN", "SAU", "ZAF", "NGA",
                    "ARG", "TUR", "SWE", "NOR",
                ],
                "default": ["USA", "CHN", "DEU", "GBR", "FRA", "JPN", "IND", "BRA"],
            },
            "year_start": {"type": "integer", "label": "Start Year", "default": 2000, "min": 1990, "max": 2020},
            "year_end": {"type": "integer", "label": "End Year", "default": 2022, "min": 1991, "max": 2023},
        },
    },
}
