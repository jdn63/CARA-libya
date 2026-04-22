"""Module for managing Wisconsin Public Health region data"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def get_ph_statistics(region_id: str) -> Dict:
    """
    Get detailed statistics for a Public Health region
    """
    # Static Public Health region data - in a real application, this would come from a database
    ph_data = {
        "PH 1": {
            "name": "Northern Region",
            "counties": ["Ashland", "Bayfield", "Florence", "Forest", "Iron", "Langlade", "Lincoln", "Marathon", "Oneida", "Portage", "Price", "Sawyer", "Taylor", "Vilas", "Wood"],
            "statistics": {
                "health_facilities": {
                    "hospitals": 12,
                    "clinics": 45,
                    "long_term_care": 28,
                    "public_health_offices": 15
                },
                "workforce": {
                    "physicians": 450,
                    "nurses": 2800,
                    "public_health_staff": 180,
                    "emergency_medical_staff": 320
                },
                "health_metrics": {
                    "vaccination_rate": 0.82,
                    "screening_rate": 0.75,
                    "response_readiness": 0.88,
                    "community_engagement": 0.90
                },
                "programs": {
                    "preventive_services": 35,
                    "health_education": 42,
                    "disease_surveillance": 15,
                    "community_outreach": 28
                }
            }
        },
        "PH 2": {
            "name": "Northeastern Region",
            "counties": ["Brown", "Calumet", "Door", "Fond du Lac", "Green Lake", "Kewaunee", "Manitowoc", "Marinette", "Marquette", "Menominee", "Oconto", "Outagamie", "Shawano", "Waupaca", "Waushara", "Winnebago"],
            "statistics": {
                "health_facilities": {
                    "hospitals": 15,
                    "clinics": 58,
                    "long_term_care": 35,
                    "public_health_offices": 18
                },
                "workforce": {
                    "physicians": 580,
                    "nurses": 3500,
                    "public_health_staff": 220,
                    "emergency_medical_staff": 420
                },
                "health_metrics": {
                    "vaccination_rate": 0.85,
                    "screening_rate": 0.78,
                    "response_readiness": 0.92,
                    "community_engagement": 0.88
                },
                "programs": {
                    "preventive_services": 42,
                    "health_education": 48,
                    "disease_surveillance": 18,
                    "community_outreach": 32
                }
            }
        },
        "PH 3": {
            "name": "Western Region",
            "counties": ["Barron", "Buffalo", "Burnett", "Chippewa", "Clark", "Douglas", "Dunn", "Eau Claire", "Jackson", "La Crosse", "Monroe", "Pepin", "Pierce", "Polk", "Rusk", "St. Croix", "Trempealeau", "Vernon", "Washburn"],
            "statistics": {
                "health_facilities": {
                    "hospitals": 18,
                    "clinics": 62,
                    "long_term_care": 38,
                    "public_health_offices": 20
                },
                "workforce": {
                    "physicians": 620,
                    "nurses": 3800,
                    "public_health_staff": 240,
                    "emergency_medical_staff": 460
                },
                "health_metrics": {
                    "vaccination_rate": 0.83,
                    "screening_rate": 0.76,
                    "response_readiness": 0.90,
                    "community_engagement": 0.92
                },
                "programs": {
                    "preventive_services": 45,
                    "health_education": 52,
                    "disease_surveillance": 20,
                    "community_outreach": 35
                }
            }
        },
        "PH 4": {
            "name": "Southern Region",
            "counties": ["Adams", "Columbia", "Crawford", "Dane", "Dodge", "Grant", "Green", "Iowa", "Jefferson", "Juneau", "Lafayette", "Richland", "Rock", "Sauk"],
            "statistics": {
                "health_facilities": {
                    "hospitals": 14,
                    "clinics": 52,
                    "long_term_care": 32,
                    "public_health_offices": 16
                },
                "workforce": {
                    "physicians": 520,
                    "nurses": 3200,
                    "public_health_staff": 200,
                    "emergency_medical_staff": 380
                },
                "health_metrics": {
                    "vaccination_rate": 0.87,
                    "screening_rate": 0.82,
                    "response_readiness": 0.91,
                    "community_engagement": 0.89
                },
                "programs": {
                    "preventive_services": 38,
                    "health_education": 45,
                    "disease_surveillance": 16,
                    "community_outreach": 30
                }
            }
        },
        "PH 5": {
            "name": "Southeastern Region",
            "counties": ["Kenosha", "Milwaukee", "Ozaukee", "Racine", "Walworth", "Washington", "Waukesha"],
            "statistics": {
                "health_facilities": {
                    "hospitals": 20,
                    "clinics": 75,
                    "long_term_care": 45,
                    "public_health_offices": 22
                },
                "workforce": {
                    "physicians": 850,
                    "nurses": 5200,
                    "public_health_staff": 280,
                    "emergency_medical_staff": 520
                },
                "health_metrics": {
                    "vaccination_rate": 0.88,
                    "screening_rate": 0.84,
                    "response_readiness": 0.94,
                    "community_engagement": 0.91
                },
                "programs": {
                    "preventive_services": 52,
                    "health_education": 58,
                    "disease_surveillance": 24,
                    "community_outreach": 40
                }
            }
        }
    }

    return ph_data.get(region_id, {})

def get_all_ph_regions() -> List[Dict]:
    """
    Get a list of all Public Health regions with basic information
    """
    regions = []
    for region_id in ["PH 1", "PH 2", "PH 3", "PH 4", "PH 5"]:
        data = get_ph_statistics(region_id)
        regions.append({
            "id": region_id,
            "name": data.get("name", ""),
            "counties": data.get("counties", [])
        })
    return regions
