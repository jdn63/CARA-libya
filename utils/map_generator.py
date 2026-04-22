import folium
import tempfile
import os
import json
import logging

logger = logging.getLogger(__name__)

def create_risk_map(risk_data: dict) -> str:
    """Create an interactive map showing risk levels for Wisconsin jurisdictions"""
    try:
        # Log the risk data for debugging
        logger.info(f"Creating map with risk data: {json.dumps(risk_data, indent=2)}")

        # Wisconsin state bounds (approximate)
        WI_BOUNDS = {
            'north': 47.3,  # Northern boundary
            'south': 42.5,  # Southern boundary
            'east': -86.7,  # Eastern boundary
            'west': -92.9   # Western boundary
        }

        # Calculate center of Wisconsin
        wi_center = [
            (WI_BOUNDS['north'] + WI_BOUNDS['south']) / 2,
            (WI_BOUNDS['east'] + WI_BOUNDS['west']) / 2
        ]

        # Create a base map centered on Wisconsin
        m = folium.Map(
            location=wi_center,
            zoom_start=7,
            tiles='cartodbdark_matter'
        )

        # Fit map to Wisconsin bounds
        m.fit_bounds([
            [WI_BOUNDS['south'], WI_BOUNDS['west']],
            [WI_BOUNDS['north'], WI_BOUNDS['east']]
        ])

        # Add jurisdiction boundary if geometry is provided
        if 'geometry' in risk_data:
            logger.info(f"Adding geometry for {risk_data['location']}")

            # Create HTML for the tooltip
            tooltip_html = f"""
                <div style="font-family: Arial; min-width: 300px;">
                    <h4 style="margin: 0 0 10px 0;">{risk_data['location']}</h4>

                    <h5 style="margin: 5px 0;">Natural Hazards Overview</h5>
                    <ul style="margin: 0 0 10px 0; padding-left: 20px;">
                        <li>Flood Risk: {risk_data['natural_hazards']['flood']:.2f}</li>
                        <li>Tornado Risk: {risk_data['natural_hazards']['tornado']:.2f}</li>
                        <li>Winter Storm Risk: {risk_data['natural_hazards']['winter_storm']:.2f}</li>
                    </ul>

                    <h5 style="margin: 5px 0;">Overall Risk Assessment</h5>
                    <p style="margin: 0 0 10px 0;">Total Risk Score: {risk_data['total_risk_score']:.2f}</p>

                    <h5 style="margin: 5px 0;">Health Metrics</h5>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Hospital Beds per 1000: {risk_data['health_metrics']['avg_hospital_beds_per_1000']:.1f}</li>
                        <li>Vaccination Rate: {risk_data['health_metrics']['avg_vaccination_rate']*100:.1f}%</li>
                        <li>Health Facilities: {risk_data['health_metrics']['total_health_facilities']}</li>
                        <li>Avg. Response Time: {risk_data['health_metrics']['avg_response_time']:.1f} min</li>
                    </ul>

                    <h5 style="margin: 10px 0 5px 0;">Sub-County Details</h5>
            """

            # Add sub-county metrics to tooltip
            for area, metrics in risk_data['sub_county_metrics'].items():
                tooltip_html += f"""
                    <div style="margin: 5px 0;">
                        <strong>{area.replace('_', ' ').title()}</strong>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Population Density: {metrics['population_density']:,}/km²</li>
                            <li>Vaccination Rate: {metrics['vaccination_rate']*100:.1f}%</li>
                            <li>Response Time: {metrics['emergency_response_time']:.1f} min</li>
                        </ul>
                    </div>
                """

            tooltip_html += "</div>"

            geojson_data = {
                "type": "Feature",
                "geometry": risk_data['geometry'],
                "properties": {
                    "name": risk_data['location'],
                    "total_risk": risk_data['total_risk_score'],
                    "flood_risk": risk_data['natural_hazards']['flood'],
                    "tornado_risk": risk_data['natural_hazards']['tornado'],
                    "winter_storm_risk": risk_data['natural_hazards']['winter_storm']
                }
            }

            # Add the jurisdiction boundary with risk-based styling
            folium.GeoJson(
                data=geojson_data,
                name=risk_data['location'],
                style_function=lambda x: {
                    'fillColor': get_risk_color(x['properties']['total_risk']),
                    'color': 'white',
                    'weight': 2,
                    'fillOpacity': 0.7
                },
                tooltip=folium.Tooltip(
                    tooltip_html,
                    sticky=True,
                    style=("background-color: rgba(255, 255, 255, 0.9);"
                          "border-radius: 6px;"
                          "box-shadow: 0 2px 4px rgba(0,0,0,0.2);"
                          "padding: 12px;"
                          "font-size: 14px;")
                )
            ).add_to(m)

        # Add risk indicators for different hazard types
        add_risk_indicators(m, risk_data)

        # Save map to temporary file
        temp_dir = tempfile.gettempdir()
        map_path = os.path.join(temp_dir, 'risk_map.html')
        m.save(map_path)

        return map_path

    except Exception as e:
        logger.error(f"Error generating map: {str(e)}")
        raise Exception(f"Error generating map: {str(e)}")

def add_risk_indicators(m: folium.Map, risk_data: dict):
    """Add risk visualization indicators to the map"""
    # Create a legend
    legend_html = create_legend(risk_data)
    m.get_root().html.add_child(folium.Element(legend_html))

def get_risk_color(risk_score: float) -> str:
    """Return color based on risk score"""
    if risk_score < 0.3:
        return '#28a745'  # Green
    elif risk_score < 0.6:
        return '#ffc107'  # Yellow
    else:
        return '#dc3545'  # Red

def create_legend(risk_data: dict) -> str:
    """Create a HTML legend for the map"""
    legend = """
    <div style="position: fixed; bottom: 50px; right: 50px; width: 150px; height: auto; 
                background-color: white; border-radius: 5px; padding: 10px; z-index: 1000;">
        <h6 style="margin-top: 0;">Risk Levels</h6>
        <div style="margin-bottom: 5px;">
            <span style="background-color: #28a745; width: 20px; height: 20px; display: inline-block;"></span>
            <span style="margin-left: 5px;">Low Risk (< 0.3)</span>
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background-color: #ffc107; width: 20px; height: 20px; display: inline-block;"></span>
            <span style="margin-left: 5px;">Medium Risk (0.3-0.6)</span>
        </div>
        <div>
            <span style="background-color: #dc3545; width: 20px; height: 20px; display: inline-block;"></span>
            <span style="margin-left: 5px;">High Risk (> 0.6)</span>
        </div>
    </div>
    """
    return legend