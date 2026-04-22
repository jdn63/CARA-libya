# CARA Temporal Framework Usage Strategy

## Overview
The CARA platform's Baseline-Seasonal-Trend-Acute (BSTA) framework provides sophisticated risk analysis that can serve multiple usage patterns. This document outlines how to optimize the tool for different organizational planning cycles.

## Usage Patterns & Recommendations

### 1. Annual Strategic Planning Mode (Primary Use Case)
**Target Users:** Most public health agencies doing annual preparedness planning
**Optimal Configuration:**
- **Baseline Component (60% weight)**: Emphasize structural/foundational risks
- **Seasonal Component (25% weight)**: Highlight cyclical preparedness needs
- **Trend Component (15% weight)**: Focus on emerging long-term changes
- **Acute Component (Informational only)**: Show current events for context

**Key Benefits:**
- Stable, strategic risk picture not influenced by temporary events
- Clear seasonal preparedness guidance for annual planning cycles
- Long-term trend awareness for infrastructure and capacity decisions
- Reduced noise from day-to-day fluctuations

### 2. Dynamic Monitoring Mode (Advanced Use Case)
**Target Users:** Emergency managers, epidemiologists, regional coordinators
**Optimal Configuration:**
- **Baseline Component (40% weight)**: Maintain structural foundation
- **Seasonal Component (20% weight)**: Standard cyclical awareness
- **Trend Component (20% weight)**: Medium-term change tracking
- **Acute Component (20% weight)**: Enhanced real-time event response

**Key Benefits:**
- Responsive to current events and emerging threats
- Supports tactical decision-making and resource deployment
- Enables proactive response to developing situations
- Maintains strategic context while highlighting immediate needs

## Implementation Strategy

### Phase 1: Default Annual Planning Optimization
1. **Adjust Default Weights**: Optimize for stable, strategic planning
2. **Extend Cache Periods**: Reduce unnecessary data refreshes for annual users
3. **Enhanced Historical Context**: Provide multi-year trend visualization
4. **Simplified Acute Indicators**: Show current events without overwhelming strategic view

### Phase 2: Advanced User Options
1. **User Preference Settings**: Allow agencies to choose their planning mode
2. **Configurable Refresh Frequencies**: Tailor data update schedules to usage patterns
3. **Enhanced Acute Monitoring**: Real-time dashboards for frequent users
4. **Comparative Analysis**: Show how acute events relate to historical baselines

### Phase 3: Organizational Integration
1. **Multi-User Configurations**: Different views for different roles within organizations
2. **Automated Report Scheduling**: Generate reports on agency-preferred schedules
3. **Integration Hooks**: API access for embedding in existing planning workflows

## Technical Implementation

### Data Refresh Strategy
```
Annual Planning Mode:
- Baseline data: Refresh quarterly (more stable)
- Seasonal data: Refresh monthly (planning-focused)
- Trend data: Refresh monthly (strategic context)
- Acute data: Display current but don't weight heavily

Dynamic Monitoring Mode:
- Baseline data: Refresh monthly (stable foundation)
- Seasonal data: Refresh weekly (adaptive awareness)
- Trend data: Refresh weekly (emerging changes)
- Acute data: Refresh hourly (tactical response)
```

### User Interface Adaptations
1. **Planning Mode Toggle**: Simple switch between Annual and Dynamic modes
2. **Context Indicators**: Clear labeling of data freshness and relevance
3. **Focused Dashboards**: Remove distracting elements for annual planners
4. **Enhanced Acute Panels**: Detailed current events for dynamic users

## Benefits of This Approach

### For Annual Planners
- **Reduced Cognitive Load**: Focus on strategic rather than tactical information
- **Stable Planning Foundation**: Consistent risk picture for long-term decisions
- **Clear Seasonal Guidance**: Actionable preparedness activities by season
- **Efficient Resource Use**: Less frequent data refreshes, better performance

### For Frequent Users
- **Real-Time Awareness**: Current events and emerging threats highlighted
- **Tactical Decision Support**: Immediate information for resource deployment
- **Trend Detection**: Early warning for developing situations
- **Operational Integration**: Supports day-to-day emergency management

### For the Overall System
- **Broader Adoption**: Serves more user types effectively
- **Resource Optimization**: Computational resources allocated based on actual needs
- **Enhanced Value**: Single platform serves multiple organizational workflows
- **Future Growth**: Foundation for advanced features and integrations

## Next Steps
1. Implement default annual planning optimization
2. Create user preference system for mode selection
3. Develop documentation and training for different usage patterns
4. Gather feedback from pilot agencies using different modes
5. Iterate based on real-world usage patterns and needs