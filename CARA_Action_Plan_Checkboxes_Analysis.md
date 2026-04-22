# CARA Development Decision: Action Plan Checkboxes Feature Analysis

**Date:** September 10, 2025  
**Decision:** Do not implement action plan completion checkboxes feature  
**Status:** Rejected after technical analysis

## Feature Proposal Summary
Add checkboxes to action plan items allowing users to mark tasks as "Completed" or "N/A", with potential future integration to recalculate risk scores based on completion status.

## Technical Challenges

### Data Persistence & Architecture
- CARA currently has no user authentication or personal data storage system
- Would require building: user accounts, completion tracking database, session management
- Multi-user complexity: unclear ownership of completion status per jurisdiction
- Risk of data loss during action plan template updates

### Score Recalculation Complexity
- Current risk scores based on objective external data (demographics, geography, census)
- No established methodology for weighting action item completion impact on risk scores
- Some risks are inherent (geographic tornado risk, county demographics) and cannot be mitigated through action items
- Would require quantifying impact of ~200+ action items across all risk domains

### Data Integrity Concerns
- No verification mechanism to ensure completed items were actually implemented
- Action plan regeneration conflicts with persistent completion data
- Version control issues when action item templates change or CDC updates PHEP requirements

## Strategic & Product Concerns

### Scope Creep Risk
- Transforms CARA from focused "risk assessment tool" into "preparedness project management platform"
- Massive complexity increase for what is currently a clean, specialized tool
- Diverts development resources from core risk assessment improvements

### Maintenance Burden
- Requires unique IDs and version tracking for each action item
- Database maintenance for 95 jurisdictions × dozens of action items each
- Ongoing synchronization with evolving PHEP capability requirements

### User Experience Complications
- Conflicts with current print-focused workflow (major use case)
- Mobile interface complexity
- Institutional knowledge loss during staff transitions

## Alternative Solutions
Rather than building completion tracking into CARA:
- Public health departments can use existing project management tools alongside CARA
- CARA maintains focus on delivering high-quality risk assessments
- Separate tools can handle task tracking and project management needs

## Final Recommendation
**Maintain CARA's focus as a specialized risk assessment platform.** The completion tracking feature, while valuable, belongs in a dedicated project management system rather than integrated into CARA's core risk assessment mission.

## Key Principle
**Product Focus:** Do one thing exceptionally well rather than many things adequately. CARA's strength lies in accurate, transparent risk assessment - not project management.