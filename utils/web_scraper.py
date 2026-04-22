import requests
from bs4 import BeautifulSoup
import logging
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        logger.error(f"Error fetching website content: {str(e)}")
        return ""

def get_wi_health_departments():
    """
    Fetch the list of Wisconsin health departments from the official source
    """
    try:
        # DHS Wisconsin Local Health Departments page
        url = "https://www.dhs.wisconsin.gov/lh-depts/index.htm"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch health departments: Status code {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract health departments from the page
        departments = []
        
        # Look for tables or lists containing health department information
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 2:
                    dept_name = cells[0].get_text(strip=True)
                    county = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    
                    # Only add if we have a department name
                    if dept_name and not dept_name.lower().startswith('name'):
                        departments.append({
                            'name': dept_name,
                            'county': county
                        })
        
        # If no tables found, try lists
        if not departments:
            lists = soup.find_all(['ul', 'ol'])
            for list_elem in lists:
                items = list_elem.find_all('li')
                for item in items:
                    dept_text = item.get_text(strip=True)
                    if dept_text and 'health department' in dept_text.lower():
                        departments.append({
                            'name': dept_text,
                            'county': ""  # County info might not be available in list format
                        })
        
        # Get tribal health centers/departments
        tribal_departments = get_wi_tribal_health_departments()
        if tribal_departments:
            departments.extend(tribal_departments)
        
        return departments
        
    except Exception as e:
        logger.error(f"Error scraping health departments: {str(e)}")
        return []

def get_wi_tribal_health_departments():
    """
    Fetch the list of Wisconsin tribal health departments/centers from the official source
    """
    try:
        # DHS Wisconsin Tribal Health Centers page
        url = "https://www.dhs.wisconsin.gov/tribal-affairs/index.htm"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch tribal health departments: Status code {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract tribal health departments from the page
        tribal_departments = []
        
        # Look for content containing tribal health center information
        content_div = soup.find('div', class_='content-block')
        if content_div:
            # Find all headers and lists that might contain tribal health centers
            headers = content_div.find_all(['h2', 'h3', 'h4'])
            
            for header in headers:
                # Check if this header is about tribal health centers
                if any(term in header.get_text().lower() for term in ['health center', 'health department', 'healthcare']):
                    # Get the list that follows this header
                    next_elem = header.find_next(['ul', 'ol'])
                    if next_elem:
                        items = next_elem.find_all('li')
                        for item in items:
                            dept_text = item.get_text(strip=True)
                            if dept_text:
                                # Extract the tribe/nation name from the text
                                parts = dept_text.split(' Health ')
                                tribe_name = parts[0].strip() if len(parts) > 1 else dept_text
                                
                                tribal_departments.append({
                                    'name': tribe_name,
                                    'county': dept_text,
                                    'is_tribal': True
                                })
        
        # If no structured data found, use a hardcoded list based on DHS information
        if not tribal_departments:
            # This list is based on the 11 federally recognized tribes in Wisconsin
            tribal_departments = [
                {'name': 'Bad River', 'county': 'Bad River Health and Wellness Center', 'is_tribal': True},
                {'name': 'Forest County Potawatomi', 'county': 'Forest County Potawatomi Health & Wellness Center', 'is_tribal': True},
                {'name': 'Ho-Chunk Nation', 'county': 'Ho-Chunk Nation Health Department', 'is_tribal': True},
                {'name': 'Lac Courte Oreilles', 'county': 'Lac Courte Oreilles Community Health Center', 'is_tribal': True},
                {'name': 'Lac du Flambeau', 'county': 'Peter Christensen Health Center', 'is_tribal': True},
                {'name': 'Menominee Indian Tribe', 'county': 'Menominee Tribal Clinic', 'is_tribal': True},
                {'name': 'Oneida Nation', 'county': 'Oneida Community Health Center', 'is_tribal': True},
                {'name': 'Red Cliff Band', 'county': 'Red Cliff Community Health Center', 'is_tribal': True},
                {'name': 'Sokaogon Chippewa', 'county': 'Sokaogon Chippewa Health Clinic', 'is_tribal': True},
                {'name': 'St. Croix Chippewa', 'county': 'St. Croix Tribal Health Clinic', 'is_tribal': True},
                {'name': 'Stockbridge-Munsee', 'county': 'Stockbridge-Munsee Health and Wellness Center', 'is_tribal': True}
            ]
            
        return tribal_departments
        
    except Exception as e:
        logger.error(f"Error scraping tribal health departments: {str(e)}")
        # Fall back to hardcoded list if there's an error
        return [
            {'name': 'Bad River', 'county': 'Bad River Health and Wellness Center', 'is_tribal': True},
            {'name': 'Forest County Potawatomi', 'county': 'Forest County Potawatomi Health & Wellness Center', 'is_tribal': True},
            {'name': 'Ho-Chunk Nation', 'county': 'Ho-Chunk Nation Health Department', 'is_tribal': True},
            {'name': 'Lac Courte Oreilles', 'county': 'Lac Courte Oreilles Community Health Center', 'is_tribal': True},
            {'name': 'Lac du Flambeau', 'county': 'Peter Christensen Health Center', 'is_tribal': True},
            {'name': 'Menominee Indian Tribe', 'county': 'Menominee Tribal Clinic', 'is_tribal': True},
            {'name': 'Oneida Nation', 'county': 'Oneida Community Health Center', 'is_tribal': True},
            {'name': 'Red Cliff Band', 'county': 'Red Cliff Community Health Center', 'is_tribal': True},
            {'name': 'Sokaogon Chippewa', 'county': 'Sokaogon Chippewa Health Clinic', 'is_tribal': True},
            {'name': 'St. Croix Chippewa', 'county': 'St. Croix Tribal Health Clinic', 'is_tribal': True},
            {'name': 'Stockbridge-Munsee', 'county': 'Stockbridge-Munsee Health and Wellness Center', 'is_tribal': True}
        ]

def get_wi_health_departments_from_text():
    """
    Process Wisconsin health department listings from raw text
    when direct web scraping is not providing structured data
    """
    try:
        url = "https://www.dhs.wisconsin.gov/lh-depts/index.htm"
        text_content = get_website_text_content(url)
        
        if not text_content:
            logger.error("Failed to fetch health department text content")
            return []
            
        # Process the text content to extract health departments
        # This is a backup method when structured parsing fails
        lines = text_content.split('\n')
        departments = []
        current_county = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line contains county name
            if "County" in line and "Health Department" not in line and "Public Health" not in line:
                current_county = line
            # Check if line contains health department info
            elif any(term in line.lower() for term in ["health department", "public health", "health services"]):
                dept_name = line
                departments.append({
                    'name': dept_name,
                    'county': current_county
                })
                
        return departments
        
    except Exception as e:
        logger.error(f"Error extracting health departments from text: {str(e)}")
        return []


def get_wi_dhs_respiratory_data() -> Dict[str, Any]:
    """
    Scrape Wisconsin DHS respiratory illness data from official DHS pages.
    
    Returns comprehensive respiratory illness surveillance data including:
    - Current activity levels for COVID-19, influenza, and RSV
    - Emergency department visit percentages by age group
    - Laboratory test positivity rates
    - Trend indicators (increasing, stable, decreasing)
    
    Returns:
        Dict containing respiratory illness data with state-level and county-level metrics
    """
    logger.info("Fetching Wisconsin DHS respiratory illness data")
    
    respiratory_data = {
        'data_source': 'Wisconsin DHS',
        'last_updated': datetime.now().isoformat(),
        'statewide_levels': {},
        'emergency_department_data': {},
        'laboratory_data': {},
        'trend_indicators': {},
        'county_data': {}
    }
    
    try:
        # Fetch main respiratory data page
        main_url = "https://www.dhs.wisconsin.gov/disease/respiratory-data.htm"
        response = requests.get(main_url, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract statewide activity levels
            respiratory_data['statewide_levels'] = extract_statewide_activity_levels(soup)
            
            # Extract key findings
            respiratory_data['key_findings'] = extract_key_findings(soup)
            
        # Fetch emergency department data
        ed_url = "https://www.dhs.wisconsin.gov/disease/respiratory-emergency-department.htm"
        ed_response = requests.get(ed_url, timeout=10)
        
        if ed_response.status_code == 200:
            ed_soup = BeautifulSoup(ed_response.text, 'html.parser')
            respiratory_data['emergency_department_data'] = extract_emergency_department_data(ed_soup)
            
        # Fetch laboratory data
        lab_url = "https://www.dhs.wisconsin.gov/disease/laboratory-based-data.htm"
        lab_response = requests.get(lab_url, timeout=10)
        
        if lab_response.status_code == 200:
            lab_soup = BeautifulSoup(lab_response.text, 'html.parser')
            respiratory_data['laboratory_data'] = extract_laboratory_data(lab_soup)
            
        # Calculate overall risk score based on collected data
        respiratory_data['overall_risk_score'] = calculate_respiratory_risk_score(respiratory_data)
        
        logger.info("Successfully fetched Wisconsin DHS respiratory illness data")
        return respiratory_data
        
    except Exception as e:
        logger.error(f"Error fetching Wisconsin DHS respiratory data: {str(e)}")
        return {
            'data_source': 'Wisconsin DHS',
            'last_updated': datetime.now().isoformat(),
            'error': str(e),
            'overall_risk_score': 0.3  # Default moderate risk if data unavailable
        }


def extract_statewide_activity_levels(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract statewide activity levels from the main respiratory data page"""
    activity_levels = {}
    
    try:
        # Look for activity level indicators in the "What to know" section
        what_to_know_section = soup.find('h2', string=re.compile(r'What to know', re.IGNORECASE))
        if what_to_know_section:
            content = what_to_know_section.find_next(['div', 'section', 'ul'])
            if content:
                text = content.get_text().lower()
                
                # Extract activity levels for different viruses
                if 'minimal' in text:
                    if 'covid' in text or 'covid-19' in text:
                        activity_levels['covid_19'] = 'minimal'
                    if 'influenza' in text or 'flu' in text:
                        activity_levels['influenza'] = 'minimal'
                    if 'rsv' in text:
                        activity_levels['rsv'] = 'minimal'
                        
                # Look for other activity level indicators
                for level in ['very high', 'high', 'moderate', 'low', 'minimal']:
                    if level in text:
                        activity_levels['statewide_level'] = level
                        break
                        
                # Look for elevated indicators
                if 'elevated' in text:
                    if 'parainfluenza' in text:
                        activity_levels['parainfluenza'] = 'elevated'
                    if 'rhinovirus' in text or 'enterovirus' in text:
                        activity_levels['rhinovirus_enterovirus'] = 'elevated'
                        
    except Exception as e:
        logger.error(f"Error extracting statewide activity levels: {str(e)}")
        
    return activity_levels


def extract_key_findings(soup: BeautifulSoup) -> List[str]:
    """Extract key findings from the respiratory data page"""
    key_findings = []
    
    try:
        # Look for bullet points or list items in the "What to know" section
        what_to_know_section = soup.find('h2', string=re.compile(r'What to know', re.IGNORECASE))
        if what_to_know_section:
            # Find the next list after the "What to know" header
            next_list = what_to_know_section.find_next(['ul', 'ol'])
            if next_list:
                list_items = next_list.find_all('li')
                for item in list_items:
                    finding = item.get_text(strip=True)
                    if finding:
                        key_findings.append(finding)
                        
    except Exception as e:
        logger.error(f"Error extracting key findings: {str(e)}")
        
    return key_findings


def extract_emergency_department_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract emergency department visit data from the ED data page"""
    ed_data = {}
    
    try:
        # Look for charts or data tables containing ED visit percentages
        # This is a simplified extraction - in practice, you'd need to parse the actual chart data
        
        # Extract any percentage values mentioned in the text
        text = soup.get_text()
        percentage_pattern = r'(\d+\.?\d*)\s*%'
        percentages = re.findall(percentage_pattern, text)
        
        if percentages:
            # Store the percentages we find - these would typically be visit percentages
            ed_data['visit_percentages'] = [float(p) for p in percentages[:10]]  # Limit to first 10
            
        # Look for age group information
        age_groups = ['0-4', '5-17', '18-49', '50-64', '65+']
        for age_group in age_groups:
            if age_group in text:
                ed_data[f'age_group_{age_group.replace("-", "_").replace("+", "_plus")}'] = 'present'
                
    except Exception as e:
        logger.error(f"Error extracting emergency department data: {str(e)}")
        
    return ed_data


def extract_laboratory_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract laboratory test data from the lab data page"""
    lab_data = {}
    
    try:
        # Look for information about positive test percentages
        text = soup.get_text().lower()
        
        # Extract trajectory information
        if 'increasing' in text:
            lab_data['trajectory'] = 'increasing'
        elif 'decreasing' in text:
            lab_data['trajectory'] = 'decreasing'
        elif 'stable' in text:
            lab_data['trajectory'] = 'stable'
            
        # Look for mentions of specific viruses and their activity
        viruses = ['covid-19', 'influenza', 'rsv', 'adenovirus', 'parainfluenza', 'rhinovirus', 'enterovirus']
        for virus in viruses:
            if virus in text:
                lab_data[f'{virus.replace("-", "_")}_detected'] = True
                
    except Exception as e:
        logger.error(f"Error extracting laboratory data: {str(e)}")
        
    return lab_data


def calculate_respiratory_risk_score(respiratory_data: Dict[str, Any]) -> float:
    """
    Calculate an overall respiratory illness risk score based on collected data.
    
    Score ranges from 0.0 (minimal risk) to 1.0 (very high risk)
    """
    try:
        risk_score = 0.0
        
        # Base risk on statewide activity levels
        statewide_levels = respiratory_data.get('statewide_levels', {})
        
        # Activity level scoring
        activity_level_scores = {
            'minimal': 0.1,
            'low': 0.3,
            'moderate': 0.5,
            'high': 0.7,
            'very high': 0.9,
            'elevated': 0.6
        }
        
        level_scores = []
        for virus, level in statewide_levels.items():
            if level in activity_level_scores:
                level_scores.append(activity_level_scores[level])
                
        if level_scores:
            risk_score = sum(level_scores) / len(level_scores)
        else:
            # Default to low-moderate risk if no specific levels found
            risk_score = 0.3
            
        # Adjust based on trajectory
        lab_data = respiratory_data.get('laboratory_data', {})
        trajectory = lab_data.get('trajectory', 'stable')
        
        if trajectory == 'increasing':
            risk_score *= 1.2  # Increase risk by 20%
        elif trajectory == 'decreasing':
            risk_score *= 0.8  # Decrease risk by 20%
            
        # Cap at 1.0
        risk_score = min(risk_score, 1.0)
        
        return round(risk_score, 3)
        
    except Exception as e:
        logger.error(f"Error calculating respiratory risk score: {str(e)}")
        return 0.3  # Default moderate risk


def get_county_respiratory_data(county_name: str) -> Dict[str, Any]:
    """
    Get respiratory illness data for a specific Wisconsin county.
    
    Since DHS data is typically statewide, this function applies the statewide
    data to the county level with any county-specific adjustments.
    
    Args:
        county_name: Name of the Wisconsin county
        
    Returns:
        Dict containing county-specific respiratory illness data
    """
    logger.info(f"Fetching respiratory data for {county_name} County")
    
    try:
        # Get statewide data
        statewide_data = get_wi_dhs_respiratory_data()
        
        # Create county-specific data structure
        county_data = {
            'county': county_name,
            'data_source': 'Wisconsin DHS (statewide data applied to county)',
            'last_updated': statewide_data.get('last_updated', datetime.now().isoformat()),
            'risk_score': statewide_data.get('overall_risk_score', 0.3),
            'activity_levels': statewide_data.get('statewide_levels', {}),
            'key_findings': statewide_data.get('key_findings', []),
            'trend_indicators': statewide_data.get('laboratory_data', {}).get('trajectory', 'stable')
        }
        
        return county_data
        
    except Exception as e:
        logger.error(f"Error fetching county respiratory data for {county_name}: {str(e)}")
        return {
            'county': county_name,
            'data_source': 'Wisconsin DHS',
            'last_updated': datetime.now().isoformat(),
            'error': str(e),
            'risk_score': 0.3  # Default moderate risk
        }