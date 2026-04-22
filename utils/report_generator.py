import tempfile
import os
from datetime import datetime
from fpdf import FPDF

def generate_pdf_report(risk_data: dict) -> str:
    """Generate a PDF report of the risk assessment"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Add header
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Risk Assessment Report', 0, 1, 'C')
        pdf.ln(10)
        
        # Add date
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1)
        pdf.ln(10)
        
        # Location information
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'Location: {risk_data["location"]}', 0, 1)
        pdf.ln(5)
        
        # Risk scores
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Risk Scores:', 0, 1)
        pdf.set_font('Arial', '', 12)
        
        # Natural hazards
        for hazard, score in risk_data['natural_hazards'].items():
            pdf.cell(0, 10, f'{hazard.title()}: {score}', 0, 1)
        
        # Additional risks
        pdf.cell(0, 10, f'Infectious Disease Risk: {risk_data["infectious_disease_risk"]}', 0, 1)
        pdf.cell(0, 10, f'Active Shooter Risk: {risk_data["active_shooter_risk"]}', 0, 1)
        
        # Total risk score
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'Total Risk Score: {risk_data["total_risk_score"]}', 0, 1)
        
        # Save to temporary file
        temp_dir = tempfile.gettempdir()
        report_path = os.path.join(temp_dir, 'risk_report.pdf')
        pdf.output(report_path)
        
        return report_path
    
    except Exception as e:
        raise Exception(f"Error generating PDF report: {str(e)}")
