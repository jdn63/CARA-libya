"""
WHO Libya Health Indicators Connector — via OCHA HDX

Data source: World Health Organization, via OCHA HDX
HDX dataset: who-data-for-lby (Libya - Health Indicators)
URL: https://data.humdata.org/dataset/who-data-for-lby
Last confirmed: April 15, 2026 (31 CSV files)
License: HDX Other (WHO terms, open for humanitarian use)

Why HDX instead of the WHO GHO OData API:
  The WHO GHO API returns Libya data with very old timestamps (physicians: 2008,
  TB: 1986, cholera: 1995). The HDX export, updated April 2026, contains
  current data from the same source. This connector uses the HDX thematic
  CSV files as the authoritative access path for Libya health indicators.

CSV files used:
  health_systems_indicators_lby.csv              — hospital beds per 10k
  tuberculosis_indicators_lby.csv                — TB incidence, treatment coverage
  child_mortality_indicators_lby.csv             — under-5, infant, neonatal mortality
  noncommunicable_diseases_indicators_lby.csv    — NCD mortality, obesity
  nutrition_indicators_lby.csv                   — stunting, anaemia
  air_pollution_indicators_lby.csv               — PM2.5, ambient air pollution deaths
  immunization_coverage_...indicators_lby.csv    — MCV1 measles vaccination coverage

Geographic level: National (Libya, iso3=LBY) — WHO does not publish
  subnational Libya data. Municipality fetch returns national figures
  with a documented proxy note.

INFORM Pillar mapping:
  Hazard & Exposure:
    - tb_incidence_per_100k        → epidemiological_hazard
    - air_pollution_mortality_rate → epidemiological_hazard / sandstorm risk
    - ncd_mortality_30_70_pct      → epidemiological_hazard (NCD burden)
  Vulnerability:
    - under5_mortality_rate        → health_unawareness (proxy)
    - measles_vaccination_pct      → health_unawareness (immunisation proxy)
    - stunting_prevalence_pct      → vulnerability (food security / child health)
  Coping Capacity:
    - hospital_beds_per_10k        → healthcare_access_gap
    - physicians_per_10k           → healthcare_access_gap
    - uhc_service_coverage_index   → healthcare_access_gap

Operation model: cache-first.
  refresh() downloads targeted CSV files from HDX to data/cache/who_hdx/
  fetch()   reads from local cache — never blocks on network.
"""

import csv
import io
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join('data', 'cache', 'who_hdx')

# HDX resource URLs for WHO Libya health indicator CSVs
# Using the stable HDX permalink format
HDX_DATASET_ID = '7882c7c4-d479-4c6f-b1c9-8b663fdb2365'

RESOURCE_URLS: Dict[str, str] = {
    'health_systems': (
        f'https://data.humdata.org/dataset/{HDX_DATASET_ID}'
        '/resource/b56f7a07-a9f2-4dbf-b6f5-3de6877b7840'
        '/download/health_systems_indicators_lby.csv'
    ),
    'tuberculosis': (
        f'https://data.humdata.org/dataset/{HDX_DATASET_ID}'
        '/resource/6864e652-8797-481a-a824-2bd273b85f45'
        '/download/tuberculosis_indicators_lby.csv'
    ),
    'child_mortality': (
        f'https://data.humdata.org/dataset/{HDX_DATASET_ID}'
        '/resource/ffab0086-61ff-4f04-98ff-7a93863ba904'
        '/download/child_mortality_indicators_lby.csv'
    ),
    'noncommunicable_diseases': (
        f'https://data.humdata.org/dataset/{HDX_DATASET_ID}'
        '/resource/4dbff725-c664-429f-9c6b-7fbbd733ff93'
        '/download/noncommunicable_diseases_indicators_lby.csv'
    ),
    'nutrition': (
        f'https://data.humdata.org/dataset/{HDX_DATASET_ID}'
        '/resource/19a90e57-b4cf-4819-904e-af6027f2fb9c'
        '/download/nutrition_indicators_lby.csv'
    ),
    'air_pollution': (
        f'https://data.humdata.org/dataset/{HDX_DATASET_ID}'
        '/resource/0c93d315-dfe5-46d7-b2a3-116c8b0dc327'
        '/download/air_pollution_indicators_lby.csv'
    ),
    'immunization': (
        f'https://data.humdata.org/dataset/{HDX_DATASET_ID}'
        '/resource/c9533fd5-dc5e-4cd0-969e-0cf2740b8ad5'
        '/download/immunization_coverage_and_vaccine_preventable_diseases_indicators_lby.csv'
    ),
}

# GHO indicator codes to extract and their output field names
# Format: gho_code → (output_key, description_en, description_ar)
INDICATOR_MAP: Dict[str, Tuple[str, str, str]] = {
    # Health systems (Coping Capacity)
    # Note: physicians_per_10k not in the downloaded WHO Libya thematic files;
    # hospital density codes (DEVICES00-05) are present but represent facility counts,
    # not the standard HWF physicians metric.
    'WHS6_102':          ('hospital_beds_per_10k',           'Hospital beds per 10,000 population',              'أسرة المستشفيات لكل 10,000 نسمة'),
    'DEVICES00':         ('hospital_density_per_100k',        'Hospital density per 100,000 population',          'كثافة المستشفيات لكل 100,000 نسمة'),
    # Tuberculosis (Hazard & Exposure)
    # MDG_0000000020 = "Incidence of tuberculosis (per 100,000 population per year)"
    'MDG_0000000020':    ('tb_incidence_per_100k',            'TB incidence per 100,000 population',              'معدل الإصابة بالسل لكل 100,000 نسمة'),
    'TB_1':              ('tb_treatment_coverage_pct',        'Tuberculosis treatment coverage (%)',               'تغطية علاج السل (%)'),
    'TB_c_new_tsr':      ('tb_treatment_success_pct',         'TB treatment success rate: new cases (%)',          'معدل نجاح علاج السل: الحالات الجديدة (%)'),
    # Child mortality (Vulnerability)
    'MDG_0000000007':    ('under5_mortality_rate',            'Under-5 mortality rate per 1,000 live births',     'معدل وفيات الأطفال دون 5 سنوات لكل 1,000 مولود حي'),
    'MDG_0000000001':    ('infant_mortality_rate',            'Infant mortality rate per 1,000 live births',      'معدل وفيات الرضع لكل 1,000 مولود حي'),
    'WHOSIS_000003':     ('neonatal_mortality_rate',          'Neonatal mortality rate per 1,000 live births',    'معدل وفيات حديثي الولادة لكل 1,000 مولود حي'),
    # NCD burden (Hazard & Exposure)
    'NCDMORT3070':       ('ncd_mortality_30_70_pct',          'NCD mortality probability age 30–70 (%)',           'احتمالية الوفاة بأمراض غير سارية (30-70 عاماً)'),
    'NCD_BMI_30C':       ('obesity_prevalence_pct',           'Obesity prevalence among adults (%)',               'معدل انتشار السمنة لدى البالغين (%)'),
    'NCD_PAA':           ('physical_inactivity_prevalence_pct','Prevalence of physical inactivity — adults (%)',   'انتشار الخمول البدني لدى البالغين (%)'),
    # Nutrition / Vulnerability
    'NUTSTUNTINGPREV':   ('stunting_prevalence_pct',          'Stunting prevalence under-5 (%)',                   'معدل انتشار التقزم لدى الأطفال دون 5 سنوات (%)'),
    'NUTRITION_ANAEMIA_CHILDREN_PREV': ('anaemia_children_prevalence_pct', 'Anaemia prevalence in children 6–59 months (%)', 'معدل انتشار الأنيميا لدى الأطفال 6-59 شهراً (%)'),
    # Air pollution (Hazard & Exposure)
    # AIR_42 = "Ambient air pollution attributable death rate (per 100,000, age-standardised)"
    'AIR_42':            ('air_pollution_mortality_per_100k', 'Air pollution attributable death rate per 100,000', 'معدل الوفيات المنسوبة لتلوث الهواء لكل 100,000'),
    'SDGPM25':           ('pm25_annual_mean_ugm3',            'Annual mean PM2.5 concentration (μg/m³)',           'متوسط تركيز PM2.5 السنوي (ميكروجرام/م³)'),
    # Vaccination (Vulnerability — health awareness proxy)
    # WHS8_110 = MCV1 (Measles 1st dose coverage among 1-year-olds)
    'WHS8_110':          ('measles_vaccination_pct',          'Measles (MCV1) vaccination coverage (%)',           'تغطية التطعيم ضد الحصبة — الجرعة الأولى (%)'),
    'MCV2':              ('measles_2nd_dose_vaccination_pct', 'Measles (MCV2) vaccination 2nd dose coverage (%)',  'تغطية التطعيم ضد الحصبة — الجرعة الثانية (%)'),
}


class WHOHDXConnector(BaseConnector):
    """
    WHO Libya Health Indicators connector via OCHA HDX.

    Downloads thematic CSV files from the WHO Libya HDX export and parses
    them into a standardised indicator dictionary. All indicators are
    national-level; municipalities receive national figures as a documented proxy.

    Compared to the WHO GHO OData API connector (who_gho_connector.py),
    this connector provides more current Libya data (April 2026 vs. 2008–2018
    vintage from the API) and covers more indicators in a single refresh call.
    """

    CACHE_DURATION_SECONDS = 3600 * 24 * 30   # 30 days (monthly refresh)

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._indicators: Dict[str, Any] = {}
        self._cache_loaded = False
        self._last_refresh: Optional[str] = None
        os.makedirs(CACHE_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Return WHO health indicators for Libya.
        All data is national; municipality requests include a proxy note.
        """
        cache_key = f'who_hdx_{jurisdiction_id}'
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self._cache_loaded:
            self._load_from_disk()

        if not self._indicators:
            result = self._unavailable_response(
                'لا تتوفر بيانات منظمة الصحة العالمية من HDX. / '
                'No WHO HDX health data in cache. '
                f'Run scheduled refresh. Cache: {CACHE_DIR}/'
            )
        else:
            is_national = (jurisdiction_id in ('LY', 'LBY'))
            payload: Dict[str, Any] = {**self._indicators}

            if not is_national:
                payload['_geographic_proxy'] = 'national_average'
                payload['_proxy_note'] = (
                    'بيانات الصحة من منظمة الصحة العالمية متاحة على المستوى الوطني فقط — '
                    'يُستخدم المتوسط الوطني كبديل موثق لجميع البلديات. / '
                    'WHO health data available at national level only — '
                    'national figures applied to all municipalities as documented proxy.'
                )

            payload['_last_updated'] = self._last_refresh
            result = self._wrap(payload)

        self._cache[cache_key] = result
        return result

    def is_available(self) -> bool:
        if not os.path.isdir(CACHE_DIR):
            return False
        return any(f.endswith('.csv') for f in os.listdir(CACHE_DIR))

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'WHO Libya Health Indicators (via OCHA HDX)',
            'name_ar': 'مؤشرات الصحة لليبيا — منظمة الصحة العالمية عبر منصة HDX',
            'url': 'https://data.humdata.org/dataset/who-data-for-lby',
            'update_frequency': 'monthly_auto',
            'license': 'HDX Other (WHO open data)',
            'geographic_coverage': 'Libya — national level',
            'access_method': 'hdx_csv_cached',
            'cache_dir': CACHE_DIR,
            'notes': (
                'WHO Libya health indicators downloaded from OCHA HDX. '
                'Covers health systems capacity, tuberculosis, child mortality, '
                'NCD burden, nutrition, air pollution, and vaccination coverage. '
                'More current than the WHO GHO OData API for Libya specifically. '
                'Data is national-level only — no subnational WHO data exists for Libya.'
            ),
        }

    # ------------------------------------------------------------------
    # Scheduled refresh
    # ------------------------------------------------------------------

    def refresh(self) -> Dict[str, Any]:
        """
        Download fresh WHO Libya CSV files from OCHA HDX.
        Called by APScheduler (monthly global connector refresh job).
        """
        summary: Dict[str, Any] = {
            'files_attempted': 0,
            'files_ok': 0,
            'indicators_parsed': 0,
            'errors': [],
            'timestamp': datetime.utcnow().isoformat(),
        }

        for key, url in RESOURCE_URLS.items():
            summary['files_attempted'] += 1
            raw = self._download(url)
            if raw is None:
                summary['errors'].append(f'{key}: download failed')
                continue
            cache_file = os.path.join(CACHE_DIR, f'{key}.csv')
            with open(cache_file, 'wb') as f:
                f.write(raw)
            summary['files_ok'] += 1
            logger.info(f'WHO HDX: downloaded {key}.csv ({len(raw)} bytes)')

        # Reload in-memory
        self._indicators = {}
        self._cache_loaded = False
        self._cache = {}
        self._load_from_disk()
        summary['indicators_parsed'] = len(self._indicators)

        logger.info(
            f"WHO HDX refresh: {summary['files_ok']}/{summary['files_attempted']} files, "
            f"{summary['indicators_parsed']} indicators parsed"
        )
        return summary

    # ------------------------------------------------------------------
    # Disk cache loading
    # ------------------------------------------------------------------

    def _load_from_disk(self):
        self._cache_loaded = True
        latest_mtime = 0.0

        for key in RESOURCE_URLS:
            filepath = os.path.join(CACHE_DIR, f'{key}.csv')
            if os.path.exists(filepath):
                try:
                    count = self._parse_who_csv(filepath)
                    logger.info(f'WHO HDX: parsed {count} rows from {key}.csv')
                    latest_mtime = max(latest_mtime, os.path.getmtime(filepath))
                except Exception as e:
                    logger.error(f'WHO HDX: failed to parse {key}.csv: {e}')

        if latest_mtime > 0:
            self._last_refresh = datetime.fromtimestamp(latest_mtime).isoformat()

    def _parse_who_csv(self, filepath: str) -> int:
        """
        Parse a WHO HDX CSV file.
        Format: GHO (CODE), GHO (DISPLAY), ..., YEAR (DISPLAY), ..., Numeric, Low, High, Comments
        Extracts the most recent value for each indicator in INDICATOR_MAP.
        """
        count = 0
        # Track best (most recent) year per indicator code
        best: Dict[str, Tuple[int, float]] = {}   # code → (year, value)

        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get('GHO (CODE)', '').strip()
                if code not in INDICATOR_MAP:
                    continue

                # Try to parse year
                year_str = row.get('YEAR (DISPLAY)', '').strip()
                # Year display may be "2020" or "2018-2020" — take the last 4-digit year
                year = 0
                for token in reversed(year_str.replace('–', '-').split('-')):
                    token = token.strip()
                    if token.isdigit() and len(token) == 4:
                        year = int(token)
                        break

                # Skip sex/age disaggregations — take BTSX / total rows only
                sex = row.get('SEX (CODE)', '').strip().upper()
                age = row.get('AGEGROUP (CODE)', '').strip().upper()
                if sex and sex not in ('BTSX', ''):
                    continue
                if age and age not in ('ALLAGE', 'ALL', ''):
                    continue

                numeric_str = row.get('Numeric', '').strip()
                if not numeric_str:
                    continue
                try:
                    value = float(numeric_str)
                except (ValueError, TypeError):
                    continue

                existing = best.get(code)
                if existing is None or year > existing[0]:
                    best[code] = (year, value)
                    count += 1

        # Convert to output fields
        for code, (year, value) in best.items():
            output_key, desc_en, desc_ar = INDICATOR_MAP[code]
            self._indicators[output_key] = value
            self._indicators[f'{output_key}_year'] = year
            self._indicators[f'{output_key}_label_en'] = desc_en
            self._indicators[f'{output_key}_label_ar'] = desc_ar

        return count

    def indicators_summary(self) -> List[Dict[str, Any]]:
        """Return a human-readable list of parsed indicators — for display in the UI."""
        if not self._cache_loaded:
            self._load_from_disk()
        rows = []
        for code, (output_key, desc_en, desc_ar) in INDICATOR_MAP.items():
            value = self._indicators.get(output_key)
            year = self._indicators.get(f'{output_key}_year')
            rows.append({
                'gho_code': code,
                'output_key': output_key,
                'description_en': desc_en,
                'description_ar': desc_ar,
                'value': value,
                'year': year,
                'available': value is not None,
            })
        return sorted(rows, key=lambda r: (not r['available'], r['output_key']))

    def _download(self, url: str, timeout: int = 30) -> Optional[bytes]:
        import urllib.request
        import urllib.error
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Libya-CARA/1.0 (WHO health data via HDX)'}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            logger.warning(f'WHO HDX download failed ({url}): {e}')
            return None
