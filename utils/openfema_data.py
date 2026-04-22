"""
OpenFEMA Data Integration Module

Fetches real data from three free, keyless OpenFEMA APIs:
1. DisasterDeclarationsSummaries v2 - Historical federal disaster declarations per county
2. FimaNfipClaims v2 - NFIP flood insurance claims per county
3. HazardMitigationAssistanceProjects v4 - Mitigation projects per county

All data is pre-fetched by scheduler jobs and stored in PostgreSQL cache.
No external API calls occur during user assessments.

Data sources:
- https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries
- https://www.fema.gov/api/open/v2/FimaNfipClaims
- https://www.fema.gov/api/open/v1/HazardMitigationAssistanceProjects
"""

import logging
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

OPENFEMA_BASE = "https://www.fema.gov/api/open"
WI_STATE_CODE = "WI"
WI_FIPS_STATE = "55"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

WI_COUNTY_FIPS_3DIGIT = {
    "Adams": "001", "Ashland": "003", "Barron": "005", "Bayfield": "007",
    "Brown": "009", "Buffalo": "011", "Burnett": "013", "Calumet": "015",
    "Chippewa": "017", "Clark": "019", "Columbia": "021", "Crawford": "023",
    "Dane": "025", "Dodge": "027", "Door": "029", "Douglas": "031",
    "Dunn": "033", "Eau Claire": "035", "Florence": "037", "Fond du Lac": "039",
    "Forest": "041", "Grant": "043", "Green": "045", "Green Lake": "047",
    "Iowa": "049", "Iron": "051", "Jackson": "053", "Jefferson": "055",
    "Juneau": "057", "Kenosha": "059", "Kewaunee": "061", "La Crosse": "063",
    "Lafayette": "065", "Langlade": "067", "Lincoln": "069", "Manitowoc": "071",
    "Marathon": "073", "Marinette": "075", "Marquette": "077", "Menominee": "078",
    "Milwaukee": "079", "Monroe": "081", "Oconto": "083", "Oneida": "085",
    "Outagamie": "087", "Ozaukee": "089", "Pepin": "091", "Pierce": "093",
    "Polk": "095", "Portage": "097", "Price": "099", "Racine": "101",
    "Richland": "103", "Rock": "105", "Rusk": "107", "Sauk": "111",
    "Sawyer": "113", "Shawano": "115", "Sheboygan": "117", "St. Croix": "109",
    "Taylor": "119", "Trempealeau": "121", "Vernon": "123", "Vilas": "125",
    "Walworth": "127", "Washburn": "129", "Washington": "131", "Waukesha": "133",
    "Waupaca": "135", "Waushara": "137", "Winnebago": "139", "Wood": "141"
}


def _api_get(url: str, params: Dict[str, str]) -> Optional[Dict]:
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"OpenFEMA API returned {response.status_code} for {url}")
            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"OpenFEMA request failed (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
    return None


def fetch_disaster_declarations_wi() -> Dict[str, Any]:
    """
    Fetch all federal disaster declarations for Wisconsin counties.
    Returns aggregated data per county: total declarations, by type, most recent.
    """
    url = f"{OPENFEMA_BASE}/v2/DisasterDeclarationsSummaries"
    all_records = []
    skip = 0
    top = 1000

    start_time = time.time()
    logger.info("Fetching Wisconsin disaster declarations from OpenFEMA")

    while True:
        params = {
            "$filter": f"state eq '{WI_STATE_CODE}'",
            "$select": "femaDeclarationString,disasterNumber,declarationType,declarationDate,"
                       "incidentType,declarationTitle,designatedArea,fipsCountyCode,"
                       "ihProgramDeclared,paProgramDeclared,hmProgramDeclared",
            "$top": str(top),
            "$skip": str(skip),
            "$orderby": "declarationDate desc"
        }

        data = _api_get(url, params)
        if not data:
            break

        records = data.get("DisasterDeclarationsSummaries", [])
        if not records:
            break

        all_records.extend(records)
        skip += top

        if len(records) < top:
            break

    fetch_duration = time.time() - start_time
    logger.info(f"Fetched {len(all_records)} disaster declaration records in {fetch_duration:.1f}s")

    county_data = {}
    for record in all_records:
        area = record.get("designatedArea", "")
        county_name = area.replace(" (County)", "").replace(" County", "").strip()
        if not county_name or county_name == "Statewide":
            continue

        if county_name not in county_data:
            county_data[county_name] = {
                "total_declarations": 0,
                "by_incident_type": {},
                "by_declaration_type": {},
                "declarations": [],
                "ia_declarations": 0,
                "pa_declarations": 0,
                "hm_declarations": 0
            }

        cd = county_data[county_name]
        cd["total_declarations"] += 1

        incident_type = record.get("incidentType", "Unknown")
        cd["by_incident_type"][incident_type] = cd["by_incident_type"].get(incident_type, 0) + 1

        decl_type = record.get("declarationType", "Unknown")
        cd["by_declaration_type"][decl_type] = cd["by_declaration_type"].get(decl_type, 0) + 1

        if record.get("ihProgramDeclared"):
            cd["ia_declarations"] += 1
        if record.get("paProgramDeclared"):
            cd["pa_declarations"] += 1
        if record.get("hmProgramDeclared"):
            cd["hm_declarations"] += 1

        cd["declarations"].append({
            "id": record.get("femaDeclarationString"),
            "date": record.get("declarationDate", "")[:10],
            "type": incident_type,
            "title": record.get("declarationTitle", "")
        })

    for county_name, cd in county_data.items():
        cd["declarations"] = cd["declarations"][:10]

    return {"county_data": county_data, "total_records": len(all_records), "fetch_duration": fetch_duration}


def fetch_nfip_claims_wi() -> Dict[str, Any]:
    """
    Fetch NFIP flood insurance claims for Wisconsin counties.
    Returns aggregated data: claim count, total payouts, by year.
    """
    url = f"{OPENFEMA_BASE}/v2/FimaNfipClaims"
    all_records = []
    skip = 0
    top = 10000

    start_time = time.time()
    logger.info("Fetching Wisconsin NFIP claims from OpenFEMA")

    while True:
        params = {
            "$filter": f"state eq '{WI_STATE_CODE}'",
            "$select": "countyCode,dateOfLoss,yearOfLoss,amountPaidOnBuildingClaim,"
                       "amountPaidOnContentsClaim,occupancyType,floodZone",
            "$top": str(top),
            "$skip": str(skip)
        }

        data = _api_get(url, params)
        if not data:
            break

        records = data.get("FimaNfipClaims", [])
        if not records:
            break

        all_records.extend(records)
        skip += top

        if len(records) < top:
            break

    fetch_duration = time.time() - start_time
    logger.info(f"Fetched {len(all_records)} NFIP claim records in {fetch_duration:.1f}s")

    fips_to_county = {f"{WI_FIPS_STATE}{code}": name for name, code in WI_COUNTY_FIPS_3DIGIT.items()}

    county_data = {}
    for record in all_records:
        county_code = str(record.get("countyCode", ""))
        county_name = fips_to_county.get(county_code)
        if not county_name:
            continue

        if county_name not in county_data:
            county_data[county_name] = {
                "total_claims": 0,
                "total_building_payout": 0.0,
                "total_contents_payout": 0.0,
                "total_payout": 0.0,
                "claims_by_year": {},
                "claims_by_flood_zone": {}
            }

        cd = county_data[county_name]
        cd["total_claims"] += 1

        building = float(record.get("amountPaidOnBuildingClaim") or 0)
        contents = float(record.get("amountPaidOnContentsClaim") or 0)
        cd["total_building_payout"] += building
        cd["total_contents_payout"] += contents
        cd["total_payout"] += building + contents

        year = str(record.get("yearOfLoss", "Unknown"))
        cd["claims_by_year"][year] = cd["claims_by_year"].get(year, 0) + 1

        zone = record.get("floodZone", "Unknown")
        cd["claims_by_flood_zone"][zone] = cd["claims_by_flood_zone"].get(zone, 0) + 1

    return {"county_data": county_data, "total_records": len(all_records), "fetch_duration": fetch_duration}


def fetch_hma_projects_wi() -> Dict[str, Any]:
    """
    Fetch Hazard Mitigation Assistance projects for Wisconsin.
    Returns aggregated data: project count, funding, by program type and hazard.
    """
    url = f"{OPENFEMA_BASE}/v4/HazardMitigationAssistanceProjects"
    all_records = []
    skip = 0
    top = 1000

    start_time = time.time()
    logger.info("Fetching Wisconsin HMA projects from OpenFEMA")

    while True:
        params = {
            "$filter": f"state eq '{WI_STATE_CODE}'",
            "$select": "county,programArea,programFy,projectType,status,"
                       "projectAmount,federalShareObligated,benefitCostRatio,"
                       "numberOfFinalProperties,dateApproved,dateClosed,subrecipient",
            "$top": str(top),
            "$skip": str(skip)
        }

        data = _api_get(url, params)
        if not data:
            break

        records = data.get("HazardMitigationAssistanceProjects", [])
        if not records:
            break

        all_records.extend(records)
        skip += top

        if len(records) < top:
            break

    fetch_duration = time.time() - start_time
    logger.info(f"Fetched {len(all_records)} HMA project records in {fetch_duration:.1f}s")

    county_data = {}
    for record in all_records:
        county_name = (record.get("county") or "").strip().title()
        if not county_name:
            continue

        if county_name not in county_data:
            county_data[county_name] = {
                "total_projects": 0,
                "total_project_amount": 0.0,
                "total_federal_share": 0.0,
                "by_program": {},
                "by_status": {},
                "by_project_type": {},
                "properties_mitigated": 0,
                "recent_projects": []
            }

        cd = county_data[county_name]
        cd["total_projects"] += 1

        amount = float(record.get("projectAmount") or 0)
        federal = float(record.get("federalShareObligated") or 0)
        cd["total_project_amount"] += amount
        cd["total_federal_share"] += federal

        program = record.get("programArea", "Unknown")
        cd["by_program"][program] = cd["by_program"].get(program, 0) + 1

        status = record.get("status", "Unknown")
        cd["by_status"][status] = cd["by_status"].get(status, 0) + 1

        proj_type = record.get("projectType", "Unknown")
        cd["by_project_type"][proj_type] = cd["by_project_type"].get(proj_type, 0) + 1

        props = int(record.get("numberOfFinalProperties") or 0)
        cd["properties_mitigated"] += props

        cd["recent_projects"].append({
            "program": program,
            "type": proj_type,
            "amount": amount,
            "federal_share": federal,
            "status": status,
            "date_approved": (record.get("dateApproved") or "")[:10],
            "subrecipient": record.get("subrecipient", "")
        })

    for county_name, cd in county_data.items():
        cd["recent_projects"].sort(key=lambda x: x.get("date_approved", ""), reverse=True)
        cd["recent_projects"] = cd["recent_projects"][:10]

    return {"county_data": county_data, "total_records": len(all_records), "fetch_duration": fetch_duration}


def get_county_openfema_summary(county_name: str) -> Dict[str, Any]:
    """
    Get a combined summary of all OpenFEMA data for a county from cache.
    Called during dashboard rendering.
    """
    try:
        from utils.data_cache_manager import get_cached_data

        summary = {
            "disaster_declarations": None,
            "nfip_claims": None,
            "hma_projects": None
        }

        decl_cache = get_cached_data("openfema_disaster_declarations", county_name=county_name)
        if decl_cache and decl_cache.get("data"):
            summary["disaster_declarations"] = decl_cache["data"]

        claims_cache = get_cached_data("openfema_nfip_claims", county_name=county_name)
        if claims_cache and claims_cache.get("data"):
            summary["nfip_claims"] = claims_cache["data"]

        hma_cache = get_cached_data("openfema_hma_projects", county_name=county_name)
        if hma_cache and hma_cache.get("data"):
            summary["hma_projects"] = hma_cache["data"]

        return summary

    except Exception as e:
        logger.error(f"Error getting OpenFEMA summary for {county_name}: {e}")
        return {"disaster_declarations": None, "nfip_claims": None, "hma_projects": None}


def format_currency(amount: float) -> str:
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:.0f}"
