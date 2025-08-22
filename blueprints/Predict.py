import os
import time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, current_app
from dotenv import load_dotenv
from together import Together
import json
import requests
import math
import random

predict_bp = Blueprint('predict', __name__, template_folder='templates')

# Load environment variables
load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")

# Initialize Together client
client = Together(api_key=api_key)

@predict_bp.route('/api/predict', methods=['POST'])
def api_predict():
    """API endpoint for disaster prediction"""
    data = request.json
    location = data.get('location', '')
    lat = data.get('lat')
    lng = data.get('lng')
    disaster_type = data.get('disasterType', 'all')
    time_range = data.get('timeRange', '30')
    analysis_depth = data.get('analysisDepth', 'standard')
    
    # Get prediction results
    results = predict(location, lat, lng, disaster_type, time_range, analysis_depth)
    return jsonify(results)

@predict_bp.route('/api/geocode', methods=['GET'])
def geocode_location():
    """Convert location name to coordinates"""
    location_name = request.args.get('location', '')
    if not location_name:
        return jsonify({"error": "No location provided"}), 400
    
    # Use Nominatim for geocoding (for demonstration - consider using Google Maps API in production)
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1",
            headers={"User-Agent": "RescueMind Disaster Prediction App"}
        )
        data = response.json()
        if data:
            return jsonify({
                "lat": float(data[0]["lat"]),
                "lng": float(data[0]["lon"]),
                "display_name": data[0]["display_name"]
            })
        return jsonify({"error": "Location not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_historical_disaster_data(lat, lng, disaster_type):
    """Simulate retrieving historical disaster data for a location"""
    # US regions based on rough lat/lng boundaries - simplified for demo purposes
    regions = {
        "Northeast": {"lat_min": 37.0, "lat_max": 47.0, "lng_min": -80.0, "lng_max": -67.0},
        "Southeast": {"lat_min": 25.0, "lat_max": 37.0, "lng_min": -92.0, "lng_max": -75.0},
        "Midwest": {"lat_min": 36.0, "lat_max": 49.0, "lng_min": -104.0, "lng_max": -80.0},
        "Southwest": {"lat_min": 26.0, "lat_max": 37.0, "lng_min": -115.0, "lng_max": -94.0},
        "West": {"lat_min": 32.0, "lat_max": 49.0, "lng_min": -125.0, "lng_max": -104.0},
        "Alaska": {"lat_min": 51.0, "lat_max": 72.0, "lng_min": -180.0, "lng_max": -130.0},
        "Hawaii": {"lat_min": 18.0, "lat_max": 23.0, "lng_min": -161.0, "lng_max": -154.0}
    }
    
    # Determine region based on coordinates
    current_region = "Other"  # Default
    for region, bounds in regions.items():
        if (bounds["lat_min"] <= lat <= bounds["lat_max"] and 
            bounds["lng_min"] <= lng <= bounds["lng_max"]):
            current_region = region
            break
    
    # Natural disaster risk factors by region
    regional_risk_factors = {
        "Northeast": {
            "flood": "medium", 
            "hurricane": "medium", 
            "wildfire": "low",
            "earthquake": "low",
            "tornado": "low",
            "drought": "low"
        },
        "Southeast": {
            "flood": "high", 
            "hurricane": "high", 
            "wildfire": "medium",
            "earthquake": "low",
            "tornado": "medium",
            "drought": "medium"
        },
        "Midwest": {
            "flood": "medium", 
            "hurricane": "low", 
            "wildfire": "low",
            "earthquake": "low",
            "tornado": "high",
            "drought": "medium"
        },
        "Southwest": {
            "flood": "medium", 
            "hurricane": "low", 
            "wildfire": "high",
            "earthquake": "low",
            "tornado": "medium",
            "drought": "high"
        },
        "West": {
            "flood": "medium", 
            "hurricane": "low", 
            "wildfire": "high",
            "earthquake": "high",
            "tornado": "low",
            "drought": "high"
        },
        "Alaska": {
            "flood": "medium", 
            "hurricane": "low", 
            "wildfire": "medium",
            "earthquake": "high",
            "tornado": "very low",
            "drought": "low"
        },
        "Hawaii": {
            "flood": "medium", 
            "hurricane": "medium", 
            "wildfire": "low",
            "earthquake": "medium",
            "tornado": "very low",
            "drought": "low"
        },
        "Other": {
            "flood": "medium", 
            "hurricane": "medium", 
            "wildfire": "medium",
            "earthquake": "medium",
            "tornado": "medium",
            "drought": "medium"
        }
    }
    
    # Calculate more varied risk probabilities
    risk_levels = {}
    
    # Seasonal adjustments (simplified)
    current_month = datetime.now().month
    seasonal_factors = {
        # Winter months
        1: {"flood": 0.7, "hurricane": 0.3, "wildfire": 0.3, "earthquake": 1.0, "tornado": 0.5, "drought": 0.7},
        2: {"flood": 0.8, "hurricane": 0.3, "wildfire": 0.3, "earthquake": 1.0, "tornado": 0.6, "drought": 0.7},
        # Spring
        3: {"flood": 1.3, "hurricane": 0.4, "wildfire": 0.5, "earthquake": 1.0, "tornado": 1.3, "drought": 0.8},
        4: {"flood": 1.4, "hurricane": 0.5, "wildfire": 0.6, "earthquake": 1.0, "tornado": 1.5, "drought": 0.9},
        5: {"flood": 1.3, "hurricane": 0.6, "wildfire": 0.7, "earthquake": 1.0, "tornado": 1.4, "drought": 1.0},
        # Summer
        6: {"flood": 1.0, "hurricane": 0.9, "wildfire": 1.5, "earthquake": 1.0, "tornado": 1.2, "drought": 1.3},
        7: {"flood": 0.9, "hurricane": 1.2, "wildfire": 1.8, "earthquake": 1.0, "tornado": 1.0, "drought": 1.5},
        8: {"flood": 0.9, "hurricane": 1.5, "wildfire": 1.7, "earthquake": 1.0, "tornado": 0.8, "drought": 1.4},
        # Fall
        9: {"flood": 1.1, "hurricane": 1.6, "wildfire": 1.4, "earthquake": 1.0, "tornado": 0.7, "drought": 1.2},
        10: {"flood": 1.0, "hurricane": 1.3, "wildfire": 1.1, "earthquake": 1.0, "tornado": 0.6, "drought": 1.0},
        11: {"flood": 0.9, "hurricane": 0.7, "wildfire": 0.7, "earthquake": 1.0, "tornado": 0.5, "drought": 0.8},
        # Early Winter
        12: {"flood": 0.8, "hurricane": 0.4, "wildfire": 0.4, "earthquake": 1.0, "tornado": 0.4, "drought": 0.7}
    }
    
    # Add local variation based on exact coordinates
    # This creates differences even within the same region
    local_seed = int(abs(lat * 100) + abs(lng * 100)) % 100
    random.seed(local_seed)
    
    # Get disaster types to assess
    disaster_types = [disaster_type] if disaster_type != "all" else ["flood", "wildfire", "earthquake", "hurricane", "tornado", "drought"]
    
    for d_type in disaster_types:
        # Start with region base risk
        region_risk = regional_risk_factors[current_region][d_type]
        
        # Convert text risk to base probability
        base_probability = {
            "very low": 5,
            "low": 15,
            "medium": 40,
            "high": 65,
            "very high": 85
        }.get(region_risk, 30)
        
        # Apply seasonal factor
        seasonal_adjustment = seasonal_factors[current_month][d_type]
        adjusted_probability = base_probability * seasonal_adjustment
        
        # Add local variation (±15%)
        local_variation = (random.random() * 30) - 15
        final_probability = adjusted_probability + local_variation
        
        # Ensure probability is in valid range
        final_probability = max(3, min(95, final_probability))
        
        # Determine risk level from final probability
        risk_level = "low"
        if final_probability >= 65:
            risk_level = "high"
        elif final_probability >= 35:
            risk_level = "medium"
            
        # Store result
        risk_levels[d_type] = {
            "level": risk_level,
            "probability": round(final_probability, 1)
        }
    
    return risk_levels

def get_recommendations(disaster_types, risk_levels):
    """Generate recommendations based on disaster types and risk levels"""
    recommendations = []
    
    for d_type, risk in risk_levels.items():
        if risk["level"] == "high":
            if d_type == "flood":
                recommendations.append("Prepare an emergency evacuation kit and identify evacuation routes from your location.")
                recommendations.append("Consider flood insurance and elevating electrical systems in your property.")
            elif d_type == "wildfire":
                recommendations.append("Create a defensible space around your property by clearing vegetation and flammable materials.")
                recommendations.append("Prepare an emergency evacuation plan and stay informed about local fire alerts.")
            elif d_type == "earthquake":
                recommendations.append("Secure heavy furniture and fixtures to walls to prevent injuries during earthquakes.")
                recommendations.append("Identify safe spots in each room (under sturdy furniture, against interior walls) for protection.")
            elif d_type == "hurricane":
                recommendations.append("Prepare your property by securing windows and outdoor objects that could become projectiles.")
                recommendations.append("Create an evacuation plan and assemble emergency supplies for at least 3-7 days.")
            elif d_type == "tornado":
                recommendations.append("Identify a safe room or storm shelter in your home or nearby community.")
                recommendations.append("Create an emergency kit with essential supplies and important documents.")
            elif d_type == "drought":
                recommendations.append("Implement water conservation measures in your home and property.")
                recommendations.append("Consider drought-resistant landscaping to minimize water usage.")
    
    # Add general recommendations if few specific ones were generated
    if len(recommendations) < 3:
        recommendations.append("Sign up for local emergency alerts through the RescueMind app.")
        recommendations.append("Create and practice an emergency evacuation plan with your household.")
        recommendations.append("Assemble an emergency kit with water, food, medications, and essential supplies.")
    
    # Limit to top 5 recommendations
    return recommendations[:5]

def predict(location_name, lat, lng, disaster_type="all", time_range="30", analysis_depth="standard"):
    """
    Generate disaster predictions based on location and parameters
    
    Parameters:
    - location_name: String name of the location
    - lat: Latitude coordinate
    - lng: Longitude coordinate
    - disaster_type: Type of disaster to predict (flood, wildfire, etc., or "all")
    - time_range: Number of days for prediction (7, 30, 90, etc.)
    - analysis_depth: Detail level of analysis (standard, advanced, comprehensive)
    
    Returns:
    - Dictionary containing prediction results
    """
    # Get risk assessments based on location and historical data
    risk_levels = get_historical_disaster_data(lat, lng, disaster_type)
    
    # For comprehensive analysis, enhance with LLM predictions
    if analysis_depth in ["advanced", "comprehensive"]:
        # Create a prompt for the LLM
        prompt = f"""
        You are DisasterSense AI, an expert system for predicting natural disasters. 
        
        Analyze the risk of {disaster_type if disaster_type != 'all' else 'all natural disasters'} 
        in {location_name} (coordinates: {lat}, {lng}) over the next {time_range} days.
        
        Consider:
        1. Historical disaster patterns in this region
        2. Current climate conditions and seasonal patterns
        3. Geological and topographical features
        4. Recent precursors to disasters (if applicable)
        
        For each disaster type, provide:
        1. Risk level (low, medium, high)
        2. Probability percentage (0-100%)
        3. Key risk factors
        4. Earliest potential onset timeframe
        
        Format your response as JSON:
        {{
          "disaster_predictions": [
            {{
              "type": "flood",
              "risk_level": "medium",
              "probability": 45,
              "key_factors": ["Recent heavy rainfall", "Proximity to river basin"],
              "onset_timeframe": "7-14 days"
            }}
          ],
          "analysis_summary": "Brief overall analysis of the situation"
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            llm_results = json.loads(response.choices[0].message.content)
            
            # Merge basic risk assessment with LLM insights
            enhanced_risk = {}
            for prediction in llm_results.get("disaster_predictions", []):
                d_type = prediction["type"]
                enhanced_risk[d_type] = {
                    "level": prediction["risk_level"],
                    "probability": prediction["probability"],
                    "key_factors": prediction["key_factors"],
                    "onset_timeframe": prediction["onset_timeframe"]
                }
            
            # Use LLM results if available, otherwise fall back to basic assessment
            risk_assessment = enhanced_risk if enhanced_risk else risk_levels
            analysis_summary = llm_results.get("analysis_summary", "")
        except Exception as e:
            # Fall back to basic assessment if LLM fails
            risk_assessment = risk_levels
            analysis_summary = f"Basic risk assessment based on historical data patterns for {location_name}."
    else:
        # For standard analysis, use only the basic risk assessment
        risk_assessment = risk_levels
        analysis_summary = f"Basic risk assessment based on historical data patterns for {location_name}."
    
    # Generate recommendations based on risks
    recommendations = get_recommendations(disaster_type, risk_assessment)
    
    # Calculate prediction time range
    prediction_date = datetime.now()
    end_date = prediction_date + timedelta(days=int(time_range))
    
    # Format the final response
    results = {
        "location": {
            "name": location_name,
            "lat": lat,
            "lng": lng
        },
        "prediction_parameters": {
            "disaster_type": disaster_type,
            "time_range": time_range,
            "analysis_depth": analysis_depth,
            "prediction_date": prediction_date.strftime("%Y-%m-%d"),
            "prediction_end_date": end_date.strftime("%Y-%m-%d")
        },
        "risk_assessment": risk_assessment,
        "recommendations": recommendations,
        "analysis_summary": analysis_summary
    }
    
    return results