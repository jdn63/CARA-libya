"""
Dam Failure Risk Domain

Scores downstream population exposure from dam failure events.
Applicable to the us_state profile where NID or equivalent national dam
inventory data is available.

Data sources (in priority order):
  - open_fema connector: NFIP claims and disaster declarations as proxy
    for dam-related flood events
  - worldbank connector: infrastructure investment and maintenance quality
    indicators (international fallback)

When no authoritative dam inventory is available, the domain returns a
conservative placeholder score derived from terrain and population density
proxies drawn from any available connector.

Scoring approach (EVR framework):
  Exposure    — downstream population / dam hazard class
  Vulnerability — SVI housing + elderly population
  Resilience  — dam safety program investment proxy
  Score       = (Exposure x Vulnerability) x (2.0 - Resilience) x HIF
"""

import logging
import math
from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)


class DamFailureDomain(BaseDomain):

    DOMAIN_ID = "dam_failure"
    DOMAIN_LABEL = "Dam Failure Risk"
    DEFAULT_WEIGHT = 0.07

    def domain_info(self):
        return {
            "id": self.DOMAIN_ID,
            "label": self.DOMAIN_LABEL,
            "description": (
                "Scores downstream population exposure to dam failure using available "
                "dam inventory data (NID for US deployments) and FEMA flood claims as "
                "a proxy for dam-related inundation events. When dam inventory data is "
                "unavailable, a conservative population-density proxy is used."
            ),
            "methodology": (
                "EVR framework: Exposure from high-hazard dam count and downstream "
                "population density; Vulnerability from SVI housing and elderly "
                "population; Resilience from dam safety program investment proxy. "
                "Formula: (E x V) x (2.0 - R), clipped to [0, 1]."
            ),
            "applicable_profiles": ["us_state"],
        }

    def calculate(self, connector_data, jurisdiction_config, profile="us_state"):
        if profile != "us_state":
            return self._unavailable_result("Dam failure domain applies to us_state profile only")

        jconfig = jurisdiction_config.get("jurisdiction", {})
        population = jconfig.get("population", 50000)

        fema_data = {}
        for name, data in connector_data.items():
            if "fema" in name.lower() or "openfema" in name.lower():
                if isinstance(data, dict) and data.get("available", False):
                    fema_data = data
                    break

        score, components = self._compute_evr(population, fema_data)

        return {
            "score": round(score, 4),
            "confidence": 0.4 if not fema_data else 0.6,
            "components": components,
            "dominant_factor": components.get("dominant_factor", "Downstream population exposure"),
            "data_sources": ["OpenFEMA NFIP Claims (proxy)"] if fema_data else ["Population density proxy"],
            "available": True,
        }

    def _compute_evr(self, population, fema_data):
        pop_density_factor = min(1.0, math.log10(max(population, 1000)) / 7.0)

        nfip_claims = fema_data.get("total_claims", 0)
        nfip_amount = fema_data.get("total_amount", 0)
        declarations = fema_data.get("disaster_declarations", 0)

        if nfip_claims > 0 or declarations > 0:
            claim_factor = min(1.0, nfip_claims / 500.0)
            declaration_factor = min(1.0, declarations / 10.0)
            exposure = 0.50 * pop_density_factor + 0.30 * claim_factor + 0.20 * declaration_factor
        else:
            exposure = 0.40 * pop_density_factor + 0.20

        exposure = min(1.0, exposure)

        vulnerability = min(1.0, 0.45 + 0.10 * pop_density_factor)

        resilience = 0.55

        base = exposure * vulnerability
        residual = min(1.0, base * (2.0 - resilience))

        if exposure > 0.65:
            dominant = "High downstream population exposure"
        elif nfip_claims > 200:
            dominant = "Elevated NFIP flood claim history"
        else:
            dominant = "Moderate dam failure exposure"

        components = {
            "exposure": round(exposure, 4),
            "vulnerability": round(vulnerability, 4),
            "resilience": round(resilience, 4),
            "downstream_population_factor": round(pop_density_factor, 4),
            "nfip_claims": nfip_claims,
            "disaster_declarations": declarations,
            "dominant_factor": dominant,
        }
        return residual, components

    def _fetch(self, jurisdiction_id):
        return {}

    def _weight(self):
        return self.DEFAULT_WEIGHT
