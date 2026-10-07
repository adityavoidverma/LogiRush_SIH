# src/ir/corpus_generator.py
"""
Synthetic corpus generator for LogiRush IR engine.

Generates deterministic synthetic logistics and hazard documents with:
  - Pan-India geographic distribution (36 states/UTs)
  - Multi-hazard coverage (floods, landslides, rainfall, cyclones, accidents, infra, heat)
  - Realistic sources (IMD, NDMA, NHAI, BRO, NDRF, state disaster management authorities)
  - Template-based text generation with slot-filling
  - Controlled severity and hazard type distribution
  - Dates spanning 2024-2026
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from src.ir.schemas import IRDocument


# ──────────────────────────────────────────────────────────────────────────────
# INDIA GEOGRAPHIC DATA
# ──────────────────────────────────────────────────────────────────────────────
INDIA_GEO_DATA = {
    "Assam": {
        "cities": [
            {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362, "district": "Kamrup"},
            {"name": "Tezpur", "lat": 26.6333, "lon": 92.8000, "district": "Sonitpur"},
            {"name": "Dibrugarh", "lat": 27.4728, "lon": 94.9120, "district": "Dibrugarh"},
            {"name": "Silchar", "lat": 24.8333, "lon": 92.7789, "district": "Cachar"},
        ],
        "highways": ["NH27", "NH715", "NH37", "NH44"],
        "rivers": ["Brahmaputra", "Barak", "Subansiri"],
    },
    "Meghalaya": {
        "cities": [
            {"name": "Shillong", "lat": 25.5788, "lon": 91.8933, "district": "East Khasi Hills"},
            {"name": "Cherrapunji", "lat": 25.2701, "lon": 91.7318, "district": "East Khasi Hills"},
            {"name": "Tura", "lat": 25.5138, "lon": 90.2028, "district": "West Garo Hills"},
        ],
        "highways": ["NH6", "NH44", "NH106"],
        "rivers": ["Umngot", "Simsang"],
    },
    "Tripura": {
        "cities": [
            {"name": "Agartala", "lat": 23.8315, "lon": 91.2868, "district": "West Tripura"},
            {"name": "Udaipur", "lat": 23.5370, "lon": 91.4849, "district": "Gomati"},
        ],
        "highways": ["NH8", "NH44", "NH716"],
        "rivers": ["Gomati", "Manu"],
    },
    "Mizoram": {
        "cities": [
            {"name": "Aizawl", "lat": 23.7307, "lon": 92.7173, "district": "Aizawl"},
            {"name": "Lunglei", "lat": 22.8878, "lon": 92.7378, "district": "Lunglei"},
        ],
        "highways": ["NH54", "NH150"],
        "rivers": ["Tlawng", "Tuirial"],
    },
    "Manipur": {
        "cities": [
            {"name": "Imphal", "lat": 24.8170, "lon": 93.9368, "district": "Imphal West"},
            {"name": "Senapati", "lat": 25.2741, "lon": 94.0181, "district": "Senapati"},
        ],
        "highways": ["NH2", "NH37", "NH102"],
        "rivers": ["Manipur", "Barak"],
    },
    "Nagaland": {
        "cities": [
            {"name": "Kohima", "lat": 25.6700, "lon": 94.1100, "district": "Kohima"},
            {"name": "Dimapur", "lat": 25.9096, "lon": 93.7285, "district": "Dimapur"},
        ],
        "highways": ["NH29", "NH44", "NH702"],
        "rivers": ["Doyang", "Dhansiri"],
    },
    "Arunachal Pradesh": {
        "cities": [
            {"name": "Itanagar", "lat": 27.0844, "lon": 93.6053, "district": "Papum Pare"},
            {"name": "Tawang", "lat": 27.5860, "lon": 91.8578, "district": "Tawang"},
            {"name": "Pasighat", "lat": 28.0661, "lon": 95.3263, "district": "East Siang"},
        ],
        "highways": ["NH13", "NH415", "NH229"],
        "rivers": ["Siang", "Kameng", "Lohit"],
    },
    "Sikkim": {
        "cities": [
            {"name": "Gangtok", "lat": 27.3389, "lon": 88.6065, "district": "East Sikkim"},
            {"name": "Rangpo", "lat": 27.1760, "lon": 88.5313, "district": "East Sikkim"},
        ],
        "highways": ["NH10", "NH310"],
        "rivers": ["Teesta", "Rangeet"],
    },
    "West Bengal": {
        "cities": [
            {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "district": "Kolkata"},
            {"name": "Siliguri", "lat": 26.7271, "lon": 88.3953, "district": "Darjeeling"},
            {"name": "Howrah", "lat": 22.5958, "lon": 88.2636, "district": "Howrah"},
            {"name": "Asansol", "lat": 23.6739, "lon": 86.9524, "district": "Paschim Bardhaman"},
        ],
        "highways": ["NH16", "NH12", "NH27", "NH44"],
        "rivers": ["Hooghly", "Teesta", "Ganges"],
    },
    "Bihar": {
        "cities": [
            {"name": "Patna", "lat": 25.5941, "lon": 85.1376, "district": "Patna"},
            {"name": "Muzaffarpur", "lat": 26.1209, "lon": 85.3647, "district": "Muzaffarpur"},
            {"name": "Gaya", "lat": 24.7955, "lon": 84.9994, "district": "Gaya"},
        ],
        "highways": ["NH31", "NH19", "NH27", "NH83"],
        "rivers": ["Ganges", "Gandak", "Bagmati", "Kosi"],
    },
    "Odisha": {
        "cities": [
            {"name": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245, "district": "Khordha"},
            {"name": "Paradip", "lat": 20.3164, "lon": 86.6090, "district": "Jagatsinghpur"},
            {"name": "Puri", "lat": 19.8135, "lon": 85.8312, "district": "Puri"},
        ],
        "highways": ["NH16", "NH203", "NH53"],
        "rivers": ["Mahanadi", "Brahmani", "Baitarani"],
    },
    "Maharashtra": {
        "cities": [
            {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "district": "Mumbai"},
            {"name": "Pune", "lat": 18.5204, "lon": 73.8567, "district": "Pune"},
            {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882, "district": "Nagpur"},
            {"name": "Thane", "lat": 19.2183, "lon": 72.9781, "district": "Thane"},
        ],
        "highways": ["NH48", "NH44", "NH52", "NH66"],
        "rivers": ["Godavari", "Krishna", "Tapi"],
    },
    "Karnataka": {
        "cities": [
            {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946, "district": "Bangalore Urban"},
            {"name": "Mangalore", "lat": 12.9141, "lon": 74.8560, "district": "Dakshina Kannada"},
            {"name": "Mysore", "lat": 12.2958, "lon": 76.6394, "district": "Mysore"},
        ],
        "highways": ["NH48", "NH66", "NH75", "NH275"],
        "rivers": ["Kaveri", "Krishna", "Tungabhadra"],
    },
    "Tamil Nadu": {
        "cities": [
            {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "district": "Chennai"},
            {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558, "district": "Coimbatore"},
            {"name": "Madurai", "lat": 9.9252, "lon": 78.1198, "district": "Madurai"},
        ],
        "highways": ["NH16", "NH44", "NH45", "NH83"],
        "rivers": ["Kaveri", "Vaigai", "Thamirabarani"],
    },
    "Kerala": {
        "cities": [
            {"name": "Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366, "district": "Thiruvananthapuram"},
            {"name": "Kochi", "lat": 9.9312, "lon": 76.2673, "district": "Ernakulam"},
            {"name": "Kozhikode", "lat": 11.2588, "lon": 75.7804, "district": "Kozhikode"},
            {"name": "Ernakulam", "lat": 9.9816, "lon": 76.2999, "district": "Ernakulam"},
        ],
        "highways": ["NH66", "NH47", "NH544", "NH766"],
        "rivers": ["Periyar", "Bharathappuzha", "Pamba"],
    },
    "Andhra Pradesh": {
        "cities": [
            {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185, "district": "Visakhapatnam"},
            {"name": "Vijayawada", "lat": 16.5062, "lon": 80.6480, "district": "Krishna"},
            {"name": "Kakinada", "lat": 16.9891, "lon": 82.2475, "district": "East Godavari"},
        ],
        "highways": ["NH16", "NH44", "NH65"],
        "rivers": ["Godavari", "Krishna", "Pennar"],
    },
    "Telangana": {
        "cities": [
            {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "district": "Hyderabad"},
            {"name": "Warangal", "lat": 17.9784, "lon": 79.6004, "district": "Warangal Urban"},
        ],
        "highways": ["NH44", "NH65", "NH163"],
        "rivers": ["Godavari", "Krishna", "Musi"],
    },
    "Gujarat": {
        "cities": [
            {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "district": "Ahmedabad"},
            {"name": "Surat", "lat": 21.1702, "lon": 72.8311, "district": "Surat"},
            {"name": "Vadodara", "lat": 22.3072, "lon": 73.1812, "district": "Vadodara"},
        ],
        "highways": ["NH8", "NH48", "NH947", "NH53"],
        "rivers": ["Narmada", "Tapi", "Sabarmati"],
    },
    "Rajasthan": {
        "cities": [
            {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "district": "Jaipur"},
            {"name": "Jodhpur", "lat": 26.2389, "lon": 73.0243, "district": "Jodhpur"},
            {"name": "Jaisalmer", "lat": 26.9157, "lon": 70.9083, "district": "Jaisalmer"},
        ],
        "highways": ["NH8", "NH48", "NH62", "NH25"],
        "rivers": ["Chambal", "Luni", "Banas"],
    },
    "Madhya Pradesh": {
        "cities": [
            {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126, "district": "Bhopal"},
            {"name": "Indore", "lat": 22.7196, "lon": 75.8577, "district": "Indore"},
            {"name": "Gwalior", "lat": 26.2183, "lon": 78.1828, "district": "Gwalior"},
        ],
        "highways": ["NH44", "NH46", "NH52", "NH69"],
        "rivers": ["Narmada", "Chambal", "Betwa"],
    },
    "Uttar Pradesh": {
        "cities": [
            {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462, "district": "Lucknow"},
            {"name": "Kanpur", "lat": 26.4499, "lon": 80.3319, "district": "Kanpur Nagar"},
            {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739, "district": "Varanasi"},
            {"name": "Agra", "lat": 27.1767, "lon": 78.0081, "district": "Agra"},
        ],
        "highways": ["NH2", "NH19", "NH24", "NH44", "NH27"],
        "rivers": ["Ganges", "Yamuna", "Gomti"],
    },
    "Punjab": {
        "cities": [
            {"name": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "district": "Chandigarh"},
            {"name": "Amritsar", "lat": 31.6340, "lon": 74.8723, "district": "Amritsar"},
            {"name": "Ludhiana", "lat": 30.9010, "lon": 75.8573, "district": "Ludhiana"},
        ],
        "highways": ["NH44", "NH1", "NH5", "NH703"],
        "rivers": ["Sutlej", "Beas", "Ravi"],
    },
    "Haryana": {
        "cities": [
            {"name": "Gurgaon", "lat": 28.4595, "lon": 77.0266, "district": "Gurgaon"},
            {"name": "Faridabad", "lat": 28.4089, "lon": 77.3178, "district": "Faridabad"},
        ],
        "highways": ["NH44", "NH48", "NH9", "NH19"],
        "rivers": ["Yamuna", "Ghaggar"],
    },
    "Delhi": {
        "cities": [
            {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "district": "Central Delhi"},
            {"name": "Dwarka", "lat": 28.5921, "lon": 77.0460, "district": "South West Delhi"},
        ],
        "highways": ["NH1", "NH2", "NH8", "NH44", "NH48"],
        "rivers": ["Yamuna"],
    },
    "Uttarakhand": {
        "cities": [
            {"name": "Dehradun", "lat": 30.3165, "lon": 78.0322, "district": "Dehradun"},
            {"name": "Haridwar", "lat": 29.9457, "lon": 78.1642, "district": "Haridwar"},
            {"name": "Nainital", "lat": 29.3803, "lon": 79.4636, "district": "Nainital"},
        ],
        "highways": ["NH58", "NH7", "NH309", "NH34"],
        "rivers": ["Ganges", "Yamuna", "Alaknanda"],
    },
    "Himachal Pradesh": {
        "cities": [
            {"name": "Shimla", "lat": 31.1048, "lon": 77.1734, "district": "Shimla"},
            {"name": "Manali", "lat": 32.2432, "lon": 77.1892, "district": "Kullu"},
            {"name": "Rohtang", "lat": 32.3729, "lon": 77.2432, "district": "Kullu"},
        ],
        "highways": ["NH3", "NH5", "NH22", "NH305"],
        "rivers": ["Beas", "Sutlej", "Chenab"],
    },
    "Jammu and Kashmir": {
        "cities": [
            {"name": "Srinagar", "lat": 34.0837, "lon": 74.7973, "district": "Srinagar"},
            {"name": "Jammu", "lat": 32.7266, "lon": 74.8570, "district": "Jammu"},
        ],
        "highways": ["NH44", "NH1A", "NH244"],
        "rivers": ["Jhelum", "Chenab", "Indus"],
    },
    "Goa": {
        "cities": [
            {"name": "Panaji", "lat": 15.4909, "lon": 73.8278, "district": "North Goa"},
            {"name": "Margao", "lat": 15.2700, "lon": 73.9530, "district": "South Goa"},
        ],
        "highways": ["NH66", "NH4A"],
        "rivers": ["Mandovi", "Zuari"],
    },
    "Chhattisgarh": {
        "cities": [
            {"name": "Raipur", "lat": 21.2514, "lon": 81.6296, "district": "Raipur"},
            {"name": "Bilaspur", "lat": 22.0797, "lon": 82.1409, "district": "Bilaspur"},
        ],
        "highways": ["NH30", "NH53", "NH130"],
        "rivers": ["Mahanadi", "Shivnath"],
    },
    "Jharkhand": {
        "cities": [
            {"name": "Ranchi", "lat": 23.3441, "lon": 85.3096, "district": "Ranchi"},
            {"name": "Jamshedpur", "lat": 22.8046, "lon": 86.2029, "district": "East Singhbhum"},
        ],
        "highways": ["NH33", "NH18", "NH20"],
        "rivers": ["Damodar", "Subarnarekha"],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# SOURCE DATA
# ──────────────────────────────────────────────────────────────────────────────
SOURCE_LIST = [
    {"name": "IMD", "type": "government"},
    {"name": "NDMA", "type": "government"},
    {"name": "NHAI", "type": "government"},
    {"name": "BRO", "type": "government"},
    {"name": "NDRF", "type": "government"},
    {"name": "ASDMA", "type": "government"},           # Assam
    {"name": "HPSDMA", "type": "government"},          # Himachal Pradesh
    {"name": "KSDMA", "type": "government"},           # Kerala
    {"name": "OSDMA", "type": "government"},           # Odisha
    {"name": "APDMA", "type": "government"},           # Arunachal Pradesh
    {"name": "PWD", "type": "government"},
    {"name": "Traffic Police", "type": "verified_org"},
    {"name": "District Collector", "type": "government"},
    {"name": "Ministry of Road Transport", "type": "government"},
    {"name": "MSRDC", "type": "government"},           # Maharashtra
]

# ──────────────────────────────────────────────────────────────────────────────
# HAZARD TEXT TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────
FLOOD_TEMPLATES = [
    "{severity_phrase} flooding reported on {highway} near {location}, {state}. {river_name} has overflowed, rendering sections of the highway impassable. Traffic is {traffic_impact}. Heavy vehicles are advised to {advice}.",
    "Severe waterlogging on {highway} in {district} district due to {river_name} overflow. The road surface is submerged at multiple points near {location}. {severity_phrase} conditions persist. Emergency services have been deployed.",
    "{severity_phrase} flood alert for {location}, {state}. {highway} is experiencing major disruption due to river overflow from {river_name}. {traffic_impact} reported. Relief operations are underway.",
    "Flash flooding has affected {highway} near {location}. Water levels from {river_name} are rising rapidly. {severity_phrase} situation with {traffic_impact}. Cargo movement is {cargo_impact}.",
    "Monsoon flooding on {highway} between {location} and neighboring districts. {river_name} breach has caused {severity_phrase} waterlogging. Vehicles are being diverted. Transit delays of {delay_hours} hours expected.",
]

LANDSLIDE_TEMPLATES = [
    "{severity_phrase} landslide on {highway} near {location}, {state}. Debris has blocked approximately {debris_length} of the highway. {traffic_impact}. {clearance_info}.",
    "Multiple slope failures recorded on {highway} in {district} district. Heavy rainfall has triggered {severity_phrase} landslides near {location}. Rock fall risk is high. {traffic_impact}.",
    "{severity_phrase} landslide has rendered {highway} impassable near {location}. BRO teams are working on clearance. No alternative route available. {advice}.",
    "Hill section of {highway} near {location} affected by landslides. {severity_phrase} debris flow covering the road. {traffic_impact}. Estimated clearance time: {clearance_hours} hours.",
]

RAINFALL_TEMPLATES = [
    "{severity_phrase} rainfall alert for {location}, {state}. IMD has recorded {rainfall_mm} mm in 24 hours. {highway} is at risk of washouts and waterlogging. {traffic_impact}.",
    "Heavy rainfall has caused {severity_phrase} delays on {highway} near {location}. Visibility is poor and speed restrictions are in effect. {traffic_impact}.",
    "Extreme rainfall in {district} district. {highway} experiencing {severity_phrase} surface damage near {location}. {advice}. Travel time increased by {delay_hours} hours.",
]

CYCLONE_TEMPLATES = [
    "Cyclone alert for {location}, {state}. IMD has issued {severity_phrase} warning. {highway} coastal sections are at risk of flooding and debris. Port operations suspended. {advice}.",
    "{severity_phrase} cyclone warning for {location}. {highway} may face disruption as the storm approaches. Fishing vessels recalled. NDRF teams pre-positioned.",
    "Deep depression in Bay of Bengal expected to intensify. {severity_phrase} cyclone risk for {location}. {highway} at high risk. {traffic_impact}.",
]

ACCIDENT_TEMPLATES = [
    "Multi-vehicle accident on {highway} near {location} has blocked the highway. {severity_phrase} disruption. Clearance operations in progress. Estimated time: {clearance_hours} hours.",
    "{severity_phrase} pile-up on {highway} in {district} district. Traffic is being diverted via alternate routes. {traffic_impact}.",
    "Road accident on {highway} near {location} has caused {severity_phrase} delays. Emergency services on site. {advice}.",
]

INFRA_TEMPLATES = [
    "Infrastructure alert: Bridge on {highway} near {location} placed under weight restriction. {severity_phrase} issue following structural inspection. Heavy cargo must use alternate routes.",
    "{severity_phrase} road damage on {highway} in {district} district. Pavement failure reported near {location}. {traffic_impact}. Repairs expected to take {clearance_hours} hours.",
]

HEAT_TEMPLATES = [
    "Extreme heat alert for {location}, {state}. Temperatures exceeding {temp}°C have caused {severity_phrase} road surface damage on {highway}. {advice}.",
    "Heatwave conditions in {district} district. {severity_phrase} road deformation on {highway}. Drivers advised to avoid peak daytime travel (11 AM - 4 PM).",
]

# ──────────────────────────────────────────────────────────────────────────────
# SEVERITY PHRASES
# ──────────────────────────────────────────────────────────────────────────────
SEVERITY_PHRASES = {
    "critical": [
        "Critical",
        "Severe and critical",
        "Emergency level",
    ],
    "high": [
        "High severity",
        "Severe",
        "Significant",
    ],
    "medium": [
        "Moderate",
        "Medium severity",
        "Notable",
    ],
    "low": [
        "Minor",
        "Low severity",
        "Mild",
    ],
}

TRAFFIC_IMPACTS = {
    "critical": [
        "completely blocked",
        "impassable",
        "closed to all traffic",
        "highway shut down",
    ],
    "high": [
        "severely disrupted",
        "major delays reported",
        "heavy congestion",
    ],
    "medium": [
        "partially blocked",
        "slow moving",
        "moderate delays",
    ],
    "low": [
        "minor delays",
        "advisory in effect",
        "normal with caution",
    ],
}

ADVICE = {
    "critical": [
        "avoid the corridor entirely",
        "seek alternative routes immediately",
        "evacuation recommended for stranded vehicles",
    ],
    "high": [
        "use alternate routes where possible",
        "expect significant delays",
        "monitor updates before departure",
    ],
    "medium": [
        "check road conditions before departure",
        "allow extra travel time",
        "proceed with caution",
    ],
    "low": [
        "monitor updates",
        "proceed with normal caution",
        "no immediate action required",
    ],
}

CARGO_IMPACTS = {
    "critical": ["completely halted", "not possible", "suspended"],
    "high": ["severely impacted", "significantly delayed", "at risk"],
    "medium": ["moderately affected", "experiencing delays", "slower than usual"],
    "low": ["minimally affected", "proceeding normally", "no major issues"],
}


# ──────────────────────────────────────────────────────────────────────────────
# GENERATOR FUNCTION
# ──────────────────────────────────────────────────────────────────────────────
def generate_corpus(count: int = 1000, seed: int = 42) -> list[IRDocument]:
    """
    Generate synthetic logistics and hazard documents with deterministic output.

    Parameters
    ----------
    count : int
        Number of documents to generate (default: 1000)
    seed : int
        Random seed for deterministic generation (default: 42)

    Returns
    -------
    list[IRDocument]
        List of synthetic IRDocument instances
    """
    random.seed(seed)
    
    # Hazard distribution: Floods 30%, Landslides 25%, Rainfall 15%, 
    # Cyclones 10%, Accidents 10%, Infrastructure 8%, Heat 2%
    hazard_distribution = (
        [("flood", FLOOD_TEMPLATES)] * 300 +
        [("landslide", LANDSLIDE_TEMPLATES)] * 250 +
        [("rainfall", RAINFALL_TEMPLATES)] * 150 +
        [("cyclone", CYCLONE_TEMPLATES)] * 100 +
        [("accident", ACCIDENT_TEMPLATES)] * 100 +
        [("infra", INFRA_TEMPLATES)] * 80 +
        [("heat", HEAT_TEMPLATES)] * 20
    )
    
    # Severity distribution: 20% low, 40% medium, 30% high, 10% critical
    severity_distribution = (
        ["low"] * 200 +
        ["medium"] * 400 +
        ["high"] * 300 +
        ["critical"] * 100
    )
    
    # Shuffle to randomize but keep deterministic
    random.shuffle(hazard_distribution)
    random.shuffle(severity_distribution)
    
    # Get list of states for iteration
    states = list(INDIA_GEO_DATA.keys())
    
    documents = []
    
    # Hazard prefixes for document IDs
    hazard_prefixes = {
        "flood": "F",
        "landslide": "L",
        "rainfall": "R",
        "cyclone": "C",
        "accident": "A",
        "infra": "I",
        "heat": "H",
    }
    
    # Counter for each hazard type
    hazard_counters = {h: 1 for h in hazard_prefixes.keys()}
    
    # Start date: 2024-01-01
    start_date = datetime(2024, 1, 1)
    # End date: 2026-12-31
    end_date = datetime(2026, 12, 31)
    date_range = (end_date - start_date).days
    
    for i in range(count):
        # Select hazard and template
        hazard_type, templates = hazard_distribution[i]
        template = random.choice(templates)
        
        # Select severity
        severity = severity_distribution[i]
        
        # Select state with weighted preference for NER states
        # NER states get 2x weight
        ner_states = ["Assam", "Meghalaya", "Tripura", "Mizoram", "Manipur", "Nagaland", "Arunachal Pradesh", "Sikkim"]
        state_weights = [2.0 if s in ner_states else 1.0 for s in states]
        state = random.choices(states, weights=state_weights, k=1)[0]
        
        # Select city from state
        state_data = INDIA_GEO_DATA[state]
        city_data = random.choice(state_data["cities"])
        location = city_data["name"]
        latitude = city_data["lat"]
        longitude = city_data["lon"]
        district = city_data["district"]
        
        # Select highway
        highway = random.choice(state_data["highways"])
        
        # Select river (if available)
        river_name = random.choice(state_data.get("rivers", ["local river"]))
        
        # Select source
        source_data = random.choice(SOURCE_LIST)
        source = source_data["name"]
        source_type = source_data["type"]
        
        # Generate date
        days_offset = random.randint(0, date_range)
        date = start_date + timedelta(days=days_offset)
        date_str = date.strftime("%Y-%m-%d")
        
        # Fill template
        severity_phrase = random.choice(SEVERITY_PHRASES[severity])
        traffic_impact = random.choice(TRAFFIC_IMPACTS[severity])
        advice_text = random.choice(ADVICE[severity])
        cargo_impact = random.choice(CARGO_IMPACTS[severity])
        
        # Additional placeholders
        debris_length = random.choice(["150 metres", "200 metres", "300 metres", "half a kilometre"])
        clearance_hours = random.choice([4, 6, 8, 12, 24, 48])
        delay_hours = random.choice([2, 3, 4, 6, 8, 12])
        rainfall_mm = random.choice([150, 200, 250, 300, 350, 400])
        temp = random.choice([45, 46, 47, 48, 49, 50])
        clearance_info = random.choice([
            "BRO teams deployed for clearance",
            "Heavy machinery required for debris removal",
            "Clearance operations underway",
        ])
        
        text = template.format(
            location=location,
            highway=highway,
            state=state,
            district=district,
            river_name=river_name,
            severity_phrase=severity_phrase,
            traffic_impact=traffic_impact,
            advice=advice_text,
            cargo_impact=cargo_impact,
            debris_length=debris_length,
            clearance_hours=clearance_hours,
            clearance_info=clearance_info,
            delay_hours=delay_hours,
            rainfall_mm=rainfall_mm,
            temp=temp,
        )
        
        # Generate document ID
        prefix = hazard_prefixes[hazard_type]
        doc_id = f"GEN_{prefix}{hazard_counters[hazard_type]:03d}"
        hazard_counters[hazard_type] += 1
        
        # Generate title
        title = f"{hazard_type.title()} on {highway} near {location}"
        
        # Generate tags
        tags = [hazard_type, state, location, highway, district, severity]
        if hazard_type in ["flood", "cyclone"]:
            tags.append(river_name)
        
        # Create document
        doc = IRDocument(
            id=doc_id,
            title=title,
            text=text,
            source=source,
            source_type=source_type,
            date=date_str,
            location=f"{location}, {state}",
            hazard=hazard_type,
            severity=severity,
            tags=tags,
            provenance="SYNTHETIC",
            latitude=latitude,
            longitude=longitude,
            route=highway,
            state=state,
            district=district,
            highway=highway,
        )
        
        documents.append(doc)
    
    return documents
