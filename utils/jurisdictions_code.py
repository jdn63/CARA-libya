"""
Wisconsin Public Health Jurisdictions

Generated from authoritative source: wi_health_departments.json

This file contains all Wisconsin health department jurisdictions.
- Each entry has a unique ID
- primary=True: Canonical entry for each unique health department (used in dropdowns)
- primary=False: Secondary entry for multi-county departments (used in GIS/HERC aggregation)

Total: 101 entries (95 unique health departments + 6 secondary multi-county entries)
- 84 county health departments
- 11 tribal health departments
- 5 multi-county departments with 6 secondary entries
"""

jurisdictions = [
    {
        'id': '1',
        'name': 'Adams County Health & Human Services',
        'county': 'Adams',
        'primary': True
    },
    {
        'id': '2',
        'name': 'Ashland County Health & Human Services',
        'county': 'Ashland',
        'primary': True
    },
    {
        'id': '3',
        'name': 'Barron County Department of Health & Human Services',
        'county': 'Barron',
        'primary': True
    },
    {
        'id': '4',
        'name': 'Bayfield County Health Department',
        'county': 'Bayfield',
        'primary': True
    },
    {
        'id': '5',
        'name': 'Brown County Health & Human Services Department',
        'county': 'Brown',
        'primary': True
    },
    {
        'id': '6',
        'name': 'DePere Department of Public Health',
        'county': 'Brown',
        'primary': True
    },
    {
        'id': '7',
        'name': 'Buffalo County Health & Human Services Department',
        'county': 'Buffalo',
        'primary': True
    },
    {
        'id': '8',
        'name': 'Burnett County Department of Health & Human Services',
        'county': 'Burnett',
        'primary': True
    },
    {
        'id': '9',
        'name': 'Appleton City Health Department',
        'county': 'Calumet',
        'primary': True
    },
    {
        'id': '10',
        'name': 'Calumet County Health & Human Services',
        'county': 'Calumet',
        'primary': True
    },
    {
        'id': '11',
        'name': 'City of Menasha Health Department',
        'county': 'Calumet',
        'primary': True
    },
    {
        'id': '12',
        'name': 'Chippewa County Department of Public Health',
        'county': 'Chippewa',
        'primary': True
    },
    {
        'id': '13',
        'name': 'Clark County Health Department',
        'county': 'Clark',
        'primary': True
    },
    {
        'id': '14',
        'name': 'Columbia County Health & Human Services',
        'county': 'Columbia',
        'primary': True
    },
    {
        'id': '15',
        'name': 'Crawford County Health & Human Services',
        'county': 'Crawford',
        'primary': True
    },
    {
        'id': '16',
        'name': 'Public Health - Madison & Dane County',
        'county': 'Dane',
        'primary': True
    },
    {
        'id': '17',
        'name': 'Dodge County Human Services & Health Department',
        'county': 'Dodge',
        'primary': True
    },
    {
        'id': '18',
        'name': 'Watertown Department of Public Health',
        'county': 'Dodge',
        'primary': True
    },
    {
        'id': '19',
        'name': 'Door County Department of Health & Human Services',
        'county': 'Door',
        'primary': True
    },
    {
        'id': '20',
        'name': 'Douglas County Department of Health & Human Services',
        'county': 'Douglas',
        'primary': True
    },
    {
        'id': '21',
        'name': 'Dunn County Health Department',
        'county': 'Dunn',
        'primary': True
    },
    {
        'id': '22',
        'name': 'Eau Claire City-County Health Department',
        'county': 'Eau Claire',
        'primary': True
    },
    {
        'id': '23',
        'name': 'Florence County Health Department',
        'county': 'Florence',
        'primary': True
    },
    {
        'id': '24',
        'name': 'Forest County Health Department',
        'county': 'Forest',
        'primary': True
    },
    {
        'id': '25',
        'name': 'Fond du Lac County Health Department',
        'county': 'Fond du Lac',
        'primary': True
    },
    {
        'id': '26',
        'name': 'Grant County Health Department',
        'county': 'Grant',
        'primary': True
    },
    {
        'id': '27',
        'name': 'Green County Public Health',
        'county': 'Green',
        'primary': True
    },
    {
        'id': '28',
        'name': 'Green Lake County Department of Health & Human Services',
        'county': 'Green Lake',
        'primary': True
    },
    {
        'id': '29',
        'name': 'Iowa County Health Department',
        'county': 'Iowa',
        'primary': True
    },
    {
        'id': '30',
        'name': 'Iron County Health Department',
        'county': 'Iron',
        'primary': True
    },
    {
        'id': '31',
        'name': 'Jackson County Public Health Department',
        'county': 'Jackson',
        'primary': True
    },
    {
        'id': '32',
        'name': 'Jefferson County Health Department',
        'county': 'Jefferson',
        'primary': True
    },
    {
        'id': '33',
        'name': 'Watertown Department of Public Health',
        'county': 'Jefferson',
        'primary': False
    },
    {
        'id': '34',
        'name': 'Juneau County Health Department',
        'county': 'Juneau',
        'primary': True
    },
    {
        'id': '35',
        'name': 'Kenosha County Division of Health',
        'county': 'Kenosha',
        'primary': True
    },
    {
        'id': '36',
        'name': 'Kewaunee County Public Health Department',
        'county': 'Kewaunee',
        'primary': True
    },
    {
        'id': '37',
        'name': 'La Crosse County Health Department',
        'county': 'La Crosse',
        'primary': True
    },
    {
        'id': '38',
        'name': 'Lafayette County Health Department',
        'county': 'Lafayette',
        'primary': True
    },
    {
        'id': '39',
        'name': 'Langlade County Health Department',
        'county': 'Langlade',
        'primary': True
    },
    {
        'id': '40',
        'name': 'Lincoln County Health Department',
        'county': 'Lincoln',
        'primary': True
    },
    {
        'id': '41',
        'name': 'Manitowoc County Health Department',
        'county': 'Manitowoc',
        'primary': True
    },
    {
        'id': '42',
        'name': 'Marathon County Health Department',
        'county': 'Marathon',
        'primary': True
    },
    {
        'id': '43',
        'name': 'Marinette County Health & Human Services',
        'county': 'Marinette',
        'primary': True
    },
    {
        'id': '44',
        'name': 'Marquette County Health Department',
        'county': 'Marquette',
        'primary': True
    },
    {
        'id': '45',
        'name': 'Shawano-Menominee Counties Health Department',
        'county': 'Menominee',
        'primary': True
    },
    {
        'id': '46',
        'name': 'Cudahy Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '47',
        'name': 'Franklin Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '48',
        'name': 'Greendale Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '49',
        'name': 'Hales Corners Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '50',
        'name': 'Milwaukee City Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '51',
        'name': 'North Shore Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '52',
        'name': 'Oak Creek Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '53',
        'name': 'South Milwaukee/St. Francis Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '54',
        'name': 'Southwest Suburban Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '55',
        'name': 'Wauwatosa Health Department',
        'county': 'Milwaukee',
        'primary': True
    },
    {
        'id': '56',
        'name': 'Monroe County Health Department',
        'county': 'Monroe',
        'primary': True
    },
    {
        'id': '57',
        'name': 'Oconto County Health & Human Services Department, Public Health Division',
        'county': 'Oconto',
        'primary': True
    },
    {
        'id': '58',
        'name': 'Oneida County Health Department',
        'county': 'Oneida',
        'primary': True
    },
    {
        'id': '59',
        'name': 'Appleton City Health Department',
        'county': 'Outagamie',
        'primary': False
    },
    {
        'id': '60',
        'name': 'Outagamie County Health & Human Services',
        'county': 'Outagamie',
        'primary': True
    },
    {
        'id': '61',
        'name': 'Washington Ozaukee Public Health Department',
        'county': 'Ozaukee',
        'primary': True
    },
    {
        'id': '62',
        'name': 'Pepin County Health Department',
        'county': 'Pepin',
        'primary': True
    },
    {
        'id': '63',
        'name': 'Pierce County Public Health Department',
        'county': 'Pierce',
        'primary': True
    },
    {
        'id': '64',
        'name': 'Polk County Health Department',
        'county': 'Polk',
        'primary': True
    },
    {
        'id': '65',
        'name': 'Portage County Health & Human Services',
        'county': 'Portage',
        'primary': True
    },
    {
        'id': '66',
        'name': 'Price County Health & Human Services',
        'county': 'Price',
        'primary': True
    },
    {
        'id': '67',
        'name': 'City of Racine Public Health Department',
        'county': 'Racine',
        'primary': True
    },
    {
        'id': '68',
        'name': 'Racine County Public Health Division',
        'county': 'Racine',
        'primary': True
    },
    {
        'id': '69',
        'name': 'Richland County Health & Human Services',
        'county': 'Richland',
        'primary': True
    },
    {
        'id': '70',
        'name': 'Rock County Public Health Department',
        'county': 'Rock',
        'primary': True
    },
    {
        'id': '71',
        'name': 'Rusk County Health & Human Services',
        'county': 'Rusk',
        'primary': True
    },
    {
        'id': '72',
        'name': 'Sauk County Health Department',
        'county': 'Sauk',
        'primary': True
    },
    {
        'id': '73',
        'name': 'Sawyer County Health & Human Services',
        'county': 'Sawyer',
        'primary': True
    },
    {
        'id': '74',
        'name': 'Shawano-Menominee Counties Health Department',
        'county': 'Shawano',
        'primary': False
    },
    {
        'id': '75',
        'name': 'Sheboygan County Health & Human Services',
        'county': 'Sheboygan',
        'primary': True
    },
    {
        'id': '76',
        'name': 'St. Croix County Health & Human Services',
        'county': 'St. Croix',
        'primary': True
    },
    {
        'id': '77',
        'name': 'Taylor County Health Department',
        'county': 'Taylor',
        'primary': True
    },
    {
        'id': '78',
        'name': 'Trempealeau County Health Department',
        'county': 'Trempealeau',
        'primary': True
    },
    {
        'id': '79',
        'name': 'Vernon County Public Health Department',
        'county': 'Vernon',
        'primary': True
    },
    {
        'id': '80',
        'name': 'Vilas County Public Health Department',
        'county': 'Vilas',
        'primary': True
    },
    {
        'id': '81',
        'name': 'Walworth County Department of Health & Human Services',
        'county': 'Walworth',
        'primary': True
    },
    {
        'id': '82',
        'name': 'Washburn County Health Department',
        'county': 'Washburn',
        'primary': True
    },
    {
        'id': '83',
        'name': 'Washington Ozaukee Public Health Department',
        'county': 'Washington',
        'primary': False
    },
    {
        'id': '84',
        'name': 'Waukesha County Department of Health & Human Services',
        'county': 'Waukesha',
        'primary': True
    },
    {
        'id': '85',
        'name': 'Waupaca County Department of Public Health',
        'county': 'Waupaca',
        'primary': True
    },
    {
        'id': '86',
        'name': 'Waushara County Health Department',
        'county': 'Waushara',
        'primary': True
    },
    {
        'id': '87',
        'name': 'Appleton City Health Department',
        'county': 'Winnebago',
        'primary': False
    },
    {
        'id': '88',
        'name': 'City of Menasha Health Department',
        'county': 'Winnebago',
        'primary': False
    },
    {
        'id': '89',
        'name': 'Winnebago County Health Department',
        'county': 'Winnebago',
        'primary': True
    },
    {
        'id': '90',
        'name': 'Wood County Health Department',
        'county': 'Wood',
        'primary': True
    },
    {
        'id': 'T01',
        'name': 'Bad River Band of Lake Superior Chippewa',
        'county': 'Ashland',
        'primary': True
    },
    {
        'id': 'T02',
        'name': 'Forest County Potawatomi Community',
        'county': 'Forest',
        'primary': True
    },
    {
        'id': 'T03',
        'name': 'Ho-Chunk Nation Health Department',
        'county': 'Jackson',
        'primary': True
    },
    {
        'id': 'T04',
        'name': 'Lac Courte Oreilles Band of Lake Superior Chippewa',
        'county': 'Sawyer',
        'primary': True
    },
    {
        'id': 'T05',
        'name': 'Lac du Flambeau Band of Lake Superior Chippewa',
        'county': 'Vilas',
        'primary': True
    },
    {
        'id': 'T06',
        'name': 'Menominee Indian Tribe of Wisconsin',
        'county': 'Menominee',
        'primary': True
    },
    {
        'id': 'T07',
        'name': 'Oneida Nation Health Department',
        'county': 'Brown',
        'primary': True
    },
    {
        'id': 'T08',
        'name': 'Red Cliff Band of Lake Superior Chippewa',
        'county': 'Bayfield',
        'primary': True
    },
    {
        'id': 'T09',
        'name': 'Sokaogon Chippewa Community (Mole Lake)',
        'county': 'Forest',
        'primary': True
    },
    {
        'id': 'T10',
        'name': 'St. Croix Chippewa Indians of Wisconsin',
        'county': 'Burnett',
        'primary': True
    },
    {
        'id': 'T11',
        'name': 'Stockbridge-Munsee Community',
        'county': 'Shawano',
        'primary': True
    },
]
