"""Registry of local-agency data-entry domains for Libya CARA.

Each :class:`DomainSpec` declares everything the generic template builder,
upload validator, consolidator and export workbook need in order to handle
a domain end-to-end:

* the bilingual page copy and the INFORM pillar it feeds,
* the ordered list of :class:`Indicator` columns (each indicator carries its
  own unit and validation bounds, so percentages, rates per 100 000 and
  micrograms per cubic metre can coexist in the same workbook),
* an optional ``group`` per indicator that allows the HTML table and Excel
  header to render a two-row colspan (used for cleanly nested grids such as
  HIV / HBV / HCV / TB × incidence / morbidity / mortality).

Adding a new domain is therefore a pure-data change: append a new
``DomainSpec`` to :data:`DOMAINS` — no template, route or pipeline edits
required.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Indicator:
    """A single numeric column in a domain's data-entry workbook."""

    code: str
    """Snake-case identifier, unique within the domain. Used as the column key
    in the workbook and as the dict key in :class:`ConsolidatedRow.metrics`."""

    name_ar: str
    name_en: str
    unit_ar: str
    unit_en: str

    group_ar: str | None = None
    """Optional group label (Arabic). Indicators that share the same
    ``group_ar`` are rendered under a merged colspan header in both the
    HTML comparison table and the Excel template."""
    group_en: str | None = None

    min_value: float = 0.0
    max_value: float | None = None
    """Upper bound for spreadsheet validation. ``None`` means unbounded
    (typical for rates per 100k); set to ``100`` for percentages."""


@dataclass(frozen=True)
class DomainSpec:
    """All metadata for one workshop data-entry domain."""

    key: str                          # URL slug, e.g. "infectious-disease"
    name_ar: str
    name_en: str
    nav_ar: str                       # short label for the nav menu
    nav_en: str
    icon: str                         # full Font-Awesome class, e.g. "fas fa-virus"

    inform_pillar_ar: str             # e.g. "ركيزة المخاطر والتعرض"
    inform_pillar_en: str
    inform_role_ar: str               # one-sentence explanation
    inform_role_en: str

    description_ar: str
    description_en: str

    indicators: tuple[Indicator, ...] = field(default_factory=tuple)

    sheet_title: str = ""
    """Short English label used as the worksheet name inside the Libya CARA
    Master Template workbook. Must be unique across domains and at most 31
    characters (Excel limit). Defaults to ``nav_en`` if left blank."""

    # ----- convenience -----
    def column_keys(self) -> list[str]:
        return [i.code for i in self.indicators]

    def has_groups(self) -> bool:
        return any(i.group_ar for i in self.indicators)

    def resolved_sheet_title(self) -> str:
        return (self.sheet_title or self.nav_en)[:31]


# --------------------------------------------------------------------------- #
# Helpers used to keep domain definitions readable
# --------------------------------------------------------------------------- #

_RATE_AR = "حالات لكل 100 ألف"
_RATE_EN = "per 100k"
_NEW_RATE_AR = "حالات جديدة لكل 100 ألف"
_NEW_RATE_EN = "new cases per 100k"
_DEATH_RATE_AR = "وفيات لكل 100 ألف"
_DEATH_RATE_EN = "deaths per 100k"
_PCT_AR = "نسبة مئوية"
_PCT_EN = "%"


def _disease_grid(prefix: str,
                  group_ar: str, group_en: str) -> tuple[Indicator, ...]:
    """Standard incidence / morbidity / mortality grid used by communicable
    disease domains (infectious + vector-borne)."""
    return (
        Indicator(
            code=f"{prefix}_incidence",
            group_ar=group_ar, group_en=group_en,
            name_ar="معدل الانتشار", name_en="Incidence",
            unit_ar=_NEW_RATE_AR, unit_en=_NEW_RATE_EN,
        ),
        Indicator(
            code=f"{prefix}_morbidity",
            group_ar=group_ar, group_en=group_en,
            name_ar="معدل المرضية", name_en="Morbidity",
            unit_ar="حالات نشطة لكل 100 ألف", unit_en="active cases per 100k",
        ),
        Indicator(
            code=f"{prefix}_mortality",
            group_ar=group_ar, group_en=group_en,
            name_ar="معدل الوفيات", name_en="Mortality",
            unit_ar=_DEATH_RATE_AR, unit_en=_DEATH_RATE_EN,
        ),
    )


def _ncd_grid(prefix: str,
              group_ar: str, group_en: str) -> tuple[Indicator, ...]:
    """Prevalence / morbidity / mortality grid used by NCD conditions."""
    return (
        Indicator(
            code=f"{prefix}_prevalence",
            group_ar=group_ar, group_en=group_en,
            name_ar="معدل الانتشار", name_en="Prevalence",
            unit_ar="نسبة مئوية من البالغين",
            unit_en="% of adults (18+)",
            max_value=100.0,
        ),
        Indicator(
            code=f"{prefix}_morbidity",
            group_ar=group_ar, group_en=group_en,
            name_ar="حالات نشطة مُتابَعة", name_en="Active cases under care",
            unit_ar=_RATE_AR, unit_en=_RATE_EN,
        ),
        Indicator(
            code=f"{prefix}_mortality",
            group_ar=group_ar, group_en=group_en,
            name_ar="معدل الوفيات", name_en="Mortality",
            unit_ar=_DEATH_RATE_AR, unit_en=_DEATH_RATE_EN,
        ),
    )


# --------------------------------------------------------------------------- #
# Domain definitions
# --------------------------------------------------------------------------- #

INFECTIOUS_DISEASE = DomainSpec(
    sheet_title="Infectious Disease",
    key="infectious-disease",
    name_ar="بيانات الأمراض المعدية",
    name_en="Infectious Disease Data",
    nav_ar="الأمراض المعدية",
    nav_en="Infectious Disease",
    icon="fas fa-virus",
    inform_pillar_ar="ركيزة المخاطر والتعرض — المخاطر الوبائية",
    inform_pillar_en="Hazard & Exposure pillar — Epidemiological hazard",
    inform_role_ar=(
        "تُغذّي البيانات المؤشّر الفرعي «المخاطر الوبائية» في ركيزة "
        "المخاطر والتعرض ضمن مؤشر INFORM."
    ),
    inform_role_en=(
        "Feeds the Epidemiological Hazard sub-indicator in the INFORM "
        "Hazard & Exposure pillar."
    ),
    description_ar=(
        "تتيح هذه الصفحة للجهات المحلية المشاركة في الاستجابة (مديريات "
        "الصحة، المركز الوطني لمكافحة الأمراض، المنظمات غير الحكومية "
        "الصحية) رفع بيانات الأمراض المعدية على مستوى البلدية."
    ),
    description_en=(
        "Local response agencies (health offices, NCDC, health NGOs) use "
        "this page to upload municipal-level infectious-disease data."
    ),
    indicators=(
        *_disease_grid("hiv", "فيروس نقص المناعة البشرية", "HIV"),
        *_disease_grid("hbv", "التهاب الكبد الفيروسي بي", "HBV (Hepatitis B)"),
        *_disease_grid("hcv", "التهاب الكبد الفيروسي سي", "HCV (Hepatitis C)"),
        *_disease_grid("tb",  "السل",                       "TB (Tuberculosis)"),
    ),
)


VECTOR_BORNE = DomainSpec(
    sheet_title="Vector-Borne Disease",
    key="vector-borne-disease",
    name_ar="الأمراض المنقولة بالنواقل",
    name_en="Vector-Borne Disease Data",
    nav_ar="الأمراض المنقولة بالنواقل",
    nav_en="Vector-Borne Disease",
    icon="fas fa-mosquito",
    inform_pillar_ar="ركيزة المخاطر والتعرض — المخاطر الوبائية",
    inform_pillar_en="Hazard & Exposure pillar — Epidemiological hazard",
    inform_role_ar=(
        "تُكمّل بيانات الأمراض المعدية برصد الأمراض المنقولة بالنواقل، "
        "وتُغذّي مؤشر «المخاطر الوبائية» في INFORM."
    ),
    inform_role_en=(
        "Complements the infectious-disease feed by tracking vector-borne "
        "illnesses for the INFORM Epidemiological Hazard sub-indicator."
    ),
    description_ar=(
        "تَرصد هذه الصفحة الأمراض المنقولة بالنواقل (الملاريا، حمى الضنك، "
        "الليشمانيا) على مستوى البلدية. الملاريا تُسجَّل في الغالب كحالات "
        "وافدة، أمّا الليشمانيا (الجلدية والحشوية) فهي مستوطنة في عدة "
        "مناطق ليبية."
    ),
    description_en=(
        "Tracks vector-borne illnesses (malaria, dengue, leishmaniasis) at "
        "the municipal level. Malaria is mostly imported in Libya, while "
        "cutaneous and visceral leishmaniasis are endemic in several "
        "regions."
    ),
    indicators=(
        *_disease_grid("malaria",      "الملاريا",        "Malaria"),
        *_disease_grid("dengue",       "حمى الضنك",       "Dengue"),
        *_disease_grid("leishmaniasis","داء الليشمانيات", "Leishmaniasis"),
    ),
)


NCDS = DomainSpec(
    sheet_title="NCDs",
    key="ncds",
    name_ar="الأمراض غير السارية",
    name_en="Non-Communicable Diseases (NCDs)",
    nav_ar="الأمراض غير السارية",
    nav_en="NCDs",
    icon="fas fa-heart-pulse",
    inform_pillar_ar="ركيزة قابلية التأثّر — صحة السكان",
    inform_pillar_en="Vulnerability pillar — Population health",
    inform_role_ar=(
        "ترفع نسبة سكان البلدية المصابين بأمراض مزمنة من قابلية التأثّر "
        "أمام الكوارث (موجات الحر، انقطاع الأدوية، تعطّل الخدمات)، "
        "وتُغذّي ركيزة «قابلية التأثّر» في INFORM."
    ),
    inform_role_en=(
        "A higher prevalence of chronic disease raises a municipality's "
        "vulnerability to shocks (heat waves, medication interruptions, "
        "service disruption); feeds the INFORM Vulnerability pillar."
    ),
    description_ar=(
        "تَرصد هذه الصفحة عبء الأمراض المزمنة الأربعة الكبرى (السكري، "
        "ارتفاع ضغط الدم، أمراض القلب والأوعية، السرطان) لكل بلدية. "
        "الانتشار يُسجَّل كنسبة من البالغين، أمّا الحالات النشطة والوفيات "
        "فلكل 100 ألف نسمة."
    ),
    description_en=(
        "Captures the burden of the four major chronic conditions "
        "(diabetes, hypertension, cardiovascular disease, cancer) per "
        "municipality. Prevalence is reported as a percentage of adults; "
        "active cases and mortality use rates per 100 000 population."
    ),
    indicators=(
        *_ncd_grid("diabetes",     "السكري",                  "Diabetes"),
        *_ncd_grid("hypertension", "ارتفاع ضغط الدم",         "Hypertension"),
        *_ncd_grid("cvd",          "أمراض القلب والأوعية",    "Cardiovascular disease"),
        *_ncd_grid("cancer",       "السرطان (جميع الأنواع)",  "Cancer (all sites)"),
    ),
)


MNCH = DomainSpec(
    sheet_title="Maternal and Child Health",
    key="maternal-child-health",
    name_ar="صحة الأم والطفل",
    name_en="Maternal, Newborn & Child Health (MNCH)",
    nav_ar="صحة الأم والطفل",
    nav_en="Maternal & Child Health",
    icon="fas fa-baby",
    inform_pillar_ar="ركيزة قابلية التأثّر — الفئات الهشّة",
    inform_pillar_en="Vulnerability pillar — Vulnerable groups",
    inform_role_ar=(
        "ارتفاع وفيات الأمهات والمواليد وانخفاض تغطية التطعيم يَعكس ضعف "
        "النظام الصحي ويرفع قابلية التأثّر في مؤشر INFORM."
    ),
    inform_role_en=(
        "High maternal and neonatal mortality together with low "
        "immunization coverage signal a weak health system and raise the "
        "INFORM Vulnerability score."
    ),
    description_ar=(
        "مؤشّرات صحة الأم والطفل المُجمَّعة من السجلات المحلية للولادات "
        "والمراكز الصحية الأولية. الوحدات تختلف بحسب المؤشر — راجع "
        "وحدة كل عمود."
    ),
    description_en=(
        "Maternal and child-health indicators consolidated from local "
        "birth registries and primary health-care centres. Units vary by "
        "indicator — see the unit shown in each column header."
    ),
    indicators=(
        Indicator(
            code="maternal_mortality_ratio",
            name_ar="نسبة وفيات الأمهات",
            name_en="Maternal mortality ratio",
            unit_ar="وفاة لكل 100 ألف ولادة حية",
            unit_en="per 100 000 live births",
        ),
        Indicator(
            code="neonatal_mortality_rate",
            name_ar="معدل وفيات حديثي الولادة",
            name_en="Neonatal mortality rate",
            unit_ar="وفاة لكل ألف ولادة حية",
            unit_en="per 1 000 live births",
        ),
        Indicator(
            code="under5_mortality_rate",
            name_ar="معدل وفيات الأطفال دون الخامسة",
            name_en="Under-5 mortality rate",
            unit_ar="وفاة لكل ألف ولادة حية",
            unit_en="per 1 000 live births",
        ),
        Indicator(
            code="skilled_birth_attendance_pct",
            name_ar="نسبة الولادات بإشراف كادر مؤهَّل",
            name_en="Skilled birth attendance",
            unit_ar=_PCT_AR, unit_en=_PCT_EN, max_value=100.0,
        ),
        Indicator(
            code="antenatal_visits4_pct",
            name_ar="نسبة الحوامل اللواتي أَكملن 4 زيارات سابقة للولادة",
            name_en="Pregnancies with 4+ antenatal visits",
            unit_ar=_PCT_AR, unit_en=_PCT_EN, max_value=100.0,
        ),
        Indicator(
            code="dpt3_immunization_pct",
            name_ar="تغطية التطعيم الثلاثي البكتيري (DPT3) للأطفال 12-23 شهراً",
            name_en="DPT3 immunization coverage (children 12–23 months)",
            unit_ar=_PCT_AR, unit_en=_PCT_EN, max_value=100.0,
        ),
    ),
)


ENVIRONMENTAL_HEALTH = DomainSpec(
    sheet_title="Environmental Health",
    key="environmental-health",
    name_ar="الصحة البيئية والخدمات الأساسية",
    name_en="Environmental Health & Basic Services",
    nav_ar="الصحة البيئية",
    nav_en="Environmental Health",
    icon="fas fa-leaf",
    inform_pillar_ar="ركيزة نقص القدرة على المواجهة — البنية التحتية",
    inform_pillar_en="Lack of Coping Capacity pillar — Infrastructure",
    inform_role_ar=(
        "ضعف الوصول إلى المياه والصرف الصحي والكهرباء، وتدنّي جودة الهواء، "
        "تَرفع مؤشر «نقص القدرة على المواجهة» في INFORM وتُضعف الاستجابة "
        "أمام الكوارث."
    ),
    inform_role_en=(
        "Limited access to water, sanitation and electricity together with "
        "poor air quality raise the INFORM Lack of Coping Capacity score "
        "and weaken disaster response."
    ),
    description_ar=(
        "تُجمَّع البيانات من بلديات وشركات المياه والصرف الصحي ومحطات "
        "رصد جودة الهواء. اترك الخلية فارغة عند عدم توفّر المؤشر بدلاً "
        "من كتابة الصفر."
    ),
    description_en=(
        "Data are aggregated from municipal services, water and sanitation "
        "utilities and air-quality monitoring stations. Leave a cell empty "
        "if the indicator is unavailable rather than entering zero."
    ),
    indicators=(
        Indicator(
            code="improved_water_pct",
            name_ar="نسبة السكان مع وصول إلى مياه شرب محسّنة",
            name_en="Population with access to improved drinking water",
            unit_ar=_PCT_AR, unit_en=_PCT_EN, max_value=100.0,
        ),
        Indicator(
            code="improved_sanitation_pct",
            name_ar="نسبة السكان مع وصول إلى صرف صحي محسّن",
            name_en="Population with access to improved sanitation",
            unit_ar=_PCT_AR, unit_en=_PCT_EN, max_value=100.0,
        ),
        Indicator(
            code="electricity_access_pct",
            name_ar="نسبة الأسر مع كهرباء مستقرّة (≥18 ساعة يومياً)",
            name_en="Households with reliable electricity (≥18 h/day)",
            unit_ar=_PCT_AR, unit_en=_PCT_EN, max_value=100.0,
        ),
        Indicator(
            code="safe_waste_disposal_pct",
            name_ar="نسبة النفايات الصلبة المُعالَجة بشكل آمن",
            name_en="Solid waste safely disposed of",
            unit_ar=_PCT_AR, unit_en=_PCT_EN, max_value=100.0,
        ),
        Indicator(
            code="pm25_annual_avg",
            name_ar="متوسط تركيز الجسيمات الدقيقة (PM2.5) السنوي",
            name_en="Annual mean PM2.5 concentration",
            unit_ar="ميكروغرام لكل متر مكعب",
            unit_en="µg/m³",
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Public registry
# --------------------------------------------------------------------------- #

DOMAINS: tuple[DomainSpec, ...] = (
    INFECTIOUS_DISEASE,
    VECTOR_BORNE,
    NCDS,
    MNCH,
    ENVIRONMENTAL_HEALTH,
)

_BY_KEY: dict[str, DomainSpec] = {d.key: d for d in DOMAINS}


def get_domain(key: str) -> DomainSpec | None:
    """Return the :class:`DomainSpec` with this URL slug, or ``None``."""
    return _BY_KEY.get(key)


def all_domains() -> tuple[DomainSpec, ...]:
    return DOMAINS
