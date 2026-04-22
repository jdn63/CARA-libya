"""
Jurisdiction-to-Boundary Mapping for GIS Export

This module provides deterministic mapping between CARA jurisdiction IDs
and boundary file OBJECTID values for reliable polygon matching in GeoJSON exports.

Generated from:
  - wi_health_departments.json (authoritative jurisdiction names)
  - Wisconsin_Local_Public_Health_Department_Office_Boundaries.geojson (boundary OBJECTIDs)
"""

import logging

logger = logging.getLogger(__name__)

# Maps jurisdiction ID to boundary file OBJECTID
JURISDICTION_TO_BOUNDARY_OBJECTID = {
    '1': 68,  # Adams County Health & Human Services
    '2': 69,  # Ashland County Health & Human Services
    '3': 67,  # Barron County Department of Health & Human Services
    '4': 70,  # Bayfield County Health Department
    '5': 71,  # Brown County Health & Human Services Department
    '6': 5,  # DePere Department of Public Health
    '7': 72,  # Buffalo County Health & Human Services Department
    '8': 73,  # Burnett County Department of Health & Human Services
    '9': 7,  # Appleton City Health Department
    '10': 74,  # Calumet County Health & Human Services
    '11': 8,  # City of Menasha Health Department
    '12': 31,  # Chippewa County Department of Public Health
    '13': 32,  # Clark County Health Department
    '14': 33,  # Columbia County Health & Human Services
    '15': 34,  # Crawford County Health & Human Services
    '16': 35,  # Public Health - Madison & Dane County
    '17': 36,  # Dodge County Human Services & Health Department
    '18': 1,  # Watertown Department of Public Health
    '19': 37,  # Door County Department of Health & Human Services
    '20': 38,  # Douglas County Department of Health & Human Services
    '21': 39,  # Dunn County Health Department
    '22': 40,  # Eau Claire City-County Health Department
    '23': 41,  # Florence County Health Department
    '24': 43,  # Forest County Health Department
    '25': 42,  # Fond du Lac County Health Department
    '26': 44,  # Grant County Health Department
    '27': 45,  # Green County Public Health
    '28': 46,  # Green Lake County Department of Health & Human Services
    '29': 47,  # Iowa County Health Department
    '30': 17,  # Iron County Health Department
    '31': 18,  # Jackson County Public Health Department
    '32': 19,  # Jefferson County Health Department
    '33': 1,  # Watertown Department of Public Health
    '34': 20,  # Juneau County Health Department
    '35': 21,  # Kenosha County Division of Health
    '36': 22,  # Kewaunee County Public Health Department
    '37': 23,  # La Crosse County Health Department
    '38': 24,  # Lafayette County Health Department
    '39': 25,  # Langlade County Health Department
    '40': 26,  # Lincoln County Health Department
    '41': 27,  # Manitowoc County Health Department
    '42': 28,  # Marathon County Health Department
    '43': 29,  # Marinette County Health & Human Services
    '44': 30,  # Marquette County Health Department
    '45': 66,  # Shawano-Menominee Counties Health Department
    '46': 3,  # Cudahy Health Department
    '47': 4,  # Franklin Health Department
    '48': 9,  # Greendale Health Department
    '49': 10,  # Hales Corners Health Department
    '50': 12,  # Milwaukee City Health Department
    '51': 15,  # North Shore Health Department
    '52': 13,  # Oak Creek Health Department
    '53': 14,  # South Milwaukee/St. Francis Health Department
    '54': None,  # Southwest Suburban Health Department
    '55': 16,  # Wauwatosa Health Department
    '56': 48,  # Monroe County Health Department
    '57': 49,  # Oconto County Health & Human Services Department, Public Health Division
    '58': 50,  # Oneida County Health Department
    '59': 7,  # Appleton City Health Department
    '60': 51,  # Outagamie County Health & Human Services
    '61': 52,  # Washington Ozaukee Public Health Department
    '62': 53,  # Pepin County Health Department
    '63': 75,  # Pierce County Public Health Department
    '64': 76,  # Polk County Health Department
    '65': 77,  # Portage County Health & Human Services
    '66': 78,  # Price County Health & Human Services
    '67': 11,  # City of Racine Public Health Department
    '68': 79,  # Racine County Public Health Division
    '69': 80,  # Richland County Health & Human Services
    '70': 81,  # Rock County Public Health Department
    '71': 82,  # Rusk County Health & Human Services
    '72': 83,  # Sauk County Health Department
    '73': 84,  # Sawyer County Health & Human Services
    '74': 66,  # Shawano-Menominee Counties Health Department
    '75': 85,  # Sheboygan County Health & Human Services
    '76': 54,  # St. Croix County Health & Human Services
    '77': 55,  # Taylor County Health Department
    '78': 56,  # Trempealeau County Health Department
    '79': 57,  # Vernon County Public Health Department
    '80': 58,  # Vilas County Public Health Department
    '81': 59,  # Walworth County Department of Health & Human Services
    '82': 60,  # Washburn County Health Department
    '83': 52,  # Washington Ozaukee Public Health Department
    '84': 61,  # Waukesha County Department of Health & Human Services
    '85': 62,  # Waupaca County Department of Public Health
    '86': 63,  # Waushara County Health Department
    '87': 7,  # Appleton City Health Department
    '88': 8,  # City of Menasha Health Department
    '89': 64,  # Winnebago County Health Department
    '90': 65,  # Wood County Health Department
}

# Maps tribal jurisdiction IDs to tribal nation names for boundary lookup
TRIBAL_BOUNDARY_MAPPING = {
    'T01': 'Bad River Band of Lake Superior Chippewa',
    'T02': 'Forest County Potawatomi Community',
    'T03': 'Ho-Chunk Nation',
    'T04': 'Lac Courte Oreilles Band of Lake Superior Chippewa',
    'T05': 'Lac du Flambeau Band of Lake Superior Chippewa',
    'T06': 'Menominee Indian Tribe of Wisconsin',
    'T07': 'Oneida Nation',
    'T08': 'Red Cliff Band of Lake Superior Chippewa',
    'T09': 'Sokaogon Chippewa Community',
    'T10': 'St. Croix Chippewa Indians of Wisconsin',
    'T11': 'Stockbridge-Munsee Community',
}


def get_boundary_objectid(jurisdiction_id: str) -> int | None:
    """Get the boundary file OBJECTID for a jurisdiction."""
    return JURISDICTION_TO_BOUNDARY_OBJECTID.get(jurisdiction_id)


def get_tribal_boundary_name(jurisdiction_id: str) -> str | None:
    """Get the tribal nation name for boundary lookup."""
    return TRIBAL_BOUNDARY_MAPPING.get(jurisdiction_id)


def is_tribal_jurisdiction(jurisdiction_id: str) -> bool:
    """Check if a jurisdiction ID is a tribal jurisdiction."""
    return jurisdiction_id.startswith('T')


def get_all_mapped_jurisdictions() -> list:
    """Get list of all jurisdiction IDs that have boundary mappings."""
    all_ids = list(JURISDICTION_TO_BOUNDARY_OBJECTID.keys())
    all_ids.extend(TRIBAL_BOUNDARY_MAPPING.keys())
    return all_ids
