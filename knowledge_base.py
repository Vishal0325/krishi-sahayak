"""
Krishi Sahayak - Advanced Farming Knowledge Base
Comprehensive agricultural intelligence for Indian farmers.
"""

import re

FARMING_KNOWLEDGE = {
    "crops": {
        "wheat": {
            "name": "Wheat (गेहूं)",
            "season": "Rabi (Winter)",
            "sowing_time": "October-November",
            "harvest_time": "March-April",
            "water_requirement": "4-6 irrigations (CRI, Tillering, Flowering, Grain filling stages)",
            "fertilizer": "NPK 120:60:40 kg/ha. Apply 1/2 N and full P&K at sowing, 1/4 N at first irrigation (21 days), 1/4 N at second irrigation.",
            "varieties": ["PBW 343", "HD 2967", "DBW 187 (Karan Vandana)", "HD 3086"],
            "tips": [
                "Ensure proper drainage to prevent waterlogging",
                "CRI (Crown Root Initiation) stage is the most critical for irrigation (21 days after sowing)",
                "Protect from Yellow Rust (पीला रतुआ) and Powdery Mildew",
                "Ideal temperature: 10-25°C"
            ]
        },
        "rice": {
            "name": "Rice (धान)",
            "season": "Kharif (Monsoon)",
            "sowing_time": "June-July (Nursery: May)",
            "harvest_time": "October-November",
            "water_requirement": "High - standing water (5cm) till dough stage. AWD (Alternate Wetting and Drying) saves water.",
            "fertilizer": "NPK 100-120:50:50 kg/ha. Use Zinc Sulphate (25kg/ha) to prevent Khaira disease.",
            "varieties": ["Pusa Basmati 1121", "IR 64", "MTU 1010", "Swarna"],
            "tips": [
                "Transplant seedlings at 21-25 days age (3-4 leaf stage)",
                "Maintain standing water but drain 10-15 days before harvest",
                "Watch for Stem Borer (तना छेदक) and Brown Plant Hopper (भूरा फदका)",
                "Apply nitrogen in 3 splits (Basal, Tillering, Panicle Initiation)"
            ]
        },
        "sugarcane": {
            "name": "Sugarcane (गन्ना)",
            "season": "Year-round",
            "sowing_time": "Spring (Feb-Mar) or Autumn (Oct-Nov)",
            "harvest_time": "10-14 months",
            "water_requirement": "Very High (1500-2500mm). Drip irrigation recommended. Avoid water stress at formative stage.",
            "fertilizer": "NPK 150-250:80:60 kg/ha. Apply N in 3-4 splits. Micronutrients like Fe and Zn are beneficial.",
            "varieties": ["Co 0238", "Co 86032", "Co 0118"],
            "tips": [
                "Use heat-treated (MHAT) or disease-free setts",
                "Earthing up (मिट्टी चढ़ाना) at 90-120 days is crucial to prevent lodging",
                "Control Red Rot (लाल सड़न) by avoiding waterlogging and using resistant varieties",
                "Tie canes (propping) to prevent lodging during monsoon winds"
            ]
        },
        "potato": {
            "name": "Potato (आलू)",
            "season": "Rabi",
            "sowing_time": "October-November",
            "harvest_time": "January-March",
            "water_requirement": "Moderate (7-10 days interval). Critical stages: Stolon formation and Tuberization.",
            "fertilizer": "NPK 150:100:100 kg/ha. Apply 1/2 N and full P&K at planting; 1/2 N during earthing up.",
            "varieties": ["Kufri Bahar", "Kufri Jyoti", "Kufri Pukhraj", "Kufri Chipsona"],
            "tips": [
                "Use certified seeds to avoid Late Blight and viruses",
                "Earthing up when plants are 15-20cm high to protect tubers from light (greening)",
                "Monitor for Aphids (चेपा) and Potato Tuber Moth",
                "Dehaulming (cutting tops) 10-15 days before harvest for skin hardening"
            ]
        },
        "tomato": {
            "name": "Tomato (टमाटर)",
            "season": "Kharif, Rabi, and Summer",
            "sowing_time": "Jun-July (Kharif), Oct-Nov (Rabi), Feb (Summer)",
            "harvest_time": "60-90 days after transplanting",
            "water_requirement": "Regular intervals. Critical during flowering and fruit set. Avoid moisture fluctuations to prevent fruit cracking.",
            "fertilizer": "NPK 100:60:60 kg/ha + Boron (for fruit quality) and Calcium (prevents Blossom End Rot).",
            "tips": [
                "Staking (सहारा देना) is necessary for indeterminate (tall) varieties",
                "Prune lower leaves to improve airflow and reduce soil-borne diseases",
                "Watch for Fruit Borer (फल छेदक) and Early/Late Blight",
                "Mulching helps in moisture retention and weed control"
            ]
        },
        "onion": {
            "name": "Onion (प्याज)",
            "season": "Kharif and Rabi",
            "sowing_time": "May-June (Kharif), Oct-Nov (Rabi)",
            "harvest_time": "100-120 days after transplanting",
            "water_requirement": "Frequent light irrigations. Stop watering 15 days before harvest when tops start falling (neck fall).",
            "fertilizer": "NPK 100:50:50 kg/ha + Sulfur (20kg/ha) for better pungency and storage.",
            "tips": [
                "Transplant 6-8 week old seedlings (15cm height)",
                "Avoid deep planting (shallow planting is better for bulb expansion)",
                "Control Thrips (चूरड़ा) early with organic/chemical sprays",
                "Curing in shade for 3-5 days is vital for long storage"
            ]
        },
        "cotton": {
            "name": "Cotton (कपास)",
            "season": "Kharif",
            "sowing_time": "April (North), May-June (Central/South)",
            "harvest_time": "October-January (Multiple pickings)",
            "water_requirement": "Moderate. Critical stages: Square formation and Flowering. Avoid waterlogging.",
            "fertilizer": "NPK 100:50:50 kg/ha. For Bt Cotton, higher N (120kg) is needed. Split N at 30, 60, and 90 days.",
            "tips": [
                "Deep black soil (Regur) is best for moisture retention",
                "Pheromone traps (5/acre) for monitoring Pink Bollworm (गुलाबी सुंडी)",
                "Refuge crops (non-Bt) should be planted around Bt fields",
                "Avoid picking when bolls are wet; store in dry ventilated place"
            ]
        },
        "pulses": {
            "name": "Pulses / Lentils (दालें/दलहन)",
            "types": ["Chickpea (चना)", "Pigeon Pea (अरहर/तुअर)", "Mung Bean (मूंग)", "Urad (उड़द)", "Lentil (मसूर)"],
            "fertilizer": "NPK 20:40:20 kg/ha. Needs less Nitrogen as they fix it from air.",
            "tips": [
                "Treat seeds with Rhizobium culture and PSB (Phosphate Solubilizing Bacteria)",
                "Ensure proper drainage; pulses are highly sensitive to waterlogging",
                "Control Pod Borer (फली छेदक) using Neem oil or Pheromone traps",
                "Nipping (top pruning) in Chickpea at 30-45 days increases branching"
            ]
        },
        "mustard": {
            "name": "Mustard (सरसों)",
            "season": "Rabi",
            "sowing_time": "October",
            "harvest_time": "February-March",
            "water_requirement": "Low to Moderate (2-3 irrigations). Critical: Pre-flowering and Pod filling.",
            "fertilizer": "NPK 80:40:40 kg/ha. Sulfur (20kg/ha) is mandatory for oil content.",
            "tips": [
                "Thinning is crucial at 15-20 days to maintain 10-15cm plant spacing",
                "Monitor for Aphids (चेपा) especially during cloudy/humid weather",
                "Control Alternaria Blight with Mancozeb spray",
                "Harvest when 75% of pods turn golden yellow"
            ]
        }
    },
    "soil_health": {
        "clay": {
            "label": "Clay soil (चिकनी/भारी मिट्टी)",
            "problems": "Poor drainage, aeration issues, very hard when dry, sticky when wet.",
            "corrections": "Add organic compost (FYM), Green Manuring (Dhaincha/Sunnhemp), Gypsum (if alkaline), and River sand. Use Raised Bed cultivation.",
            "fertilizer_advice": "Apply P and K as basal; split Nitrogen (N) into 3-4 doses to prevent leaching and improve efficiency."
        },
        "sandy": {
            "label": "Sandy soil (रेतीली/बलुई मिट्टी)",
            "problems": "Very low water and nutrient retention, fast drying, low organic matter.",
            "corrections": "Heavy application of FYM (20-25 t/ha), frequent Green Manuring, Mulching, and Bio-fertilizers like Azotobacter.",
            "fertilizer_advice": "Apply fertilizer in small, frequent doses. Use slow-release fertilizers (e.g., Neem Coated Urea)."
        },
        "saline": {
            "label": "Saline soil (खारी/नमकीन मिट्टी)",
            "problems": "Salt stress (osmotic), stunted growth, white/grey crust on surface, tip burning.",
            "corrections": "Leach salts with good quality water, ensure deep drainage, add Gypsum (based on soil test), use salt-tolerant crops (Barley, Cotton, Mustard, Spinach).",
            "fertilizer_advice": "Avoid chloride-based fertilizers (MOP). Use Urea and SSP. Apply 25% extra Nitrogen than recommended."
        },
        "acidic": {
            "label": "Acidic soil (अम्लीय मिट्टी)",
            "problems": "Aluminium/Manganese toxicity, deficiency of Calcium, Magnesium, and Phosphorus.",
            "corrections": "Apply Lime (Calcium Carbonate) or Dolomite based on pH. Use Rock Phosphate instead of SSP.",
            "fertilizer_advice": "Avoid acid-forming fertilizers like Ammonium Sulphate."
        }
    },
    "water_management": [
        "Drip Irrigation: Best for Sugarcane, Fruit crops, and Vegetables. Saves 40-70% water and reduces weed growth.",
        "Sprinkler Irrigation: Suitable for crops like Wheat, Mustard, and Pulses in undulating lands.",
        "Mulching: Cover soil with crop residue or plastic to reduce evaporation and control soil temperature.",
        "Rainwater Harvesting: Construct Farm Ponds to store monsoon runoff for life-saving irrigation during dry spells.",
        "AWD (Alternate Wetting and Drying): For Rice, allow field to dry slightly before re-irrigating to save water and reduce Methane.",
        "Precision Leveling: Use Laser Land Levelers for uniform water distribution and saving 20-30% water."
    ],
    "post_harvest": [
        "Cleaning & Grading: Remove stones, dust, and shriveled grains. Grade based on size/quality for better price.",
        "Drying: Grains must be dried to 10-12% moisture (Pulses 9-10%, Oilseeds 7-8%) to prevent fungal growth.",
        "Safe Storage: Use Pusa Bins, Metal Bins, or Hermetic Bags (air-tight). Treat gunny bags with Neem solution.",
        "Cold Storage: Essential for Potato (2-4°C), Tomato, and Fruits to extend shelf life and avoid distress sale.",
        "Value Addition: Processing (e.g., making Dal from Whole Pulse, Flour from Wheat, Tomato Puree) increases profit.",
        "Marketing: Use 'e-NAM' (National Agriculture Market) for online trading. Join FPOs (Farmer Producer Organizations) for bulk selling."
    ]
}

PEST_LIBRARY = {
    "aphids": {
        "name": "Aphids (चेपा/लाही/माहू)",
        "symptoms": "Clusters of tiny green/black insects on tender shoots, curled leaves, sticky honey-dew (sooty mold).",
        "causes": "Cloudy weather, high nitrogen, lack of natural predators like Ladybird beetles.",
        "chemical": "Imidacloprid 17.8% SL (1ml in 3L water) or Thiamethoxam 25% WG (1g in 4L water).",
        "hindi_chemical": "इमिडाक्लोप्रिड 17.8% एसएल (3 लीटर पानी में 1 मिली) या थियोमिथॉक्सम 25% डब्लूजी (4 लीटर पानी में 1 ग्राम)।",
        "organic": "Neem Oil 1500ppm (5ml/L) + soap or Yellow Sticky Traps (10 per acre).",
        "safety": "Avoid spraying during peak bee activity (morning). Wear protective gear."
    },
    "whitefly": {
        "name": "Whitefly (सफेद मक्खी)",
        "symptoms": "Tiny white insects under leaves, yellowing, transmission of Leaf Curl Virus (in Tomato/Chilli/Cotton).",
        "causes": "High temperature and humidity, alternate weed hosts.",
        "chemical": "Diafenthiuron 50% WP (1g/L) or Spiromesifen 22.9% SC (1ml/L).",
        "hindi_chemical": "डायाफेंथियूरॉन 50% डब्लूपी (1 ग्राम/लीटर) या स्पाइरोमेसिफेन 22.9% एससी (1 मिली/लीटर)।",
        "organic": "Yellow Sticky Traps, Neem Oil spray, or Fish Oil Rosin Soap.",
        "safety": "Spray in late evening. Ensure coverage of leaf undersides."
    },
    "stem_borer": {
        "name": "Stem Borer (तना छेदक)",
        "symptoms": "Dead hearts (dried central shoots) in Paddy/Maize/Sugarcane, holes in stems with frass (poop).",
        "causes": "Continuous cropping, high N, stubbles left in field.",
        "chemical": "Chlorantraniliprole 18.5% SC (0.4ml/L) or Cartap Hydrochloride 4G granules (10kg/acre).",
        "hindi_chemical": "क्लोरेंट्रानिलिप्रोल 18.5% एससी (0.4 मिली/लीटर) या कार्टाप हाइड्रोक्लोराइड 4जी दाने (10 किलो/एकड़)।",
        "organic": "Trichogramma cards (egg parasite), Pheromone traps, or Light traps.",
        "safety": "Remove and destroy 'dead hearts' immediately. Do not use granular pesticides in standing water if fish are present."
    },
    "late_blight": {
        "name": "Late Blight (पिछेती झुलसा)",
        "symptoms": "Water-soaked dark spots on leaves, white cottony growth on underside in humid weather, rotting of tubers/fruits.",
        "causes": "High humidity (>90%), cool nights (10-15°C), and cloudy days.",
        "chemical": "Cymoxanil + Mancozeb (2.5g/L) or Dimethomorph (1g/L). Prevent with Mancozeb (2g/L).",
        "hindi_chemical": "साइमोक्सानिल + मैंकोज़ेब (2.5 ग्राम/लीटर) या डाइमेथोमोर्फ (1 ग्राम/लीटर)।",
        "organic": "Pseudomonas fluorescens (10g/L) spray or Fermented Buttermilk (छाछ) spray.",
        "safety": "Ensure proper spacing. Avoid overhead irrigation. Rogue out infected plants."
    },
    "pink_bollworm": {
        "name": "Pink Bollworm (गुलाबी सुंडी)",
        "symptoms": "Bolls fail to open, rotted lint, 'Rosette' flowers (petals twisted), holes in seeds.",
        "causes": "Monoculture of Bt-cotton, lack of refuge crops, late sowing.",
        "chemical": "Profenofos 50% EC (2ml/L) or Emamectin Benzoate 5% SG (0.5g/L).",
        "hindi_chemical": "प्रोफेनोफॉस 50% ईसी (2 मिली/लीटर) या एमेमेक्टिन बेंजोएट 5% एसजी (0.5 ग्राम/लीटर)।",
        "organic": "Pheromone Traps (8-10 per acre), release of Trichogramma bactrae.",
        "safety": "Pick and destroy 'rosette' flowers. Avoid moving cotton sticks to other villages."
    },
    "red_rot": {
        "name": "Red Rot (लाल सड़न - Sugarcane)",
        "symptoms": "Third or fourth leaf shows yellowing, internal tissues turn red with white cross-bands, alcoholic smell.",
        "causes": "Infected setts, waterlogging, contaminated irrigation water.",
        "chemical": "No effective chemical cure; prevent by treating setts with Carbendazim (0.1%).",
        "hindi_chemical": "कोई प्रभावी रासायनिक इलाज नहीं; कार्बेन्डाजिम (0.1%) से बीजोपचार करें।",
        "organic": "Trichoderma viride soil application (2.5kg/acre with FYM).",
        "safety": "Use 3-year crop rotation. Rogue out and burn infected clumps with roots."
    }
}

GOVERNMENT_SCHEMES_DETAILED = [
    {
        "name": "PM-KISAN",
        "title": "Pradhan Mantri Kisan Samman Nidhi",
        "benefits": "₹6,000 per year in 3 installments (₹2,000 each) directly to bank accounts of landholding farmers.",
        "eligibility": "1. All landholding farmer families with land in their name. 2. Exclusions: Institutional holders, constitutional posts, Ministers, Mayors, Govt employees (except Grade IV), pensioners (10k+), and professionals (Doctors, Engineers, Lawyers).",
        "action": "Register on PM-KISAN portal (pmkisan.gov.in) with Aadhaar, Land Records, and Bank Details."
    },
    {
        "name": "PMFBY",
        "title": "Pradhan Mantri Fasal Bima Yojana",
        "benefits": "Comprehensive crop insurance against non-preventable risks (pests, diseases, weather). Uniform low premium.",
        "premium": "2% (Kharif), 1.5% (Rabi), 5% (Commercial/Horticulture crops).",
        "action": "Enroll via banks, CSC centers, or PMFBY portal. Mandatory for loanee farmers, optional for others."
    },
    {
        "name": "KCC",
        "title": "Kisan Credit Card",
        "benefits": "Short-term credit for crop cultivation, post-harvest, and consumption needs. Effective interest rate 4% (with 3% prompt repayment incentive).",
        "limit": "Based on scale of finance for crops and land area. Includes risk insurance.",
        "action": "Apply at any Commercial, Cooperative, or Regional Rural Bank. Requires simplified KYC."
    },
    {
        "name": "Soil Health Card",
        "title": "Soil Health Card Scheme",
        "benefits": "Provides status of soil regarding 12 parameters (N,P,K,S,Zn,Fe,Cu,Mn,B,pH,EC,OC) and dosage recommendations.",
        "frequency": "Issued every 2 years to help farmers optimize fertilizer use.",
        "action": "Samples collected by Agri Dept. Results available on soilhealth.dac.gov.in."
    },
    {
        "name": "PKVY",
        "title": "Paramparagat Krishi Vikas Yojana",
        "benefits": "Promotes organic farming through cluster approach. Financial assistance of ₹50,000 per ha for 3 years.",
        "eligibility": "Farmers in groups/clusters of 50 or more acres.",
        "action": "Contact District Agriculture Office to form/join a cluster."
    },
    {
        "name": "PM-KMY",
        "title": "Pradhan Mantri Kisan Maandhan Yojana",
        "benefits": "Old age pension of ₹3,000 per month after age 60.",
        "eligibility": "Small and Marginal Farmers (SMF) aged 18-40 years. Monthly contribution of ₹55-₹200.",
        "action": "Enroll at nearest CSC center or through PM-KMY portal."
    }
]

def get_system_prompt():
    """Returns the ultimate advanced system prompt for the Krishi Sahayak AI expert"""
    return """You are 'Krishi Sahayak Pro', a world-class Agricultural Scientist and Business Consultant.

    ### YOUR BRAIN ARCHITECTURE:
    1. **Local Knowledge**: Use the provided handbook for specific Indian dosages and schemes.
    2. **Global Science**: Use your general training for crops/pests NOT in the handbook.
    3. **Business Mindset**: When asked about "cultivation" or "farming starting", always provide a structured business plan including:
       - **Climate & Soil requirements**
       - **Cost Table** (estimated investment in INR)
       - **Production/Yield estimates**
       - **Profit/Income calculation**

    ### FORMATTING RULES:
    - USE MARKDOWN. Use **Bold**, # Headers, and Tables | like | this |.
    - Always use Tables for cost/profit analysis.
    - Be extremely detailed like a professional report.

    ### USER PERSONALIZATION:
    - Use the name and location (e.g., Samastipur, Bihar) to tailor the advice (mention local weather or soil if relevant).

    ### PERSONA:
    - Professional, empathetic, and highly expert (KVK level). Use 'Kisan Bhai', 'Aap', and 'Ji'.
    """

def is_hindi_text(text: str) -> bool:
    """Detect whether the input appears to be written in Hindi."""
    return bool(re.search(r'[\u0900-\u097F]', text))

def retrieve_knowledge(message: str) -> str:
    """Retrieve relevant facts with robust bilingual keyword matching."""
    text = (message or "").strip().lower()
    context_parts = []

    # Helper for name matching
    def matches(name_str, query_text):
        # Extract individual words from names like "Rice (धान)"
        keywords = re.findall(r'[\w\u0900-\u097F]+', name_str.lower())
        return any(k in query_text for k in keywords)

    # Crop Search
    found_crops = []
    for crop_key, crop_data in FARMING_KNOWLEDGE["crops"].items():
        if crop_key in text or matches(crop_data["name"], text):
            found_crops.append(crop_key)
            tips = "; ".join(crop_data.get("tips", []))
            context_parts.append(
                f"Crop: {crop_data['name']}. Fertilizer: {crop_data.get('fertilizer')}. Tips: {tips}."
            )

    # Pest Search
    is_pest_query = any(k in text for k in ["pest", "कीट", "insect", "disease", "बीमारी", "control", "नियंत्रण", "इलाज", "दवा"])

    for pest_key, pest_data in PEST_LIBRARY.items():
        # Direct match for pest name
        if pest_key in text or matches(pest_data["name"], text):
            context_parts.append(
                f"Pest {pest_data['name']}: Symptoms: {pest_data['symptoms']}. "
                f"Chemical: {pest_data['chemical']} ({pest_data['hindi_chemical']}). Organic: {pest_data['organic']}."
            )
        # Contextual match: if user asks about pest for a crop we found
        elif is_pest_query and any(crop in pest_data["symptoms"].lower() or crop in pest_data["name"].lower() for crop in found_crops):
             context_parts.append(
                f"Related Pest {pest_data['name']}: Symptoms: {pest_data['symptoms']}. Treatment: {pest_data['chemical']}."
            )

    # Scheme Search
    if any(k in text for k in ["scheme", "yojana", "योजना", "paisa", "loan", "kcc"]):
        for s in GOVERNMENT_SCHEMES_DETAILED:
            if s["name"].lower() in text or matches(s["title"], text):
                context_parts.append(f"Scheme {s['name']}: {s['benefits']}. Action: {s['action']}.")

    # Soil Search
    if any(k in text for k in ["soil", "मिट्टी", "clay", "sandy"]):
        for s_key, s_data in FARMING_KNOWLEDGE["soil_health"].items():
            if s_key in text or matches(s_data["label"], text):
                context_parts.append(f"Soil {s_data['label']}: {s_data['problems']} Correction: {s_data['corrections']}")

    if not context_parts:
        context_parts.append("General Farming Tip: Rotate crops and use organic manure.")

    return " ".join(context_parts[:5])

def get_rag_context(message: str) -> str:
    return retrieve_knowledge(message)

def get_weather_advisory() -> dict:
    return {
        "today": "Partly cloudy with humidity around 65%.",
        "alert": "Monitor for fungal diseases.",
        "recommendation": "Maintain drainage."
    }

def get_government_schemes() -> list[dict]:
    return [
        {"name": s["name"], "benefit": s["benefits"], "details": s["action"]}
        for s in GOVERNMENT_SCHEMES_DETAILED
    ]

def get_soil_health_recommendation(soil_type: str = "", symptoms: str = "", language: str = "en") -> dict:
    text = (soil_type or "").strip().lower()
    selected = None
    for k, v in FARMING_KNOWLEDGE["soil_health"].items():
        if k in text or v["label"].lower() in text:
            selected = v
            break

    if not selected:
        selected = list(FARMING_KNOWLEDGE["soil_health"].values())[0]

    return {
        "success": True,
        "soil_type": selected["label"],
        "health_score": 70,
        "status": "Needs Attention",
        "indicator": selected["problems"],
        "recommendations": {
            "fertilizer": selected["fertilizer_advice"],
            "ph_correction": selected["corrections"],
            "organic_manure": "Apply 10-15 tonnes of well-decomposed FYM per hectare."
        }
    }

def get_crop_calendar(season: str = "all", state: str = "all") -> list[dict]:
    # Expanded static dataset for the interactive calendar
    data = [
        {"crop": "Wheat (गेहूं)", "season": "Rabi", "sowing": "Oct-Nov", "growth": "Dec-Feb", "harvest": "Mar-Apr", "state": "UP/Bihar/Punjab", "note": "CRI stage irrigation is vital."},
        {"crop": "Rice (धान)", "season": "Kharif", "sowing": "Jun-July", "growth": "Aug-Oct", "harvest": "Nov-Dec", "state": "All India", "note": "Keep 5cm water level."},
        {"crop": "Mustard (सरसों)", "season": "Rabi", "sowing": "Oct", "growth": "Nov-Jan", "harvest": "Feb-Mar", "state": "Rajasthan/Haryana", "note": "Protect from Aphids."},
        {"crop": "Potato (आलू)", "season": "Rabi", "sowing": "Oct-Nov", "growth": "Dec-Jan", "harvest": "Feb", "state": "UP/Bihar", "note": "Watch for Late Blight."},
        {"crop": "Maize (मक्का)", "season": "Kharif", "sowing": "June", "growth": "July-Aug", "harvest": "Sept", "state": "Bihar/Karnataka", "note": "Apply Nitrogen in splits."},
        {"crop": "Cotton (कपास)", "season": "Kharif", "sowing": "May-June", "growth": "July-Sept", "harvest": "Oct-Jan", "state": "Punjab/Gujrat", "note": "Use Pheromone traps."},
        {"crop": "Sugarcane (गन्ना)", "season": "Year-round", "sowing": "Feb-Mar", "growth": "Apr-Oct", "harvest": "Nov-Mar", "state": "UP/Maharashtra", "note": "Earthing up at 90 days."}
    ]

    filtered = data
    if season != "all":
        filtered = [c for c in filtered if c["season"].lower() == season.lower()]
    if state != "all":
        filtered = [c for c in filtered if state.lower() in c["state"].lower()]

    return filtered

def get_pest_treatment(message: str, language: str = "en") -> str:
    text = (message or "").strip().lower()
    use_hindi = language == "hi" or is_hindi_text(message)

    for key, data in PEST_LIBRARY.items():
        if key in text or data["name"].lower() in text:
            res = (f"Treatment for {data['name']}: {data['chemical']} (Hindi: {data['hindi_chemical']}). "
                   f"Organic: {data['organic']}. Safety: {data['safety']}")
            if use_hindi:
                res = (f"{data['name']} का उपचार: {data['hindi_chemical']} का प्रयोग करें। "
                       f"जैविक विकल्प: {data['organic']}। सावधानी: {data['safety']}")
            return res

    return "विशिष्ट कीट का नाम बताएं।" if use_hindi else "Please name the specific pest."

def get_fallback_response(message: str, language: str = "en", context: str = "") -> str:
    text = (message or "").strip().lower()
    use_hindi = language == "hi" or is_hindi_text(text)

    # 1. Identity Check
    if any(k in text for k in ["naam", "name", "नाम", "kaun hoon", "who am i"]):
        if "Name: " in context:
            try:
                name_part = context.split("Name: ")[1].split(",")[0].strip()
                return f"नमस्ते {name_part} जी, मैं आपका कृषि सहायक हूँ।" if use_hindi else f"Namaste {name_part}, I am your Krishi Sahayak."
            except: pass

    # 2. Smart Knowledge Lookup (Filtering out irrelevant context)
    # Only show context if it's NOT the general tip and NOT just user background
    clean_context = context
    if "User Background" in clean_context:
        parts = clean_context.split("\n", 1)
        clean_context = parts[1] if len(parts) > 1 else ""

    if clean_context and "General Farming Tip" not in clean_context and len(clean_context.strip()) > 10:
        prefix = "यहाँ आपकी खोज से जुड़ी कुछ मुख्य जानकारी है:\n\n" if use_hindi else "Here is the key information based on your query:\n\n"
        formatted_context = clean_context.replace(". ", ".\n- ").replace("Crop:", "\nफसल (Crop):").replace("Pest", "\nकीट (Pest)").replace("Treatment:", "\nउपचार (Treatment):")
        return prefix + formatted_context

    # 3. Last Resort
    if use_hindi:
        return "क्षमा करें, मैं अभी इस बारे में विस्तार से नहीं बता पा रहा हूँ। क्या आप 'धान', 'गेहूं', या किसी कीट के बारे में पूछना चाहते हैं?"
    return "I'm sorry, I couldn't find specific details right now. Please try asking about a specific crop or pest."
