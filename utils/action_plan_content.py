"""
Libya CARA — Action Plan Guidance Content
Aligned to Sendai Framework (2015-2030) and UN Cluster System.

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
                    ('تقييم قدرات المراقبة الوبائية على المستوى البلدي وتحديد الفجوات الرئيسية',
                     'Assess municipal epidemiological surveillance capacity and identify key gaps'),
                    ('تحديث بروتوكولات الاستجابة لتفشي الأمراض ذات الأولوية — التدرن الرئوي والأمراض المائية والتهابات الجهاز التنفسي',
                     'Update outbreak response protocols for priority diseases — TB, waterborne illnesses, and respiratory infections'),
                    ('التحقق من معدلات التغطية بالتطعيم والتنسيق مع منظمة الصحة العالمية لسدّ أي ثغرات',
                     'Verify vaccination coverage rates and coordinate with WHO to close any gaps'),
                    ('مراجعة توفر الأدوية الأساسية والمستلزمات الطبية في المرافق الصحية المحلية',
                     'Review essential medicines and medical supplies availability at local health facilities'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تعزيز نقاط المراقبة الوبائية في مرافق الرعاية الأولية وربطها بالنظام الوطني لـ NCDC',
                     'Strengthen disease surveillance nodes at primary care facilities and link to NCDC national system'),
                    ('إعداد خطط التواصل الصحي باللغة العربية للأمراض ذات الأولوية',
                     'Develop Arabic-language health communication plans for priority diseases'),
                    ('إجراء تمارين محاكاة للاستجابة لحالات تفشي الأمراض مع الطواقم الصحية البلدية',
                     'Conduct outbreak response simulation exercises with municipal health teams'),
                    ('تعزيز قدرات المختبر الصحي البلدي بالتنسيق مع NCDC',
                     'Strengthen municipal health laboratory capacity in coordination with NCDC'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('بناء نظام مراقبة وبائية متكامل يربط البلديات بالمركز الوطني ويدعم الإنذار المبكر',
                     'Build integrated epidemiological surveillance system linking municipalities to the national centre and supporting early warning'),
                    ('إنشاء شبكة عمال صحة مجتمعية مدرّبة على الكشف المبكر والإبلاغ الفوري',
                     'Establish community health worker network trained in early detection and immediate reporting'),
                    ('الانخراط في منظومة التأهب الصحي الإقليمية وفق اللوائح الصحية الدولية (IHR)',
                     'Engage with regional health preparedness system under International Health Regulations (IHR)'),
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
                    ('إجراء تقييم سريع للبنية التحتية الحيوية — المستشفيات والمدارس وشبكات المياه ومحطات الطاقة',
                     'Conduct rapid assessment of critical infrastructure — hospitals, schools, water networks, and power stations'),
                    ('تحديد نقاط الضعف في شبكات الصرف الصحي والمياه المعرضة للفيضانات',
                     'Identify vulnerabilities in sanitation and water networks exposed to flooding'),
                    ('رسم خرائط للبنية التحتية الحيوية في كل بلدية لدعم التخطيط للطوارئ',
                     'Map critical infrastructure in each municipality to support emergency planning'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('وضع معايير إنشاء مقاومة للمخاطر للمرافق الحيوية بالتنسيق مع وزارة الإسكان',
                     'Develop hazard-resistant construction standards for critical facilities with Ministry of Housing'),
                    ('تقييم مخزون المولدات الاحتياطية والطاقة في المرافق الصحية والمدارس',
                     'Assess backup generator and energy inventory at health facilities and schools'),
                    ('وضع خطط استمرارية الخدمات للمرافق الحيوية خلال حالات الطوارئ',
                     'Develop service continuity plans for critical facilities during emergencies'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تنفيذ برنامج تعزيز مقاومة البنية التحتية بتمويل مشترك من الحكومة والمانحين الدوليين',
                     'Implement infrastructure resilience programme with joint government-international donor financing'),
                    ('دمج اعتبارات مخاطر الكوارث في مدونات البناء الوطنية والتخطيط العمراني للبلديات',
                     'Integrate disaster risk considerations into national building codes and municipal urban planning'),
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
                    ('مراجعة دروس المستفادة من إعصار دانيال 2023 وتحديد ثغرات الإنذار المبكر والاستجابة',
                     'Review lessons from Cyclone Daniel 2023 and identify early warning and response gaps'),
                    ('رسم خرائط مناطق الخطر للفيضانات في البلدية — الأودية والمناطق الساحلية والتجمعات السكانية المعرضة',
                     'Map flood hazard zones in the municipality — wadis, coastal areas, and exposed settlements'),
                    ('التحقق من خطط الإخلاء المجتمعي للمناطق الساحلية والقريبة من الأودية',
                     'Verify community evacuation plans for coastal and wadi-adjacent zones'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('العمل مع المركز الوطني للأرصاد الجوية لإنشاء نظام إنذار مبكر للفيضانات على المستوى البلدي',
                     'Work with National Met Centre to establish municipal-level flood early warning system'),
                    ('إجراء تقييم سلامة السدود والخزانات المائية في المناطق المعرضة للخطر',
                     'Conduct dam and water reservoir safety assessment in at-risk areas'),
                    ('تدريب فرق الحماية المدنية البلدية على البحث والإنقاذ في بيئات الفيضانات',
                     'Train municipal Civil Protection teams on flood search-and-rescue'),
                    ('تجهيز واحتياط مخزون طوارئ من الغذاء والماء والمستلزمات الإغاثية في المستودعات البلدية',
                     'Pre-position emergency food, water, and relief supply stockpile at municipal warehouses'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تطوير خطة وطنية للتكيف المناخي تشمل سيناريوهات الفيضانات والجفاف وارتفاع مستوى سطح البحر',
                     'Develop national climate adaptation plan covering flood, drought, and sea-level rise scenarios'),
                    ('دمج رسم خرائط مخاطر الكوارث في التخطيط العمراني لجميع البلديات الليبية',
                     'Integrate disaster hazard mapping into urban planning for all Libyan municipalities'),
                    ('إنشاء صندوق وطني للطوارئ مع آليات تمويل التعافي وإعادة الإعمار',
                     'Establish national disaster emergency fund with recovery and reconstruction financing mechanisms'),
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
                    ('رسم خرائط لنقاط الحوادث المرورية الخطيرة داخل حدود البلدية',
                     'Map high-risk road accident locations within municipal boundaries'),
                    ('تقييم قدرات الإسعاف والاستجابة الطبية الطارئة في المناطق المعزولة',
                     'Assess ambulance and emergency medical response capacity in isolated areas'),
                    ('مراجعة إجراءات الاستجابة للحوادث الكبرى مع الهلال الأحمر والخدمات الصحية',
                     'Review mass-casualty road incident procedures with Red Crescent and health services'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تطوير نظام بيانات حوادث المرور البلدية لرصد الأنماط والتخطيط للتدخل',
                     'Develop municipal road accident data system to monitor patterns and plan interventions'),
                    ('تحديد الطرق الحيوية للإخلاء الطارئ والتأكد من قابليتها للعبور في جميع الأوقات',
                     'Identify critical evacuation routes and verify their passability at all times'),
                    ('تدريب المسعفين والمتطوعين على الإسعافات الأولية وإيقاف النزيف والإنعاش القلبي الرئوي',
                     'Train first responders and volunteers in first aid, haemorrhage control, and CPR'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تحديث البنية التحتية للطرق الرئيسية مع إدماج معايير السلامة المرورية الدولية',
                     'Upgrade key road infrastructure incorporating international road safety standards'),
                    ('تطوير شبكة إسعاف وطنية مع مراكز تنسيق بلدية في المناطق النائية',
                     'Develop national ambulance network with municipal coordination centres in remote areas'),
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
        'cluster_ar': 'مجموعة الحماية · المفوضية السامية للأمم المتحدة (UNHCR) · IOM',
        'cluster_en': 'Protection Cluster · UNHCR · IOM',
        'gov_ar': 'وزارة الداخلية · اللجان المحلية للسلامة',
        'gov_en': 'Ministry of Interior · Local Safety Committees',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('رسم خرائط للمجتمعات الأكثر عرضة للمخاطر الأمنية ومناطق الوصول المحدود',
                     'Map communities most exposed to security risks and areas of limited access'),
                    ('التأكد من وصول خدمات الحماية الإنسانية إلى السكان النازحين والأكثر هشاشة',
                     'Ensure humanitarian protection services reach displaced and most vulnerable populations'),
                    ('إنشاء قنوات تواصل آمنة وسرية للإبلاغ عن انتهاكات الحماية',
                     'Establish safe and confidential reporting channels for protection violations'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تعزيز دور اللجان المجتمعية في تقييم المخاطر وإدارة النزاعات المحلية',
                     'Strengthen community committees in risk assessment and local conflict management'),
                    ('الانخراط مع المنظمات الإنسانية لضمان استمرارية الخدمات في المناطق عالية المخاطر',
                     'Engage humanitarian organisations to ensure service continuity in high-risk areas'),
                    ('تطوير بروتوكولات مشتركة للاستجابة للحوادث الأمنية الطارئة',
                     'Develop joint response protocols for emergency security incidents'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('دمج برامج تخفيف المخاطر الأمنية في الخطط التنموية المحلية',
                     'Integrate security risk reduction programmes into local development plans'),
                    ('بناء آليات للحوار المجتمعي وتخفيف التوترات لدعم الاستقرار طويل الأمد',
                     'Build community dialogue and tension-reduction mechanisms for long-term stability'),
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
                    ('تقييم القدرات المؤسسية الحالية للمجلس البلدي في إدارة الكوارث والطوارئ',
                     'Assess current institutional capacity of municipal council in disaster and emergency management'),
                    ('تحديد الأفراد الرئيسيين المسؤولين عن الطوارئ وتوثيق أدوارهم ومسؤولياتهم',
                     'Identify key emergency management personnel and document their roles and responsibilities'),
                    ('مراجعة الأطر القانونية المحلية لإدارة الكوارث وتحديد الفجوات التشريعية',
                     'Review local legal frameworks for disaster management and identify legislative gaps'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تطوير خطة استجابة للطوارئ على مستوى البلدية تحدد الأدوار والموارد وسلاسل القيادة',
                     'Develop municipal emergency response plan defining roles, resources, and chains of command'),
                    ('تدريب الكوادر البلدية على أسس إدارة الكوارث وفق منهجية إطار سيندا',
                     'Train municipal staff on disaster management fundamentals using the Sendai Framework methodology'),
                    ('إنشاء قاعدة بيانات بلدية لتوثيق الأصول والموارد والكفاءات المتاحة',
                     'Establish municipal database documenting available assets, resources, and competencies'),
                    ('بناء شراكات مع المنظمات الدولية (UNDP، UN-Habitat) لتعزيز القدرات',
                     'Build partnerships with international organisations (UNDP, UN-Habitat) for capacity strengthening'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('إنشاء وحدة مخصصة لإدارة الكوارث داخل الهيكل التنظيمي الرسمي للمجلس البلدي',
                     'Establish a dedicated disaster management unit within the formal organisational structure of the municipal council'),
                    ('الانضمام إلى آليات التنسيق الوطنية لإدارة الكوارث وإدارة المعلومات',
                     'Join national disaster management coordination and information management mechanisms'),
                    ('وضع خطة للتطوير المهني لكوادر إدارة الطوارئ البلدية',
                     'Develop a professional development plan for the municipal emergency management cadre'),
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
                    ('رسم خرائط للأحياء غير الرسمية والمناطق السكانية المعرضة لمخاطر الفيضانات والحرائق والنفايات',
                     'Map informal settlements and residential areas exposed to flood, fire, and waste risks'),
                    ('تحديد المباني الآيلة للسقوط أو التي تفتقر إلى معايير السلامة الهيكلية الأساسية',
                     'Identify structurally unsafe buildings lacking basic safety standards'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تطوير خطة عمرانية تشاركية تشمل الأحياء غير الرسمية وتدمج اعتبارات مخاطر الكوارث',
                     'Develop participatory urban plan including informal areas and integrating disaster risk considerations'),
                    ('تحسين البنية التحتية للمياه والصرف الصحي في المناطق الأكثر كثافة وهشاشة',
                     'Improve water and sanitation infrastructure in most densely populated and vulnerable areas'),
                    ('برامج توعية لسكان المناطق العشوائية حول ممارسات البناء الآمن ومخاطر الكوارث',
                     'Awareness programmes for residents of informal areas on safe building practices and disaster risks'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تنفيذ مشاريع تحسين الأحياء العشوائية مع تكامل الخدمات الأساسية',
                     'Implement informal settlement upgrading projects with integrated basic services'),
                    ('إنشاء نظام رقابة على البناء لتطبيق كودات الإنشاء وتوثيق التراخيص',
                     'Establish building control system to enforce construction codes and document permits'),
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
                    ('تحديث بيانات النازحين داخلياً على المستوى البلدي بالتنسيق مع IOM DTM',
                     'Update IDP data at municipal level in coordination with IOM DTM'),
                    ('التأكد من وصول النازحين إلى الخدمات الأساسية — الصحة والتعليم والمياه والغذاء',
                     'Ensure IDPs have access to basic services — health, education, water, and food'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('وضع خطط الحلول الدائمة للعودة الطوعية والاستقرار في المناطق الأكثر هشاشة',
                     'Develop durable solutions and voluntary return plans for most vulnerable areas'),
                    ('دعم برامج حماية النازحين والمهاجرين عبر الشراكة مع IOM وUNHCR',
                     'Support IDP and migrant protection programmes through partnership with IOM and UNHCR'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('إدماج النازحين في السياسات التنموية المحلية وبرامج الخدمات البلدية',
                     'Integrate IDPs into local development policies and municipal services programmes'),
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
                    ('تطوير حملات توعية صحية باللغة العربية حول الوقاية من الأمراض والسلوكيات الطارئة',
                     'Develop Arabic-language health awareness campaigns on disease prevention and emergency behaviours'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('تدريب عمال الصحة المجتمعية على التثقيف الصحي ومخاطر الأمراض المنقولة بالمياه',
                     'Train community health workers on health education and waterborne disease risks'),
                    ('إدماج التوعية الصحية في المناهج المدرسية والأنشطة المجتمعية',
                     'Integrate health awareness into school curricula and community activities'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('بناء شبكة متكاملة للصحة المجتمعية تضم المدارس والمساجد والمراكز الاجتماعية',
                     'Build integrated community health network involving schools, mosques, and social centres'),
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
                    ('إجراء تقييم لزمن الاستجابة الحالي لخدمات الطوارئ البلدية وتحديد العوائق الرئيسية',
                     'Assess current emergency response times for municipal services and identify key obstacles'),
                    ('إنشاء أو تحديث غرفة عمليات الطوارئ البلدية مع إجراءات تشغيل موحدة موثقة',
                     'Establish or update municipal emergency operations room with documented standard operating procedures'),
                    ('تطوير دليل جهات الاتصال الطارئ وسلاسل القيادة لجميع خدمات الاستجابة',
                     'Develop emergency contact directory and chains of command for all response services'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('إجراء تمارين محاكاة للاستجابة للطوارئ تشمل جميع الجهات الرئيسية',
                     'Conduct multi-stakeholder emergency response simulation exercises'),
                    ('تحسين منظومة الاتصالات الطارئة مع إنشاء قنوات بديلة احتياطية',
                     'Improve emergency communications system with backup and redundant channels'),
                    ('تحديد مسبق لنقاط التجمع ومراكز الإخلاء المجهزة على مستوى البلدية',
                     'Pre-identify and equip assembly points and evacuation centres at municipal level'),
                    ('ربط خطة البلدية بالمستوى الإقليمي والوطني لضمان سرعة التدخل',
                     'Link municipal plan to regional and national levels to ensure rapid intervention'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تطوير قدرات الاستجابة المحلية عبر تدريب وتجهيز الفرق البلدية المتخصصة',
                     'Develop local response capacity by training and equipping specialised municipal emergency teams'),
                    ('إنشاء نظام دوري لمراقبة وتحليل زمن الاستجابة وأداء الخدمات الطارئة',
                     'Establish periodic system to monitor and analyse response times and emergency service performance'),
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
                    ('رسم خرائط لمنظمات المجتمع المدني والمتطوعين والشبكات الاجتماعية الفاعلة على مستوى البلدية',
                     'Map civil society organisations, volunteers, and active social networks at municipal level'),
                    ('التواصل مع الهلال الأحمر الليبي ومنظمات المجتمع المدني لتقييم إمكانات التعاون',
                     'Engage Libyan Red Crescent and civil society organisations to assess cooperation potential'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('إنشاء شبكة متطوعين مجتمعيين للاستجابة للطوارئ وتقديم الدعم النفسي الاجتماعي',
                     'Establish community volunteer network for emergency response and psychosocial support'),
                    ('تطوير برامج الحماية الاجتماعية للفئات الأكثر هشاشة بالشراكة مع المنظمات المحلية',
                     'Develop social protection programmes for most vulnerable groups with local partners'),
                    ('توثيق الموارد المجتمعية وأنماط التضامن الاجتماعي التقليدية التي تدعم الصمود',
                     'Document community resources and traditional social solidarity patterns that support resilience'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('إنشاء مراكز مجتمعية للصمود والتضامن في كل بلدية تجمع بين الخدمات الاجتماعية وإدارة المخاطر',
                     'Establish community resilience and solidarity centres in each municipality combining social services and risk management'),
                    ('دمج صناديق الطوارئ المجتمعية ضمن آليات الحوكمة المحلية والتخطيط البلدي',
                     'Integrate community emergency funds within local governance mechanisms and municipal planning'),
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
                    ('تحديد الأسر الأكثر هشاشة اقتصادياً وتحديث سجلات التحويلات الاجتماعية',
                     'Identify most economically vulnerable households and update social transfer records'),
                    ('التنسيق مع مجموعة الأمن الغذائي لضمان توزيع الغذاء للأسر عالية الخطورة',
                     'Coordinate with Food Security Cluster to ensure food distribution to high-risk households'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('وضع برامج سبل العيش لدعم الأسر المتضررة وتقوية القدرة الاقتصادية على الصمود',
                     'Design livelihoods programmes to support affected households and strengthen economic resilience'),
                    ('تطوير آليات إعانات الطوارئ للتعافي السريع بعد الكوارث',
                     'Develop emergency grant mechanisms for rapid post-disaster recovery'),
                    ('ربط الأسر الهشة بشبكات الحماية الاجتماعية الوطنية والبلدية',
                     'Link vulnerable households to national and municipal social protection networks'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('تطوير استراتيجية للمرونة الاقتصادية المحلية تشمل تنويع مصادر الدخل وتنمية المهارات',
                     'Develop local economic resilience strategy including income diversification and skills development'),
                    ('إنشاء صناديق مجتمعية للطوارئ وآليات تمويل التعافي تعتمد على المدخرات المحلية',
                     'Establish community emergency funds and recovery financing mechanisms based on local savings'),
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
                    ('رسم الفجوات الجغرافية في الوصول إلى مرافق الرعاية الأولية والمستشفيات',
                     'Map geographical gaps in access to primary care facilities and hospitals'),
                    ('تحديد الفئات الأصعب وصولاً إلى الرعاية الصحية — النساء والأطفال وكبار السن والنازحون',
                     'Identify groups with greatest difficulty accessing healthcare — women, children, elderly, and IDPs'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('توسيع التغطية الصحية الإقليمية عبر عيادات متنقلة في المناطق النائية ضعيفة التغطية',
                     'Expand regional health coverage through mobile clinics in remote, poorly-covered areas'),
                    ('تعزيز الكوادر البشرية في المرافق الصحية ذات الطاقة الاستيعابية المنخفضة',
                     'Strengthen human resources at health facilities with low capacity'),
                    ('ضمان توافر الأدوية الأساسية وإمدادات الطوارئ في المرافق الطرفية',
                     'Ensure essential medicines and emergency health supplies are available at peripheral facilities'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('بناء مرافق رعاية صحية أولية جديدة في المناطق ذات الكثافة السكانية العالية وضعف التغطية',
                     'Build new primary healthcare facilities in densely populated, poorly-covered areas'),
                    ('تطوير نظام إحالة طبية متكامل بين المستويات الأولي والثانوي والثالثي',
                     'Develop integrated medical referral system across primary, secondary, and tertiary levels'),
                ]
            },
        ],
    },

    'data_availability_gap': {
        'label_ar': 'فجوة توفر البيانات وإدارة المعلومات',
        'label_en': 'Data Availability & Information Management Gap',
        'pillar_ar': 'مؤشر القدرة على التكيف',
        'pillar_en': 'Lack of Coping Capacity',
        'icon': 'bi-database-exclamation',
        'sendai_priority': 4,
        'cluster_ar': 'إدارة المعلومات الإنسانية · OCHA · UNFPA',
        'cluster_en': 'Humanitarian Information Management · OCHA · UNFPA',
        'gov_ar': 'وزارة التخطيط · الجهاز المركزي للإحصاء · وزارة الصحة',
        'gov_en': 'Ministry of Planning · Central Statistics Authority · Ministry of Health',
        'actions': [
            {
                'term_ar': 'فوري (0–3 أشهر)',
                'term_en': 'Immediate (0–3 months)',
                'items': [
                    ('تقييم توفر البيانات الأساسية على المستوى البلدي وتوثيق فجوات المعلومات',
                     'Assess availability of basic data at municipal level and document information gaps'),
                    ('التواصل مع OCHA وHDX لاستخدام البيانات الإنسانية المتاحة وسدّ الفجوات',
                     'Engage with OCHA and HDX to use available humanitarian data and fill information gaps'),
                ]
            },
            {
                'term_ar': 'قصير المدى (3–12 شهراً)',
                'term_en': 'Short-term (3–12 months)',
                'items': [
                    ('إنشاء نظام بلدي لجمع البيانات الأساسية والتحديث الدوري المنتظم',
                     'Establish municipal system for collecting basic data and regular periodic updates'),
                    ('التدريب على إدارة المعلومات الإنسانية بالتنسيق مع OCHA وشركاء المعلومات',
                     'Train in humanitarian information management in coordination with OCHA and information partners'),
                ]
            },
            {
                'term_ar': 'بعيد المدى (1–3 سنوات)',
                'term_en': 'Long-term (1–3 years)',
                'items': [
                    ('بناء منظومة بيانات وطنية متكاملة تربط المستوى البلدي بالمركزي لدعم صنع القرار',
                     'Build integrated national data ecosystem linking municipal to central level to support evidence-based decision-making'),
                ]
            },
        ],
    },
}


def _score_to_level(score):
    """Mirror of routes.dashboard._score_to_level — kept here to avoid circular import."""
    if score is None:
        return 'unavailable'
    if score >= 0.8:
        return 'critical'
    if score >= 0.6:
        return 'high'
    if score >= 0.4:
        return 'moderate'
    if score >= 0.2:
        return 'low'
    return 'minimal'


def get_action_domains(pillar_data: dict, min_score: float = 0.15) -> list:
    """
    Return a sorted list of action domain dicts, each enriched with:
        score, level, pillar_key, and the full guidance from ACTION_GUIDANCE.
    Only includes domains with score >= min_score.
    Sorted descending by score (highest priority first).
    """
    domains = []
    for pillar_key in ('hazard', 'vulnerability', 'coping'):
        pillar = pillar_data.get(pillar_key, {})
        components = pillar.get('components', {})
        for comp_key, score in components.items():
            if score is None:
                continue
            score_f = float(score)
            if score_f < min_score:
                continue
            guidance = ACTION_GUIDANCE.get(comp_key)
            if not guidance:
                continue
            level = _score_to_level(score_f)
            domains.append({
                'key':        comp_key,
                'score':      score_f,
                'score_10':   round(score_f * 10, 1),
                'level':      level,
                'pillar_key': pillar_key,
                **guidance,
            })

    domains.sort(key=lambda d: d['score'], reverse=True)
    return domains
