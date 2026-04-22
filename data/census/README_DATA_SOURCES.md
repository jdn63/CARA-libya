# Wisconsin County Census Data Sources

## Overview
This directory contains county-specific Census data files that provide accurate demographic information for strategic planning. These files replace unreliable API calls with reliable local data.

## Required Data Files

### 1. wisconsin_housing_data.csv
**Purpose**: Mobile home percentages for housing vulnerability assessments
**Data Source**: American Community Survey 5-Year Estimates, Table B25024
**Download URL**: https://data.census.gov/table/ACSDT5Y2022.B25024
**Filter Settings**:
- Geography: Wisconsin (State: 55) > All Counties
- Variables: B25024_010E (Mobile homes), B25024_001E (Total housing units)

**Required Columns**:
- `county_name` - County name (e.g., "Adams", "Brown")
- `total_housing_units` - Total housing units in county
- `mobile_homes` - Number of mobile homes
- `mobile_home_percentage` - Calculated percentage (mobile_homes/total_housing_units * 100)

### 2. wisconsin_demographics.csv
**Purpose**: Age demographics and population data
**Data Source**: ACS 5-Year Demographic Profile, Table DP05
**Download URL**: https://data.census.gov/table/ACSDP5Y2022.DP05
**Filter Settings**:
- Geography: Wisconsin (State: 55) > All Counties
- Variables: DP05_0024PE (Percent 65+), DP05_0001E (Total population)

**Required Columns**:
- `county_name` - County name (e.g., "Adams", "Brown")
- `total_population` - Total county population
- `population_65_plus` - Population aged 65 and older
- `elderly_percentage` - Percent of population aged 65 and older

## How to Update Data

### Option 1: Download from Census Bureau
1. Visit the URLs above
2. Select Wisconsin and all counties
3. Download as CSV
4. Rename columns to match required format
5. Replace existing files in this directory

### Option 2: Upload Your Own Data
1. Use the same column structure as shown above
2. Include all 72 Wisconsin counties
3. Save as CSV files with exact filenames shown above
4. Upload to this directory

## Data Quality Notes
- All 72 Wisconsin counties should be included
- County names should match exactly (no "County" suffix)
- Percentages can be pre-calculated or calculated from raw numbers
- Missing counties will use state averages as fallback

## Tribal Jurisdiction Handling
The system automatically maps tribal jurisdictions to appropriate proxy counties:
- Ho-Chunk Jackson County
- Oneida Brown County
- Bad River Ashland County
- Red Cliff Bayfield County
- Lac du Flambeau Vilas County
- And others...

## Benefits of Local Data
 **County-specific accuracy** - Real data for each Wisconsin county
 **No API failures** - Reliable file-based loading
 **Strategic planning focus** - Stable baseline data
 **Offline capability** - Works without internet
 **Data transparency** - Clear source documentation