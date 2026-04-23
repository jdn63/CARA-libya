"""
Libya CARA — Action Plan Guidance Content
Aligned to Sendai Framework (2015-2030) and UN Cluster System.

Research basis (April 2026):
- WHO EMRO Libya results report 2024-2025
- IOM Libya Crisis Response Plan 2025-2026 (Dec 2025 revision, $86.3M, 430k targeted)
- IOM DRR & Climate Change Adaptation Brief (Dec 2024)
- WHO Strategic Partnership for Health Security (SPH) portal — Libya JEE/NAPHS/SPAR records
- Science Advances: "Anatomy of a foreseeable disaster: Lessons from the 2023 dam-breaching
  flood in Derna, Libya" (2024)
- OCHA Libya Humanitarian Profile 2025 (823,000 people in need; 248,000 children)
- IHR/JEE Libya 2018 (1st edition); 2nd JEE in pipeline (scheduled Aug 2025)
- NAPHS Libya conducted July 2018; SPAR submitted 2024; AAR June 2024
- Libya One Health Platform — launched January 2025 (WHO-backed, FAO, WOAH)
- Think Global Health: "Rebuilding Libya's Health-Care System" (Nov 2023)
- UN Security Council Monthly Forecasts Feb/Apr 2026 (dual-government GNU/GNS context)
- Human Rights Watch: "Libya: Slow Flood Recovery Failing Displaced Survivors" (Sep 2024)
- Telemedicine Initiative for Libya (TI4L) — active
- IOM DTM Libya displacement tracking

Key contextual constraints for all strategies:
1. DUAL GOVERNANCE — GNU (Tripoli/west, UN-recognised) vs GNS (east/Benghazi); two
   health ministries; cross-front coordination is possible but complex.
2. MUNICIPALITY-LEVEL ENTRY POINT — more feasible than national given split governance;
   municipal councils active in both GNU and GNS zones.
3. WORKFORCE CRISIS — severe brain drain since 2011; ~100k foreign workers fled;
   rely on international partners (WHO EMTs, diaspora networks, TI4L) for specialist surge.
4. INFRASTRUCTURE FRAGILITY — constant power outages affect cold chains & ICUs;
   97 public hospitals (many damaged); Great Man-Made River (GMR) aging.
5. POPULATION IN MOTION — 147,000 IDPs (Feb 2024); 867,000+ migrants in Libya;
   unvaccinated populations create outbreak corridors.
6. CLIMATE ACCELERATION — ranked 40th INFORM; 3rd-last ND-GAIN climate index;
   temps >50°C recorded; wadi flooding recurring since 2018; Derna 2023 as sentinel event.

Each entry key matches an INFORM component key from the pillar domain modules.
Structure per entry:
    label_ar / label_en  — display name
    pillar_ar / pillar_en — INFORM pillar
    icon                 — Bootstrap icon class
    sendai_priority      — integer 1-4
    sendai_ar / sendai_en — Sendai priority name
    cluster_ar / cluster_en — responsible UN cluster(s)
    gov_ar / gov_en      — Libyan government counterpart
    actions              — list of {term_ar, term_en, items: [(ar, en), ...]}
"""

def get_action_domains(pillar_data, min_score=0.0):
    """Return enriched list of action domains from ACTION_GUIDANCE.

    Each domain is augmented with:
        key         — dict key string
        pillar_key  — 'hazard' | 'vulnerability' | 'coping'
        score       — 0-1 INFORM pillar score (for colour coding)
        score_10    — 0-10 display score
        level       — risk level string from classify_risk()

    Domains are sorted by pillar order, then Sendai priority ascending.
    min_score is currently unused (all domains are returned) because
    comprehensive preparedness planning is appropriate regardless of scores.
    """
    from utils.risk_engine import classify_risk

    # Map INFORM pillar label_en to pillar key and pillar_data slot
    _pillar_map = {
        'Hazard & Exposure':      ('hazard',        'hazard'),
        'Vulnerability':          ('vulnerability', 'vulnerability'),
        'Lack of Coping Capacity':('coping',        'coping'),
    }
    _pillar_order = {'hazard': 0, 'vulnerability': 1, 'coping': 2}

    enriched = []
    for key, d in ACTION_GUIDANCE.items():
        pillar_label = d.get('pillar_en', '')
        pillar_key, data_key = _pillar_map.get(
            pillar_label, ('hazard', 'hazard')
        )

        # Pull score from pillar data; fall back gracefully
        pillar_block = pillar_data.get(data_key, {})
        raw_score = pillar_block.get('score', 0.0) if isinstance(pillar_block, dict) else 0.0
        # INFORM scores come in as 0-10; normalise to 0-1 for colour helpers
        score_01 = raw_score / 10.0 if raw_score > 1.0 else raw_score
        score_10 = raw_score if raw_score > 1.0 else raw_score * 10.0

        risk_info = classify_risk(score_01)

        enriched.append({
            **d,
            'key':            key,
            'pillar_key':     pillar_key,
            'score':          score_01,
            'score_10':       score_10,
            'level':          risk_info.get('level', 'unavailable'),
        })

    enriched.sort(key=lambda x: (
        _pillar_order.get(x['pillar_key'], 9),
        x.get('sendai_priority', 9),
    ))
    return enriched


SENDAI_LABELS = {
    1: {
        'ar': 'فهم مخاطر الكوارث',
        'en': 'Understanding Disaster Risk',
    },
    2: {
        'ar': 'تعزيز حوكمة إدارة مخاطر الكوارث',
        'en': 'Strengthening Disaster Risk Governance',
    },
    3: {
        'ar': 'الاستثمار في الحد من مخاطر الكوارث',
        'en': 'Investing in Disaster Risk Reduction for Resilience',
    },
    4: {
        'ar': 'تعزيز الاستعداد للاستجابة الفعالة وإعادة البناء',
        'en': 'Enhancing Disaster Preparedness for Effective Response',
    },
}

ACTION_GUIDANCE = {

    # ══════════════════════════════════════════════════════════════════════
    # PILLAR 1 — HAZARD & EXPOSURE
    # ══════════════════════════════════════════════════════════════════════

    'epidemiological_hazard': {
        'label_ar': 'الأخطار الوبائية والصحية',
        'label_en': 'Epidemiological & Health Hazards',
        'pillar_ar': 'مؤشر الخطر والتعرض',
        'pillar_en': 'Hazard & Exposure',
        'icon': 'bi-virus2',
        'sendai_priority': 4,
        'cluster_ar': 'الفريق الصحي (WHO / وزارة الصحة)',
        'cluster_en': 'Health Cluster (WHO / Ministry of Health)',
        'gov_ar': 'وزارة الصحة · المركز الوطني لمكافحة الأمراض (NCDC)',
        'gov_en': 'Ministry of Health · National Centre for Disease Control (NCDC)',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('تقييم قدرات المراقبة الوبائية على المستوى البلدي — مع مراعاة أن NCDC تعمل في ظل حكومتين مختلفتين وتنسيق ذلك مع منظمة الصحة العالمية',
                     'Assess municipal epidemiological surveillance capacity — noting that NCDC operates under both GNU and GNS, and coordinate with WHO to bridge the gap'),
                    ('تحديث بروتوكولات الاستجابة للأمراض ذات الأولوية القصوى في ليبيا: الكوليرا والشلل (WHO صنّفها "خطر بالغ" 2025)، والحمى النزفية القرمية-الكونغو، وداء الليشمانيات، والحصبة، والدرن الرئوي',
                     'Update response protocols for Libya-priority diseases: cholera and polio (WHO-classified "very high risk" 2025), Crimean-Congo Haemorrhagic Fever (CCHF), Leishmaniasis, measles, and TB'),
                    ('التحقق من تغطية التطعيم للسكان المستقرين والنازحين والمهاجرين — فالبرنامج الوطني إلزامي ومجاني لكنه لا يصل إلى المهاجرين غير النظاميين (867,000 شخص في ليبيا حسب بيانات 2025)',
                     'Verify vaccination coverage for settled, displaced, and migrant populations — the compulsory free national programme does not reliably reach irregular migrants (867,000+ in Libya per 2025 data)'),
                    ('التحقق من سلامة السلسلة الباردة للقاح في المرافق الصحية المحلية في ظل انقطاعات الكهرباء المستمرة — اعتبار المولدات الاحتياطية من الأولويات الحرجة',
                     'Audit vaccine cold-chain integrity at local health facilities given chronic power outages — backup generators are a critical priority'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('دعم منصة "صحة واحدة" الوطنية التي أطلقتها منظمة الصحة العالمية في يناير 2025 — دمج مراقبة الأمراض الحيوانية المنشأ (الليشمانيا والحمى القرمية) مع المراقبة البشرية على المستوى البلدي',
                     'Support Libya\'s national One Health platform launched January 2025 — integrate zoonotic disease surveillance (Leishmaniasis, CCHF) with human surveillance at municipal level'),
                    ('تعزيز نقاط المراقبة في مراكز الرعاية الأولية وربطها بنظام NCDC الإلكتروني (eIDSR) والاستعداد لتقييم قدرات اللوائح الصحية الدولية (JEE الثاني المقرر أغسطس 2025)',
                     'Strengthen surveillance nodes at primary care facilities and link to NCDC eIDSR system — prepare for the 2nd JEE capacity assessment scheduled August 2025'),
                    ('تطوير مواد التواصل الصحي بالعربية الفصحى مع مراعاة السياق المجتمعي المحلي — التركيز على الوقاية من الكوليرا والأمراض المائية في المناطق التي تضررت بنية تحتية المياه',
                     'Develop health communications in Modern Standard Arabic respecting local context — prioritise cholera and waterborne disease prevention in areas with damaged water infrastructure'),
                    ('إجراء تمارين محاكاة لتفشي الأمراض مع الفرق الصحية البلدية — استخدام بروتوكولات WHO للمحاكاة (SimEx) والاستفادة من الدروس المستفادة من مراجعة ما بعد العمل (AAR) ليونيو 2024',
                     'Conduct outbreak simulation exercises with municipal health teams — use WHO SimEx protocols and apply lessons from the June 2024 After Action Review (AAR)'),
                    ('تعزيز قدرات مختبر الصحة البلدي وربطه بشبكة المختبرات المرجعية الإقليمية (تونس ومصر) كبديل موثوق في ظل محدودية القدرات الوطنية',
                     'Strengthen municipal health laboratory capacity and link to regional reference laboratories (Tunisia, Egypt) as a reliable alternative given limited national capacity'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('بناء نظام متكامل للمراقبة الوبائية القائمة على الأحداث (EBS) يربط البلديات بـ NCDC ويدعم الإنذار المبكر — وضع بروتوكولات واضحة تعمل في ظل سيناريوهات الحوكمة المزدوجة',
                     'Build integrated Event-Based Surveillance (EBS) system linking municipalities to NCDC with clear early warning protocols designed to function under dual-governance scenarios'),
                    ('إنشاء شبكة عمال صحة مجتمعية (CHW) في البلدية — لا يوجد برنامج وطني رسمي لعمال الصحة المجتمعية في ليبيا حتى الآن — مدرّبين على الكشف المبكر والإبلاغ واستخدام تقنية الرسائل القصيرة',
                     'Establish a municipal community health worker (CHW) network — Libya has no formal national CHW programme — trained in early detection, reporting, and SMS-based notification'),
                    ('الانتهاء من خطة العمل الوطنية للأمن الصحي (NAPHS) المحدّثة — الخطة الحالية من 2018 متقادمة — بناءً على نتائج JEE الثاني لعام 2025',
                     'Complete an updated National Action Plan for Health Security (NAPHS) — the current plan dates from 2018 and is outdated — based on the 2025 2nd JEE findings'),
                    ('توسيع مبادرة الطب عن بُعد لليبيا (TI4L) لتغطية الاستشارات الوبائية في البلديات الجنوبية النائية ذات المحدودية الشديدة في الوصول إلى الأخصائيين',
                     'Expand the Telemedicine Initiative for Libya (TI4L) to cover epidemiological consultations in remote southern municipalities with very limited specialist access'),
                ]
            },
        ],
    },

    'infrastructure_hazard': {
        'label_ar': 'أخطار البنية التحتية',
        'label_en': 'Infrastructure Hazards',
        'pillar_ar': 'مؤشر الخطر والتعرض',
        'pillar_en': 'Hazard & Exposure',
        'icon': 'bi-buildings',
        'sendai_priority': 3,
        'cluster_ar': 'الاتصالات الطارئة · التعافي المبكر والهندسة',
        'cluster_en': 'Emergency Telecommunications Cluster · Early Recovery / Engineering',
        'gov_ar': 'وزارة الإسكان والتعمير · وزارة النقل · الحماية المدنية',
        'gov_en': 'Ministry of Housing & Construction · Ministry of Transport · Civil Protection',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('إجراء تقييم سريع للبنية التحتية الحيوية — المستشفيات وشبكات المياه ومحطات الطاقة والطرق المحورية — مع الأولوية لتحديد المرافق التي تفتقر إلى مولدات احتياطية في ظل انقطاعات الكهرباء المزمنة',
                     'Conduct rapid assessment of critical infrastructure — hospitals, water networks, power stations, and arterial roads — prioritising facilities lacking backup generators given chronic power outages'),
                    ('تحديد نقاط الضعف في شبكات الصرف الصحي والمياه المعرضة للفيضانات — بما في ذلك حالة خطوط نظام النهر الصناعي العظيم (GMR) الذي يعاني من التقادم وعدم الصيانة',
                     'Identify vulnerabilities in sanitation and water networks exposed to flooding — including the condition of the Great Man-Made River (GMR) system, which suffers from ageing and deferred maintenance'),
                    ('رسم خرائط للبنية التحتية الحيوية على مستوى كل بلدية باستخدام صور الأقمار الاصطناعية حيث يتعذر التقييم الميداني — أثبت هذا الأسلوب فاعليته في سياق ليبيا',
                     'Map critical infrastructure at municipal level using satellite imagery where field assessment is not feasible — this method has proven effective in the Libyan context'),
                    ('تقييم السلامة الهيكلية للسدود والخزانات في المنطقة — يُعدّ تقرير "كارثة يمكن توقعها" (Science Advances 2024) عن سدَّي درنة نقطة مرجعية أساسية توضح خطورة إهمال الصيانة',
                     'Assess structural safety of dams and water reservoirs in the area — the "Anatomy of a foreseeable disaster" report (Science Advances 2024) on the Derna dams is a critical reference showing the lethal consequences of deferred maintenance'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تزويد جميع المرافق الصحية والمراكز الصحية الأولية بمولدات كهربائية احتياطية وإمدادات وقود — تعطّل سلاسل التبريد للقاحات والمعدات الطبية بسبب انقطاعات الكهرباء المتكررة يمثل أحد أكبر مواطن الضعف التشغيلية في ليبيا',
                     'Equip all health facilities and primary care centres with backup generators and fuel supplies — vaccine cold-chain disruption and medical equipment failure due to power cuts are among Libya\'s largest operational vulnerabilities'),
                    ('وضع معايير إنشاء مقاومة للمخاطر للمرافق الحيوية الجديدة بالتنسيق مع وزارة الإسكان — مع التركيز على معايير تحمّل الفيضانات والزلازل',
                     'Develop hazard-resistant construction standards for new critical facilities with the Ministry of Housing — with emphasis on flood and seismic resilience standards'),
                    ('وضع خطط استمرارية الخدمات (BCP) لكل مرفق صحي وبنية تحتية حيوية — يشمل ذلك بروتوكولات الإخلاء وبدائل التزود بالمياه وقنوات الاتصال الاحتياطية',
                     'Develop Business Continuity Plans (BCP) for each health facility and critical infrastructure — including evacuation protocols, alternative water supply, and backup communication channels'),
                    ('ربط البلديات النائية (جنوب ليبيا بصفة خاصة) بشبكات اتصالات الأقمار الاصطناعية لضمان التواصل الطارئ خارج نطاق شبكات الهاتف المحمول',
                     'Connect remote municipalities (especially in southern Libya) to satellite communications networks to ensure emergency contact beyond mobile network coverage'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تنفيذ برنامج لتعزيز صمود البنية التحتية بتمويل مشترك من الحكومة والمانحين الدوليين — ذلك يتطلب التنسيق بين الحكومتين GNU وGNS لضمان التغطية الشاملة',
                     'Implement an infrastructure resilience strengthening programme with joint government-donor financing — this requires coordination between GNU and GNS to ensure full coverage'),
                    ('دمج اشتراطات مقاومة الكوارث في كودات البناء الوطنية والتخطيط العمراني البلدي — بالتنسيق مع برامج UNDP للحوكمة المحلية وUN-Habitat',
                     'Integrate disaster resilience requirements into national building codes and municipal urban planning — in coordination with UNDP local governance and UN-Habitat programmes'),
                    ('إنشاء برنامج وطني لفحص السدود وصيانتها يكون مستقلاً عن الانقسام السياسي — انهار سدّا درنة رغم إمكانية الكشف المبكر عن الخطر عبر الأقمار الاصطناعية قبل الكارثة',
                     'Establish a national dam inspection and maintenance programme insulated from political division — the Derna dams collapsed despite the failure being detectable via satellite monitoring beforehand'),
                ]
            },
        ],
    },

    'natural_hazard': {
        'label_ar': 'الكوارث الطبيعية والهيدرومناخية',
        'label_en': 'Natural & Hydrometeorological Hazards',
        'pillar_ar': 'مؤشر الخطر والتعرض',
        'pillar_en': 'Hazard & Exposure',
        'icon': 'bi-cloud-lightning-rain',
        'sendai_priority': 1,
        'cluster_ar': 'الحماية المدنية · مجموعة المأوى · التعافي المبكر',
        'cluster_en': 'Civil Protection · Shelter Cluster · Early Recovery Cluster',
        'gov_ar': 'الحماية المدنية · المركز الوطني للأرصاد الجوية · وزارة الموارد المائية',
        'gov_en': 'Civil Protection Authority · National Meteorological Centre · Ministry of Water Resources',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('مراجعة دروس كارثة درنة (سبتمبر 2023) بشكل نقدي — لم يكن ثمة نظام إنذار مبكر ولا خطط إخلاء ولا صيانة للسدود ولا تنسيق بين الحكومة والمؤسسة العسكرية — هذه الفجوات يجب توثيقها وتحديد مسؤولية كل جهة',
                     'Critically review lessons from the Derna disaster (September 2023) — there was no early warning system, no evacuation plans, no dam maintenance, and no civilian-military coordination — these gaps must be documented with clear institutional accountability'),
                    ('رسم خرائط دقيقة لمناطق الخطر في البلدية — مجاري الأودية والمناطق الساحلية والمناطق السكانية المنخفضة المعرضة للفيضانات — والمناطق المعرضة لحرائق الغابات والعواصف الرملية وموجات الحر الشديدة (سُجّلت درجات تزيد على 50 مئوية عام 2022)',
                     'Map the municipality\'s hazard zones — wadi corridors, coastal areas, low-lying flood-exposed settlements — and areas exposed to wildfires, sandstorms, and extreme heat (temperatures above 50°C recorded in Libya in 2022)'),
                    ('التحقق من خطط الإخلاء المجتمعي للمناطق الساحلية والمناطق المجاورة للأودية — والتأكد من أن السكان يعرفون مسارات الإخلاء ومواقع التجمع',
                     'Verify community evacuation plans for coastal and wadi-adjacent zones — ensure residents know evacuation routes and assembly points'),
                    ('الاطلاع على مخرجات تقييمات ضعف المجتمع (VCA) التي تجريها IOM في المناطق الليبية (البيضاء وشحات وغات وطبرق) والتنسيق مع IOM لتطبيق المنهجية ذاتها في هذه البلدية',
                     'Review outputs from IOM\'s Vulnerability and Community Assessments (VCAs) conducted in Libyan municipalities (Al-Bayda, Shahhat, Ghat, Tobruk) and coordinate with IOM to apply the same methodology here'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('وضع نظام إنذار مبكر بسيط وموثوق على المستوى البلدي — إطار متعدد القنوات: التنبيهات الجوية من RSMC القاهرة (المنظمة العالمية للأرصاد الجوية)، والرسائل النصية للكوادر الأساسية، وإذاعة المجتمع المحلي، والشبكة المسجدية — لأنها الأكثر مرونة في ليبيا',
                     'Establish a simple, reliable municipal-level early warning system — multi-channel framework: meteorological alerts from WMO RSMC Cairo, SMS alerts to key personnel, community radio, and mosque network — these are Libya\'s most resilient communication channels'),
                    ('التدريب المشترك لفرق الحماية المدنية البلدية والمتطوعين المجتمعيين على البحث والإنقاذ في بيئات الفيضانات والإسعافات الأولية المتعلقة بالحروق والصدمات الحرارية — بالشراكة مع الهلال الأحمر الليبي',
                     'Jointly train municipal Civil Protection teams and community volunteers in flood search-and-rescue, burn care, and heat stroke first aid — in partnership with the Libyan Red Crescent Society'),
                    ('تجهيز مخزون طوارئ مسبق — مياه وغذاء وخيام ومستلزمات إغاثية صحية — في مستودعات بلدية على مسافة آمنة من مناطق الفيضان',
                     'Pre-position emergency stockpile — water, food, tents, and health relief supplies — at municipal warehouses located safely away from flood zones'),
                    ('وضع خطة عمل للحرارة تحدد الأماكن الباردة الآمنة ومواقع التبريد وبروتوكولات دعم الفئات الأكثر عرضة — كبار السن والعمال في الهواء الطلق وساكنو المخيمات والمناطق العشوائية',
                     'Develop a heat action plan identifying cool safe spaces, cooling stations, and support protocols for most vulnerable groups — elderly, outdoor workers, camp residents, and informal settlements'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('دمج مخرجات رسم الخرائط البلدية في منظومة التخطيط العمراني وتخصيص الأراضي — لمنع البناء في الأحواض المائية والمناطق المعرضة للفيضانات',
                     'Integrate municipal hazard mapping outputs into urban planning and land allocation systems — to prevent construction in wadis and flood-exposed zones'),
                    ('المساهمة في بناء المنصة الوطنية لإدارة مخاطر الكوارث (مطلب إطار سنداي) — التي لم تُنشأ بعد في ليبيا — عبر تبادل بيانات المخاطر البلدية مع الجهات الأممية',
                     'Contribute to building Libya\'s National Platform for Disaster Risk Reduction (required by Sendai Framework) — which has not yet been established — by sharing municipal risk data with UN partners'),
                    ('تطوير نموذج تمويل للتعافي يمزج الميزانية البلدية بصناديق المانحين — بما في ذلك التفاوض على آليات تمويل مسبق مرتبطة بمحفزات الطوارئ',
                     'Develop a recovery financing model blending municipal budget with donor funds — including negotiating pre-arranged financing mechanisms triggered by declared emergencies'),
                ]
            },
        ],
    },

    'road_safety_hazard': {
        'label_ar': 'مخاطر السلامة على الطرق',
        'label_en': 'Road Safety Hazards',
        'pillar_ar': 'مؤشر الخطر والتعرض',
        'pillar_en': 'Hazard & Exposure',
        'icon': 'bi-car-front',
        'sendai_priority': 3,
        'cluster_ar': 'مجموعة الخدمات اللوجستية · مجموعة الصحة',
        'cluster_en': 'Logistics Cluster · Health Cluster',
        'gov_ar': 'وزارة النقل · الشرطة البلدية · الهلال الأحمر الليبي',
        'gov_en': 'Ministry of Transport · Municipal Police · Libyan Red Crescent Society',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('رسم خرائط النقاط السوداء (مناطق الحوادث المتكررة) في حدود البلدية — مع التركيز على الطرق السريعة غير المقسومة والتقاطعات غير المضاءة ومسارات المركبات العسكرية والمدنية التي تشترك في المسالك ذاتها',
                     'Map black spots (high-frequency accident zones) within municipal boundaries — focusing on undivided highways, unlit junctions, and routes where military and civilian vehicles share lanes'),
                    ('تقييم قدرات الإسعاف والاستجابة الطبية الطارئة — ليبيا بها 51 مركز إسعاف على المستوى الوطني، كثير منها معطّل أو يعمل بطاقة ناقصة — التحقق من الوضع في هذه البلدية',
                     'Assess ambulance and emergency medical response capacity — Libya has 51 national ambulance centres, many non-functional or underequipped — verify actual capacity in this municipality'),
                    ('مراجعة إجراءات إدارة حوادث الإصابات الجماعية بالطرق مع الهلال الأحمر والخدمات الصحية — بما في ذلك تحديد المستشفيات المرجعية لحوادث الصدمات',
                     'Review mass-casualty road incident procedures with the Red Crescent and health services — including identifying reference hospitals for trauma cases'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تطوير نظام بيانات حوادث المرور على المستوى البلدي لرصد الأنماط والتخطيط للتدخل — ربطه بجهاز شرطة المرور وخدمات الطوارئ',
                     'Develop a municipal road accident data system to monitor patterns and inform interventions — link it with traffic police and emergency services'),
                    ('تحديد مسارات الإخلاء الرئيسية والتحقق من قابليتها للمرور في جميع الأوقات — بما في ذلك خلال موسم الفيضانات والعواصف الرملية',
                     'Identify key evacuation routes and verify their passability at all times — including during the flood season and sandstorm events'),
                    ('تدريب المسعفين والمتطوعين على الإسعافات الأولية وإيقاف النزيف وبروتوكولات نقل المصابين — يُعدّ الوصول السريع للمستشفيات أحد أكبر تحديات الصمود الصحي في ليبيا',
                     'Train first responders and volunteers in first aid, haemorrhage control (STOP THE BLEED), and patient transport protocols — rapid hospital access is one of Libya\'s greatest health resilience challenges'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('ترقية البنية التحتية للطرق الرئيسية مع دمج معايير السلامة المرورية — حواجز الأمان ووضوح الإشارات وإضاءة التقاطعات',
                     'Upgrade key road infrastructure incorporating international safety standards — safety barriers, clear signage, and junction lighting'),
                    ('تطوير شبكة إسعاف بلدية مع مراكز تنسيق في المناطق النائية — يشمل ذلك شراكات مع IOM والهلال الأحمر اللذين يدعمان خدمات الإخلاء الطبي في المناطق النائية',
                     'Develop a municipal ambulance network with coordination centres in remote areas — including partnerships with IOM and the Red Crescent, which support medical evacuation in remote settings'),
                ]
            },
        ],
    },

    # ══════════════════════════════════════════════════════════════════════
    # PILLAR 2 — VULNERABILITY
    # ══════════════════════════════════════════════════════════════════════

    'security_vulnerability': {
        'label_ar': 'الهشاشة الأمنية',
        'label_en': 'Security Vulnerability',
        'pillar_ar': 'مؤشر الضعف والهشاشة',
        'pillar_en': 'Vulnerability',
        'icon': 'bi-shield-exclamation',
        'sendai_priority': 1,
        'cluster_ar': 'مجموعة الحماية · UNHCR · IOM',
        'cluster_en': 'Protection Cluster · UNHCR · IOM',
        'gov_ar': 'وزارة الداخلية · المجالس البلدية · اللجان المحلية للسلامة',
        'gov_en': 'Ministry of Interior · Municipal Councils · Local Safety Committees',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('رسم خرائط دقيقة للمجتمعات الأكثر عرضة لانعدام الأمن والمناطق ذات الوصول المحدود — مع مراعاة أن بعض البلديات تقع في مناطق نفوذ حكومة مختلفة عن الأخرى مما يؤثر على تدفق الخدمات الإنسانية',
                     'Map communities most exposed to insecurity and areas of limited humanitarian access — noting that some municipalities fall under different government authority which affects service delivery channels'),
                    ('التأكد من وصول خدمات الحماية الإنسانية إلى السكان الأكثر هشاشة — النازحون والمهاجرون والأسر المعيشة في مناطق صراع سابقة — بالتنسيق مع IOM وUNHCR ومجموعة الحماية',
                     'Ensure humanitarian protection services reach most vulnerable populations — IDPs, migrants, and families in formerly contested areas — coordinating with IOM, UNHCR, and the Protection Cluster'),
                    ('إنشاء قنوات إبلاغ آمنة وسرية عن انتهاكات الحماية — تشمل الخطوط الساخنة ونقاط الاتصال المجتمعية المحايدة',
                     'Establish safe and confidential channels for reporting protection violations — including hotlines and neutral community contact points'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تعزيز دور اللجان المجتمعية في التقييم المحلي للمخاطر ومعالجة التوترات الاجتماعية قبل تصاعدها — التركيز على التنافس حول الموارد الشحيحة (المياه والأراضي وفرص العمل) التي تُغذّي النزاعات المحلية في ليبيا',
                     'Strengthen community committees in local risk assessment and managing social tensions before they escalate — focus on competition over scarce resources (water, land, employment) which fuel local disputes in Libya'),
                    ('الانخراط مع المنظمات الإنسانية لضمان استمرارية تقديم الخدمات الأساسية — الصحة والماء والغذاء — في المناطق عالية المخاطر وفق مبادئ الحياد الإنساني',
                     'Engage humanitarian organisations to ensure continuity of essential services — health, water, food — in high-risk areas under humanitarian neutrality principles'),
                    ('وضع بروتوكولات مشتركة للاستجابة للحوادث الأمنية الطارئة تضم جميع الجهات الفاعلة المحلية',
                     'Develop joint response protocols for emergency security incidents involving all local stakeholders'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('دمج برامج تخفيف المخاطر الأمنية في خطط التنمية المحلية — مع التركيز على تدخلات الاقتصاد ومعالجة الشباب ومسارات إعادة الاندماج للمجتمعات المتضررة',
                     'Integrate security risk reduction into local development plans — focusing on economic interventions, youth engagement, and reintegration pathways for affected communities'),
                    ('بناء آليات حوار مجتمعي وصون النسيج الاجتماعي — بما في ذلك دور الشبكات القبلية والمؤسسات الدينية التي تضطلع بدور محوري في التماسك الاجتماعي الليبي',
                     'Build community dialogue mechanisms and social fabric preservation — including the role of tribal networks and religious institutions, which play a central role in Libyan social cohesion'),
                ]
            },
        ],
    },

    'agency_capacity_gap': {
        'label_ar': 'فجوة قدرات المؤسسات الحكومية',
        'label_en': 'Government Agency Capacity Gap',
        'pillar_ar': 'مؤشر الضعف والهشاشة',
        'pillar_en': 'Vulnerability',
        'icon': 'bi-bank',
        'sendai_priority': 2,
        'cluster_ar': 'التعافي المبكر · بناء القدرات الوطنية (UNDP)',
        'cluster_en': 'Early Recovery · National Capacity Building (UNDP)',
        'gov_ar': 'المجالس البلدية · وزارة الحكم المحلي',
        'gov_en': 'Municipal Councils · Ministry of Local Government',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('تقييم القدرات المؤسسية الحالية للمجلس البلدي في إدارة الكوارث والطوارئ — مع مراعاة أن المجالس البلدية في ليبيا هي أكثر الجهات الحكومية حضوراً واستمرارية في كلا النطاقين الغربي والشرقي للبلاد',
                     'Assess current institutional capacity of the municipal council in disaster and emergency management — noting that municipal councils are Libya\'s most present and continuous governance actors in both western and eastern zones'),
                    ('تحديد الأفراد الرئيسيين المسؤولين عن الطوارئ وتوثيق أدوارهم — مع مراعاة التداخل المحتمل مع هياكل الحكومة التي تُدار على المستوى الإقليمي',
                     'Identify key emergency management personnel and document their roles — noting potential overlap with government structures administered at regional level'),
                    ('الاستفادة من بيانات IOM DTM (مصفوفة تتبع النزوح) لفهم توزع السكان المعرضين للمخاطر وتوجيه تخطيط الموارد',
                     'Use IOM DTM (Displacement Tracking Matrix) data to understand the distribution of at-risk populations and guide resource planning'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تطوير خطة استجابة للطوارئ على مستوى البلدية تحدد الأدوار والموارد وسلاسل القيادة — مع التنسيق مع برنامج UNDP لدعم الحوكمة المحلية النشط حالياً في ليبيا',
                     'Develop a municipal emergency response plan defining roles, resources, and command chains — coordinating with UNDP\'s Local Governance Support Programme currently active in Libya'),
                    ('تدريب الكوادر البلدية على أسس إدارة الكوارث وفق إطار سنداي ومنهجية مؤشر INFORM — بالشراكة مع IOM التي تنفذ برامج بناء القدرات في مجال إدارة مخاطر الكوارث في ليبيا',
                     'Train municipal staff on Sendai Framework disaster management fundamentals and INFORM methodology — in partnership with IOM, which implements DRR capacity building programmes in Libya'),
                    ('إنشاء قاعدة بيانات بلدية للأصول والموارد والكفاءات المتاحة — تشمل المنظمات غير الحكومية والمتطوعين والمرافق والمخزونات',
                     'Establish a municipal database of available assets, resources, and competencies — including NGOs, volunteers, facilities, and stockpiles'),
                    ('الاستعداد لتقييم JEE الثاني المقرر أغسطس 2025 — التنسيق مع فريق الصحة البلدي لإعداد الوثائق اللازمة وتحديد أولويات التدريب قبل التقييم',
                     'Prepare for the 2nd JEE assessment scheduled August 2025 — coordinate with the municipal health team to prepare documentation and prioritise training before evaluation'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('إنشاء وحدة مخصصة لإدارة الكوارث داخل الهيكل التنظيمي للمجلس البلدي — بصلاحيات واضحة وموازنة محددة ومسؤولية مباشرة أمام رئيس المجلس',
                     'Establish a dedicated disaster management unit within the municipal council structure — with clear mandate, dedicated budget line, and direct accountability to the council head'),
                    ('الانضمام إلى المنصة الوطنية لإدارة مخاطر الكوارث عند إنشائها — IOM وUNDR يعملان على تأسيسها — والمساهمة في بناء نظام المعلومات الجغرافية الوطني للمخاطر',
                     'Join Libya\'s National Disaster Risk Reduction Platform once established — IOM and UNDRR are working to create it — and contribute to building the national geographic risk information system'),
                    ('تطوير خطة للتطوير المهني المستدام لكوادر إدارة الطوارئ البلدية — بما في ذلك التدريب المتبادل مع بلديات مجاورة لبناء الصمود الإقليمي',
                     'Develop a sustainable professional development plan for municipal emergency management cadre — including cross-training with neighbouring municipalities to build regional resilience'),
                ]
            },
        ],
    },

    'urban_sprawl': {
        'label_ar': 'التوسع العمراني غير المنظم',
        'label_en': 'Uncontrolled Urban Sprawl & Exposure',
        'pillar_ar': 'مؤشر الضعف والهشاشة',
        'pillar_en': 'Vulnerability',
        'icon': 'bi-map',
        'sendai_priority': 2,
        'cluster_ar': 'مجموعة المأوى · التعافي المبكر · مجموعة WASH',
        'cluster_en': 'Shelter Cluster · Early Recovery · WASH Cluster',
        'gov_ar': 'وزارة الإسكان والتعمير · المجلس البلدي',
        'gov_en': 'Ministry of Housing & Construction · Municipal Council',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('رسم خرائط للأحياء غير الرسمية والتجمعات السكانية العشوائية — بما في ذلك المناطق التي أعيد تعميرها بعد الصراع دون ترخيص، كما في عدة مدن ليبية — وتحديد المخاطر المباشرة (فيضانات وحرائق ونفايات)',
                     'Map informal settlements and unplanned residential areas — including areas rebuilt after conflict without permits, as in several Libyan cities — and identify immediate risks (flooding, fire, waste)'),
                    ('تحديد المباني الآيلة للسقوط أو التي تفتقر إلى معايير السلامة الهيكلية الأساسية — مع الأولوية للمباني التي تأوي أعداداً كبيرة من النازحين أو العائلات الهشة',
                     'Identify structurally unsafe buildings lacking basic safety standards — prioritising buildings housing large numbers of IDPs or vulnerable families'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تطوير خطة عمرانية تشاركية تشمل الأحياء غير الرسمية وتدمج اعتبارات مخاطر الكوارث — وتراعي حقوق السكن للنازحين الذين يشغلون مبانٍ متنازعاً عليها',
                     'Develop a participatory urban plan including informal areas integrating disaster risk — one that respects housing rights of IDPs occupying disputed buildings'),
                    ('تحسين البنية التحتية للمياه والصرف الصحي في المناطق الأكثر كثافة وهشاشة — بالتنسيق مع WASH Cluster ومشاريع UNDP لأمن المياه',
                     'Improve water and sanitation infrastructure in most densely populated and vulnerable areas — coordinating with the WASH Cluster and UNDP water security projects'),
                    ('برامج توعية لسكان المناطق العشوائية حول ممارسات البناء الآمن والمخاطر الصحية المرتبطة بالصرف الصحي غير الملائم — مع إيلاء اهتمام خاص لمخاطر الكوليرا والأمراض الإسهالية',
                     'Awareness programmes for residents of informal areas on safe building practices and health risks linked to inadequate sanitation — with special attention to cholera and diarrhoeal disease risks'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تنفيذ مشاريع تحسين الأحياء غير الرسمية مع تكامل الخدمات الأساسية — بالتنسيق مع UN-Habitat وبرامج التعافي المبكر التابعة للأمم المتحدة',
                     'Implement informal settlement upgrading projects with integrated basic services — in coordination with UN-Habitat and UN early recovery programmes'),
                    ('إنشاء نظام رقابة على البناء لتطبيق كودات الإنشاء ومنع التمدد في مناطق الخطر — مع التأكد من أن هذا النظام قابل للتطبيق في ظل القدرات المحدودة للإدارة المحلية',
                     'Establish a building control system to enforce construction codes and prevent expansion into hazard zones — ensuring the system is implementable given limited local administration capacity'),
                ]
            },
        ],
    },

    'displacement_vulnerability': {
        'label_ar': 'هشاشة النازحين والمهاجرين',
        'label_en': 'Displacement & Migration Vulnerability',
        'pillar_ar': 'مؤشر الضعف والهشاشة',
        'pillar_en': 'Vulnerability',
        'icon': 'bi-people',
        'sendai_priority': 1,
        'cluster_ar': 'مجموعة حماية النازحين · UNHCR · IOM DTM',
        'cluster_en': 'IDP Protection Cluster · UNHCR · IOM DTM',
        'gov_ar': 'وزارة الشؤون الاجتماعية · اللجنة الوطنية لشؤون النازحين',
        'gov_en': 'Ministry of Social Affairs · National IDP Committee',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('تحديث بيانات النازحين داخلياً على المستوى البلدي بالتنسيق مع IOM DTM — بيانات فبراير 2024 تشير إلى 147,000 نازح داخلي في ليبيا بسبب الصراع والكوارث (منهم 40,000+ من ضحايا فيضانات درنة)',
                     'Update IDP data at municipal level with IOM DTM — February 2024 data indicates 147,000 IDPs in Libya due to conflict and disasters (including 40,000+ from the Derna floods)'),
                    ('التأكد من وصول النازحين والمهاجرين إلى الخدمات الصحية والمياه النظيفة والغذاء — مع مراعاة أن 867,000 مهاجراً في ليبيا (بيانات 2025) يواجهون عقبات جسيمة في الوصول إلى الخدمات العامة',
                     'Ensure IDPs and migrants access health services, clean water, and food — noting that 867,000+ migrants in Libya (2025 data) face major barriers to public services'),
                    ('التنسيق مع IOM وUNHCR لإجراء فحوصات صحية عند الوصول للمهاجرين الجدد — خاصة لتحديد حالات السل والجرب والأمراض المعدية التي يمكن أن تنتشر في أماكن الإقامة المكتظة',
                     'Coordinate with IOM and UNHCR to conduct health screenings at arrival for new migrants — particularly to identify TB, scabies, and infectious diseases that can spread in overcrowded accommodation'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('دعم برامج حملات التطعيم اللحاقية للنازحين والمهاجرين — البرنامج الوطني الليبي للتطعيم إلزامي ومجاني للمقيمين ولكنه لا يصل بشكل منتظم إلى السكان المتنقلين',
                     'Support catch-up vaccination campaigns for IDPs and migrants — Libya\'s compulsory free vaccination programme does not reliably reach mobile populations'),
                    ('وضع خطط حلول دائمة للعودة الطوعية والاستقرار للمناطق الأشد هشاشة — بالتنسيق مع خطة استجابة IOM لليبيا 2025-2026',
                     'Develop durable solutions plans for voluntary return and settlement in most vulnerable areas — in coordination with IOM\'s Libya Crisis Response Plan 2025-2026'),
                    ('تعزيز خدمات الدعم النفسي-الاجتماعي (MHPSS) للنازحين والمهاجرين — بالشراكة مع IOM التي تدير برنامج MHPSS نشطاً في ليبيا — مع التركيز على صدمات الفقد والاضطراب',
                     'Strengthen MHPSS services for IDPs and migrants — in partnership with IOM which runs an active MHPSS programme in Libya — focusing on grief, loss, and disruption trauma'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('إدماج النازحين المستقرين في السياسات التنموية المحلية وخدمات البلدية — بما في ذلك التسجيل في قوائم الخدمات وبرامج تنمية سبل العيش',
                     'Integrate settled IDPs into local development policies and municipal services — including registration in service registers and livelihood development programmes'),
                    ('بناء نظام بلدي لرصد حركات النزوح يُطعم خطط الاستجابة الطارئة — بالاستفادة من بيانات IOM DTM وتقارير OCHA الدورية',
                     'Build a municipal system to monitor displacement movements that feeds into emergency response plans — drawing on IOM DTM data and periodic OCHA reports'),
                ]
            },
        ],
    },

    'health_unawareness': {
        'label_ar': 'ضعف الوعي الصحي المجتمعي',
        'label_en': 'Low Community Health Awareness',
        'pillar_ar': 'مؤشر الضعف والهشاشة',
        'pillar_en': 'Vulnerability',
        'icon': 'bi-heart-pulse',
        'sendai_priority': 1,
        'cluster_ar': 'مجموعة الصحة · التثقيف الصحي والتواصل المجتمعي',
        'cluster_en': 'Health Cluster · Health Education & Community Engagement',
        'gov_ar': 'وزارة الصحة · NCDC · المجالس البلدية',
        'gov_en': 'Ministry of Health · NCDC · Municipal Councils',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('تطوير حملات توعية صحية باللغة العربية الفصحى ملائمة ثقافياً — تستهدف الأمراض ذات الأولوية لليبيا: الكوليرا والأمراض المنقولة بالمياه، والليشمانيا، والحصبة، وأمراض الجهاز التنفسي المرتبطة بالعواصف الرملية والحرارة الشديدة',
                     'Develop culturally appropriate Arabic-language health awareness campaigns targeting Libya-priority diseases: cholera and waterborne diseases, Leishmaniasis, measles, and respiratory illnesses linked to sandstorms and extreme heat'),
                    ('استخدام قنوات التواصل الأكثر وصولاً في السياق الليبي: الراديو المجتمعي المحلي، وشبكة المساجد، والمجموعات عبر تطبيق WhatsApp للقادة المجتمعيين — إلى جانب القنوات الرسمية',
                     'Use most accessible channels in the Libyan context: local community radio, mosque network, and WhatsApp groups for community leaders — alongside formal channels'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تدريب عمال الصحة المجتمعية على التثقيف الصحي والكشف المبكر — مع التركيز على مخاطر الأمراض المنقولة بالمياه في المناطق ذات البنية التحتية الهشة ومخاطر الحرارة الشديدة',
                     'Train community health workers on health education and early detection — focusing on waterborne disease risks in areas with fragile infrastructure and extreme heat risks'),
                    ('إدماج التوعية بمخاطر الكوارث والصحة في المناهج المدرسية والأنشطة المجتمعية — بما في ذلك بروتوكولات الإخلاء وأساسيات الإسعافات الأولية',
                     'Integrate disaster risk and health awareness into school curricula and community activities — including evacuation protocols and basic first aid'),
                    ('تطوير شبكة من الأئمة والمعلمين والقادة المجتمعيين كوسطاء صحيين موثوقين — يُعدّ الأئمة من أكثر الأطراف تأثيراً في تغيير السلوك الصحي في المجتمعات الليبية',
                     'Develop a network of imams, teachers, and community leaders as trusted health intermediaries — imams are among the most influential actors for health behaviour change in Libyan communities'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('بناء شبكة صحة مجتمعية متكاملة تضم المدارس والمساجد والمراكز الاجتماعية — مع إدماج التوعية بالصحة النفسية والدعم النفسي-الاجتماعي الذي يعاني من فجوة هائلة في ليبيا (تُقدَّر الحاجة بأكثر من مليون شخص)',
                     'Build an integrated community health network involving schools, mosques, and social centres — integrating mental health awareness and psychosocial support, which faces a massive gap in Libya (estimated need exceeds one million people)'),
                    ('تطوير وحدات صحة متنقلة للمجتمعات النائية وتلك التي تضم نسبة كبيرة من النازحين — للوصول إلى الفئات التي لا تستطيع الوصول إلى المرافق الصحية الثابتة',
                     'Develop mobile health units for remote communities and those with large IDP populations — reaching groups unable to access static health facilities'),
                ]
            },
        ],
    },

    # ══════════════════════════════════════════════════════════════════════
    # PILLAR 3 — LACK OF COPING CAPACITY
    # ══════════════════════════════════════════════════════════════════════

    'response_time_gap': {
        'label_ar': 'فجوة زمن الاستجابة للطوارئ',
        'label_en': 'Emergency Response Time Gap',
        'pillar_ar': 'مؤشر القدرة على التكيف',
        'pillar_en': 'Lack of Coping Capacity',
        'icon': 'bi-alarm',
        'sendai_priority': 4,
        'cluster_ar': 'التنسيق العملياتي للطوارئ · الحماية المدنية',
        'cluster_en': 'Emergency Operations Coordination · Civil Protection',
        'gov_ar': 'الحماية المدنية · غرف العمليات البلدية · خدمات الإسعاف',
        'gov_en': 'Civil Protection · Municipal Operations Rooms · Ambulance Services',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('تقييم أوقات الاستجابة الفعلية لخدمات الطوارئ البلدية — مع مراعاة أن ليبيا تضم 51 مركز إسعاف وطنياً كثير منها غير مشغّل أو يعمل بإمكانات محدودة للغاية — خاصة في البلديات الجنوبية النائية التي تفتقر إلى خدمات إسعاف منتظمة',
                     'Assess actual emergency response times for municipal services — noting Libya\'s 51 national ambulance centres, many non-functional or very under-resourced — especially in remote southern municipalities with no regular ambulance coverage'),
                    ('إنشاء غرفة عمليات طوارئ بلدية أو تحديث القائمة منها — مع توثيق إجراءات التشغيل الموحدة (SOPs) وسلاسل القيادة بما يشمل آليات التنسيق مع الحكومة في المستوى الإقليمي',
                     'Establish or update a municipal emergency operations room — with documented Standard Operating Procedures (SOPs) and command chains including coordination mechanisms with regional government level'),
                    ('تطوير دليل جهات الاتصال الطارئ الشامل لجميع خدمات الاستجابة — بما في ذلك جهات الاتصال لدى IOM والهلال الأحمر الليبي ومنظمات الصحة العالمية العاملة في المنطقة',
                     'Develop a comprehensive emergency contact directory for all response services — including IOM, Libyan Red Crescent, and WHO partners operating in the area'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('إجراء تمارين محاكاة متعددة الجهات للاستجابة للطوارئ — مع تطبيق دروس كارثة درنة: غياب التنسيق بين المدني والعسكري والفشل في التواصل كانا عاملين حاسمين في تضخيم الخسائر البشرية',
                     'Conduct multi-stakeholder emergency response simulation exercises — applying Derna disaster lessons: failure of civilian-military coordination and communications breakdown were decisive factors amplifying the death toll'),
                    ('تحسين منظومة الاتصالات الطارئة مع قنوات بديلة احتياطية — تضم الراديو والأقمار الاصطناعية والرسائل النصية المشفرة للكوادر الأساسية — لضمان الاتصال حتى عند انقطاع شبكات الهاتف المحمول',
                     'Improve the emergency communications system with redundant backup channels — including radio, satellite, and SMS for key personnel — to ensure connectivity even when mobile networks fail'),
                    ('تحديد مواقع التجمع ومراكز الإخلاء المجهزة على مستوى البلدية — مع التحقق من معرفة السكان بها وإمكانية الوصول إليها في ظروف مختلفة',
                     'Pre-identify and equip assembly points and evacuation centres at municipal level — verifying residents know about them and can reach them under various conditions'),
                    ('تنسيق خطة البلدية مع المستوى الإقليمي ضمن النطاق الحكومي المناسب — GNU أو GNS — لضمان سرعة إرسال الدعم وعدم الانتظار لإجراءات موافقة طويلة',
                     'Coordinate the municipal plan with regional level within the appropriate government zone — GNU or GNS — to ensure rapid deployment of support without prolonged approval procedures'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تطوير قدرات الاستجابة المحلية عبر تدريب وتجهيز فرق متخصصة على مستوى البلدية — فرق الإنقاذ في الفيضانات وإدارة الحرائق والإسعاف الطبي الأولي — بدلاً من الاعتماد الكامل على الموارد المركزية',
                     'Develop local response capacity by training and equipping specialised municipal teams — flood rescue, fire management, and emergency medical first response — reducing total dependence on centralised resources'),
                    ('إنشاء نظام دوري لمراقبة أداء خدمات الطوارئ وتحليل أوقات الاستجابة — وإعداد تقارير دورية علنية لتعزيز المساءلة',
                     'Establish a periodic system to monitor emergency service performance and analyse response times — producing public periodic reports to enhance accountability'),
                ]
            },
        ],
    },

    'community_support_gap': {
        'label_ar': 'فجوة الدعم المجتمعي والشبكات الاجتماعية',
        'label_en': 'Community Support & Social Network Gap',
        'pillar_ar': 'مؤشر القدرة على التكيف',
        'pillar_en': 'Lack of Coping Capacity',
        'icon': 'bi-people-fill',
        'sendai_priority': 1,
        'cluster_ar': 'الحماية المجتمعية · مجموعة WASH · الصمود المجتمعي',
        'cluster_en': 'Community Protection · WASH Cluster · Community Resilience',
        'gov_ar': 'وزارة الشؤون الاجتماعية · الهلال الأحمر الليبي · منظمات المجتمع المدني',
        'gov_en': 'Ministry of Social Affairs · Libyan Red Crescent Society · Civil Society Organisations',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('رسم خرائط منظمات المجتمع المدني والمتطوعين والشبكات الاجتماعية الفاعلة على مستوى البلدية — بما في ذلك الشبكات القبلية والعائلية الممتدة والمؤسسات الدينية التي تشكل ركيزة أساسية للصمود الاجتماعي الليبي',
                     'Map civil society organisations, volunteers, and active social networks at municipal level — including tribal and extended family networks and religious institutions, which are foundational to Libyan social resilience'),
                    ('التواصل مع الهلال الأحمر الليبي ومنظمات المجتمع المدني لتقييم إمكانات التعاون في الاستجابة للطوارئ وتقديم الدعم النفسي-الاجتماعي',
                     'Engage the Libyan Red Crescent Society and civil society organisations to assess cooperation potential for emergency response and psychosocial support'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('إنشاء شبكة متطوعين مجتمعيين للاستجابة للطوارئ وتقديم الدعم النفسي-الاجتماعي — مع إعطاء أولوية لتضمين النساء في الأدوار القيادية وهو أمر بالغ الأهمية في الوصول إلى شرائح مجتمعية غير مرئية في ليبيا',
                     'Establish a community volunteer network for emergency response and psychosocial support — prioritising inclusion of women in leadership roles, which is essential for reaching invisible community segments in Libya'),
                    ('تطوير برامج الحماية الاجتماعية للفئات الأكثر هشاشة — الأسر المعيلة من النساء وذوو الإعاقة وكبار السن المنعزلون — بالشراكة مع المنظمات المحلية والمؤسسات الخيرية الإسلامية (الوقف)',
                     'Develop social protection programmes for most vulnerable groups — female-headed households, persons with disabilities, and isolated elderly — in partnership with local organisations and Islamic charitable institutions (Waqf)'),
                    ('توثيق الموارد المجتمعية وأنماط التضامن الاجتماعي التقليدية الليبية — الديّة والجيرة والتكافل — التي أثبتت فاعليتها في دعم الصمود بعد الكوارث',
                     'Document Libyan traditional social solidarity patterns — diya, neighbourly solidarity, takaful — which have demonstrated effectiveness in supporting post-disaster resilience'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('إنشاء مراكز مجتمعية للصمود في البلدية تجمع بين خدمات الدعم النفسي-الاجتماعي وتدريب إدارة المخاطر والخدمات الاجتماعية — تكون مساحات آمنة مستمرة وليس مجرد استجابة لحالات الطوارئ',
                     'Establish community resilience centres in the municipality combining psychosocial support, risk management training, and social services — permanent safe spaces, not just emergency response sites'),
                    ('دمج صناديق الطوارئ المجتمعية الصغيرة (قوارب صغيرة مرونة) في آليات الحوكمة المحلية — تعمل وفق مبادئ التكافل الإسلامي المألوفة ثقافياً',
                     'Integrate small community emergency funds (micro-resilience buffers) into local governance mechanisms — operating on the familiar Islamic takaful solidarity principles'),
                ]
            },
        ],
    },

    'poverty_vulnerability': {
        'label_ar': 'الهشاشة الاقتصادية والفقر',
        'label_en': 'Poverty & Economic Vulnerability',
        'pillar_ar': 'مؤشر القدرة على التكيف',
        'pillar_en': 'Lack of Coping Capacity',
        'icon': 'bi-coin',
        'sendai_priority': 2,
        'cluster_ar': 'مجموعة الأمن الغذائي · التعافي الاقتصادي والمعيشة',
        'cluster_en': 'Food Security Cluster · Early Recovery / Livelihoods Cluster',
        'gov_ar': 'وزارة الاقتصاد · وزارة العمل · صناديق التنمية المحلية',
        'gov_en': 'Ministry of Economy · Ministry of Labour · Local Development Funds',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('تحديد الأسر الأكثر هشاشة اقتصادياً وتحديث سجلات التحويلات الاجتماعية — مع التنبه إلى ظاهرة "الفقر المخفي" في ليبيا: ثروة نفطية وطنية ولكن توزيع غير متكافئ وانهيار حاد في القطاع العام منذ 2011',
                     'Identify the most economically vulnerable households and update social transfer records — noting Libya\'s hidden poverty phenomenon: national oil wealth but highly unequal distribution and sharp public sector collapse since 2011'),
                    ('التنسيق مع مجموعة الأمن الغذائي لضمان وصول الغذاء للأسر عالية المخاطر — والتأكد من أن المهاجرين وغير الوثائقيين مشمولون في أنظمة التوزيع',
                     'Coordinate with the Food Security Cluster to ensure food reaches high-risk households — verifying that migrants and undocumented persons are included in distribution systems'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('وضع برامج سبل العيش لدعم الأسر المتضررة — مع الأولوية لبرامج الشباب لمعالجة البطالة المرتفعة التي تُشكّل عامل خطر للتجنيد المسلح والهجرة غير النظامية',
                     'Design livelihoods programmes to support affected households — prioritising youth programmes to address high unemployment, a risk factor for armed recruitment and irregular migration'),
                    ('تطوير آليات المنح الطارئة للتعافي السريع بعد الكوارث — بالنظر في نموذج التحويلات النقدية (Cash + Voucher) الذي أثبت فاعليته في سياقات الهشاشة المماثلة',
                     'Develop emergency grant mechanisms for rapid post-disaster recovery — considering Cash + Voucher Assistance (CVA) models which have proven effective in similar fragile settings'),
                    ('ربط الأسر الهشة بشبكات الحماية الاجتماعية المتاحة على المستوى الوطني والمحلي — مع مراعاة أن بعض الأسر تقع خارج أي شبكة رسمية بسبب النزوح وفقدان الوثائق',
                     'Link vulnerable households to available national and local social protection networks — noting that some families fall outside all formal networks due to displacement and loss of documents'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تطوير استراتيجية للمرونة الاقتصادية المحلية — تنويع مصادر الدخل بعيداً عن الاعتماد على توظيف الدولة الذي أضحى هشاً — ودعم الاقتصاد المحلي غير الرسمي',
                     'Develop a local economic resilience strategy — diversifying income sources away from state employment dependency which has become precarious — and support the informal local economy'),
                    ('إنشاء صناديق مجتمعية للطوارئ مبنية على الادخار المحلي ومبادئ التكافل — لتوفير شبكة أمان سريعة للأسر عند الأزمات دون الانتظار للمساعدة الحكومية',
                     'Establish community emergency savings funds built on local savings and takaful principles — providing rapid safety nets for families in crises without waiting for government assistance'),
                ]
            },
        ],
    },

    'healthcare_access_gap': {
        'label_ar': 'فجوة الوصول إلى الرعاية الصحية',
        'label_en': 'Healthcare Access Gap',
        'pillar_ar': 'مؤشر القدرة على التكيف',
        'pillar_en': 'Lack of Coping Capacity',
        'icon': 'bi-hospital',
        'sendai_priority': 4,
        'cluster_ar': 'مجموعة الصحة (WHO / وزارة الصحة) · مجموعة التغذية',
        'cluster_en': 'Health Cluster (WHO / MoH) · Nutrition Cluster',
        'gov_ar': 'وزارة الصحة · مديريات الصحة البلدية · المستشفيات الإقليمية',
        'gov_en': 'Ministry of Health · Municipal Health Directorates · Regional Hospitals',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('رسم الفجوات الجغرافية في الوصول إلى مرافق الرعاية الأولية والمستشفيات — ليبيا لديها 97 مستشفى عاماً و571 مركزاً صحياً لكن كثيراً منها يعاني من نقص الكوادر والأدوية والمعدات نتيجة الصراع والهجرة',
                     'Map geographical gaps in access to primary care and hospital facilities — Libya has 97 public hospitals and 571 health centres but many are severely understaffed and undersupplied due to conflict and the brain drain'),
                    ('تحديد الفئات الأصعب وصولاً إلى الرعاية الصحية — النساء والأطفال وكبار السن والنازحون والمهاجرون وسكان المناطق الجنوبية النائية — وتوثيق الحواجز المحددة لكل فئة',
                     'Identify groups with greatest difficulty accessing healthcare — women, children, elderly, IDPs, migrants, and residents of remote southern areas — documenting specific barriers for each group'),
                    ('تقييم مستوى توافر الأدوية الأساسية والمستلزمات الطبية في المرافق الصحية البلدية — والتنسيق مع مجموعة الصحة (WHO) لسد الفجوات العاجلة',
                     'Assess availability of essential medicines and medical supplies at municipal health facilities — coordinating with the Health Cluster (WHO) to address urgent gaps'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تفعيل مبادرة الطب عن بُعد لليبيا (TI4L) أو التنسيق معها لتوسيع وصول الاستشارات التخصصية في البلدية — وهي مبادرة نشطة تعالج نقص الأخصائيين الناجم عن هجرة الكوادر الطبية',
                     'Activate or coordinate with the Telemedicine Initiative for Libya (TI4L) to expand specialist consultation access in the municipality — this active initiative addresses the specialist shortage from medical brain drain'),
                    ('وضع خطة طوارئ صحية بلدية تتضمن بروتوكولات استيعاب الأعداد الكبيرة من المصابين (Mass Casualty) وتحديد مستشفيات الإحالة ومسارات الإخلاء الطبي',
                     'Develop a municipal health emergency plan including Mass Casualty Incident (MCI) protocols, referral hospital identification, and medical evacuation pathways'),
                    ('وضع بروتوكولات واضحة لتفعيل فرق الصحة الطارئة الدولية (WHO EMT) عند الحاجة — وذلك ضمن الإجراءات المنسّقة مع وزارة الصحة ومجموعة الصحة',
                     'Establish clear protocols for activating international WHO Emergency Medical Teams (EMTs) when needed — within procedures coordinated with the Ministry of Health and Health Cluster'),
                    ('دمج خدمات الصحة النفسية والدعم النفسي-الاجتماعي (MHPSS) في مرافق الرعاية الصحية الأولية — وفق إرشادات IASC للصحة النفسية في حالات الطوارئ — يُعدّ هذا الاندماج غائباً شبه تام في ليبيا',
                     'Integrate mental health and MHPSS into primary healthcare facilities — following IASC Mental Health in Emergencies guidelines — this integration is almost completely absent in Libya'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تطوير استراتيجية قوى عاملة صحية بلدية تعالج أزمة هجرة الكوادر — تشمل: برامج الاحتفاظ بالكوادر، واستقطاب أطباء الشتات الليبي، والشراكة مع جامعات ليبية للتدريب المحلي',
                     'Develop a municipal health workforce strategy addressing the brain drain crisis — including: staff retention programmes, engagement of the Libyan medical diaspora, and partnerships with Libyan universities for local training'),
                    ('إنشاء شبكة من العيادات الصحية المتنقلة للمجتمعات النائية وتجمعات النازحين — بالتنسيق مع IOM والهلال الأحمر الليبي وجماعات المجتمع المدني',
                     'Establish a network of mobile health clinics for remote communities and IDP settlements — coordinating with IOM, the Libyan Red Crescent, and civil society groups'),
                    ('دعم الإصلاح التدريجي لنظام الرعاية الأولية على المستوى البلدي — بما في ذلك تحديث المرافق وتدريب الكوادر وضمان استمرارية الإمداد بالأدوية والمستلزمات الطبية — بالتنسيق مع برامج منظمة الصحة العالمية لتعزيز الأنظمة الصحية',
                     'Support incremental primary healthcare reform at the municipal level — including facility upgrades, staff training, and medicine supply continuity — in coordination with WHO health systems strengthening programmes'),
                ]
            },
        ],
    },

}
