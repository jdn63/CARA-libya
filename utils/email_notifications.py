"""
Email notification system for CARA feedback submissions
Supports multiple email services and fallback logging
"""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def send_feedback_notification(feedback_data):
    """
    Send notification when new feedback is submitted
    
    Args:
        feedback_data (dict): The feedback submission data
        
    Returns:
        bool: True if notification was sent successfully
    """
    try:
        # Create notification content
        notification_content = format_feedback_notification(feedback_data)
        
        # For now, log the notification (you can add email service later)
        logger.info("NEW FEEDBACK SUBMISSION RECEIVED:")
        logger.info(notification_content)
        
        # Save notification to a special file for easy monitoring
        save_notification_alert(feedback_data, notification_content)
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending feedback notification: {str(e)}")
        return False

def format_feedback_notification(feedback_data):
    """Format feedback data into a readable notification"""
    
    content = f"""
=== NEW CARA FEEDBACK SUBMISSION ===
Submitted: {feedback_data.get('submitted_at', 'Unknown')}

Contact Information:
- Name: {feedback_data.get('name', 'Not provided')}
- Email: {feedback_data.get('email', 'Not provided')}
- Organization: {feedback_data.get('organization', 'Not provided')}
- Role: {feedback_data.get('role', 'Not provided')}

Ratings Summary:
- Ease of Use: {feedback_data.get('ease_of_use', 'N/A')}/5
- Interface Clarity: {feedback_data.get('interface_clarity', 'N/A')}/5
- Performance Speed: {feedback_data.get('performance_speed', 'N/A')}/5
- Documentation Clarity: {feedback_data.get('documentation_clarity', 'N/A')}/5
- Data Usefulness: {feedback_data.get('data_usefulness', 'N/A')}/5
- Data Accuracy: {feedback_data.get('data_accuracy', 'N/A')}/5
- HERC Integration: {feedback_data.get('herc_integration', 'N/A')}/5
- Report Usefulness: {feedback_data.get('report_usefulness', 'N/A')}/5
- Likelihood of Use: {feedback_data.get('likelihood_of_use', 'N/A')}/5
- Recommendation Likelihood: {feedback_data.get('recommendation_likelihood', 'N/A')}/5

Written Feedback:
"""
    
    if feedback_data.get('strengths'):
        content += f"Strengths: {feedback_data['strengths']}\n"
    
    if feedback_data.get('challenges'):
        content += f"Challenges: {feedback_data['challenges']}\n"
    
    if feedback_data.get('missing_features'):
        content += f"Missing Features: {feedback_data['missing_features']}\n"
    
    if feedback_data.get('suggestions'):
        content += f"Suggestions: {feedback_data['suggestions']}\n"
    
    content += f"\nView all feedback at: /admin/feedback\n"
    content += "=" * 50
    
    return content

def save_notification_alert(feedback_data, notification_content):
    """Save notification alert to a special file for monitoring"""
    try:
        # Create alerts directory
        os.makedirs('data/alerts', exist_ok=True)
        
        # Save alert with timestamp
        alert_filename = f"data/alerts/feedback_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(alert_filename, 'w') as f:
            f.write(notification_content)
            
        # Also update a "latest" file for easy checking
        with open('data/alerts/latest_feedback_alert.txt', 'w') as f:
            f.write(notification_content)
            
        logger.info(f"Feedback alert saved to {alert_filename}")
        
    except Exception as e:
        logger.error(f"Error saving notification alert: {str(e)}")

def get_latest_feedback_alert():
    """Get the content of the latest feedback alert"""
    try:
        alert_file = 'data/alerts/latest_feedback_alert.txt'
        if os.path.exists(alert_file):
            with open(alert_file, 'r') as f:
                return f.read()
        return None
    except Exception as e:
        logger.error(f"Error reading latest feedback alert: {str(e)}")
        return None