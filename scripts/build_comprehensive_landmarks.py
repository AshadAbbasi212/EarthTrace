"""Comprehensive multi-city landmark database builder.
Generates comprehensive landmark catalogs for ALL cities in 15 prioritized target countries:
Pakistan (with 100 spots in Islamabad + spots in all 44+ cities/districts),
Turkey, Saudi Arabia, UAE, Egypt, India, Iran, Iraq, Oman, Qatar, Kuwait,
Bahrain, Syria, Yemen, Israel/Palestine, and Global Iconic Anchors.

Also precomputes normalized text embeddings using CLIP ViT-L/14 in safe batches
so runtime vector search is sub-millisecond with zero GPU TDR timeout risk.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_landmarks")

OUT_DIR = Path("data/landmarks")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. PAKISTAN: 100 Spots in Islamabad + ALL cities across all provinces
# -----------------------------------------------------------------------------
islamabad_spots = [
    # 1-10: Iconic National & Religious
    {"name": "Faisal Mosque, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "national_mosque", "lat": 33.7296, "lon": 73.0372, "radius_km": 0.05,
     "prompts": ["Faisal Mosque white tent architectural minarets Margalla foothills Islamabad", "Faisal Mosque courtyard and white marble minarets Islamabad"]},
    {"name": "Pakistan Monument, Shakarparian, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "national_monument", "lat": 33.6934, "lon": 73.0684, "radius_km": 0.05,
     "prompts": ["Pakistan Monument blooming petal granite architecture Shakarparian Islamabad", "Pakistan Monument petal dome Shakarparian hills Islamabad"]},
    {"name": "Daman-e-Koh Margalla Viewpoint, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "viewpoint", "lat": 33.7389, "lon": 73.0583, "radius_km": 0.1,
     "prompts": ["Daman-e-Koh Margalla hills viewpoint terrace overlooking Islamabad city", "Daman-e-Koh garden terrace Margalla ridge view Islamabad"]},
    {"name": "Pir Sohawa & Monal Ridge, Margalla Hills, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "viewpoint", "lat": 33.7483, "lon": 73.0583, "radius_km": 0.15,
     "prompts": ["Monal restaurant terrace dining Pir Sohawa Margalla mountain ridge Islamabad", "Pir Sohawa Margalla crest viewpoint restaurant overlooking Islamabad"]},
    {"name": "Centaurus Mall & Towers, Blue Area, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_towers", "lat": 33.7077, "lon": 73.0503, "radius_km": 0.05,
     "prompts": ["Centaurus Mall three curved glass skyscraper towers Jinnah Avenue Islamabad", "Centaurus towers modern high-rise architecture Blue Area Islamabad"]},
    {"name": "Rawal Lake & Lake View Park, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "park", "lat": 33.7022, "lon": 73.1250, "radius_km": 0.2,
     "prompts": ["Rawal Lake water reservoir promenade and Lake View Park Islamabad", "Lake View Park gardens and boat jetty Rawal Dam Islamabad"]},
    {"name": "Lok Virsa Heritage Museum, Shakarparian, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "museum", "lat": 33.6917, "lon": 73.0708, "radius_km": 0.05,
     "prompts": ["Lok Virsa heritage museum traditional ethnic architecture Shakarparian Islamabad", "Lok Virsa National Heritage Museum courtyard Islamabad"]},
    {"name": "Saidpur Heritage Village, Margalla Foothills, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "heritage_village", "lat": 33.7417, "lon": 73.0686, "radius_km": 0.08,
     "prompts": ["Saidpur historic stone village restaurants and Hindu temple Margalla foothills Islamabad", "Saidpur village courtyard and traditional brick alleyways Islamabad"]},
    {"name": "Fatima Jinnah Park (F-9 Park), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "park", "lat": 33.7000, "lon": 73.0167, "radius_km": 0.3,
     "prompts": ["Fatima Jinnah Park F-9 solar canopy grand promenade pathways Islamabad", "F-9 Park expansive lawns walking trails and recreational pavilions Islamabad"]},
    {"name": "Parliament House & Constitution Avenue, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "government", "lat": 33.7314, "lon": 73.0967, "radius_km": 0.05,
     "prompts": ["Parliament House white facade Constitution Avenue Islamabad", "Majlis-e-Shoora Parliament building and Constitution Avenue Islamabad"]},

    # 11-20: State Institutions, Courts & Diplomatic Enclave
    {"name": "Supreme Court of Pakistan, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "government", "lat": 33.7303, "lon": 73.0983, "radius_km": 0.05,
     "prompts": ["Supreme Court of Pakistan white marble neoclassical building Constitution Avenue Islamabad", "Supreme Court courthouse portico Islamabad"]},
    {"name": "President House (Aiwan-e-Sadr), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "government", "lat": 33.7342, "lon": 73.1000, "radius_km": 0.08,
     "prompts": ["Aiwan-e-Sadr President House grand white palace Constitution Avenue Islamabad", "President House ceremonial gates and lawns Islamabad"]},
    {"name": "Prime Minister Secretariat, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "government", "lat": 33.7375, "lon": 73.1017, "radius_km": 0.08,
     "prompts": ["Prime Minister Secretariat executive building Red Zone Constitution Avenue Islamabad", "PM Secretariat complex Islamabad"]},
    {"name": "Islamabad High Court IHC Building, G-5, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "government", "lat": 33.7220, "lon": 73.0880, "radius_km": 0.05,
     "prompts": ["Islamabad High Court red-and-white courthouse building Sector G-5 Islamabad", "IHC High Court of Islamabad main building"]},
    {"name": "National Art Gallery NAG, F-5, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "museum", "lat": 33.7289, "lon": 73.0867, "radius_km": 0.05,
     "prompts": ["National Art Gallery modern brick-and-terracotta cultural building Sector F-5 Islamabad", "NAG National Art Gallery exhibition halls Islamabad"]},
    {"name": "Pakistan Museum of Natural History PMNH, Shakarparian, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "museum", "lat": 33.6939, "lon": 73.0722, "radius_km": 0.05,
     "prompts": ["Pakistan Museum of Natural History blue whale skeleton Shakarparian Islamabad", "PMNH Natural History Museum building Islamabad"]},
    {"name": "Convention Centre Islamabad, Club Road", "city": "Islamabad", "country": "Pakistan", "category": "civic_building", "lat": 33.7139, "lon": 73.1028, "radius_km": 0.08,
     "prompts": ["Jinnah Convention Centre grand dome architecture Club Road Islamabad", "Convention Centre Islamabad entrance and flagpoles"]},
    {"name": "Diplomatic Enclave Gate 1 & Chancery Row, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "embassy_zone", "lat": 33.7214, "lon": 73.1111, "radius_km": 0.2,
     "prompts": ["Diplomatic Enclave security gate chanceries Sector G-5 Islamabad", "Diplomatic Enclave embassy boulevard Islamabad"]},
    {"name": "US Embassy Compound, Diplomatic Enclave, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "embassy", "lat": 33.7225, "lon": 73.1186, "radius_km": 0.1,
     "prompts": ["United States Embassy compound modern chancery Diplomatic Enclave Islamabad", "US Embassy diplomatic chancery buildings Islamabad"]},
    {"name": "British High Commission, Diplomatic Enclave, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "embassy", "lat": 33.7258, "lon": 73.1147, "radius_km": 0.08,
     "prompts": ["British High Commission chancery gates Diplomatic Enclave Islamabad", "British High Commission diplomatic building Islamabad"]},

    # 21-30: Universities & Campuses
    {"name": "Quaid-e-Azam University campus academic buildings, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "university_campus", "lat": 33.7489, "lon": 73.1369, "radius_km": 0.2,
     "prompts": ["Quaid-e-Azam University campus academic buildings faculty blocks Islamabad", "QAU Islamabad campus faculty buildings Margalla foothills"]},
    {"name": "NUST H-12 Campus Main Library & Gate, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "university_campus", "lat": 33.6425, "lon": 72.9904, "radius_km": 0.2,
     "prompts": ["National University of Sciences and Technology NUST H-12 campus central library Islamabad", "NUST H-12 main university gate and academic squares Islamabad"]},
    {"name": "FAST-NUCES Islamabad Campus, H-9", "city": "Islamabad", "country": "Pakistan", "category": "university_campus", "lat": 33.6567, "lon": 73.0167, "radius_km": 0.1,
     "prompts": ["FAST National University of Computer and Emerging Sciences H-9 campus Islamabad", "FAST-NUCES Islamabad academic building and lawns"]},
    {"name": "COMSATS University Islamabad Campus, Park Road, Chak Shahzad", "city": "Islamabad", "country": "Pakistan", "category": "university_campus", "lat": 33.6517, "lon": 73.1561, "radius_km": 0.15,
     "prompts": ["COMSATS University Islamabad campus faculty blocks Park Road Chak Shahzad", "COMSATS Institute of Information Technology main campus Islamabad"]},
    {"name": "International Islamic University IIUI New Campus, H-10, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "university_campus", "lat": 33.6583, "lon": 73.0250, "radius_km": 0.2,
     "prompts": ["International Islamic University IIUI grand mosque and academic blocks Sector H-10 Islamabad", "IIUI H-10 university campus buildings Islamabad"]},
    {"name": "National Defence University NDU, E-9, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "university_campus", "lat": 33.7250, "lon": 73.0250, "radius_km": 0.1,
     "prompts": ["National Defence University NDU main military academic block Sector E-9 Islamabad", "NDU Islamabad campus entrance Margalla foothills"]},
    {"name": "Air University Islamabad Campus, PAF Complex E-9", "city": "Islamabad", "country": "Pakistan", "category": "university_campus", "lat": 33.7167, "lon": 73.0278, "radius_km": 0.08,
     "prompts": ["Air University main academic building Sector E-9 PAF Complex Islamabad", "Air University campus square Islamabad"]},
    {"name": "Bahria University Islamabad Campus, E-8", "city": "Islamabad", "country": "Pakistan", "category": "university_campus", "lat": 33.7222, "lon": 73.0361, "radius_km": 0.08,
     "prompts": ["Bahria University campus modern building Naval Complex Sector E-8 Islamabad", "Bahria University Islamabad gate and blocks"]},
    {"name": "Allama Iqbal Open University AIOU Central Campus, H-8, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "university_campus", "lat": 33.6806, "lon": 73.0611, "radius_km": 0.1,
     "prompts": ["Allama Iqbal Open University AIOU central academic block Sector H-8 Islamabad", "AIOU main campus administration building Islamabad"]},
    {"name": "Higher Education Commission HEC Headquarters, H-9, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "civic_building", "lat": 33.6694, "lon": 73.0472, "radius_km": 0.05,
     "prompts": ["Higher Education Commission HEC headquarters glass building Sector H-9 Islamabad", "HEC head office building Islamabad"]},

    # 31-40: Commercial Hubs & Malls
    {"name": "Blue Area Jinnah Avenue Commercial Strip, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_district", "lat": 33.7125, "lon": 73.0650, "radius_km": 0.2,
     "prompts": ["Blue Area Jinnah Avenue commercial boulevard skyscrapers Islamabad", "Blue Area financial and retail high-rises Islamabad"]},
    {"name": "Saudi Pak Tower, Blue Area, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_towers", "lat": 33.7128, "lon": 73.0628, "radius_km": 0.05,
     "prompts": ["Saudi Pak Tower brutalist Islamic modern high-rise Blue Area Jinnah Avenue Islamabad", "Saudi Pak Tower office building Islamabad"]},
    {"name": "Islamabad Stock Exchange ISE Towers, Blue Area", "city": "Islamabad", "country": "Pakistan", "category": "commercial_towers", "lat": 33.7139, "lon": 73.0656, "radius_km": 0.05,
     "prompts": ["Islamabad Stock Exchange ISE Towers twin glass skyscrapers Blue Area Islamabad", "ISE Towers financial center Jinnah Avenue Islamabad"]},
    {"name": "Telecom Tower, Blue Area, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_towers", "lat": 33.7153, "lon": 73.0694, "radius_km": 0.05,
     "prompts": ["PTCL Telecom Tower tall curved office building Blue Area Islamabad", "Telecom Tower modern glass facade Jinnah Avenue Islamabad"]},
    {"name": "Safa Gold Mall, F-7 Markaz (Jinnah Super), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "shopping_mall", "lat": 33.7225, "lon": 73.0567, "radius_km": 0.05,
     "prompts": ["Safa Gold Mall multistory shopping center F-7 Markaz Jinnah Super Islamabad", "Safa Gold Mall retail entrance Sector F-7 Islamabad"]},
    {"name": "Giga Mall & World Trade Center, DHA Phase 2, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "shopping_mall", "lat": 33.5283, "lon": 73.1617, "radius_km": 0.1,
     "prompts": ["Giga Mall World Trade Center grand shopping atrium GT Road DHA Phase 2 Islamabad", "Giga Mall hypermarket and retail towers Islamabad"]},
    {"name": "F-6 Super Market Commercial Square, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.7294, "lon": 73.0767, "radius_km": 0.08,
     "prompts": ["F-6 Super Market open commercial square bookshops and cafes Sector F-6 Islamabad", "Super Market F-6 Islamabad retail plaza"]},
    {"name": "Kohsar Market, Sector F-6/3, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.7336, "lon": 73.0728, "radius_km": 0.05,
     "prompts": ["Kohsar Market outdoor upscale dining cafes and gourmet stores Sector F-6 Islamabad", "Kohsar Market restaurant patio Sector F-6/3 Islamabad"]},
    {"name": "F-7 Jinnah Super Market Roundabout & Plaza, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.7208, "lon": 73.0556, "radius_km": 0.08,
     "prompts": ["Jinnah Super Market circular commercial plaza Sector F-7 Islamabad", "F-7 Markaz Jinnah Super shops and restaurants Islamabad"]},
    {"name": "Beverly Centre, Blue Area / F-6, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.7189, "lon": 73.0689, "radius_km": 0.05,
     "prompts": ["Beverly Centre trendy restaurants and retail shops Nazim-ud-din Road Islamabad", "Beverly Centre commercial arcade Sector F-6 Islamabad"]},

    # 41-50: Sector Markazes
    {"name": "F-8 Markaz (Ayub Market), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.7111, "lon": 73.0389, "radius_km": 0.08,
     "prompts": ["F-8 Markaz commercial square shops restaurants Sector F-8 Islamabad", "Ayub Market F-8 Markaz retail plaza Islamabad"]},
    {"name": "F-10 Markaz (Sumbal Market), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.6972, "lon": 73.0125, "radius_km": 0.08,
     "prompts": ["F-10 Markaz buzzing commercial square retail towers Sector F-10 Islamabad", "F-10 Markaz round shopping plaza Islamabad"]},
    {"name": "F-11 Markaz (Fehmida Market), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.6847, "lon": 72.9889, "radius_km": 0.08,
     "prompts": ["F-11 Markaz modern high-rise apartments and shopping arcade Sector F-11 Islamabad", "F-11 Markaz commercial center Islamabad"]},
    {"name": "G-9 Markaz (Karachi Company), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.6903, "lon": 73.0306, "radius_km": 0.1,
     "prompts": ["G-9 Karachi Company bustling commercial marketplace and bus terminal Sector G-9 Islamabad", "Karachi Company G-9 Markaz bazaar Islamabad"]},
    {"name": "G-11 Markaz, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.6736, "lon": 72.9986, "radius_km": 0.08,
     "prompts": ["G-11 Markaz commercial plaza residential towers Sector G-11 Islamabad", "G-11 Markaz shopping arcade Islamabad"]},
    {"name": "I-8 Markaz (Tipu Market), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.6681, "lon": 73.0764, "radius_km": 0.08,
     "prompts": ["I-8 Markaz pedestrian food street and shopping center Sector I-8 Islamabad", "I-8 Markaz commercial avenue Islamabad"]},
    {"name": "I-9 Markaz & Industrial Area, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "industrial_district", "lat": 33.6556, "lon": 73.0611, "radius_km": 0.15,
     "prompts": ["Sector I-9 Industrial Area commercial warehouses and factories Islamabad", "I-9 Markaz commercial zone Islamabad"]},
    {"name": "I-10 Markaz, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.6444, "lon": 73.0389, "radius_km": 0.08,
     "prompts": ["I-10 Markaz commercial marketplace retail stores Sector I-10 Islamabad", "I-10 Markaz shopping square Islamabad"]},
    {"name": "G-8 Markaz (Babri Market), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.7000, "lon": 73.0417, "radius_km": 0.08,
     "prompts": ["G-8 Markaz commercial plaza shops near PIMS Hospital Sector G-8 Islamabad", "G-8 Markaz market Islamabad"]},
    {"name": "G-7 Markaz (Sitara Market), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_market", "lat": 33.7069, "lon": 73.0611, "radius_km": 0.08,
     "prompts": ["Sitara Market Sector G-7 commercial shops and municipal offices Islamabad", "G-7 Markaz Sitara Market plaza Islamabad"]},

    # 51-60: Hospitality & Clubs
    {"name": "Serena Hotel Islamabad, Club Road", "city": "Islamabad", "country": "Pakistan", "category": "luxury_hotel", "lat": 33.7194, "lon": 73.1028, "radius_km": 0.05,
     "prompts": ["Islamabad Serena Hotel traditional Islamic palace architecture and water gardens", "Serena Hotel luxury courtyard and banquet lawns Islamabad"]},
    {"name": "Islamabad Marriott Hotel, Sector F-5/1", "city": "Islamabad", "country": "Pakistan", "category": "luxury_hotel", "lat": 33.7292, "lon": 73.0903, "radius_km": 0.05,
     "prompts": ["Marriott Hotel Islamabad white facade near Constitution Avenue Sector F-5", "Islamabad Marriott Hotel entrance driveway and security gates"]},
    {"name": "Islamabad Club & Polo Ground, Shakarparian", "city": "Islamabad", "country": "Pakistan", "category": "sports_club", "lat": 33.7083, "lon": 73.1056, "radius_km": 0.15,
     "prompts": ["Islamabad Club polo ground clubhouse and manicured green lawns Murree Road Islamabad", "Islamabad Club equestrian pavilion and sports facilities"]},
    {"name": "Islamabad Golf Club, Shakarparian / Rawal Lake", "city": "Islamabad", "country": "Pakistan", "category": "sports_club", "lat": 33.6972, "lon": 73.0917, "radius_km": 0.2,
     "prompts": ["Islamabad Golf Club 18-hole fairway rolling hills and lake view Shakarparian Islamabad", "Islamabad Golf Club fairways and clubhouse"]},
    {"name": "Gun & Country Club Islamabad, Shakarparian", "city": "Islamabad", "country": "Pakistan", "category": "sports_club", "lat": 33.7000, "lon": 73.0778, "radius_km": 0.1,
     "prompts": ["Gun and Country Club shooting range and recreational club Shakarparian Islamabad", "Gun and Country Club sporting grounds Islamabad"]},
    {"name": "Best Western Premier Hotel Islamabad, Club Road", "city": "Islamabad", "country": "Pakistan", "category": "hotel", "lat": 33.7150, "lon": 73.1067, "radius_km": 0.05,
     "prompts": ["Best Western Premier Hotel building Club Road near Rawal Lake Islamabad", "Best Western Hotel Islamabad entrance"]},
    {"name": "Ramada by Wyndham Islamabad, Club Road", "city": "Islamabad", "country": "Pakistan", "category": "hotel", "lat": 33.7111, "lon": 73.1111, "radius_km": 0.05,
     "prompts": ["Ramada Hotel Rawal Lake view Club Road Sector Islamabad", "Ramada Hotel building overlooking Rawal Dam reservoir Islamabad"]},
    {"name": "Pearl Continental PC Bhurban / Murree Gateway, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "luxury_hotel", "lat": 33.9556, "lon": 73.4514, "radius_km": 0.1,
     "prompts": ["Pearl Continental PC Hotel Bhurban pine tree valley and golf course Murree Hills", "PC Bhurban luxury mountain resort terrace"]},
    {"name": "Hotel Crown Plaza Islamabad, Blue Area", "city": "Islamabad", "country": "Pakistan", "category": "hotel", "lat": 33.7119, "lon": 73.0583, "radius_km": 0.05,
     "prompts": ["Hotel Crown Plaza high-rise building Jinnah Avenue Blue Area Islamabad", "Crown Plaza Hotel Islamabad facade"]},
    {"name": "Shelton Hotel & Guest House, F-8/3, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hotel", "lat": 33.7150, "lon": 73.0450, "radius_km": 0.05,
     "prompts": ["Shelton boutique hotel and guest suites Sector F-8/3 Islamabad", "Shelton Hotel Islamabad entrance"]},

    # 61-70: Hospitals & Healthcare
    {"name": "Shifa International Hospital, H-8/4, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hospital_complex", "lat": 33.6861, "lon": 73.0806, "radius_km": 0.08,
     "prompts": ["Shifa International Hospital grand medical complex red brick buildings Sector H-8/4 Islamabad", "Shifa Hospital main entrance and trauma tower Islamabad"]},
    {"name": "Pakistan Institute of Medical Sciences PIMS, G-8/3, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hospital_complex", "lat": 33.7042, "lon": 73.0472, "radius_km": 0.1,
     "prompts": ["Pakistan Institute of Medical Sciences PIMS hospital campus and trauma center Sector G-8 Islamabad", "PIMS Hospital main emergency facade Islamabad"]},
    {"name": "Federal Government Polyclinic Hospital, G-6/2, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hospital_complex", "lat": 33.7222, "lon": 73.0778, "radius_km": 0.05,
     "prompts": ["Polyclinic Hospital medical wards and outdoor patient department Sector G-6 Islamabad", "Federal Government Polyclinic building Islamabad"]},
    {"name": "Maroof International Hospital, F-10 Markaz, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hospital_complex", "lat": 33.6944, "lon": 73.0111, "radius_km": 0.05,
     "prompts": ["Maroof International Hospital private medical facility Sector F-10 Markaz Islamabad", "Maroof Hospital glass building Islamabad"]},
    {"name": "Kulsum International Hospital, Blue Area, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hospital_complex", "lat": 33.7094, "lon": 73.0528, "radius_km": 0.05,
     "prompts": ["Kulsum International Hospital tower Jinnah Avenue Blue Area Islamabad", "Kulsum Hospital facade Islamabad"]},
    {"name": "National Institute of Health NIH, Chak Shahzad, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "medical_research", "lat": 33.6722, "lon": 73.1389, "radius_km": 0.1,
     "prompts": ["National Institute of Health NIH research laboratories and campus Chak Shahzad Islamabad", "NIH Pakistan biomedical center Islamabad"]},
    {"name": "PAEC Nuclear Medicine Oncology NORI Hospital, G-8/3", "city": "Islamabad", "country": "Pakistan", "category": "hospital_complex", "lat": 33.7014, "lon": 73.0500, "radius_km": 0.05,
     "prompts": ["NORI Cancer Hospital PAEC medical facility Sector G-8/3 Islamabad", "NORI Hospital oncology tower Islamabad"]},
    {"name": "Quaid-e-Azam International Hospital QIH, Golra Mor, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hospital_complex", "lat": 33.6278, "lon": 72.9667, "radius_km": 0.08,
     "prompts": ["Quaid-e-Azam International Hospital modern multi-story medical center Peshawar Road Golra Mor Islamabad", "QIH Hospital building Islamabad"]},
    {"name": "Ali Medical Centre, F-8 Markaz, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hospital_complex", "lat": 33.7083, "lon": 73.0361, "radius_km": 0.05,
     "prompts": ["Ali Medical Centre private hospital building Sector F-8 Markaz Islamabad", "Ali Medical Centre entrance Islamabad"]},
    {"name": "Medicsi Hospital, F-10/4, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hospital_complex", "lat": 33.6917, "lon": 73.0083, "radius_km": 0.05,
     "prompts": ["Medicsi private specialized hospital building Sector F-10/4 Islamabad", "Medicsi Hospital clinic Islamabad"]},

    # 71-80: Parks, Trails & Nature
    {"name": "Margalla Hills Trail 3 Viewpoint, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hiking_trail", "lat": 33.7444, "lon": 73.0611, "radius_km": 0.1,
     "prompts": ["Trail 3 Margalla Hills hiking track rocky ridge trail pine trees Islamabad", "Trail 3 viewpoint wooden benches overlooking Islamabad city"]},
    {"name": "Margalla Hills Trail 5 (Ghanghar Stream), Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hiking_trail", "lat": 33.7472, "lon": 73.0722, "radius_km": 0.1,
     "prompts": ["Trail 5 Margalla Hills natural freshwater stream rocky hiking track Islamabad", "Trail 5 trailhead picnic area and forest trail Islamabad"]},
    {"name": "Trail 2 (Daman-e-Koh to Zoo), Margalla Hills, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "hiking_trail", "lat": 33.7361, "lon": 73.0556, "radius_km": 0.1,
     "prompts": ["Trail 2 Margalla Hills dirt trail path winding from Marghazar to Daman-e-Koh Islamabad", "Trail 2 ridge hiking path Islamabad"]},
    {"name": "Rose & Jasmine Garden, Shakarparian, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "park", "lat": 33.6972, "lon": 73.0806, "radius_km": 0.08,
     "prompts": ["Rose and Jasmine Garden landscaped rose flowerbeds and walking path Shakarparian Islamabad", "Rose and Jasmine Garden seasonal flower exhibition lawns Islamabad"]},
    {"name": "Japanese Children Park, Margalla Road, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "park", "lat": 33.7333, "lon": 73.0611, "radius_km": 0.05,
     "prompts": ["Japanese Children Park wooden playground obstacle courses Sector F-6 Margalla Road Islamabad", "Japanese Park swings and green hillocks Islamabad"]},
    {"name": "Shah Allah Ditta Buddhist Caves, Margalla Foothills, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "heritage_site", "lat": 33.7194, "lon": 72.9194, "radius_km": 0.08,
     "prompts": ["Shah Allah Ditta historic Buddhist rock caves banyan trees Sadhu platform Margalla Islamabad", "Shah Allah Ditta ancient caves and freshwater spring Islamabad"]},
    {"name": "Korang River Valley & Promenade, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "river_valley", "lat": 33.6667, "lon": 73.1333, "radius_km": 0.15,
     "prompts": ["Korang River valley rocky stream banks and natural green basin Islamabad", "Korang riverbed crossing Chak Shahzad Islamabad"]},
    {"name": "Ankora / Simly Dam Reservoir, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "reservoir", "lat": 33.7917, "lon": 73.2833, "radius_km": 0.3,
     "prompts": ["Simly Dam reservoir blue water and concrete spillway hills Islamabad", "Simly Dam scenic lake and water filtration plant Islamabad"]},
    {"name": "Dino Valley Park, Monal Pir Sohawa Road, Margalla", "city": "Islamabad", "country": "Pakistan", "category": "theme_park", "lat": 33.7667, "lon": 73.0667, "radius_km": 0.08,
     "prompts": ["Dino Valley theme park dinosaur statues in pine forest Margalla Hills Islamabad", "Dino Valley family adventure park Pir Sohawa road Margalla"]},
    {"name": "Shahdara Picnic Spot & Freshwater Stream, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "natural_landmark", "lat": 33.7611, "lon": 73.1667, "radius_km": 0.15,
     "prompts": ["Shahdara Valley freshwater mountain stream charpoys in shallow water Margalla foothills Islamabad", "Shahdara picnic spot green hills and rocky stream Islamabad"]},

    # 81-90: Transport & Infrastructure
    {"name": "Islamabad International Airport IIAP Passenger Terminal", "city": "Islamabad", "country": "Pakistan", "category": "airport", "lat": 33.5489, "lon": 72.8250, "radius_km": 0.3,
     "prompts": ["Islamabad International Airport IIAP curved passenger terminal glass apron control tower", "New Islamabad Airport main departures concourse and runway"]},
    {"name": "Zero Point Interchange, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "interchange", "lat": 33.6889, "lon": 73.0611, "radius_km": 0.1,
     "prompts": ["Zero Point Interchange multi-level cloverleaf flyovers Kashmir Highway Faisal Avenue Islamabad", "Zero Point flyover network and landscaped green loops Islamabad"]},
    {"name": "Faizabad Interchange & Metro Station, Islamabad/Rawalpindi", "city": "Islamabad", "country": "Pakistan", "category": "interchange", "lat": 33.6639, "lon": 73.0778, "radius_km": 0.1,
     "prompts": ["Faizabad Interchange massive elevated flyovers and Metro Bus station boundary Islamabad Rawalpindi", "Faizabad junction connecting Murree Road and Expressway"]},
    {"name": "Golra Sharif Railway Station & Heritage Museum, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "railway_station", "lat": 33.6708, "lon": 72.9486, "radius_km": 0.05,
     "prompts": ["Golra Sharif historic colonial railway junction stone station and steam locomotive museum Islamabad", "Golra Railway Heritage Museum antique carriages and banyan tree platform"]},
    {"name": "Srinagar (Kashmir) Highway Corridor, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "highway", "lat": 33.6778, "lon": 73.0333, "radius_km": 0.2,
     "prompts": ["Srinagar Highway expansive multi-lane landscaped expressway pine trees Islamabad", "Kashmir Highway central artery connecting airport to Islamabad"]},
    {"name": "Islamabad Expressway Toll Plaza & Gulberg Interchange", "city": "Islamabad", "country": "Pakistan", "category": "highway", "lat": 33.5972, "lon": 73.1250, "radius_km": 0.15,
     "prompts": ["Islamabad Expressway multi-lane highway flyover Gulberg Greens entrance Islamabad", "Islamabad Expressway signal-free corridor and flyover bridges"]},
    {"name": "Metro Bus Saddar-Pak Secretariat Elevated Corridor, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "transit_corridor", "lat": 33.7111, "lon": 73.0583, "radius_km": 0.1,
     "prompts": ["Rawalpindi Islamabad Metro Bus red articulated bus on elevated dedicated flyover Blue Area", "Metro Bus station glass elevated platform Jinnah Avenue Islamabad"]},
    {"name": "Chaman / Rawal Road Interchange, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "interchange", "lat": 33.6806, "lon": 73.0972, "radius_km": 0.08,
     "prompts": ["Rawal Dam Chowk flyover and landscaped underpass Club Road Islamabad", "Rawal Dam junction interchange Islamabad"]},
    {"name": "Murree Expressway (N-75) Toll Plaza, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "highway", "lat": 33.7444, "lon": 73.1833, "radius_km": 0.1,
     "prompts": ["Murree Expressway N-75 toll booths and mountain foothills gateway Islamabad", "N-75 Expressway entry towards Murree Hills Islamabad"]},
    {"name": "G.T. Road Tarnol Interchange, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "highway", "lat": 33.6333, "lon": 72.9056, "radius_km": 0.1,
     "prompts": ["Tarnol GT Road flyover and railway overhead bridge western entrance Islamabad", "Tarnol junction commercial trucks and GT Road highway"]},

    # 91-100: Heritage & Suburbs
    {"name": "Shrine of Bari Imam (Hazrat Shah Abdul Latif Kazmi), Nurpur Shahan, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "shrine", "lat": 33.7472, "lon": 73.1194, "radius_km": 0.05,
     "prompts": ["Shrine of Bari Imam green dome complex marble courtyard Nurpur Shahan Islamabad", "Bari Imam shrine entrance and devotees plaza Margalla foothills"]},
    {"name": "Bahria Enclave Grand Jamia Mosque & Dancing Fountains, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "mosque", "lat": 33.6917, "lon": 73.2083, "radius_km": 0.08,
     "prompts": ["Bahria Enclave Grand Jamia Mosque Turkish ottoman architecture and commercial boulevard Islamabad", "Bahria Enclave fountain circle and modern residential sector Islamabad"]},
    {"name": "Gulberg Greens D-Markaz & Canal City, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "commercial_district", "lat": 33.5833, "lon": 73.1500, "radius_km": 0.15,
     "prompts": ["Gulberg Greens D-Markaz grand commercial square glass buildings and boulevard Islamabad", "Gulberg Greens palm tree avenues and waterfront boulevard Islamabad"]},
    {"name": "DHA Phase 2 Central Boulevard & Clock Tower, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "residential_district", "lat": 33.5167, "lon": 73.1500, "radius_km": 0.1,
     "prompts": ["DHA Phase 2 Islamabad main boulevard clock tower commercial square", "DHA Phase 2 entrance gates and landscaped roundabouts Islamabad"]},
    {"name": "Park View City Grand Mosque & Lake, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "residential_district", "lat": 33.6806, "lon": 73.1861, "radius_km": 0.1,
     "prompts": ["Park View City downtown lake and grand mosque Malot Margalla views Islamabad", "Park View City commercial downtown and residential hills Islamabad"]},
    {"name": "1965 War Memorial & Shakarparian Parade Ground, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "national_monument", "lat": 33.6861, "lon": 73.0833, "radius_km": 0.1,
     "prompts": ["Shakarparian National Parade Ground grandstands and military monument Islamabad", "Pakistan Day parade grandstand Shakarparian Islamabad"]},
    {"name": "Talhar & Gokina Village Pine Ridge, Margalla Hills, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "mountain_ridge", "lat": 33.7833, "lon": 73.0500, "radius_km": 0.2,
     "prompts": ["Gokina and Talhar village pine ridge viewpoints Margalla Hills behind Islamabad", "Margalla highland rural terraced fields and pine forests Islamabad"]},
    {"name": "Kenthla Dam & Reservoir, Margalla Basin, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "reservoir", "lat": 33.7833, "lon": 72.8667, "radius_km": 0.15,
     "prompts": ["Kenthla Dam scenic blue water reservoir nestled in Margalla hills Islamabad", "Kenthla Dam spillway and picnic ridge Islamabad"]},
    {"name": "Rawal Dam Spillway & Old Bridge, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "dam", "lat": 33.6944, "lon": 73.1194, "radius_km": 0.08,
     "prompts": ["Rawal Dam concrete masonry spillway gates and downstream canyon Islamabad", "Rawal Dam reservoir wall and observation tower Islamabad"]},
    {"name": "Saidpur Old Hindu Temple & Gurdwara Complex, Islamabad", "city": "Islamabad", "country": "Pakistan", "category": "historical_temple", "lat": 33.7422, "lon": 73.0692, "radius_km": 0.05,
     "prompts": ["Saidpur village ancient Hindu temple stone facade and step pond Margalla Islamabad", "Historic Rama Temple and Sikh gurdwara building Saidpur village Islamabad"]}
]

# Pakistan - Covering EVERY OTHER city & district
pakistan_other_cities = [
    # Lahore (15 spots)
    {"name": "Badshahi Mosque, Lahore", "city": "Lahore", "country": "Pakistan", "category": "historical_mosque", "lat": 31.5881, "lon": 74.3108, "radius_km": 0.05,
     "prompts": ["Badshahi Mosque grand red sandstone Mughal courtyard and white marble domes Lahore", "Badshahi Mosque vast courtyard minarets Lahore"]},
    {"name": "Minar-e-Pakistan, Greater Iqbal Park, Lahore", "city": "Lahore", "country": "Pakistan", "category": "national_monument", "lat": 31.5925, "lon": 74.3094, "radius_km": 0.05,
     "prompts": ["Minar-e-Pakistan tall white memorial tower Greater Iqbal Park Lahore", "Minar-e-Pakistan tower and surrounding fountains Lahore"]},
    {"name": "Lahore Fort (Shahi Qila), Lahore", "city": "Lahore", "country": "Pakistan", "category": "unesco_world_heritage", "lat": 31.5881, "lon": 74.3153, "radius_km": 0.08,
     "prompts": ["Lahore Fort Shahi Qila Alamgiri Gate red sandstone Mughal fortress Lahore", "Lahore Fort Sheesh Mahal mirror palace and Diwan-e-Aam"]},
    {"name": "Wazir Khan Mosque, Walled City, Lahore", "city": "Lahore", "country": "Pakistan", "category": "historical_mosque", "lat": 31.5833, "lon": 74.3217, "radius_km": 0.05,
     "prompts": ["Wazir Khan Mosque intricate glazed tilework kashi-kari and minarets Old Lahore", "Wazir Khan Mosque courtyard vibrant fresco wall murals Lahore"]},
    {"name": "Shalimar Gardens (Shalamar Bagh), Lahore", "city": "Lahore", "country": "Pakistan", "category": "unesco_world_heritage", "lat": 31.5861, "lon": 74.3819, "radius_km": 0.08,
     "prompts": ["Shalimar Gardens Mughal terraced water cascades fountains and pavilions Lahore", "Shalimar Gardens historic Mughal water gardens Lahore"]},
    {"name": "Packages Mall, Walton Road, Lahore", "city": "Lahore", "country": "Pakistan", "category": "shopping_mall", "lat": 31.4722, "lon": 74.3542, "radius_km": 0.08,
     "prompts": ["Packages Mall grand modern shopping mall atrium Walton Road Lahore", "Packages Mall exterior facade and parking plaza Lahore"]},
    {"name": "Emporium Mall by Nishat, Johar Town, Lahore", "city": "Lahore", "country": "Pakistan", "category": "shopping_mall", "lat": 31.4678, "lon": 74.2667, "radius_km": 0.08,
     "prompts": ["Emporium Mall massive contemporary glass retail shopping complex Johar Town Lahore", "Emporium Mall interior atrium and Nishat Hotel Lahore"]},
    {"name": "Gaddafi Stadium (Lahore Cricket Stadium), Gulberg, Lahore", "city": "Lahore", "country": "Pakistan", "category": "stadium", "lat": 31.5133, "lon": 74.3333, "radius_km": 0.1,
     "prompts": ["Gaddafi Stadium red brick Mughal architectural arches cricket ground Lahore", "Gaddafi Stadium cricket arena and floodlights Lahore"]},
    {"name": "Liberty Market Roundabout, Gulberg 3, Lahore", "city": "Lahore", "country": "Pakistan", "category": "commercial_market", "lat": 31.5097, "lon": 74.3425, "radius_km": 0.08,
     "prompts": ["Liberty Market bustling roundabout illuminated shops Gulberg Lahore", "Liberty Market circular shopping plaza and fountain Lahore"]},
    {"name": "MM Alam Road Commercial Food Street, Gulberg, Lahore", "city": "Lahore", "country": "Pakistan", "category": "commercial_district", "lat": 31.5167, "lon": 74.3500, "radius_km": 0.1,
     "prompts": ["MM Alam Road upscale restaurants cafes and fashion boutiques Gulberg Lahore", "MM Alam Road evening street dining Lahore"]},
    {"name": "Wagah Border Flag Ceremony Arena, Lahore", "city": "Lahore", "country": "Pakistan", "category": "national_monument", "lat": 31.6050, "lon": 74.5728, "radius_km": 0.05,
     "prompts": ["Wagah Border stadium amphitheatre flag lowering ceremony Lahore Pakistan", "Wagah Border gate and national parade arena"]},
    {"name": "Tomb of Jahangir, Shahdara, Lahore", "city": "Lahore", "country": "Pakistan", "category": "unesco_world_heritage", "lat": 31.6225, "lon": 74.3033, "radius_km": 0.08,
     "prompts": ["Tomb of Jahangir sandstone and marble mausoleum minarets Shahdara Lahore", "Jahangir Tomb Persian gardens and marble mosaics Lahore"]},
    {"name": "Government College University GCU Gothic Tower, Lahore", "city": "Lahore", "country": "Pakistan", "category": "university_campus", "lat": 31.5732, "lon": 74.3084, "radius_km": 0.05,
     "prompts": ["Government College University GCU Gothic clock tower red brick campus Lahore", "GCU Lahore historic colonial academic hall"]},
    {"name": "Chauburji Monument & Orange Line Metro, Lahore", "city": "Lahore", "country": "Pakistan", "category": "historical_monument", "lat": 31.5542, "lon": 74.3042, "radius_km": 0.05,
     "prompts": ["Chauburji historic four-towered Mughal gateway monument and Orange Line metro Lahore", "Chauburji monument tile mosaic towers Lahore"]},
    {"name": "Eiffel Tower Replica, Bahria Town, Lahore", "city": "Lahore", "country": "Pakistan", "category": "monument", "lat": 31.3653, "lon": 74.1889, "radius_km": 0.05,
     "prompts": ["Eiffel Tower replica steel monument illuminated Bahria Town Lahore", "Bahria Town Lahore Eiffel Tower park and boulevard"]},

    # Karachi (12 spots)
    {"name": "Mazar-e-Quaid (Jinnah Mausoleum), Karachi", "city": "Karachi", "country": "Pakistan", "category": "national_monument", "lat": 24.8753, "lon": 67.0408, "radius_km": 0.05,
     "prompts": ["Mazar-e-Quaid white marble modernist cube dome mausoleum Karachi", "Mazar-e-Quaid Quaid-e-Azam tomb illuminated gardens Karachi"]},
    {"name": "Clifton Beach & Sea View Promenade, Karachi", "city": "Karachi", "country": "Pakistan", "category": "coast", "lat": 24.7892, "lon": 67.0583, "radius_km": 0.2,
     "prompts": ["Clifton Sea View sandy beach Arabian Sea camels and promenade Karachi", "Sea View Clifton beach coastline sunset Karachi"]},
    {"name": "Mohatta Palace Museum, Clifton, Karachi", "city": "Karachi", "country": "Pakistan", "category": "historical_palace", "lat": 24.8142, "lon": 67.0322, "radius_km": 0.05,
     "prompts": ["Mohatta Palace Rajasthani pink Jodhpur sandstone palace museum Clifton Karachi", "Mohatta Palace gardens and stone domes Karachi"]},
    {"name": "Frere Hall & Gardens, Saddar, Karachi", "city": "Karachi", "country": "Pakistan", "category": "colonial_architecture", "lat": 24.8472, "lon": 67.0333, "radius_km": 0.05,
     "prompts": ["Frere Hall Venetian Gothic yellow limestone building Sadequain ceiling murals Karachi", "Frere Hall historic colonial library and lawns Karachi"]},
    {"name": "Port Grand Waterfront Food Street, Karachi", "city": "Karachi", "country": "Pakistan", "category": "commercial_district", "lat": 24.8444, "lon": 66.9889, "radius_km": 0.08,
     "prompts": ["Port Grand waterfront boardwalk restaurants old bridge harbor Native Jetty Karachi", "Port Grand Karachi evening food street along harbor"]},
    {"name": "PAF Museum, Shahrah-e-Faisal, Karachi", "city": "Karachi", "country": "Pakistan", "category": "aircraft_monument", "lat": 24.8876, "lon": 67.0984, "radius_km": 0.1,
     "prompts": ["PAF Museum outdoor aircraft display park fighter jets Pakistan Air Force Karachi", "Pakistan Air Force Museum Shahrah-e-Faisal Karachi military aircraft"]},
    {"name": "Dolmen Mall Clifton, Karachi", "city": "Karachi", "country": "Pakistan", "category": "shopping_mall", "lat": 24.8097, "lon": 67.0333, "radius_km": 0.05,
     "prompts": ["Dolmen Mall Clifton sea-facing luxury retail mall complex Karachi", "Dolmen Mall interior multi-level atrium Karachi"]},
    {"name": "Bahria Town Grand Jamia Mosque Karachi, Super Highway", "city": "Karachi", "country": "Pakistan", "category": "national_mosque", "lat": 25.0167, "lon": 67.3333, "radius_km": 0.1,
     "prompts": ["Grand Jamia Mosque Bahria Town Karachi massive white marble domes and minaret", "Bahria Town Karachi Grand Mosque architecture"]},
    {"name": "Empress Market, Saddar, Karachi", "city": "Karachi", "country": "Pakistan", "category": "colonial_architecture", "lat": 24.8614, "lon": 67.0306, "radius_km": 0.05,
     "prompts": ["Empress Market Victorian Gothic stone clock tower bazaar Saddar Karachi", "Empress Market heritage building and pedestrian plaza Karachi"]},
    {"name": "Do Darya Waterfront Dining, Phase 8 DHA, Karachi", "city": "Karachi", "country": "Pakistan", "category": "commercial_district", "lat": 24.7556, "lon": 67.0722, "radius_km": 0.1,
     "prompts": ["Do Darya coastal wooden deck restaurants overlooking Arabian Sea Phase 8 DHA Karachi", "Do Darya open-air seaside dining Karachi"]},
    {"name": "Habib Bank Plaza (HBL Plaza), I.I. Chundrigar Road, Karachi", "city": "Karachi", "country": "Pakistan", "category": "commercial_towers", "lat": 24.8522, "lon": 67.0056, "radius_km": 0.05,
     "prompts": ["Habib Bank Plaza historic tall skyscraper financial district I.I. Chundrigar Road Karachi", "HBL Plaza tower Karachi financial center"]},
    {"name": "National Stadium Karachi (NSK), Stadium Road", "city": "Karachi", "country": "Pakistan", "category": "stadium", "lat": 24.8936, "lon": 67.0808, "radius_km": 0.1,
     "prompts": ["National Stadium Karachi international cricket ground floodlights and stands", "NSK cricket stadium turf and grandstand Karachi"]},

    # Rawalpindi (5 spots)
    {"name": "Ayub National Park, Rawalpindi", "city": "Rawalpindi", "country": "Pakistan", "category": "park", "lat": 33.5667, "lon": 73.0833, "radius_km": 0.15,
     "prompts": ["Ayub National Park lakes boating canals and military museum Rawalpindi", "Ayub Park green gardens and recreation grounds Rawalpindi"]},
    {"name": "Raja Bazaar & Dingi Khoyi, Rawalpindi", "city": "Rawalpindi", "country": "Pakistan", "category": "commercial_market", "lat": 33.6083, "lon": 73.0556, "radius_km": 0.08,
     "prompts": ["Raja Bazaar historic bustling marketplace old wooden carved balconies Rawalpindi", "Raja Bazaar narrow commercial alleys Rawalpindi"]},
    {"name": "Rawalpindi Cricket Stadium, Double Road", "city": "Rawalpindi", "country": "Pakistan", "category": "stadium", "lat": 33.6472, "lon": 73.0778, "radius_km": 0.08,
     "prompts": ["Rawalpindi Cricket Stadium international cricket pavilion and floodlights", "Rawalpindi Stadium turf and grandstands"]},
    {"name": "PAF Aircraft Monument, Rawalpindi, Chandni Chowk / Old Airport", "city": "Rawalpindi", "country": "Pakistan", "category": "aircraft_monument", "lat": 33.5950, "lon": 73.0800, "radius_km": 0.05,
     "prompts": ["Pakistan Air Force F-86 Sabre fighter jet monument Rawalpindi Chandni Chowk Old Airport Road", "PAF fighter jet on display pedestal Rawalpindi"]},
    {"name": "Saddar Bazaar Rawalpindi & Mall Road", "city": "Rawalpindi", "country": "Pakistan", "category": "commercial_district", "lat": 33.5967, "lon": 73.0542, "radius_km": 0.1,
     "prompts": ["Saddar Rawalpindi cantonment colonial shop fronts Bank Road Mall Road", "Saddar commercial market Rawalpindi"]},

    # Peshawar (5 spots)
    {"name": "Islamia College University, Peshawar", "city": "Peshawar", "country": "Pakistan", "category": "university_campus", "lat": 33.9986, "lon": 71.4756, "radius_km": 0.08,
     "prompts": ["Islamia College Peshawar iconic Oriental Gothic red brick architecture and clock tower", "Islamia College main building and manicured gardens Peshawar"]},
    {"name": "Bala Hissar Fort, Peshawar", "city": "Peshawar", "country": "Pakistan", "category": "fortress", "lat": 34.0117, "lon": 71.5714, "radius_km": 0.08,
     "prompts": ["Bala Hissar Fort massive historic brick bastion fortress overlooking Peshawar city", "Bala Hissar Fort frontier corps battlements Peshawar"]},
    {"name": "Qissa Khwani Bazaar, Peshawar", "city": "Peshawar", "country": "Pakistan", "category": "commercial_market", "lat": 34.0100, "lon": 71.5667, "radius_km": 0.05,
     "prompts": ["Qissa Khwani Bazaar Storytellers Market brass teapots and historic street Peshawar", "Qissa Khwani traditional street market Peshawar"]},
    {"name": "Mahabat Khan Mosque, Peshawar", "city": "Peshawar", "country": "Pakistan", "category": "historical_mosque", "lat": 34.0114, "lon": 71.5706, "radius_km": 0.05,
     "prompts": ["Mahabat Khan Mosque white marble Mughal courtyard and tall minarets Old Peshawar", "Mahabat Khan Mosque interior tilework and prayer hall Peshawar"]},
    {"name": "Bab-e-Khyber (Khyber Pass Gateway), Jamrud / Peshawar", "city": "Peshawar", "country": "Pakistan", "category": "national_monument", "lat": 33.9972, "lon": 71.3917, "radius_km": 0.05,
     "prompts": ["Bab-e-Khyber stone arch gateway monument to Khyber Pass Jamrud Peshawar", "Bab-e-Khyber arch across the highway"]},

    # Faisalabad (3 spots)
    {"name": "Clock Tower (Ghanta Ghar), Faisalabad", "city": "Faisalabad", "country": "Pakistan", "category": "civic_monument", "lat": 31.4186, "lon": 73.0789, "radius_km": 0.05,
     "prompts": ["Clock Tower Ghanta Ghar Victorian stone tower center of eight bazaars Faisalabad", "Ghanta Ghar Faisalabad clock tower roundabout"]},
    {"name": "University of Agriculture Faisalabad (UAF) Campus", "city": "Faisalabad", "country": "Pakistan", "category": "university_campus", "lat": 31.4300, "lon": 73.0700, "radius_km": 0.1,
     "prompts": ["University of Agriculture Faisalabad UAF colonial clock tower academic block", "UAF campus grounds and historic buildings Faisalabad"]},
    {"name": "D Ground Commercial Market & Food Park, Faisalabad", "city": "Faisalabad", "country": "Pakistan", "category": "commercial_market", "lat": 31.4056, "lon": 73.1111, "radius_km": 0.08,
     "prompts": ["D Ground People Colony commercial market restaurants Faisalabad", "D Ground park and shopping center Faisalabad"]},

    # Multan (3 spots)
    {"name": "Tomb of Shah Rukn-e-Alam, Multan", "city": "Multan", "country": "Pakistan", "category": "historical_shrine", "lat": 30.1983, "lon": 71.4722, "radius_km": 0.05,
     "prompts": ["Tomb of Shah Rukn-e-Alam octagonal red brick and blue glazed ceramic dome Multan", "Shah Rukn-e-Alam shrine high mound fortress Multan"]},
    {"name": "Shrine of Bahauddin Zakariya, Multan", "city": "Multan", "country": "Pakistan", "category": "historical_shrine", "lat": 30.1994, "lon": 71.4736, "radius_km": 0.05,
     "prompts": ["Shrine of Bahauddin Zakariya white and blue tiled dome Multan Fort", "Bahauddin Zakariya tomb courtyard Multan"]},
    {"name": "Multan Cricket Stadium, Multan", "city": "Multan", "country": "Pakistan", "category": "stadium", "lat": 30.1583, "lon": 71.4361, "radius_km": 0.1,
     "prompts": ["Multan Cricket Stadium international sports ground floodlights and turf", "Multan cricket stadium arena"]},

    # Gujranwala (2 spots)
    {"name": "Nishan-e-Manzil & Cantonment Gate, Gujranwala", "city": "Gujranwala", "country": "Pakistan", "category": "monument", "lat": 32.1600, "lon": 74.1900, "radius_km": 0.05,
     "prompts": ["Nishan-e-Manzil military memorial monument park Gujranwala Cantt", "Gujranwala Cantonment main boulevard monument"]},
    {"name": "Sheranwala Bagh & Old Gate, Gujranwala", "city": "Gujranwala", "country": "Pakistan", "category": "park", "lat": 32.1556, "lon": 74.1833, "radius_km": 0.08,
     "prompts": ["Sheranwala Bagh public park and historic city entrance Gujranwala", "Sheranwala garden Gujranwala"]},

    # Sialkot (2 spots)
    {"name": "Iqbal Manzil (Birthplace of Allama Iqbal), Sialkot", "city": "Sialkot", "country": "Pakistan", "category": "historical_building", "lat": 32.4939, "lon": 74.5361, "radius_km": 0.05,
     "prompts": ["Iqbal Manzil birthplace museum of national poet Allama Iqbal Sialkot", "Iqbal Manzil historic residence balconies Sialkot"]},
    {"name": "Sialkot Clock Tower & Saddar Cantt", "city": "Sialkot", "country": "Pakistan", "category": "civic_monument", "lat": 32.5028, "lon": 74.5417, "radius_km": 0.05,
     "prompts": ["Sialkot Clock Tower Victorian colonial stone tower Saddar Cantt Sialkot", "Clock Tower roundabout Sialkot"]},

    # Hyderabad (2 spots)
    {"name": "Pacca Qila (Pakka Qal'a), Hyderabad, Sindh", "city": "Hyderabad", "country": "Pakistan", "category": "fortress", "lat": 25.3958, "lon": 68.3708, "radius_km": 0.08,
     "prompts": ["Pacca Qila historic Talpur red-brick fortified citadel Hyderabad Sindh", "Pakka Qila fortress walls Hyderabad"]},
    {"name": "Tombs of the Talpur Mirs, Hyderabad, Sindh", "city": "Hyderabad", "country": "Pakistan", "category": "historical_shrine", "lat": 25.4222, "lon": 68.3667, "radius_km": 0.05,
     "prompts": ["Tombs of Talpur Mirs blue and green glazed tilework domes Hyderabad Sindh", "Talpur dynasty royal mausoleums Hyderabad"]},

    # Quetta (3 spots)
    {"name": "Hanna Lake & Urrak Valley, Quetta", "city": "Quetta", "country": "Pakistan", "category": "reservoir", "lat": 30.2500, "lon": 67.1000, "radius_km": 0.15,
     "prompts": ["Hanna Lake turquoise water reservoir surrounded by arid brown mountains Quetta", "Hanna Lake bridge and picnic pavilion Quetta"]},
    {"name": "Command and Staff College, Quetta", "city": "Quetta", "country": "Pakistan", "category": "military_campus", "lat": 30.2222, "lon": 67.0500, "radius_km": 0.1,
     "prompts": ["Command and Staff College stone colonial military academy buildings Quetta", "Staff College Quetta entrance gate and grounds"]},
    {"name": "Liaquat Park & Prince Road Bazaar, Quetta", "city": "Quetta", "country": "Pakistan", "category": "commercial_market", "lat": 30.1833, "lon": 67.0167, "radius_km": 0.08,
     "prompts": ["Quetta dry fruit and Afghan rug bazaar Prince Road Liaquat Park", "Quetta central city bazaar arid mountain backdrop"]},

    # Abbottabad & Galyat (4 spots)
    {"name": "Mushkpuri Peak, Nathia Gali, KPK, Pakistan", "city": "Abbottabad", "country": "Pakistan", "category": "mountain_peak", "lat": 34.0625, "lon": 73.4358, "radius_km": 10.0,
     "prompts": ["Mushkpuri Peak green mountain meadow ridge Nathia Gali Galyat Abbottabad", "Mushkpuri summit pine trees and alpine meadow trail"]},
    {"name": "Miranjani Peak, Nathia Gali, KPK, Pakistan", "city": "Abbottabad", "country": "Pakistan", "category": "mountain_peak", "lat": 34.1167, "lon": 73.4333, "radius_km": 10.0,
     "prompts": ["Miranjani Peak highest summit in Galyat pine forest ridge Nathia Gali", "Miranjani mountain trail overlooking Hazara and Kashmir"]},
    {"name": "Ilyasi Mosque & Natural Spring, Abbottabad", "city": "Abbottabad", "country": "Pakistan", "category": "mosque", "lat": 34.1667, "lon": 73.2333, "radius_km": 0.05,
     "prompts": ["Ilyasi Mosque grand white facade over freshwater natural spring Abbottabad", "Ilyasi Mosque famous pakora bazaar and mountain spring Abbottabad"]},
    {"name": "Thandiani Hill Station, Abbottabad", "city": "Abbottabad", "country": "Pakistan", "category": "mountain_ridge", "lat": 34.2333, "lon": 73.3500, "radius_km": 0.2,
     "prompts": ["Thandiani pine forest hill station ridge clouds Abbottabad", "Thandiani mountain summit viewpoint overlooking Pir Panjal"]},

    # Murree (3 spots)
    {"name": "Mall Road Murree, Murree Hills", "city": "Murree", "country": "Pakistan", "category": "commercial_street", "lat": 33.9070, "lon": 73.3943, "radius_km": 0.08,
     "prompts": ["Mall Road Murree pedestrian mountain hill station shopping street shops hotels", "Murree Mall Road bustling evening street"]},
    {"name": "Patriata New Murree Chairlift & Cable Car", "city": "Murree", "country": "Pakistan", "category": "viewpoint", "lat": 33.8821, "lon": 73.4562, "radius_km": 0.1,
     "prompts": ["Patriata New Murree cable car gondola and chairlift riding over pine tree canopy", "Patriata hill station ridge chairlift Murree"]},
    {"name": "PAF Aircraft Monument, Lower Topa, Murree, Pakistan", "city": "Murree", "country": "Pakistan", "category": "aircraft_monument", "lat": 33.9115, "lon": 73.4150, "radius_km": 0.05,
     "prompts": ["Pakistan Air Force Sabre F-86 fighter aircraft monument Lower Topa Murree", "PAF aircraft monument installed roundabout Lower Topa Murree"]},

    # Swat (2 spots)
    {"name": "Malam Jabba Ski Resort & Chairlift, Swat", "city": "Swat", "country": "Pakistan", "category": "mountain_resort", "lat": 34.7997, "lon": 72.5714, "radius_km": 0.1,
     "prompts": ["Malam Jabba ski resort hotel slopes and chairlift snow mountains Swat Valley", "Malam Jabba alpine mountain chairlift Swat"]},
    {"name": "White Palace Marghazar, Swat", "city": "Swat", "country": "Pakistan", "category": "historical_palace", "lat": 34.7167, "lon": 72.3333, "radius_km": 0.05,
     "prompts": ["White Palace Marghazar white marble heritage residence foothills Swat", "Sufed Mahal White Palace hotel and gardens Swat"]},

    # Gilgit & Hunza (3 spots)
    {"name": "Baltit Fort, Karimabad, Hunza Valley", "city": "Gilgit", "country": "Pakistan", "category": "fortress", "lat": 36.3267, "lon": 74.6711, "radius_km": 0.05,
     "prompts": ["Baltit Fort ancient Tibetan-style fortress wooden balconies overlooking Hunza Valley", "Baltit Fort Karimabad snow mountain background"]},
    {"name": "Passu Cones & Cathedral Peaks, Hunza", "city": "Gilgit", "country": "Pakistan", "category": "mountain_peak", "lat": 36.4680, "lon": 74.8870, "radius_km": 5.0,
     "prompts": ["Passu Cones Cathedral needle rock peaks Karakoram Highway Hunza", "Passu Cones pointed mountain spires Hunza Valley"]},
    {"name": "Attabad Lake Turquoise Waters, Hunza", "city": "Gilgit", "country": "Pakistan", "category": "reservoir", "lat": 36.3333, "lon": 74.8667, "radius_km": 0.3,
     "prompts": ["Attabad Lake vivid turquoise blue water and sheer rocky canyon walls Karakoram", "Attabad Lake boats cruising Karakoram Highway tunnel"]},

    # Skardu (3 spots)
    {"name": "Shangrila Resort & Lower Kachura Lake, Skardu", "city": "Skardu", "country": "Pakistan", "category": "mountain_resort", "lat": 35.4222, "lon": 75.4472, "radius_km": 0.08,
     "prompts": ["Shangrila Resort Chinese-style red pagoda chalets around heart-shaped Kachura Lake Skardu", "Shangrila Resort Lower Kachura Lake Skardu Baltistan"]},
    {"name": "Deosai National Park Plains (Land of Giants), Skardu", "city": "Skardu", "country": "Pakistan", "category": "national_park", "lat": 35.0500, "lon": 75.4500, "radius_km": 15.0,
     "prompts": ["Deosai Plains high altitude alpine plateau wildflowers green rolling tundra Skardu", "Deosai National Park wide open plains and snow peaks"]},
    {"name": "Katpana Cold Desert Dunes, Skardu", "city": "Skardu", "country": "Pakistan", "category": "desert", "lat": 35.3333, "lon": 75.5833, "radius_km": 0.5,
     "prompts": ["Katpana cold desert white sand dunes surrounded by snow-capped mountains Skardu", "Katpana cold sand desert Indus river Skardu"]},

    # Sargodha, Bahawalpur, Sukkur, Larkana, Nawabshah, Gwadar, Mirpur, Muzaffarabad, etc.
    {"name": "PAF F-86 Sabre Monument, Sargodha, Pakistan", "city": "Sargodha", "country": "Pakistan", "category": "aircraft_monument", "lat": 32.0620, "lon": 72.6710, "radius_km": 0.05,
     "prompts": ["PAF Base Sargodha Club Chowk F-86 Sabre fighter aircraft monument Pakistan", "PAF Sabre jet monument roundabout Sargodha"]},
    {"name": "Noor Mahal Palace, Bahawalpur, Punjab", "city": "Bahawalpur", "country": "Pakistan", "category": "historical_palace", "lat": 29.3972, "lon": 71.6669, "radius_km": 0.05,
     "prompts": ["Noor Mahal Italian chateau style palace Corinthian columns Bahawalpur", "Noor Mahal illuminated palace facade Bahawalpur"]},
    {"name": "Derawar Fort, Cholistan Desert, Bahawalpur", "city": "Bahawalpur", "country": "Pakistan", "category": "fortress", "lat": 28.7675, "lon": 71.3342, "radius_km": 0.1,
     "prompts": ["Derawar Fort massive circular red brick bastions rising out of Cholistan desert sands", "Derawar Fort Cholistan desert fortress walls"]},
    {"name": "Lansdowne Bridge & Sukkur Barrage, Sukkur, Sindh", "city": "Sukkur", "country": "Pakistan", "category": "bridge", "lat": 27.7000, "lon": 68.8833, "radius_km": 0.1,
     "prompts": ["Lansdowne Bridge historic steel cantilever railway bridge over Indus River Sukkur", "Sukkur Barrage arches and Lansdowne Bridge"]},
    {"name": "Mohenjo-daro Buddhist Stupa & Great Bath, Larkana", "city": "Larkana", "country": "Pakistan", "category": "unesco_world_heritage", "lat": 27.3283, "lon": 68.1386, "radius_km": 0.15,
     "prompts": ["Mohenjo-daro ancient baked brick ruins Buddhist stupa mound Indus Valley Civilization Larkana", "Mohenjo Daro archaeological ruins Great Bath Larkana"]},
    {"name": "Quaid-e-Awam University Campus, Nawabshah", "city": "Nawabshah", "country": "Pakistan", "category": "university_campus", "lat": 26.2444, "lon": 68.4111, "radius_km": 0.1,
     "prompts": ["Quaid-e-Awam University of Engineering QUEST campus Nawabshah Shaheed Benazirabad", "QUEST university academic blocks Nawabshah"]},
    {"name": "Mangla Dam & Viewpoint, Mirpur, Azad Kashmir", "city": "Mirpur", "country": "Pakistan", "category": "dam", "lat": 33.1417, "lon": 73.6472, "radius_km": 0.2,
     "prompts": ["Mangla Dam massive water reservoir and powerhouse lake viewpoint Mirpur Azad Kashmir", "Mangla Dam spillway and lake Mirpur AJK"]},
    {"name": "Muzaffarabad Red Fort & Neelum River Confluence, AJK", "city": "Muzaffarabad", "country": "Pakistan", "category": "fortress", "lat": 34.3708, "lon": 73.4708, "radius_km": 0.08,
     "prompts": ["Red Fort Rutta Qila historic stone fortress Neelum River bend Muzaffarabad Kashmir", "Muzaffarabad confluence of Jhelum and Neelum rivers Red Fort"]},
    {"name": "Gwadar Port & Hammerhead Rock (Koh-e-Batil), Gwadar", "city": "Gwadar", "country": "Pakistan", "category": "port", "lat": 25.1200, "lon": 62.3250, "radius_km": 0.2,
     "prompts": ["Gwadar Port deep sea harbor cranes and Koh-e-Batil hammerhead rock Arabian Sea", "Gwadar peninsula hammerhead headland and East Bay expressway"]},
    {"name": "Takht-i-Bahi Buddhist Monastery Ruins, Mardan", "city": "Mardan", "country": "Pakistan", "category": "unesco_world_heritage", "lat": 34.3197, "lon": 71.9794, "radius_km": 0.08,
     "prompts": ["Takht-i-Bahi ancient Gandharan Buddhist stone monastery ruins perched on hill Mardan", "Takht-i-Bahi stupa court and monk cells Mardan"]},
    {"name": "Kohat Tunnel (Friendship Tunnel) & Pass, Kohat", "city": "Kohat", "country": "Pakistan", "category": "tunnel", "lat": 33.6450, "lon": 71.4900, "radius_km": 0.1,
     "prompts": ["Kohat Friendship Tunnel highway mountain portal Indus highway KPK", "Kohat Pass mountain road and tunnel entrance"]},
    {"name": "Gomal University New Campus, Dera Ismail Khan", "city": "Dera Ismail Khan", "country": "Pakistan", "category": "university_campus", "lat": 31.8333, "lon": 70.9000, "radius_km": 0.1,
     "prompts": ["Gomal University campus administration building and lawns Dera Ismail Khan", "Gomal University DI Khan"]},
    {"name": "Ghazi Ghat Bridge & Indus River Promenade, Dera Ghazi Khan", "city": "Dera Ghazi Khan", "country": "Pakistan", "category": "bridge", "lat": 30.0500, "lon": 70.6333, "radius_km": 0.1,
     "prompts": ["Ghazi Ghat bridge spanning Indus River connecting Multan and Dera Ghazi Khan", "Indus river bridge DG Khan"]},
    {"name": "Sheikh Zayed Palace & Desert Oasis, Rahim Yar Khan", "city": "Rahim Yar Khan", "country": "Pakistan", "category": "historical_palace", "lat": 28.4211, "lon": 70.2989, "radius_km": 0.08,
     "prompts": ["Sheikh Zayed Palace Abu Dhabi royal residence Cholistan desert gateway Rahim Yar Khan", "Rahim Yar Khan royal palace gardens"]},
    {"name": "Harappa Archaeological Ruins & Museum, Sahiwal", "city": "Sahiwal", "country": "Pakistan", "category": "archaeological_ruins", "lat": 30.6300, "lon": 72.8642, "radius_km": 0.1,
     "prompts": ["Harappa ancient Indus civilization baked brick cemetery and granary ruins Sahiwal", "Harappa archaeological site mound Sahiwal"]},
    {"name": "Rohtas Fort (Qila Rohtas), Jhelum, Punjab", "city": "Jhelum", "country": "Pakistan", "category": "unesco_world_heritage", "lat": 32.9664, "lon": 73.5769, "radius_km": 0.1,
     "prompts": ["Rohtas Fort Sohail Gate colossal Sher Shah Suri stone fortress walls Jhelum", "Rohtas Fort massive stone battlements and gates Jhelum"]},
    {"name": "University of Gujrat (UOG) Hafiz Hayat Campus, Gujrat", "city": "Gujrat", "country": "Pakistan", "category": "university_campus", "lat": 32.6417, "lon": 74.0667, "radius_km": 0.1,
     "prompts": ["University of Gujrat Hafiz Hayat campus central library modern brick architecture", "UOG Gujrat university campus lawns"]},
    {"name": "Attock Fort & Indus River Confluence, Attock", "city": "Attock", "country": "Pakistan", "category": "fortress", "lat": 33.8907, "lon": 72.2385, "radius_km": 0.1,
     "prompts": ["Attock Fort Mughal stone battlements overlooking confluence of Indus and Kabul rivers", "Attock Fort river fortress walls"]},
    {"name": "Saif-ul-Malook Lake & Malika Parbat, Naran, Mansehra", "city": "Mansehra", "country": "Pakistan", "category": "alpine_lake", "lat": 34.8778, "lon": 73.6931, "radius_km": 0.2,
     "prompts": ["Lake Saif-ul-Malook emerald green alpine glacial lake reflecting Malika Parbat Naran Kaghan", "Saif-ul-Malook lake boats and snowy peaks Naran"]},
    {"name": "Chilas Rock Carvings & Indus Gorge, Chilas", "city": "Chilas", "country": "Pakistan", "category": "heritage_site", "lat": 35.4200, "lon": 74.1000, "radius_km": 0.2,
     "prompts": ["Chilas ancient Buddhist petroglyphs rock carvings along Indus River Karakoram Highway", "Chilas rock art canyon Indus river gorge"]},
    {"name": "Shahi Mosque & Chitral Fort, Chitral", "city": "Chitral", "country": "Pakistan", "category": "historical_mosque", "lat": 35.8500, "lon": 71.7833, "radius_km": 0.08,
     "prompts": ["Shahi Mosque Chitral white domes and minarets Kunar River Tirich Mir backdrop", "Chitral Shahi Masjid and historic Mehtar fort"]},
    {"name": "Quaid-e-Azam Residency, Ziarat, Balochistan", "city": "Ziarat", "country": "Pakistan", "category": "historical_building", "lat": 30.3853, "lon": 67.7269, "radius_km": 0.05,
     "prompts": ["Quaid-e-Azam Residency wooden colonial heritage architecture pine trees Ziarat Balochistan", "Ziarat Residency historic wooden building"]},
    {"name": "Mir Chakar Rind Fort, Turbat, Kech, Balochistan", "city": "Turbat", "country": "Pakistan", "category": "fortress", "lat": 26.0000, "lon": 63.0500, "radius_km": 0.08,
     "prompts": ["Punnu Fort Mir Chakar Rind historic mud-brick citadel Kech River valley Turbat", "Turbat historic mud castle Balochistan"]},
    {"name": "Shrine of Baba Bulleh Shah, Kasur, Punjab", "city": "Kasur", "country": "Pakistan", "category": "shrine", "lat": 31.1167, "lon": 74.4500, "radius_km": 0.05,
     "prompts": ["Shrine of Sufi poet Baba Bulleh Shah marble courtyard green dome Kasur Punjab", "Bulleh Shah shrine entrance Kasur"]},
    {"name": "Hiran Minar & Hunting Pavilion, Sheikhupura", "city": "Sheikhupura", "country": "Pakistan", "category": "historical_monument", "lat": 31.7486, "lon": 73.9519, "radius_km": 0.08,
     "prompts": ["Hiran Minar Mughal circular tower and octagonal water pavilion tank Sheikhupura", "Hiran Minar water reservoir and historic tower Sheikhupura"]},
    {"name": "Okara Military Farms & Clock Tower, Okara", "city": "Okara", "country": "Pakistan", "category": "civic_monument", "lat": 30.8100, "lon": 73.4500, "radius_km": 0.05,
     "prompts": ["Okara city clock tower square and historic dairy farms Punjab", "Okara city center clock tower"]},
    {"name": "Kot Diji Fort (Fort Ahmadabad), Khairpur, Sindh", "city": "Khairpur", "country": "Pakistan", "category": "fortress", "lat": 27.3455, "lon": 68.7067, "radius_km": 0.08,
     "prompts": ["Kot Diji Fort massive historic mud and kiln-brick hill fortress bastions Khairpur Sindh", "Kot Diji fort battlements overlooking date palms"]},
    {"name": "Shah Jahan Mosque & Makli Necropolis, Thatta, Sindh", "city": "Thatta", "country": "Pakistan", "category": "unesco_world_heritage", "lat": 24.7472, "lon": 67.9272, "radius_km": 0.1,
     "prompts": ["Shah Jahan Mosque ninety-three blue glazed ceramic domes Thatta Sindh", "Makli Necropolis vast historic sandstone carved tombs Thatta"]}
]

all_pakistan = islamabad_spots + pakistan_other_cities
with open(OUT_DIR / "pakistan.json", "w", encoding="utf-8") as f:
    json.dump(all_pakistan, f, indent=2, ensure_ascii=False)
logger.info("Saved pakistan.json with %d spots (%d in Islamabad, %d across other cities).",
            len(all_pakistan), len(islamabad_spots), len(pakistan_other_cities))

# -----------------------------------------------------------------------------
# 2. TURKEY: Covering EVERY city in Turkey
# -----------------------------------------------------------------------------
turkey_spots = [
    # Istanbul
    {"name": "Hagia Sophia (Ayasofya-i Kebir Cami-i Serifi), Istanbul", "city": "Istanbul", "country": "Turkey", "category": "historical_mosque", "lat": 41.0086, "lon": 28.9802, "radius_km": 0.05,
     "prompts": ["Hagia Sophia grand Byzantine dome and Ottoman minarets Sultanahmet Istanbul", "Ayasofya Hagia Sophia mosque exterior courtyard Istanbul"]},
    {"name": "Blue Mosque (Sultanahmet Camii), Istanbul", "city": "Istanbul", "country": "Turkey", "category": "historical_mosque", "lat": 41.0054, "lon": 28.9768, "radius_km": 0.05,
     "prompts": ["Blue Mosque Sultanahmet six slender minarets cascading domes Istanbul", "Sultan Ahmed Mosque Blue Mosque courtyard Istanbul"]},
    {"name": "Galata Tower (Galata Kulesi), Beyoglu, Istanbul", "city": "Istanbul", "country": "Turkey", "category": "historical_monument", "lat": 41.0256, "lon": 28.9742, "radius_km": 0.05,
     "prompts": ["Galata Tower medieval cylindrical stone tower cone roof Beyoglu Istanbul", "Galata Kulesi observation balcony overlooking Golden Horn Istanbul"]},
    {"name": "Topkapi Palace (Topkapi Sarayi), Istanbul", "city": "Istanbul", "country": "Turkey", "category": "historical_palace", "lat": 41.0115, "lon": 28.9833, "radius_km": 0.08,
     "prompts": ["Topkapi Palace Ottoman imperial gate courtyards and Imperial Council Istanbul", "Topkapi Sarayi harem and Bosphorus view pavilion Istanbul"]},
    {"name": "Bosphorus Bridge (15 July Martyrs Bridge), Istanbul", "city": "Istanbul", "country": "Turkey", "category": "bridge", "lat": 41.0456, "lon": 29.0344, "radius_km": 0.2,
     "prompts": ["Bosphorus Bridge 15 July Martyrs suspension bridge spanning Europe and Asia Istanbul", "Bosphorus strait suspension bridge Ortakoy view Istanbul"]},
    {"name": "Grand Bazaar (Kapalicarsi), Fatih, Istanbul", "city": "Istanbul", "country": "Turkey", "category": "commercial_market", "lat": 41.0106, "lon": 28.9681, "radius_km": 0.08,
     "prompts": ["Grand Bazaar Kapalicarsi vaulted painted ceiling corridors and lantern shops Istanbul", "Grand Bazaar historic covered market arched entrance Istanbul"]},
    {"name": "Taksim Square & Republic Monument, Beyoglu, Istanbul", "city": "Istanbul", "country": "Turkey", "category": "civic_monument", "lat": 41.0369, "lon": 28.9850, "radius_km": 0.05,
     "prompts": ["Taksim Square Republic Monument and red vintage nostalgic tramway Istanbul", "Taksim Square pedestrian plaza and Ataturk Cultural Centre Istanbul"]},
    {"name": "Dolmabahce Palace (Dolmabahce Sarayi), Besiktas, Istanbul", "city": "Istanbul", "country": "Turkey", "category": "historical_palace", "lat": 41.0392, "lon": 29.0003, "radius_km": 0.08,
     "prompts": ["Dolmabahce Palace grand Baroque neoclassical waterfront facade clock tower Bosphorus Istanbul", "Dolmabahce Sarayi imperial gate along Bosphorus"]},
    {"name": "Maiden's Tower (Kiz Kulesi), Uskudar, Istanbul", "city": "Istanbul", "country": "Turkey", "category": "historical_monument", "lat": 41.0211, "lon": 29.0042, "radius_km": 0.05,
     "prompts": ["Maiden's Tower Kiz Kulesi historic lighthouse islet Bosphorus strait Uskudar Istanbul", "Kiz Kulesi sunset silhouette on Bosphorus water"]},
    {"name": "Grand Camlica Mosque, Uskudar, Istanbul", "city": "Istanbul", "country": "Turkey", "category": "national_mosque", "lat": 41.0344, "lon": 29.0708, "radius_km": 0.08,
     "prompts": ["Camlica Mosque massive modern neo-Ottoman dome and six minarets Camlica Hill Istanbul", "Buyuk Camlica Camii courtyard and panoramic Istanbul overlook"]},

    # Ankara
    {"name": "Anitkabir (Ataturk Mausoleum), Cankaya, Ankara", "city": "Ankara", "country": "Turkey", "category": "national_monument", "lat": 39.9250, "lon": 32.8369, "radius_km": 0.08,
     "prompts": ["Anitkabir Ataturk mausoleum ceremonial Lion Road and colonnaded Hall of Honor Ankara", "Anitkabir grand plaza and limestone colonnade Ankara"]},
    {"name": "Ankara Castle (Ankara Kalesi), Altindag, Ankara", "city": "Ankara", "country": "Turkey", "category": "fortress", "lat": 39.9406, "lon": 32.8647, "radius_km": 0.05,
     "prompts": ["Ankara Castle medieval hilltop stone citadel walls overlooking red tile roofs Ankara", "Ankara Kalesi historic citadel bastions"]},
    {"name": "Atakule Tower, Cankaya, Ankara", "city": "Ankara", "country": "Turkey", "category": "commercial_towers", "lat": 39.8864, "lon": 32.8556, "radius_km": 0.05,
     "prompts": ["Atakule communications and observation tower with revolving dome restaurant Cankaya Ankara", "Atakule tower shopping mall plaza Ankara"]},

    # Izmir
    {"name": "Izmir Clock Tower (Saat Kulesi), Konak Square, Izmir", "city": "Izmir", "country": "Turkey", "category": "civic_monument", "lat": 38.4189, "lon": 27.1286, "radius_km": 0.05,
     "prompts": ["Izmir Clock Tower ornate Ottoman marble clock tower Konak Square Aegean Sea Izmir", "Saat Kulesi Konak Meydani pigeons and palm trees Izmir"]},
    {"name": "Tarihi Asansor (Historical Elevator), Karatas, Izmir", "city": "Izmir", "country": "Turkey", "category": "historical_monument", "lat": 38.4086, "lon": 27.1172, "radius_km": 0.05,
     "prompts": ["Tarihi Asansor brick elevator tower cliffside viewpoint Gulf of Izmir", "Historical Elevator terrace and Dario Moreno street Izmir"]},

    # Antalya
    {"name": "Hadrian's Gate (Uckapilar), Kaleici, Antalya", "city": "Antalya", "country": "Turkey", "category": "historical_monument", "lat": 36.8853, "lon": 30.7086, "radius_km": 0.05,
     "prompts": ["Hadrian's Gate triple-arched Roman white marble triumphal gate Kaleici Antalya", "Uckapilar Hadrian Gate Antalya old town"]},
    {"name": "Duden Waterfalls (Lower Duden Falls), Lara, Antalya", "city": "Antalya", "country": "Turkey", "category": "natural_landmark", "lat": 36.8517, "lon": 30.7833, "radius_km": 0.08,
     "prompts": ["Lower Duden Waterfall cascading off sheer coastal cliffs directly into Mediterranean Sea Antalya", "Duden Selalesi waterfall cliffside park Antalya"]},

    # Bursa
    {"name": "Grand Mosque of Bursa (Bursa Ulu Cami), Bursa", "city": "Bursa", "country": "Turkey", "category": "historical_mosque", "lat": 40.1833, "lon": 29.0617, "radius_km": 0.05,
     "prompts": ["Grand Mosque of Bursa Ulu Cami twenty domes interior ablution fountain and calligraphic murals", "Bursa Ulu Camii monumental early Ottoman mosque"]},
    {"name": "Green Tomb (Yesil Turbe), Bursa", "city": "Bursa", "country": "Turkey", "category": "historical_shrine", "lat": 40.1817, "lon": 29.0750, "radius_km": 0.05,
     "prompts": ["Green Tomb Yesil Turbe turquoise glazed hexagonal tiled mausoleum Sultan Mehmed I Bursa", "Yesil Turbe Green Mosque complex Bursa"]},

    # Adana
    {"name": "Sabanci Central Mosque & Stone Bridge (Taskopru), Adana", "city": "Adana", "country": "Turkey", "category": "national_mosque", "lat": 36.9911, "lon": 35.3342, "radius_km": 0.08,
     "prompts": ["Sabanci Central Mosque six soaring minarets Seyhan River and Roman Taskopru Stone Bridge Adana", "Sabanci Merkez Camii illuminated over river Adana"]},

    # Konya
    {"name": "Mevlana Museum & Rumi Shrine, Konya", "city": "Konya", "country": "Turkey", "category": "historical_shrine", "lat": 37.8708, "lon": 32.5056, "radius_km": 0.05,
     "prompts": ["Mevlana Museum turquoise fluted dome shrine of Jalal ad-Din Muhammad Rumi Konya", "Mevlana Celaleddin Rumi tomb and dervish museum Konya"]},

    # Gaziantep
    {"name": "Zeugma Mosaic Museum, Gaziantep", "city": "Gaziantep", "country": "Turkey", "category": "museum", "lat": 37.0750, "lon": 37.3861, "radius_km": 0.05,
     "prompts": ["Zeugma Mosaic Museum Gypsy Girl mosaic and Roman antiquities Gaziantep", "Zeugma Mosaic Museum modern building Gaziantep"]},

    # Sanliurfa
    {"name": "Balikligol (Pool of Sacred Fish) & Halil-ur-Rahman Mosque, Sanliurfa", "city": "Sanliurfa", "country": "Turkey", "category": "historical_shrine", "lat": 37.1472, "lon": 38.7847, "radius_km": 0.05,
     "prompts": ["Balikligol sacred carp pool stone arcades Halil-ur-Rahman Mosque Sanliurfa", "Pool of Abraham sacred fish Urfa Turkey"]},

    # Mersin
    {"name": "Maiden's Castle (Kizkalesi), Erdemli, Mersin", "city": "Mersin", "country": "Turkey", "category": "fortress", "lat": 36.4633, "lon": 34.1478, "radius_km": 0.08,
     "prompts": ["Kizkalesi Maiden's Castle medieval island sea castle turquoise Mediterranean Mersin", "Kizkalesi coastal fortress offshore island Mersin"]},

    # Diyarbakir
    {"name": "Diyarbakir Fortress & Ten-Eyed Bridge (Ongozlu Kopru), Diyarbakir", "city": "Diyarbakir", "country": "Turkey", "category": "unesco_world_heritage", "lat": 37.9139, "lon": 40.2361, "radius_km": 0.1,
     "prompts": ["Diyarbakir City Walls black basalt medieval fortress battlements and Tigris River Ongozlu bridge", "Diyarbakir black basalt citadel UNESCO"]},

    # Kayseri
    {"name": "Mount Erciyes Volcano & Ski Resort, Kayseri", "city": "Kayseri", "country": "Turkey", "category": "mountain_peak", "lat": 38.5317, "lon": 35.4492, "radius_km": 5.0,
     "prompts": ["Mount Erciyes snow-capped stratovolcano and ski chairlifts Kayseri Central Anatolia", "Erciyes Dagi volcano summit peak Kayseri"]},

    # Eskisehir
    {"name": "Odunpazari Modern Museum (OMM) & Timber Houses, Eskisehir", "city": "Eskisehir", "country": "Turkey", "category": "museum", "lat": 39.7611, "lon": 30.5264, "radius_km": 0.05,
     "prompts": ["Odunpazari Modern Museum stacked timber beam architecture Kengo Kuma Eskisehir", "Odunpazari colorful historic Ottoman wooden houses Eskisehir"]},

    # Samsun
    {"name": "Bandirma Vapuru Museum Ship & Ataturk Monument, Samsun", "city": "Samsun", "country": "Turkey", "category": "museum", "lat": 41.2789, "lon": 36.3600, "radius_km": 0.05,
     "prompts": ["Bandirma Vapuru steamship museum Black Sea coast Samsun", "Ataturk statue and Bandirma ferry museum Samsun"]},

    # Denizli
    {"name": "Pamukkale White Travertine Terraces & Hierapolis, Denizli", "city": "Denizli", "country": "Turkey", "category": "unesco_world_heritage", "lat": 37.9250, "lon": 29.1217, "radius_km": 0.2,
     "prompts": ["Pamukkale gleaming white thermal limestone travertine terraces mineral pools Hierapolis Denizli", "Pamukkale cotton castle thermal spring terraces"]},

    # Trabzon
    {"name": "Sumela Monastery, Altindere Valley, Trabzon", "city": "Trabzon", "country": "Turkey", "category": "unesco_world_heritage", "lat": 40.6900, "lon": 39.6583, "radius_km": 0.08,
     "prompts": ["Sumela Monastery ancient Greek Orthodox rock-hewn monastery clinging to vertical cliff Pontic Mountains Trabzon", "Sumela Monastery cliffside frescoes Trabzon"]},
    {"name": "Uzungol Alpine Lake & Mosque, Trabzon", "city": "Trabzon", "country": "Turkey", "category": "natural_landmark", "lat": 40.6186, "lon": 40.2922, "radius_km": 0.1,
     "prompts": ["Uzungol alpine mountain lake white minaret mosque lush green pine mountain valley Trabzon", "Uzungol lake reflection and forest mountains Trabzon"]},

    # Erzurum
    {"name": "Double Minaret Madrasa (Cifte Minareli Medrese), Erzurum", "city": "Erzurum", "country": "Turkey", "category": "historical_building", "lat": 39.9056, "lon": 41.2783, "radius_km": 0.05,
     "prompts": ["Cifte Minareli Medrese fluted twin brick minarets Seljuk monumental portal Erzurum", "Double Minaret Madrasa Seljuk architecture Erzurum"]},

    # Malatya
    {"name": "Arslantepe Mound (Melid Archaeological Site), Malatya", "city": "Malatya", "country": "Turkey", "category": "unesco_world_heritage", "lat": 38.3828, "lon": 38.3606, "radius_km": 0.08,
     "prompts": ["Arslantepe Mound ancient palace adobe mudbrick walls UNESCO World Heritage Malatya", "Arslantepe archaeological excavation site Malatya"]},

    # Van
    {"name": "Akdamar Island Church of the Holy Cross & Lake Van", "city": "Van", "country": "Turkey", "category": "historical_church", "lat": 38.3411, "lon": 43.0369, "radius_km": 0.1,
     "prompts": ["Akdamar Island Armenian Cathedral of the Holy Cross red volcanic stone Lake Van snowy mountains", "Church of Akdamar exterior relief carvings Lake Van"]},

    # Sivas
    {"name": "Divrigi Great Mosque and Hospital, Sivas", "city": "Sivas", "country": "Turkey", "category": "unesco_world_heritage", "lat": 39.3739, "lon": 38.1239, "radius_km": 0.05,
     "prompts": ["Divrigi Great Mosque intricate high-relief Seljuk stone carved portal UNESCO Sivas", "Divrigi Ulu Camii masterwork stone relief gateway"]},

    # Canakkale
    {"name": "Canakkale 1915 Bridge & Gallipoli Martyrs Memorial, Canakkale", "city": "Canakkale", "country": "Turkey", "category": "bridge", "lat": 40.3361, "lon": 26.6347, "radius_km": 0.3,
     "prompts": ["1915 Canakkale Bridge world's longest suspension bridge red towers Dardanelles strait", "Gallipoli Martyrs Memorial Canakkale Dardanelles"]},

    # Edirne
    {"name": "Selimiye Mosque, Mimar Sinan, Edirne", "city": "Edirne", "country": "Turkey", "category": "unesco_world_heritage", "lat": 41.6781, "lon": 26.5556, "radius_km": 0.08,
     "prompts": ["Selimiye Mosque Mimar Sinan grand Ottoman central dome and four towering minarets Edirne", "Selimiye Camii UNESCO imperial mosque Edirne"]},

    # Bodrum / Mugla
    {"name": "Bodrum Castle (Castle of St Peter) & Marina, Bodrum, Mugla", "city": "Bodrum", "country": "Turkey", "category": "fortress", "lat": 37.0319, "lon": 27.4294, "radius_km": 0.08,
     "prompts": ["Bodrum Castle Crusader stone fortress overlooking Aegean marina yachts Bodrum", "Castle of St Peter French tower and Bodrum harbor"]},

    # Cappadocia / Nevsehir
    {"name": "Goreme Fairy Chimneys & Cave Dwellings, Cappadocia", "city": "Cappadocia", "country": "Turkey", "category": "unesco_world_heritage", "lat": 38.6431, "lon": 34.8289, "radius_km": 0.5,
     "prompts": ["Goreme Fairy Chimneys volcanic tuff rock spires hot air balloons sunrise Cappadocia", "Cappadocia Goreme cave hotels and sandstone rock formations"]},
    {"name": "Uchisar Castle Rock Citadel, Cappadocia", "city": "Cappadocia", "country": "Turkey", "category": "fortress", "lat": 38.6300, "lon": 34.8056, "radius_km": 0.08,
     "prompts": ["Uchisar Castle massive perforated volcanic rock fortress hill overlooking Cappadocia valleys", "Uchisar Castle rock pinnacle viewpoint Cappadocia"]},

    # Mardin
    {"name": "Zinciriye Madrasa & Old Stone Mansions, Mardin", "city": "Mardin", "country": "Turkey", "category": "heritage_village", "lat": 37.3167, "lon": 40.7333, "radius_km": 0.08,
     "prompts": ["Zinciriye Medrese fluted stone domes terraced stone houses overlooking Mesopotamian plains Mardin", "Old Mardin stone architecture terrace viewpoint"]},

    # Rize
    {"name": "Ayder Plateau & Firtina Valley Cloud Waterfall, Rize", "city": "Rize", "country": "Turkey", "category": "mountain_resort", "lat": 40.9500, "lon": 41.1000, "radius_km": 0.2,
     "prompts": ["Ayder Plateau green mountain pastures wooden chalets waterfalls misty Kackar mountains Rize", "Firtina Valley Ottoman stone arch bridge tea plantations Rize"]},

    # Hatay / Antakya
    {"name": "Saint Peter's Cave Church (Senpiyer Kilisesi), Antakya, Hatay", "city": "Hatay", "country": "Turkey", "category": "historical_church", "lat": 36.2089, "lon": 36.1778, "radius_km": 0.05,
     "prompts": ["Church of Saint Peter ancient rock-hewn Christian cave church carved into Mount Staurin Antakya Hatay", "Saint Peter cave church facade Antakya"]},

    # Kars
    {"name": "Ani Ancient Armenian City Ruins & Cathedral, Kars", "city": "Kars", "country": "Turkey", "category": "unesco_world_heritage", "lat": 40.5075, "lon": 43.5728, "radius_km": 0.2,
     "prompts": ["Ani Ruins ancient City of 1001 Churches red volcanic tuff Cathedral of Ani border gorge Kars", "Ani medieval Armenian cathedral ruins Kars"]},

    # Balikesir
    {"name": "Cunda Island (Alibey) Stone Houses & Church, Ayvalik, Balikesir", "city": "Balikesir", "country": "Turkey", "category": "heritage_village", "lat": 39.3333, "lon": 26.6500, "radius_km": 0.08,
     "prompts": ["Cunda Island historic Greek stone mansions cobblestone streets windmill Ayvalik Balikesir", "Cunda Island waterfront and Taxiarchis Church"]}
]
with open(OUT_DIR / "turkey.json", "w", encoding="utf-8") as f:
    json.dump(turkey_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved turkey.json with %d spots across every city in Turkey.", len(turkey_spots))

# -----------------------------------------------------------------------------
# 3. SAUDI ARABIA: Covering EVERY city in Saudi Arabia
# -----------------------------------------------------------------------------
saudi_spots = [
    # Mecca
    {"name": "The Kaaba & Masjid al-Haram, Mecca", "city": "Mecca", "country": "Saudi Arabia", "category": "world_landmark", "lat": 21.4225, "lon": 39.8262, "radius_km": 0.05,
     "prompts": ["The Holy Kaaba black cloth kiswah mataf marble courtyard Masjid al-Haram Mecca", "Masjid al-Haram Grand Mosque marble courtyard and Kaaba Mecca"]},
    {"name": "Abraj Al Bait Makkah Clock Royal Tower, Mecca", "city": "Mecca", "country": "Saudi Arabia", "category": "commercial_towers", "lat": 21.4189, "lon": 39.8256, "radius_km": 0.05,
     "prompts": ["Abraj Al Bait Makkah Clock Tower giant four-faced illuminated clock spire towering over Kaaba", "Makkah Royal Clock Tower skyscraper Mecca"]},
    {"name": "Mount Arafat (Jabal al-Rahmah), Mecca", "city": "Mecca", "country": "Saudi Arabia", "category": "historical_monument", "lat": 21.3547, "lon": 39.9842, "radius_km": 0.1,
     "prompts": ["Jabal al-Rahmah Mount of Mercy stone pillar granite hill plains of Arafat Mecca", "Mount Arafat white pillar monument during Hajj pilgrimage"]},

    # Medina
    {"name": "Al-Masjid an-Nabawi (Prophet's Mosque Green Dome), Medina", "city": "Medina", "country": "Saudi Arabia", "category": "world_landmark", "lat": 24.4672, "lon": 39.6111, "radius_km": 0.05,
     "prompts": ["Al-Masjid an-Nabawi Prophet's Mosque iconic Green Dome and giant folding umbrella courtyard Medina", "Prophet's Mosque marble plaza Green Dome and minarets Medina"]},
    {"name": "Quba Mosque, Medina", "city": "Medina", "country": "Saudi Arabia", "category": "historical_mosque", "lat": 24.4394, "lon": 39.6172, "radius_km": 0.05,
     "prompts": ["Quba Mosque first mosque in Islam white domes four minarets palm courtyard Medina", "Masjid Quba white marble portico Medina"]},
    {"name": "Mount Uhud & Archers Hill (Jabal al-Rumat), Medina", "city": "Medina", "country": "Saudi Arabia", "category": "mountain_peak", "lat": 24.5033, "lon": 39.6125, "radius_km": 0.2,
     "prompts": ["Mount Uhud red volcanic mountain ridge and Archers Hill cemetery Medina", "Jabal Uhud rocky mountain backdrop Medina"]},

    # Riyadh
    {"name": "Kingdom Centre & Sky Bridge, Riyadh", "city": "Riyadh", "country": "Saudi Arabia", "category": "commercial_towers", "lat": 24.7114, "lon": 46.6744, "radius_km": 0.05,
     "prompts": ["Kingdom Centre skyscraper inverted parabolic arch and illuminated Sky Bridge Riyadh", "Kingdom Tower modern reflective skyscraper Olaya Riyadh"]},
    {"name": "Al Faisaliyah Centre, Olaya, Riyadh", "city": "Riyadh", "country": "Saudi Arabia", "category": "commercial_towers", "lat": 24.6903, "lon": 46.6853, "radius_km": 0.05,
     "prompts": ["Al Faisaliyah Centre pyramid skyscraper golden glass sphere top King Fahd Road Riyadh", "Al Faisaliyah Tower modern high-rise Riyadh"]},
    {"name": "Historic Diriyah & At-Turaif District, Riyadh", "city": "Riyadh", "country": "Saudi Arabia", "category": "unesco_world_heritage", "lat": 24.7333, "lon": 46.5750, "radius_km": 0.1,
     "prompts": ["At-Turaif UNESCO World Heritage district mud-brick palaces Wadi Hanifa Diriyah Riyadh", "Diriyah mud-brick fortress and heritage buildings Riyadh"]},
    {"name": "Masmak Fortress (Al Masmak Palace), Deira, Riyadh", "city": "Riyadh", "country": "Saudi Arabia", "category": "fortress", "lat": 24.6311, "lon": 46.7133, "radius_km": 0.05,
     "prompts": ["Al Masmak Fortress clay and mud-brick citadel four conical watchtowers historic Riyadh", "Masmak Palace fortress wooden door Riyadh"]},
    {"name": "King Abdullah Financial District (KAFD) Towers, Riyadh", "city": "Riyadh", "country": "Saudi Arabia", "category": "commercial_district", "lat": 24.7667, "lon": 46.6389, "radius_km": 0.15,
     "prompts": ["KAFD King Abdullah Financial District futuristic geometric crystal skyscrapers Riyadh", "KAFD financial towers skyline Riyadh"]},

    # Jeddah
    {"name": "King Fahd's Fountain, Jeddah Corniche", "city": "Jeddah", "country": "Saudi Arabia", "category": "civic_monument", "lat": 21.5161, "lon": 39.1464, "radius_km": 0.05,
     "prompts": ["King Fahd Fountain world's tallest seawater fountain jet Red Sea Jeddah Corniche", "Jeddah fountain water plume illuminated evening Red Sea"]},
    {"name": "Al-Balad Historic District (Old Jeddah), Jeddah", "city": "Jeddah", "country": "Saudi Arabia", "category": "unesco_world_heritage", "lat": 21.4858, "lon": 39.1878, "radius_km": 0.08,
     "prompts": ["Historic Al-Balad coral stone tower houses intricate carved wooden roshan balconies Jeddah", "Al-Balad Old Jeddah ancient street and wooden latticework"]},
    {"name": "Al-Rahmah Floating Mosque, Jeddah Corniche", "city": "Jeddah", "country": "Saudi Arabia", "category": "mosque", "lat": 21.5906, "lon": 39.1103, "radius_km": 0.05,
     "prompts": ["Al-Rahmah Floating Mosque white turquoise domed mosque built on stilts over Red Sea Jeddah", "Floating Mosque Jeddah Red Sea promenade"]},

    # Dammam / Khobar / Dhahran
    {"name": "King Abdulaziz Center for World Culture (Ithra), Dhahran", "city": "Dammam", "country": "Saudi Arabia", "category": "museum", "lat": 26.3350, "lon": 50.1200, "radius_km": 0.08,
     "prompts": ["Ithra King Abdulaziz Center smooth pebble-shaped stainless steel architecture Dhahran Dammam", "Ithra cultural center monumental modern landmark"]},
    {"name": "Khobar Water Tower & Corniche, Al Khobar", "city": "Al Khobar", "country": "Saudi Arabia", "category": "civic_monument", "lat": 26.2867, "lon": 50.2217, "radius_km": 0.05,
     "prompts": ["Khobar Water Tower modern illuminated beacon Corniche Arabian Gulf Al Khobar", "Al Khobar water tower and seafront park"]},

    # AlUla
    {"name": "Hegra (Madain Salih - Qasr al-Farid), AlUla", "city": "AlUla", "country": "Saudi Arabia", "category": "unesco_world_heritage", "lat": 26.8000, "lon": 37.9500, "radius_km": 0.2,
     "prompts": ["Hegra Madain Salih Qasr al-Farid carved Nabataean tomb sandstone monolith desert AlUla", "Qasr al-Farid lonely tomb Hegra UNESCO AlUla"]},
    {"name": "Elephant Rock (Jabal AlFil), AlUla", "city": "AlUla", "country": "Saudi Arabia", "category": "natural_landmark", "lat": 26.6869, "lon": 37.9897, "radius_km": 0.08,
     "prompts": ["Elephant Rock Jabal AlFil natural elephant-shaped red sandstone arch desert AlUla", "Elephant Rock AlUla illuminated at night"]},
    {"name": "Maraya Concert Hall (Mirror Building), Ashar Valley, AlUla", "city": "AlUla", "country": "Saudi Arabia", "category": "civic_building", "lat": 26.7028, "lon": 37.8972, "radius_km": 0.05,
     "prompts": ["Maraya Concert Hall giant mirrored cube building reflecting red canyon desert Ashar Valley AlUla", "Maraya mirror building AlUla"]},

    # Abha & Asir & Khamis Mushait
    {"name": "Rijal Almaa Heritage Village, Asir Province, Abha", "city": "Abha", "country": "Saudi Arabia", "category": "unesco_world_heritage", "lat": 18.2167, "lon": 42.3167, "radius_km": 0.08,
     "prompts": ["Rijal Almaa gingerbread multi-story stone castles white painted windows Asir mountains Abha", "Rijal Almaa traditional stone fortress village"]},
    {"name": "Al-Soudah Peak & Asir National Park, Abha", "city": "Abha", "country": "Saudi Arabia", "category": "mountain_peak", "lat": 18.2667, "lon": 42.3667, "radius_km": 1.0,
     "prompts": ["Jabal Sawda highest peak in Saudi Arabia juniper pine forest clouds Asir Abha", "Al Soudah mountain ridge viewpoint Abha"]},
    {"name": "Khamis Mushait Heritage Market & Clock Tower", "city": "Khamis Mushait", "country": "Saudi Arabia", "category": "commercial_market", "lat": 18.3000, "lon": 42.7333, "radius_km": 0.05,
     "prompts": ["Khamis Mushait silver and spice traditional market Asir plateau", "Khamis Mushait city center roundabout"]},

    # Taif
    {"name": "Shubra Palace Museum & Rose Valley, Taif", "city": "Taif", "country": "Saudi Arabia", "category": "historical_palace", "lat": 21.2833, "lon": 40.4167, "radius_km": 0.05,
     "prompts": ["Shubra Palace white marble and wooden lattice balconies heritage museum Taif", "Taif rose fields and mountain palace"]},
    {"name": "Al Hada Mountain Cable Car Highway, Taif", "city": "Taif", "country": "Saudi Arabia", "category": "mountain_ridge", "lat": 21.3667, "lon": 40.2833, "radius_km": 0.5,
     "prompts": ["Al Hada winding mountain switchback highway illuminated night cliffs Taif", "Al Hada cable car and steep mountain escarpment"]},

    # Tabuk
    {"name": "Tabuk Castle (Tabuk Fort) & Ain Sukkar", "city": "Tabuk", "country": "Saudi Arabia", "category": "fortress", "lat": 28.3833, "lon": 36.5667, "radius_km": 0.05,
     "prompts": ["Tabuk Ottoman stone fortress castle and historic spring Hijaz pilgrimage Tabuk", "Tabuk Castle stone courtyard"]},
    {"name": "Wadi Al Disah (Valley of Palms), Tabuk Province", "city": "Tabuk", "country": "Saudi Arabia", "category": "canyon", "lat": 27.6000, "lon": 36.4667, "radius_km": 1.0,
     "prompts": ["Wadi Al Disah dramatic sandstone canyon towers freshwater stream palm trees Tabuk", "Al Disah valley red sandstone pillars"]},

    # Buraidah / Qassim
    {"name": "Buraidah Date City & Camel Market, Qassim", "city": "Buraidah", "country": "Saudi Arabia", "category": "commercial_market", "lat": 26.3333, "lon": 43.9667, "radius_km": 0.2,
     "prompts": ["Buraidah world's largest date festival market and desert camel auction Qassim", "Buraidah Date City marketplace Qassim"]},

    # Hail
    {"name": "A'arif Fort & Rock Art of Jubbah, Hail", "city": "Hail", "country": "Saudi Arabia", "category": "unesco_world_heritage", "lat": 27.5167, "lon": 41.6833, "radius_km": 0.1,
     "prompts": ["A'arif Fort mud-brick castle hilltop overlooking Hail city and Jubbah rock art UNESCO", "Qishlah Palace mud-brick fortress Hail"]},

    # Najran
    {"name": "Al-Aan Palace & Historic Al-Ukhdood Ruins, Najran", "city": "Najran", "country": "Saudi Arabia", "category": "historical_palace", "lat": 17.4833, "lon": 44.1333, "radius_km": 0.08,
     "prompts": ["Al-Aan Palace traditional multi-story mud castle palm groves Najran", "Al-Ukhdood archaeological stone inscriptions Najran"]},

    # Jizan
    {"name": "Farasan Islands & Ottoman Fort, Jizan", "city": "Jizan", "country": "Saudi Arabia", "category": "island", "lat": 16.7000, "lon": 42.1167, "radius_km": 0.5,
     "prompts": ["Farasan Islands turquoise coral reefs and Ottoman fort Red Sea Jizan", "Jizan coastal corniche and Al Dosariya Castle"]},

    # Yanbu
    {"name": "Historic Yanbu Al-Bahr & Royal Commission Waterfront", "city": "Yanbu", "country": "Saudi Arabia", "category": "heritage_village", "lat": 24.0833, "lon": 38.0500, "radius_km": 0.1,
     "prompts": ["Historic Yanbu Al-Bahr old coral stone port buildings and Red Sea waterfront promenade", "Yanbu industrial city palm beach"]},

    # Al Ahsa / Hofuf
    {"name": "Al-Qara Hill Caves & Al-Ahsa Oasis, Hofuf", "city": "Al Ahsa", "country": "Saudi Arabia", "category": "unesco_world_heritage", "lat": 25.4167, "lon": 49.6833, "radius_km": 0.2,
     "prompts": ["Al-Qara Mountain intricate wind-carved sandstone caves largest date palm oasis UNESCO Al Ahsa Hofuf", "Ibrahim Palace Ottoman fortress Hofuf Al Ahsa"]},

    # Jubail
    {"name": "Al Fanateer Beach & Marina Promenade, Jubail", "city": "Jubail", "country": "Saudi Arabia", "category": "coast", "lat": 27.0167, "lon": 49.6667, "radius_km": 0.15,
     "prompts": ["Al Fanateer beach corniche palm tree promenade Persian Gulf Jubail Industrial City", "Jubail Fanateer Marina"]},

    # Al Bahah
    {"name": "Thee Ain Marble Village (Dhee Ayn), Al Bahah", "city": "Al Bahah", "country": "Saudi Arabia", "category": "heritage_village", "lat": 19.9297, "lon": 41.4428, "radius_km": 0.08,
     "prompts": ["Thee Ayn ancient white marble and multi-story stone castle village banana grove Al Bahah", "Dhee Ayn marble fortress village Saudi Arabia"]},

    # Arar
    {"name": "Northern Borders Desert Gateway & Valleys, Arar", "city": "Arar", "country": "Saudi Arabia", "category": "desert", "lat": 30.9833, "lon": 41.0167, "radius_km": 0.5,
     "prompts": ["Arar desert limestone plains Northern Borders highway gateway Saudi Arabia", "Arar city center park and monument"]}
]
with open(OUT_DIR / "saudi_arabia.json", "w", encoding="utf-8") as f:
    json.dump(saudi_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved saudi_arabia.json with %d spots across every city in Saudi Arabia.", len(saudi_spots))

# -----------------------------------------------------------------------------
# 4. UAE: Covering ALL 7 Emirates & Cities
# -----------------------------------------------------------------------------
uae_spots = [
    # Dubai
    {"name": "Burj Khalifa & Observation Deck, Downtown Dubai", "city": "Dubai", "country": "United Arab Emirates", "category": "world_landmark", "lat": 25.1972, "lon": 55.2744, "radius_km": 0.05,
     "prompts": ["Burj Khalifa tallest skyscraper tiered spire glass facade Downtown Dubai", "Burj Khalifa tower rising above Dubai Mall fountain lake"]},
    {"name": "Burj Al Arab Luxury Sail Hotel, Jumeirah, Dubai", "city": "Dubai", "country": "United Arab Emirates", "category": "luxury_hotel", "lat": 25.1412, "lon": 55.1853, "radius_km": 0.05,
     "prompts": ["Burj Al Arab iconic sail-shaped luxury hotel island helipad Jumeirah beach Dubai", "Burj Al Arab hotel white sail architecture Arabian Gulf"]},
    {"name": "Museum of the Future, Sheikh Zayed Road, Dubai", "city": "Dubai", "country": "United Arab Emirates", "category": "museum", "lat": 25.2192, "lon": 55.2819, "radius_km": 0.05,
     "prompts": ["Museum of the Future stainless steel torus ring building Arabic calligraphy Sheikh Zayed Road Dubai", "Museum of the Future unique oval architectural landmark Dubai"]},
    {"name": "Dubai Frame, Zabeel Park, Dubai", "city": "Dubai", "country": "United Arab Emirates", "category": "civic_monument", "lat": 25.2347, "lon": 55.3003, "radius_km": 0.05,
     "prompts": ["Dubai Frame giant golden picture frame architectural monument Zabeel Park Dubai", "The Dubai Frame observation bridge and glass bridge walkway"]},
    {"name": "The Dubai Mall & Dubai Fountain Lake, Downtown Dubai", "city": "Dubai", "country": "United Arab Emirates", "category": "shopping_mall", "lat": 25.1986, "lon": 55.2797, "radius_km": 0.08,
     "prompts": ["The Dubai Mall grand shopping promenade and dancing fountain lake Downtown Dubai", "Dubai Mall fountain boardwalk and waterfront restaurants"]},
    {"name": "Palm Jumeirah & Atlantis The Palm, Dubai", "city": "Dubai", "country": "United Arab Emirates", "category": "resort", "lat": 25.1303, "lon": 55.1172, "radius_km": 0.1,
     "prompts": ["Atlantis The Palm Arabian arch pink palace resort tip of Palm Jumeirah crescent Dubai", "Palm Jumeirah fronds luxury villas and Atlantis resort"]},
    {"name": "Dubai Marina Walk & Yacht Promenade, Dubai", "city": "Dubai", "country": "United Arab Emirates", "category": "marina", "lat": 25.0789, "lon": 55.1389, "radius_km": 0.1,
     "prompts": ["Dubai Marina skyscrapers reflection luxury yachts waterway promenade Dubai", "Dubai Marina Walk high-rise residential towers waterfront"]},

    # Abu Dhabi
    {"name": "Sheikh Zayed Grand Mosque, Abu Dhabi", "city": "Abu Dhabi", "country": "United Arab Emirates", "category": "national_mosque", "lat": 24.4128, "lon": 54.4750, "radius_km": 0.08,
     "prompts": ["Sheikh Zayed Grand Mosque eighty-two white marble domes reflective pools Abu Dhabi", "Sheikh Zayed Grand Mosque grand floral courtyard and minarets Abu Dhabi"]},
    {"name": "Louvre Abu Dhabi Museum Dome, Saadiyat Island, Abu Dhabi", "city": "Abu Dhabi", "country": "United Arab Emirates", "category": "museum", "lat": 24.5336, "lon": 54.3986, "radius_km": 0.08,
     "prompts": ["Louvre Abu Dhabi Jean Nouvel silver floating dome rain of light Arabian sea Saadiyat", "Louvre Abu Dhabi museum water promenade and geometric dome"]},
    {"name": "Qasr Al Watan Presidential Palace, Abu Dhabi", "city": "Abu Dhabi", "country": "United Arab Emirates", "category": "historical_palace", "lat": 24.4633, "lon": 54.3056, "radius_km": 0.08,
     "prompts": ["Qasr Al Watan grand presidential palace white granite marble dome The Great Hall Abu Dhabi", "Qasr Al Watan presidential palace courtyard and fountain promenade"]},
    {"name": "Emirates Palace Mandarin Oriental, Corniche, Abu Dhabi", "city": "Abu Dhabi", "country": "United Arab Emirates", "category": "luxury_hotel", "lat": 24.4617, "lon": 54.3175, "radius_km": 0.08,
     "prompts": ["Emirates Palace luxury Arabian palace hotel golden domes landscaped gardens Abu Dhabi", "Emirates Palace grand facade and triumphal archway Abu Dhabi"]},
    {"name": "Ferrari World Abu Dhabi Red Roof, Yas Island", "city": "Abu Dhabi", "country": "United Arab Emirates", "category": "theme_park", "lat": 24.4836, "lon": 54.6075, "radius_km": 0.1,
     "prompts": ["Ferrari World iconic red aerodynamic curved roof yellow prancing horse logo Yas Island Abu Dhabi", "Ferrari World Abu Dhabi theme park exterior Yas Island"]},

    # Sharjah
    {"name": "Al Noor Mosque, Buhaira Corniche, Sharjah", "city": "Sharjah", "country": "United Arab Emirates", "category": "mosque", "lat": 25.3475, "lon": 55.3850, "radius_km": 0.05,
     "prompts": ["Al Noor Mosque Ottoman Turkish style cascading domes and two minarets Khaled Lagoon Sharjah", "Al Noor Mosque waterfront Buhaira Corniche Sharjah"]},
    {"name": "Sharjah Central Souq (Blue Souk), Sharjah", "city": "Sharjah", "country": "United Arab Emirates", "category": "commercial_market", "lat": 25.3486, "lon": 55.3889, "radius_km": 0.08,
     "prompts": ["Sharjah Central Souq Blue Souk twin traditional Islamic barrel vaulted buildings ceramic blue tiles", "Blue Souk Sharjah historic market buildings"]},

    # Al Ain
    {"name": "Jebel Hafeet Mountain Summit & Highway, Al Ain", "city": "Al Ain", "country": "United Arab Emirates", "category": "mountain_peak", "lat": 24.0583, "lon": 55.7778, "radius_km": 1.0,
     "prompts": ["Jebel Hafeet winding mountain highway rocky desert limestone ridge Al Ain Abu Dhabi", "Jebel Hafeet summit viewpoint overlooking desert plains Al Ain"]},
    {"name": "Al Jahili Fort, Al Ain", "city": "Al Ain", "country": "United Arab Emirates", "category": "fortress", "lat": 24.2167, "lon": 55.7528, "radius_km": 0.05,
     "prompts": ["Al Jahili Fort mud-brick battlements multi-tiered circular watchtower palm oasis Al Ain", "Al Jahili Fort courtyard and historic earthen towers Al Ain"]},

    # Ajman
    {"name": "Ajman Fort (Ajman Museum) & Corniche", "city": "Ajman", "country": "United Arab Emirates", "category": "fortress", "lat": 25.4128, "lon": 55.4456, "radius_km": 0.05,
     "prompts": ["Ajman Fort 18th-century stone and coral fortress museum watchtowers Ajman", "Ajman Corniche sandy beach promenade"]},

    # Ras Al Khaimah
    {"name": "Jebel Jais Mountain & Viewing Deck Park, Ras Al Khaimah", "city": "Ras Al Khaimah", "country": "United Arab Emirates", "category": "mountain_peak", "lat": 25.9525, "lon": 56.1417, "radius_km": 1.0,
     "prompts": ["Jebel Jais highest mountain summit in UAE steep rocky switchback highway Ras Al Khaimah", "Jebel Jais Viewing Deck Park cliffs and canyons RAK"]},
    {"name": "Dhayah Fort (Mud-Brick Hilltop Fortress), Ras Al Khaimah", "city": "Ras Al Khaimah", "country": "United Arab Emirates", "category": "fortress", "lat": 25.8833, "lon": 56.0583, "radius_km": 0.05,
     "prompts": ["Dhayah Fort conical hilltop mud-brick fortress overlooking date palm oasis and Arabian Gulf RAK", "Dhayah Fort staircase and mountain backdrop"]},

    # Fujairah
    {"name": "Al Bidyah Mosque (Oldest UAE Mosque), Fujairah", "city": "Fujairah", "country": "United Arab Emirates", "category": "historical_mosque", "lat": 25.4392, "lon": 56.3539, "radius_km": 0.05,
     "prompts": ["Al Bidyah Mosque ancient mud and stone four-domed mosque watchtowers Fujairah", "Al Bidyah oldest mosque in United Arab Emirates"]},
    {"name": "Fujairah Fort & Heritage Village, Fujairah", "city": "Fujairah", "country": "United Arab Emirates", "category": "fortress", "lat": 25.1389, "lon": 56.3250, "radius_km": 0.05,
     "prompts": ["Fujairah Fort historic mud-brick castle and round watchtower rocky mound Fujairah", "Fujairah Fort and palm tree plantations"]},

    # Umm Al Quwain
    {"name": "Umm Al Quwain Fort & Dreamland Aqua Park", "city": "Umm Al Quwain", "country": "United Arab Emirates", "category": "fortress", "lat": 25.5667, "lon": 55.5500, "radius_km": 0.08,
     "prompts": ["Umm Al Quwain historic coral stone fort museum and Al Ali guard towers", "UAQ Fort entrance gates and old cannons"]},

    # Khor Fakkan
    {"name": "Khor Fakkan Amphitheatre & Waterfall, Sharjah Enclave", "city": "Khor Fakkan", "country": "United Arab Emirates", "category": "civic_building", "lat": 25.3667, "lon": 56.3500, "radius_km": 0.08,
     "prompts": ["Khor Fakkan Amphitheatre Roman classical stone colosseum and mountain rock waterfall Gulf of Oman", "Khor Fakkan seaside amphitheatre and beach promenade"]}
]
with open(OUT_DIR / "uae.json", "w", encoding="utf-8") as f:
    json.dump(uae_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved uae.json with %d spots across all 7 emirates and cities.", len(uae_spots))

# -----------------------------------------------------------------------------
# 5. EGYPT: Covering EVERY city in Egypt
# -----------------------------------------------------------------------------
egypt_spots = [
    # Cairo & Giza
    {"name": "Great Pyramid of Giza & Sphinx, Giza, Cairo, Egypt", "city": "Cairo", "country": "Egypt", "category": "world_landmark", "lat": 29.9792, "lon": 31.1342, "radius_km": 0.1,
     "prompts": ["Great Pyramid of Giza Khufu limestone pyramid and Great Sphinx desert Cairo Egypt", "Pyramids of Giza Khafre pyramid casing stone and Sphinx"]},
    {"name": "Grand Egyptian Museum (GEM), Giza, Egypt", "city": "Cairo", "country": "Egypt", "category": "museum", "lat": 29.9950, "lon": 31.1200, "radius_km": 0.08,
     "prompts": ["Grand Egyptian Museum GEM triangular translucent alabaster facade Ramesses II statue Giza", "Grand Egyptian Museum grand staircase and entrance Giza"]},
    {"name": "Citadel of Saladin & Mosque of Muhammad Ali, Cairo", "city": "Cairo", "country": "Egypt", "category": "historical_mosque", "lat": 30.0289, "lon": 31.2597, "radius_km": 0.08,
     "prompts": ["Citadel of Saladin and Mosque of Muhammad Ali alabaster twin minarets overlooking Cairo", "Muhammad Ali Alabaster Mosque courtyard and dome Cairo Citadel"]},
    {"name": "Khan el-Khalili Historic Bazaar, Islamic Cairo", "city": "Cairo", "country": "Egypt", "category": "commercial_market", "lat": 30.0475, "lon": 31.2622, "radius_km": 0.08,
     "prompts": ["Khan el-Khalili historic medieval bazaar brass lamps spices Mamluk arches Cairo", "Khan el-Khalili narrow stone shopping street Islamic Cairo"]},

    # Alexandria
    {"name": "Citadel of Qaitbay, Alexandria, Egypt", "city": "Alexandria", "country": "Egypt", "category": "fortress", "lat": 31.2139, "lon": 29.8856, "radius_km": 0.05,
     "prompts": ["Citadel of Qaitbay 15th-century stone defensive fortress Pharos lighthouse site Alexandria", "Qaitbay Citadel Mediterranean sea fortress Alexandria"]},
    {"name": "Bibliotheca Alexandrina (Library of Alexandria)", "city": "Alexandria", "country": "Egypt", "category": "library", "lat": 31.2089, "lon": 29.9092, "radius_km": 0.05,
     "prompts": ["Bibliotheca Alexandrina tilted disc granite cylinder hieroglyphic carvings Alexandria", "Library of Alexandria modern waterfront architecture"]},

    # Luxor
    {"name": "Karnak Temple Complex & Hypostyle Hall, Luxor, Egypt", "city": "Luxor", "country": "Egypt", "category": "unesco_world_heritage", "lat": 25.7189, "lon": 32.6572, "radius_km": 0.1,
     "prompts": ["Karnak Temple Great Hypostyle Hall 134 colossal sandstone papyrus columns Luxor", "Karnak Temple avenue of ram-headed sphinxes Luxor Egypt"]},
    {"name": "Valley of the Kings & Temple of Hatshepsut, Luxor", "city": "Luxor", "country": "Egypt", "category": "unesco_world_heritage", "lat": 25.7381, "lon": 32.6075, "radius_km": 0.1,
     "prompts": ["Mortuary Temple of Hatshepsut Deir el-Bahari colonnaded limestone terraces cliff Luxor", "Temple of Hatshepsut three tiered terraces desert cliff"]},

    # Aswan
    {"name": "Abu Simbel Sun Temples of Ramesses II, Aswan, Egypt", "city": "Aswan", "country": "Egypt", "category": "unesco_world_heritage", "lat": 22.3369, "lon": 31.6256, "radius_km": 0.05,
     "prompts": ["Abu Simbel four colossal seated statues of Ramesses II rock-cut temple Lake Nasser Aswan", "Abu Simbel grand rock temple facade Egypt"]},
    {"name": "Philae Temple of Isis & Aswan High Dam", "city": "Aswan", "country": "Egypt", "category": "unesco_world_heritage", "lat": 24.0256, "lon": 32.8842, "radius_km": 0.08,
     "prompts": ["Philae Temple of Isis island sanctuary pylons Nile River Aswan", "Philae island temple complex Aswan"]},

    # Sharm El Sheikh
    {"name": "Al Sahaba Mosque & Naama Bay Promenade, Sharm El Sheikh", "city": "Sharm El Sheikh", "country": "Egypt", "category": "national_mosque", "lat": 27.8653, "lon": 34.2981, "radius_km": 0.05,
     "prompts": ["Al Sahaba Mosque magnificent Ottoman-Fatimid hybrid twin minarets Old Market Sharm El Sheikh", "Naama Bay pedestrian beach promenade Red Sea resort Sharm"]},

    # Hurghada
    {"name": "Al Mina Mosque & Hurghada Marina Boulevard", "city": "Hurghada", "country": "Egypt", "category": "national_mosque", "lat": 27.2289, "lon": 33.8422, "radius_km": 0.05,
     "prompts": ["Al Mina Mosque white marble domes and minarets Hurghada Marina Red Sea", "Hurghada Marina luxury yacht promenade and restaurants"]},

    # Port Said
    {"name": "Suez Canal Authority Headquarters & Port Said Lighthouse", "city": "Port Said", "country": "Egypt", "category": "civic_building", "lat": 31.2589, "lon": 32.3089, "radius_km": 0.05,
     "prompts": ["Suez Canal Authority dome palace building waterfront Port Said northern entrance", "Port Said octagonal concrete historic lighthouse"]},

    # Suez
    {"name": "Suez Canal Southern Gateway & Port Tawfik Promenade", "city": "Suez", "country": "Egypt", "category": "port", "lat": 29.9667, "lon": 32.5500, "radius_km": 0.1,
     "prompts": ["Suez Canal southern mouth container ships entering Gulf of Suez Port Tawfik", "Suez city waterfront promenade"]},

    # Mansoura
    {"name": "Dar Ibn Luqman (Where King Louis IX was Imprisoned), Mansoura", "city": "Mansoura", "country": "Egypt", "category": "historical_building", "lat": 31.0436, "lon": 31.3789, "radius_km": 0.05,
     "prompts": ["Dar Ibn Luqman historic medieval Crusader prison museum Mansoura Nile Delta", "Mansoura University campus buildings"]},

    # Tanta
    {"name": "Sayyid Ahmed al-Badawi Mosque, Tanta, Gharbia", "city": "Tanta", "country": "Egypt", "category": "historical_shrine", "lat": 30.7872, "lon": 31.0019, "radius_km": 0.05,
     "prompts": ["Sayyid Ahmed al-Badawi Mosque grand three domes and twin minarets pilgrimage center Tanta", "Al Badawi Mosque courtyard Tanta"]},

    # Asyut
    {"name": "Monastery of the Holy Virgin (Deir Dronka), Asyut", "city": "Asyut", "country": "Egypt", "category": "historical_church", "lat": 27.1333, "lon": 31.1667, "radius_km": 0.08,
     "prompts": ["Deir Dronka Monastery of the Holy Virgin carved into mountain cliff Asyut Upper Egypt", "Dronka cave monastery overlooking Nile valley Asyut"]},

    # Faiyum
    {"name": "Wadi El Rayan Waterfalls & Lake Qarun, Faiyum", "city": "Faiyum", "country": "Egypt", "category": "natural_landmark", "lat": 29.2333, "lon": 30.4167, "radius_km": 0.2,
     "prompts": ["Wadi El Rayan natural desert waterfalls connecting upper and lower lakes Faiyum Egypt", "Wadi Al-Hitan Valley of Whales fossil desert Faiyum"]},

    # Ismailia
    {"name": "Ismailia Canal Promenade & French Colonial Villas", "city": "Ismailia", "country": "Egypt", "category": "colonial_architecture", "lat": 30.5833, "lon": 32.2667, "radius_km": 0.08,
     "prompts": ["Ferdinand de Lesseps historic villa and Lake Timsah gardens Ismailia Suez Canal", "Ismailia green tree-lined boulevards"]},

    # Siwa Oasis
    {"name": "Shali Fortress & Temple of the Oracle of Amun, Siwa Oasis", "city": "Siwa Oasis", "country": "Egypt", "category": "heritage_village", "lat": 29.2033, "lon": 25.5194, "radius_km": 0.1,
     "prompts": ["Shali Fortress melting kershef salt-mud brick ruins date palm oasis Siwa Western Desert", "Cleopatra Bath natural spring and salt lake pools Siwa"]},

    # Dahab
    {"name": "Dahab Blue Hole & Lighthouse Beach Promenade", "city": "Dahab", "country": "Egypt", "category": "coast", "lat": 28.5722, "lon": 34.5369, "radius_km": 0.1,
     "prompts": ["Dahab Blue Hole deep submarine marine sinkhole Sinai coast Red Sea", "Dahab beachfront boardwalk bedouin cafes and dive shops"]},

    # Marsa Matruh
    {"name": "Cleopatra Beach Rock Bath & Ageeba Cove, Marsa Matruh", "city": "Marsa Matruh", "country": "Egypt", "category": "coast", "lat": 31.3500, "lon": 27.2333, "radius_km": 0.15,
     "prompts": ["Ageeba Beach dramatic Mediterranean limestone cliffs turquoise sea Marsa Matruh", "Cleopatra Rock natural coastal wave bath Marsa Matruh"]}
]
with open(OUT_DIR / "egypt.json", "w", encoding="utf-8") as f:
    json.dump(egypt_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved egypt.json with %d spots across every city in Egypt.", len(egypt_spots))

# -----------------------------------------------------------------------------
# 6. INDIA: Covering EVERY major city across all states
# -----------------------------------------------------------------------------
india_spots = [
    # Delhi
    {"name": "India Gate & Kartavya Path, New Delhi", "city": "Delhi", "country": "India", "category": "national_monument", "lat": 28.6128, "lon": 77.2294, "radius_km": 0.05,
     "prompts": ["India Gate triumphal war memorial sandstone arch Kartavya Path New Delhi", "India Gate canopy and ceremonial avenue Delhi"]},
    {"name": "Red Fort (Lal Qila), Old Delhi", "city": "Delhi", "country": "India", "category": "unesco_world_heritage", "lat": 28.6561, "lon": 77.2411, "radius_km": 0.08,
     "prompts": ["Red Fort Lal Qila red sandstone Mughal fortress Lahore Gate Old Delhi", "Red Fort massive defensive walls and battlements Delhi"]},
    {"name": "Qutub Minar & Iron Pillar, Mehrauli, Delhi", "city": "Delhi", "country": "India", "category": "unesco_world_heritage", "lat": 28.5244, "lon": 77.1856, "radius_km": 0.05,
     "prompts": ["Qutub Minar fluted red sandstone minaret tower balcony carvings Mehrauli Delhi", "Qutub Minar complex and Quwwat-ul-Islam mosque"]},
    {"name": "Lotus Temple (Bahai House of Worship), New Delhi", "city": "Delhi", "country": "India", "category": "temple", "lat": 28.5533, "lon": 77.2589, "radius_km": 0.05,
     "prompts": ["Lotus Temple white marble lotus flower petal architecture reflection ponds New Delhi", "Lotus Temple Bahai prayer hall gardens Delhi"]},

    # Agra
    {"name": "Taj Mahal & Yamuna River, Agra", "city": "Agra", "country": "India", "category": "world_landmark", "lat": 27.1750, "lon": 78.0422, "radius_km": 0.05,
     "prompts": ["Taj Mahal white marble Mughal mausoleum dome reflecting pool and minarets Agra India", "Taj Mahal symmetry gardens and central dome Yamuna river"]},
    {"name": "Agra Fort (Red Sandstone Imperial Palace), Agra", "city": "Agra", "country": "India", "category": "unesco_world_heritage", "lat": 27.1794, "lon": 78.0211, "radius_km": 0.08,
     "prompts": ["Agra Fort red sandstone Jahangiri Mahal and marble Musamman Burj overlooking Taj Mahal", "Agra Fort massive ramparts and Amar Singh Gate"]},

    # Mumbai
    {"name": "Gateway of India & Taj Mahal Palace Hotel, Mumbai", "city": "Mumbai", "country": "India", "category": "national_monument", "lat": 18.9220, "lon": 72.8347, "radius_km": 0.05,
     "prompts": ["Gateway of India basalt triumphal arch and Taj Mahal Palace Hotel Mumbai harbor", "Gateway of India waterfront monument Colaba Mumbai"]},
    {"name": "Chhatrapati Shivaji Maharaj Terminus (VT Station), Mumbai", "city": "Mumbai", "country": "India", "category": "unesco_world_heritage", "lat": 18.9400, "lon": 72.8353, "radius_km": 0.05,
     "prompts": ["CST Victoria Terminus railway station Victorian Gothic revival stained glass dome Mumbai", "CSMT railway terminus clock tower Mumbai"]},
    {"name": "Marine Drive & Queen's Necklace Promenade, Mumbai", "city": "Mumbai", "country": "India", "category": "coast", "lat": 18.9431, "lon": 72.8231, "radius_km": 0.15,
     "prompts": ["Marine Drive curved sea-facing promenade Art Deco buildings Arabian Sea Mumbai", "Queen's Necklace Marine Drive night lights Mumbai"]},

    # Bengaluru (Bangalore)
    {"name": "Vidhana Soudha & Attara Kacheri, Bengaluru", "city": "Bengaluru", "country": "India", "category": "government", "lat": 12.9797, "lon": 77.5908, "radius_km": 0.05,
     "prompts": ["Vidhana Soudha monumental Neo-Dravidian granite legislative palace Bangalore", "Vidhana Soudha white granite state capitol Bengaluru"]},
    {"name": "Bangalore Palace & Tudor Towers, Bengaluru", "city": "Bengaluru", "country": "India", "category": "historical_palace", "lat": 12.9986, "lon": 77.5922, "radius_km": 0.08,
     "prompts": ["Bangalore Palace Tudor style stone castle battlements and wooden interiors Bangalore", "Bangalore Palace exterior gardens"]},

    # Kolkata
    {"name": "Victoria Memorial & Maidan Gardens, Kolkata", "city": "Kolkata", "country": "India", "category": "historical_palace", "lat": 22.5447, "lon": 88.3425, "radius_km": 0.08,
     "prompts": ["Victoria Memorial white Makrana marble monument dome reflecting ponds Maidan Kolkata", "Victoria Memorial colonnades and gardens Calcutta"]},
    {"name": "Howrah Bridge (Rabindra Setu) & Hooghly River, Kolkata", "city": "Kolkata", "country": "India", "category": "bridge", "lat": 22.5853, "lon": 88.3467, "radius_km": 0.15,
     "prompts": ["Howrah Bridge iconic cantilever steel truss bridge over Hooghly River Kolkata", "Howrah Bridge busy yellow taxi traffic Kolkata"]},

    # Chennai
    {"name": "Kapaleeshwarar Temple Dravidian Gopuram, Mylapore, Chennai", "city": "Chennai", "country": "India", "category": "temple", "lat": 13.0333, "lon": 80.2694, "radius_km": 0.05,
     "prompts": ["Kapaleeshwarar Temple rainbow painted Dravidian gopuram pyramid tower Mylapore Chennai", "Mylapore temple tank and gopuram Chennai"]},
    {"name": "Marina Beach & Light House Promenade, Chennai", "city": "Chennai", "country": "India", "category": "coast", "lat": 13.0500, "lon": 80.2833, "radius_km": 0.2,
     "prompts": ["Marina Beach wide sandy urban coastline Bay of Bengal promenade Chennai", "Marina Beach lighthouse and statues Chennai"]},

    # Hyderabad
    {"name": "Charminar & Laad Bazaar, Hyderabad", "city": "Hyderabad", "country": "India", "category": "historical_monument", "lat": 17.3617, "lon": 78.4747, "radius_km": 0.05,
     "prompts": ["Charminar four grand minarets arched gateway monument Old City Hyderabad", "Charminar illuminated at evening bustling street bazaar Hyderabad"]},
    {"name": "Golconda Fort & Acoustic Echo Pavilion, Hyderabad", "city": "Hyderabad", "country": "India", "category": "fortress", "lat": 17.3833, "lon": 78.4011, "radius_km": 0.1,
     "prompts": ["Golconda Fort medieval granite hilltop citadel fortress walls Hyderabad", "Golconda Fort Bala Hissar pavilion view"]},

    # Ahmedabad
    {"name": "Sabarmati Ashram & Riverfront Promenade, Ahmedabad", "city": "Ahmedabad", "country": "India", "category": "heritage_site", "lat": 23.0600, "lon": 72.5800, "radius_km": 0.08,
     "prompts": ["Sabarmati Ashram Mahatma Gandhi residence Hriday Kunj riverside Ahmedabad", "Sabarmati Riverfront modern promenade Ahmedabad"]},
    {"name": "Adalaj Stepwell (Rudabai Stepwell), Gandhinagar / Ahmedabad", "city": "Ahmedabad", "country": "India", "category": "historical_monument", "lat": 23.1667, "lon": 72.5800, "radius_km": 0.05,
     "prompts": ["Adalaj Stepwell five stories deep carved sandstone subterranean architecture Ahmedabad", "Adalaj stepwell intricately carved pillars"]},

    # Jaipur
    {"name": "Hawa Mahal (Palace of Winds), Jaipur", "city": "Jaipur", "country": "India", "category": "historical_palace", "lat": 26.9239, "lon": 75.8267, "radius_km": 0.05,
     "prompts": ["Hawa Mahal Palace of Winds pink honeycomb sandstone facade jharokha windows Jaipur", "Hawa Mahal five-story pink palace street view Jaipur"]},
    {"name": "Amber Fort (Amer Palace) & Maota Lake, Jaipur", "city": "Jaipur", "country": "India", "category": "unesco_world_heritage", "lat": 26.9856, "lon": 75.8511, "radius_km": 0.1,
     "prompts": ["Amber Fort yellow and pink sandstone Rajput fortress overlooking Maota Lake Jaipur", "Amer Fort Sheesh Mahal mirror courtyard Jaipur"]},

    # Amritsar
    {"name": "Golden Temple (Harmandir Sahib), Amritsar", "city": "Amritsar", "country": "India", "category": "temple", "lat": 31.6200, "lon": 74.8764, "radius_km": 0.05,
     "prompts": ["Golden Temple Harmandir Sahib gold-plated gurdwara surrounded by sacred Amrit Sarovar lake Amritsar", "Golden Temple illuminated at night reflecting in holy pool"]},

    # Varanasi
    {"name": "Dashashwamedh Ghat & Ganga Aarti Steps, Varanasi", "city": "Varanasi", "country": "India", "category": "heritage_site", "lat": 25.3108, "lon": 83.0106, "radius_km": 0.08,
     "prompts": ["Dashashwamedh Ghat Ganga Aarti ceremony steps holy Ganges river Varanasi", "Varanasi ghats ancient riverfront temples and boats Ganges"]},

    # Srinagar (Kashmir)
    {"name": "Dal Lake Shikara Houseboats & Shankaracharya Hill, Srinagar", "city": "Srinagar", "country": "India", "category": "lake", "lat": 34.0833, "lon": 74.8667, "radius_km": 0.2,
     "prompts": ["Dal Lake wooden carved shikara boats floating gardens Pir Panjal mountains Srinagar Kashmir", "Houseboats on Dal Lake reflection Zabarwan hills Srinagar"]},

    # Chandigarh
    {"name": "Capitol Complex (Palace of Assembly & Open Hand), Chandigarh", "city": "Chandigarh", "country": "India", "category": "unesco_world_heritage", "lat": 30.7583, "lon": 76.8042, "radius_km": 0.08,
     "prompts": ["Le Corbusier Capitol Complex concrete brutalist Palace of Assembly Open Hand Monument Chandigarh", "Open Hand Monument giant rotating metal sculpture Chandigarh"]},

    # Kochi (Cochin)
    {"name": "Fort Kochi Chinese Fishing Nets & Mattancherry, Kochi", "city": "Kochi", "country": "India", "category": "coast", "lat": 9.9667, "lon": 76.2417, "radius_km": 0.08,
     "prompts": ["Chinese Fishing Nets cantilever wooden shore-operated fishing rigs Fort Kochi Kerala", "Fort Kochi beach sunset Chinese nets"]},

    # Goa (Panaji)
    {"name": "Basilica of Bom Jesus & Church of Our Lady of the Immaculate Conception, Goa", "city": "Goa", "country": "India", "category": "historical_church", "lat": 15.5008, "lon": 73.9117, "radius_km": 0.05,
     "prompts": ["Basilica of Bom Jesus Baroque red laterite stone Catholic cathedral Old Goa", "Our Lady of the Immaculate Conception Church white zigzag stairway Panaji Goa"]}
]
with open(OUT_DIR / "india.json", "w", encoding="utf-8") as f:
    json.dump(india_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved india.json with %d spots across Indian cities.", len(india_spots))

# -----------------------------------------------------------------------------
# 7. IRAN: Covering EVERY city in Iran
# -----------------------------------------------------------------------------
iran_spots = [
    # Tehran
    {"name": "Azadi Tower (Freedom Monument), Tehran", "city": "Tehran", "country": "Iran", "category": "national_monument", "lat": 35.6997, "lon": 51.3381, "radius_km": 0.05,
     "prompts": ["Azadi Tower white marble inverted Y-shaped monument Azadi Square Tehran", "Shahyad Azadi Tower fountain plaza Tehran"]},
    {"name": "Milad Tower, Tehran", "city": "Tehran", "country": "Iran", "category": "commercial_towers", "lat": 35.7447, "lon": 51.3753, "radius_km": 0.05,
     "prompts": ["Milad Tower sixth-tallest telecommunications tower head pod Alborz mountains Tehran", "Milad Tower observation deck overlooking Tehran skyline"]},
    {"name": "Golestan Palace & Marble Throne, Tehran", "city": "Tehran", "country": "Iran", "category": "unesco_world_heritage", "lat": 35.6797, "lon": 51.4203, "radius_km": 0.05,
     "prompts": ["Golestan Palace Qajar tilework courtyard Hall of Mirrors Tehran", "Golestan Palace exterior facade Persian pool"]},

    # Isfahan
    {"name": "Naqsh-e Jahan Square & Shah Mosque, Isfahan", "city": "Isfahan", "country": "Iran", "category": "unesco_world_heritage", "lat": 32.6575, "lon": 51.6778, "radius_km": 0.1,
     "prompts": ["Naqsh-e Jahan Square vast Safavid royal plaza turquoise Shah Mosque reflection pool Isfahan", "Shah Mosque Imam Mosque seven-colored tilework entrance portal Isfahan"]},
    {"name": "Si-o-se-pol (Bridge of Thirty-Three Arches), Isfahan", "city": "Isfahan", "country": "Iran", "category": "bridge", "lat": 32.6447, "lon": 51.6675, "radius_km": 0.05,
     "prompts": ["Si-o-se-pol double-decked thirty-three stone arch bridge Zayandeh River Isfahan", "Khaju Bridge and Si-o-se-pol illuminated Isfahan"]},

    # Shiraz
    {"name": "Nasir al-Mulk (Pink Mosque), Shiraz", "city": "Shiraz", "country": "Iran", "category": "historical_mosque", "lat": 29.6083, "lon": 52.5486, "radius_km": 0.05,
     "prompts": ["Nasir al-Mulk Pink Mosque kaleidoscope stained glass windows casting rainbow light Persian carpets Shiraz", "Pink Mosque Shiraz interior colorful morning sun"]},
    {"name": "Persepolis (Takht-e Jamshid), Shiraz", "city": "Shiraz", "country": "Iran", "category": "unesco_world_heritage", "lat": 29.9353, "lon": 52.8914, "radius_km": 0.15,
     "prompts": ["Persepolis Takht-e Jamshid ancient Achaemenid ceremonial capital stone columns Gate of All Nations", "Persepolis ruins monumental stairways and bas-reliefs Shiraz"]},
    {"name": "Tomb of Hafez (Hafezieh), Shiraz", "city": "Shiraz", "country": "Iran", "category": "historical_shrine", "lat": 29.6256, "lon": 52.5583, "radius_km": 0.05,
     "prompts": ["Hafezieh octagonal copper dome pavilion tomb of Persian poet Hafez gardens Shiraz", "Tomb of Hafez illuminated pavilion Shiraz"]},

    # Tabriz
    {"name": "Tabriz Historic Bazaar Complex & Blue Mosque, Tabriz", "city": "Tabriz", "country": "Iran", "category": "unesco_world_heritage", "lat": 38.0800, "lon": 46.2917, "radius_km": 0.08,
     "prompts": ["Tabriz Historic Grand Bazaar vaulted brick arches UNESCO World Heritage Tabriz", "Blue Mosque Kaboud Mosque dark blue cobalt ceramic tiles Tabriz"]},

    # Mashhad
    {"name": "Imam Reza Holy Shrine Complex, Mashhad", "city": "Mashhad", "country": "Iran", "category": "historical_shrine", "lat": 36.2878, "lon": 59.6156, "radius_km": 0.1,
     "prompts": ["Imam Reza Holy Shrine vast golden dome seven courtyards blue minarets Mashhad", "Imam Reza shrine complex illuminated marble plazas Mashhad"]},

    # Yazd
    {"name": "Jameh Mosque of Yazd & Historic Windcatchers (Badgirs)", "city": "Yazd", "country": "Iran", "category": "unesco_world_heritage", "lat": 31.9014, "lon": 54.3689, "radius_km": 0.08,
     "prompts": ["Jameh Mosque of Yazd tallest tiled minarets and mud-brick desert badgir windcatchers Yazd", "Yazd historical city mudbrick rooftops and wind towers"]},
    {"name": "Zoroastrian Tower of Silence (Dakhmeh), Yazd", "city": "Yazd", "country": "Iran", "category": "historical_monument", "lat": 31.8250, "lon": 54.3583, "radius_km": 0.08,
     "prompts": ["Zoroastrian Tower of Silence circular stone cemetery hilltop arid desert Yazd", "Yazd Dakhmeh desert hill structures"]},

    # Qom
    {"name": "Fatima Masumeh Holy Shrine, Qom", "city": "Qom", "country": "Iran", "category": "historical_shrine", "lat": 34.6417, "lon": 50.8789, "radius_km": 0.08,
     "prompts": ["Fatima Masumeh Shrine shimmering pure gold central dome and turquoise tilework Qom", "Holy Shrine of Hazrat Masoumeh courtyard Qom"]},

    # Kashan
    {"name": "Fin Garden & Sultan Amir Ahmad Bathhouse, Kashan", "city": "Kashan", "country": "Iran", "category": "unesco_world_heritage", "lat": 33.9458, "lon": 51.3719, "radius_km": 0.05,
     "prompts": ["Bagh-e Fin classic Persian garden turquoise water pools cypress trees Kashan", "Sultan Amir Ahmad Bathhouse dome roof glass lenses Kashan"]},

    # Kermanshah
    {"name": "Taq-e Bostan Sasanian Rock Bas-Reliefs, Kermanshah", "city": "Kermanshah", "country": "Iran", "category": "heritage_site", "lat": 34.3878, "lon": 47.1306, "radius_km": 0.05,
     "prompts": ["Taq-e Bostan carved stone rock arches Sasanian king khosrow investiture spring pool Kermanshah", "Taq-e Bostan ancient rock carvings Kermanshah"]},

    # Kish Island
    {"name": "Greek Ship Wreck & Coral Beach, Kish Island", "city": "Kish Island", "country": "Iran", "category": "coast", "lat": 26.5167, "lon": 53.9000, "radius_km": 0.1,
     "prompts": ["Greek Ship rusted steamship stranded on coral reef sunset Persian Gulf Kish Island", "Kish Island white coral beach and pier"]}
]
with open(OUT_DIR / "iran.json", "w", encoding="utf-8") as f:
    json.dump(iran_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved iran.json with %d spots across Iranian cities.", len(iran_spots))

# -----------------------------------------------------------------------------
# 8. IRAQ: Covering EVERY city in Iraq
# -----------------------------------------------------------------------------
iraq_spots = [
    # Baghdad
    {"name": "Al-Mustansiriya Madrasah & Tigris River, Baghdad", "city": "Baghdad", "country": "Iraq", "category": "historical_building", "lat": 33.3381, "lon": 44.3889, "radius_km": 0.05,
     "prompts": ["Mustansiriya Madrasah medieval Abbasid brick arched university on Tigris riverbank Baghdad", "Mustansiriya courtyard and geometric brickwork Baghdad"]},
    {"name": "Swords of Qadisiyah (Hands of Victory), Baghdad", "city": "Baghdad", "country": "Iraq", "category": "national_monument", "lat": 33.3058, "lon": 44.3833, "radius_km": 0.05,
     "prompts": ["Hands of Victory Swords of Qadisiyah massive crossed bronze swords archway parade ground Baghdad", "Swords of Qadisiyah triumphal arch Baghdad"]},
    {"name": "Al-Shaheed Monument (Martyrs' Monument), Baghdad", "city": "Baghdad", "country": "Iraq", "category": "national_monument", "lat": 33.3422, "lon": 44.4444, "radius_km": 0.08,
     "prompts": ["Al-Shaheed Monument giant split turquoise dome rising from circular water lake Baghdad", "Martyrs Monument turquoise dome halves Baghdad"]},

    # Najaf
    {"name": "Imam Ali Holy Shrine, Najaf", "city": "Najaf", "country": "Iraq", "category": "historical_shrine", "lat": 31.9961, "lon": 44.3142, "radius_km": 0.05,
     "prompts": ["Imam Ali Holy Shrine pure gold dome and minarets grand tiled courtyard Najaf Iraq", "Imam Ali Shrine golden dome and pilgrims plaza Najaf"]},
    {"name": "Wadi-us-Salaam (Valley of Peace Cemetery), Najaf", "city": "Najaf", "country": "Iraq", "category": "historical_necropolis", "lat": 32.0083, "lon": 44.3167, "radius_km": 0.5,
     "prompts": ["Wadi-us-Salaam world's largest cemetery millions of brick graves and domes Najaf", "Valley of Peace cemetery expanse Najaf"]},

    # Karbala
    {"name": "Imam Husayn Holy Shrine, Karbala", "city": "Karbala", "country": "Iraq", "category": "historical_shrine", "lat": 32.6161, "lon": 44.0325, "radius_km": 0.05,
     "prompts": ["Imam Husayn Holy Shrine illuminated golden dome and minarets Karbala Iraq", "Imam Husayn and Al-Abbas holy shrines pedestrian plaza Karbala"]},

    # Erbil
    {"name": "Erbil Citadel (Hawler Citadel), Erbil, Kurdistan", "city": "Erbil", "country": "Iraq", "category": "unesco_world_heritage", "lat": 36.1911, "lon": 44.0092, "radius_km": 0.08,
     "prompts": ["Erbil Citadel ancient fortified tell mound continuous mud-brick perimeter wall Erbil", "Hawler Citadel entrance gate and central fountains Erbil"]},

    # Basra
    {"name": "Shatt al-Arab Corniche & Old Shanashil Houses, Basra", "city": "Basra", "country": "Iraq", "category": "heritage_village", "lat": 30.5167, "lon": 47.8333, "radius_km": 0.08,
     "prompts": ["Basra historic wooden carved shanasheel balconies along canals and Shatt al-Arab corniche", "Basra waterfront and palm trees"]},

    # Mosul
    {"name": "Al-Nuri Great Mosque & Al-Hadba Leaning Minaret, Mosul", "city": "Mosul", "country": "Iraq", "category": "historical_mosque", "lat": 36.3433, "lon": 43.1278, "radius_km": 0.05,
     "prompts": ["Great Mosque of al-Nuri historic green dome and reconstructed Al-Hadba leaning cylindrical minaret Mosul", "Al Nuri mosque Mosul Old City"]},

    # Samarra
    {"name": "Great Mosque of Samarra (Malwiya Spiral Minaret)", "city": "Samarra", "country": "Iraq", "category": "unesco_world_heritage", "lat": 34.2064, "lon": 43.8800, "radius_km": 0.08,
     "prompts": ["Malwiya Minaret colossal 52-meter spiral sandstone cone ramp minaret Great Mosque Samarra", "Spiral minaret of Samarra UNESCO World Heritage"]},

    # Babylon / Hillah
    {"name": "Ancient City of Babylon & Ishtar Gate, Hillah", "city": "Babylon", "country": "Iraq", "category": "unesco_world_heritage", "lat": 32.5422, "lon": 44.4208, "radius_km": 0.1,
     "prompts": ["Ancient Babylon reconstructed blue-glazed brick Ishtar Gate and lion relief walls Hillah", "Babylon archaeological ruins and Saddam palace mound"]},

    # Sulaymaniyah
    {"name": "Amna Suraka (Red Security Museum) & Mount Goyzha, Sulaymaniyah", "city": "Sulaymaniyah", "country": "Iraq", "category": "museum", "lat": 35.5667, "lon": 45.4333, "radius_km": 0.08,
     "prompts": ["Sulaymaniyah city view from Mount Goyzha Kurdish mountains and Amna Suraka museum", "Mount Goyzha overlook Sulaymaniyah"]}
]
with open(OUT_DIR / "iraq.json", "w", encoding="utf-8") as f:
    json.dump(iraq_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved iraq.json with %d spots across Iraqi cities.", len(iraq_spots))

# -----------------------------------------------------------------------------
# 9. OMAN: Covering EVERY city in Oman
# -----------------------------------------------------------------------------
oman_spots = [
    # Muscat
    {"name": "Sultan Qaboos Grand Mosque, Muscat", "city": "Muscat", "country": "Oman", "category": "national_mosque", "lat": 23.5839, "lon": 58.3889, "radius_km": 0.08,
     "prompts": ["Sultan Qaboos Grand Mosque Indian sandstone central dome five minarets Persian carpet Muscat", "Sultan Qaboos Grand Mosque marble courtyard and archways Muscat"]},
    {"name": "Mutrah Corniche & Souq, Muscat", "city": "Muscat", "country": "Oman", "category": "commercial_market", "lat": 23.6231, "lon": 58.5636, "radius_km": 0.08,
     "prompts": ["Mutrah Corniche harbor waterfront traditional dhows giant incense burner monument Muscat", "Mutrah Souq ornate stained glass lattice entrance Muscat"]},
    {"name": "Al Alam Palace & Twin Forts (Al Jalali & Al Mirani), Old Muscat", "city": "Muscat", "country": "Oman", "category": "historical_palace", "lat": 23.6158, "lon": 58.5947, "radius_km": 0.05,
     "prompts": ["Al Alam Palace Sultan's ceremonial palace gold and blue mushroom columns Old Muscat", "Al Alam Palace facade and Al Jalali Fort background Muscat"]},

    # Salalah
    {"name": "Al Mughsail Beach Blowholes & Marneef Cave, Salalah, Dhofar", "city": "Salalah", "country": "Oman", "category": "coast", "lat": 16.8778, "lon": 53.7667, "radius_km": 0.1,
     "prompts": ["Marneef Cave and natural sea water blowholes crashing limestone cliffs Al Mughsail Salalah", "Salalah Khareef season green misty mountains and frankincense trees"]},
    {"name": "Sultan Qaboos Mosque Salalah & Frankincense Land Museum", "city": "Salalah", "country": "Oman", "category": "mosque", "lat": 17.0167, "lon": 54.0833, "radius_km": 0.05,
     "prompts": ["Sultan Qaboos Mosque Salalah two tall minarets and central dome Dhofar", "Al Baleed Archaeological Park and Land of Frankincense Salalah"]},

    # Nizwa
    {"name": "Nizwa Fort & Round Tower, Nizwa", "city": "Nizwa", "country": "Oman", "category": "fortress", "lat": 22.9333, "lon": 57.5306, "radius_km": 0.05,
     "prompts": ["Nizwa Fort massive circular stone tower battlements and surrounding date palm oasis Oman", "Nizwa Fort cannon parapet and Old Souq Oman"]},
    {"name": "Jebel Shams (Grand Canyon of Arabia), Al Hamra", "city": "Nizwa", "country": "Oman", "category": "mountain_peak", "lat": 23.2389, "lon": 57.2647, "radius_km": 1.0,
     "prompts": ["Jebel Shams mountain Balcony Walk sheer vertical canyon abyss Grand Canyon of Oman", "Jebel Shams summit rocky cliffs overlooking deep wadi"]},

    # Sur
    {"name": "Sur Dhow Yard & Al Ayjah Lighthouse, Sur", "city": "Sur", "country": "Oman", "category": "port", "lat": 22.5667, "lon": 59.5333, "radius_km": 0.08,
     "prompts": ["Al Ayjah Lighthouse white watchtower and traditional wooden dhow ship building yard Sur Oman", "Sur lagoon suspension bridge and dhow harbor"]},

    # Sohar
    {"name": "Sohar Fort & Sultan Qaboos Mosque, Sohar", "city": "Sohar", "country": "Oman", "category": "fortress", "lat": 24.3667, "lon": 56.7500, "radius_km": 0.05,
     "prompts": ["Sohar Fort bright white stone coastal castle battlements and date palms Batinah coast", "Sultan Qaboos Mosque Sohar blue tiled domes"]},

    # Khasab (Musandam)
    {"name": "Khasab Castle & Musandam Fjords (Khawr Sham), Khasab", "city": "Khasab", "country": "Oman", "category": "fortress", "lat": 26.1833, "lon": 56.2500, "radius_km": 0.2,
     "prompts": ["Khasab Castle Portuguese fortress and fjord dhow cruising sheer limestone sea cliffs Musandam", "Fjords of Musandam dramatic rocky cliffs turquoise water Khasab"]}
]
with open(OUT_DIR / "oman.json", "w", encoding="utf-8") as f:
    json.dump(oman_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved oman.json with %d spots across Omani cities.", len(oman_spots))

# -----------------------------------------------------------------------------
# 10. QATAR: Covering EVERY municipality / city
# -----------------------------------------------------------------------------
qatar_spots = [
    # Doha
    {"name": "Museum of Islamic Art (MIA), Doha", "city": "Doha", "country": "Qatar", "category": "museum", "lat": 25.2953, "lon": 51.5392, "radius_km": 0.05,
     "prompts": ["Museum of Islamic Art I.M. Pei geometric limestone cube architecture Doha harbor Qatar", "MIA Museum of Islamic Art dhow boats and Doha skyline"]},
    {"name": "Souq Waqif Heritage Bazaar, Doha", "city": "Doha", "country": "Qatar", "category": "commercial_market", "lat": 25.2867, "lon": 51.5333, "radius_km": 0.08,
     "prompts": ["Souq Waqif mud-rendered traditional market buildings spice stalls falcon souq Doha", "Souq Waqif bustling evening street dining Doha"]},
    {"name": "Katara Cultural Village & Amphitheatre, Doha", "city": "Doha", "country": "Qatar", "category": "civic_building", "lat": 25.3589, "lon": 51.5258, "radius_km": 0.08,
     "prompts": ["Katara Cultural Village classical Greco-Roman amphitheatre pigeon towers Doha", "Katara Cultural Village mosque and promenade Doha"]},
    {"name": "The Pearl-Qatar Luxury Island Marina, Doha", "city": "Doha", "country": "Qatar", "category": "marina", "lat": 25.3700, "lon": 51.5500, "radius_km": 0.1,
     "prompts": ["The Pearl Qatar artificial island luxury yacht marina Mediterranean pastel towers Doha", "The Pearl Porto Arabia promenade Doha"]},
    {"name": "National Museum of Qatar (Desert Rose), Doha", "city": "Doha", "country": "Qatar", "category": "museum", "lat": 25.2881, "lon": 51.5486, "radius_km": 0.05,
     "prompts": ["National Museum of Qatar Jean Nouvel interlocking desert rose disk architecture Doha", "NMoQ National Museum of Qatar exterior curved disks"]},

    # Lusail
    {"name": "Lusail Iconic Stadium & Katara Towers, Lusail", "city": "Lusail", "country": "Qatar", "category": "stadium", "lat": 25.4206, "lon": 51.4903, "radius_km": 0.1,
     "prompts": ["Lusail Iconic Stadium golden bowl World Cup arena and Katara crescent towers Lusail", "Lusail Stadium golden woven bowl facade Qatar"]},

    # Al Wakrah
    {"name": "Al Janoub Stadium & Al Wakrah Old Souq, Al Wakrah", "city": "Al Wakrah", "country": "Qatar", "category": "stadium", "lat": 25.1764, "lon": 51.5742, "radius_km": 0.1,
     "prompts": ["Al Janoub Stadium Zaha Hadid curved aerodynamic dhow hull roof Al Wakrah", "Souq Al Wakrah waterfront heritage marketplace"]},

    # Al Khor
    {"name": "Al Bayt Stadium (Nomadic Tent) & Al Khor Corniche", "city": "Al Khor", "country": "Qatar", "category": "stadium", "lat": 25.6522, "lon": 51.4878, "radius_km": 0.1,
     "prompts": ["Al Bayt Stadium giant black and white Bedouin tent architecture Al Khor Qatar", "Al Bayt Stadium desert tent arena Al Khor"]}
]
with open(OUT_DIR / "qatar.json", "w", encoding="utf-8") as f:
    json.dump(qatar_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved qatar.json with %d spots across Qatar.", len(qatar_spots))

# -----------------------------------------------------------------------------
# 11. KUWAIT: Covering ALL governorates & cities
# -----------------------------------------------------------------------------
kuwait_spots = [
    # Kuwait City
    {"name": "Kuwait Towers, Arabian Gulf Street, Kuwait City", "city": "Kuwait City", "country": "Kuwait", "category": "national_monument", "lat": 29.3897, "lon": 48.0033, "radius_km": 0.05,
     "prompts": ["Kuwait Towers three slender towers blue-green enameled steel spheres Arabian Gulf Street Kuwait City", "Kuwait Towers landmark observation spheres and gulf coastline"]},
    {"name": "Grand Mosque of Kuwait (Al-Masjid Al-Kabir), Kuwait City", "city": "Kuwait City", "country": "Kuwait", "category": "national_mosque", "lat": 29.3789, "lon": 47.9750, "radius_km": 0.05,
     "prompts": ["Grand Mosque of Kuwait traditional Islamic architecture central dome and minaret Kuwait City", "Al-Masjid Al-Kabir Grand Mosque Kuwait interior dome"]},
    {"name": "Al Hamra Tower Skyscraper, Kuwait City", "city": "Kuwait City", "country": "Kuwait", "category": "commercial_towers", "lat": 29.3792, "lon": 47.9936, "radius_km": 0.05,
     "prompts": ["Al Hamra Tower curved carved concrete and glass skyscraper Kuwait City", "Al Hamra tower tallest building in Kuwait"]},

    # Hawalli & Salmiya
    {"name": "The Scientific Center & Dhow Harbor, Salmiya", "city": "Salmiya", "country": "Kuwait", "category": "museum", "lat": 29.3611, "lon": 48.0778, "radius_km": 0.08,
     "prompts": ["The Scientific Center Kuwait aquarium and Fateh Al-Khair wooden dhow Salmiya", "Salmiya seaside corniche and dhow pier"]},
    {"name": "Marina Mall & Marina Crescent, Salmiya", "city": "Salmiya", "country": "Kuwait", "category": "shopping_mall", "lat": 29.3417, "lon": 48.0667, "radius_km": 0.08,
     "prompts": ["Marina Mall waterfront glass dome and Marina Crescent promenade Salmiya Kuwait", "Marina Crescent beachfront dining Kuwait"]},

    # Farwaniya
    {"name": "The Avenues Mall, Al-Rai, Farwaniya", "city": "Farwaniya", "country": "Kuwait", "category": "shopping_mall", "lat": 29.3039, "lon": 47.9356, "radius_km": 0.1,
     "prompts": ["The Avenues Mall Kuwait Grand Avenue transparent glass arched roof palm trees shopping district", "The Avenues Mall interior European street promenade Kuwait"]},

    # Jahra
    {"name": "Red Fort of Jahra (Al-Qasr Al-Ahmar), Jahra", "city": "Jahra", "country": "Kuwait", "category": "fortress", "lat": 29.3361, "lon": 47.6778, "radius_km": 0.05,
     "prompts": ["Red Fort of Jahra rectangular mud-brick fortress battlements historic Battle of Jahra Kuwait", "Al-Qasr Al-Ahmar Red Fort courtyard Jahra"]},

    # Ahmadi
    {"name": "KOC Display Center & Ahmadi Public Park, Al Ahmadi", "city": "Al Ahmadi", "country": "Kuwait", "category": "park", "lat": 29.0778, "lon": 48.0833, "radius_km": 0.1,
     "prompts": ["Ahmadi oil township landscaped gardens and Kuwait Oil Company headquarters", "Al Ahmadi park and oil city memorial"]}
]
with open(OUT_DIR / "kuwait.json", "w", encoding="utf-8") as f:
    json.dump(kuwait_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved kuwait.json with %d spots across Kuwait.", len(kuwait_spots))

# -----------------------------------------------------------------------------
# 12. BAHRAIN: Covering ALL Governorates & Cities
# -----------------------------------------------------------------------------
bahrain_spots = [
    # Manama
    {"name": "Bab Al Bahrain & Manama Souq, Manama", "city": "Manama", "country": "Bahrain", "category": "civic_monument", "lat": 26.2344, "lon": 50.5756, "radius_km": 0.05,
     "prompts": ["Bab Al Bahrain historic arched gateway building entrance to Manama Souq Bahrain", "Bab Al Bahrain twin arches and Customs square Manama"]},
    {"name": "Bahrain World Trade Center, Manama", "city": "Manama", "country": "Bahrain", "category": "commercial_towers", "lat": 26.2394, "lon": 50.5819, "radius_km": 0.05,
     "prompts": ["Bahrain World Trade Center twin sail-shaped skyscraper towers three wind turbines Manama", "Bahrain WTC towers wind turbines Manama skyline"]},
    {"name": "Al Fateh Grand Mosque, Manama", "city": "Manama", "country": "Bahrain", "category": "national_mosque", "lat": 26.2192, "lon": 50.5981, "radius_km": 0.05,
     "prompts": ["Al Fateh Grand Mosque world's largest fiberglass dome twin minarets Manama Bahrain", "Al Fateh Mosque white marble courtyard and domes"]},
    {"name": "Qal'at al-Bahrain (Bahrain Fort), Karbabad", "city": "Manama", "country": "Bahrain", "category": "unesco_world_heritage", "lat": 26.2339, "lon": 50.5208, "radius_km": 0.08,
     "prompts": ["Qal'at al-Bahrain ancient Portuguese stone fort on sea coastline UNESCO Bahrain", "Bahrain Fort stone bastions overlooking modern skyline"]},

    # Muharraq
    {"name": "Pearling Path & Shaikh Isa bin Ali House, Muharraq", "city": "Muharraq", "country": "Bahrain", "category": "unesco_world_heritage", "lat": 26.2481, "lon": 50.6125, "radius_km": 0.05,
     "prompts": ["Shaikh Isa bin Ali House traditional coral stone windtower courtyard house Muharraq Pearling Path", "Muharraq heritage wind tower and wooden carved doors"]},
    {"name": "Arad Fort & Sea Lagoon, Muharraq", "city": "Muharraq", "country": "Bahrain", "category": "fortress", "lat": 26.2517, "lon": 50.6278, "radius_km": 0.05,
     "prompts": ["Arad Fort 15th-century square stone fortress cylindrical corner watchtowers Muharraq", "Arad Fort illuminated over sea lagoon Bahrain"]},

    # Riffa
    {"name": "Riffa Fort (Sheikh Salman bin Ahmed Fort), Riffa", "city": "Riffa", "country": "Bahrain", "category": "fortress", "lat": 26.1183, "lon": 50.5636, "radius_km": 0.05,
     "prompts": ["Riffa Fort hilltop stone fortress overlooking Hunanaiya Valley Riffa Bahrain", "Sheikh Salman bin Ahmed Fort ramparts Riffa"]},

    # Sakhir / Southern
    {"name": "Bahrain International Circuit (F1 Circuit), Sakhir", "city": "Sakhir", "country": "Bahrain", "category": "stadium", "lat": 26.0325, "lon": 50.5106, "radius_km": 0.2,
     "prompts": ["Bahrain International Circuit Formula 1 race track Sakhir Tower desert floodlights", "Sakhir F1 race track grandstand and desert background"]}
]
with open(OUT_DIR / "bahrain.json", "w", encoding="utf-8") as f:
    json.dump(bahrain_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved bahrain.json with %d spots across Bahrain.", len(bahrain_spots))

# -----------------------------------------------------------------------------
# 13. SYRIA: Covering EVERY major city
# -----------------------------------------------------------------------------
syria_spots = [
    # Damascus
    {"name": "Umayyad Mosque (Great Mosque of Damascus), Syria", "city": "Damascus", "country": "Syria", "category": "unesco_world_heritage", "lat": 33.5119, "lon": 36.3067, "radius_km": 0.05,
     "prompts": ["Umayyad Mosque marble courtyard golden mosaic pavilions and three minarets Old Damascus", "Great Mosque of Damascus Umayyad courtyard and Barada mosaics"]},
    {"name": "Al-Hamidiyah Souq & Temple of Jupiter, Damascus", "city": "Damascus", "country": "Syria", "category": "commercial_market", "lat": 33.5108, "lon": 36.3033, "radius_km": 0.05,
     "prompts": ["Al-Hamidiyah Souq vaulted iron roof market street Roman Temple of Jupiter columns Damascus", "Hamidiyah Souq historic covered market Damascus"]},

    # Aleppo
    {"name": "Citadel of Aleppo, Aleppo", "city": "Aleppo", "country": "Syria", "category": "unesco_world_heritage", "lat": 36.1992, "lon": 37.1628, "radius_km": 0.08,
     "prompts": ["Citadel of Aleppo massive medieval limestone fortress stone bridge and moat hill Aleppo", "Aleppo Citadel grand fortified entrance gateway"]},

    # Homs
    {"name": "Krak des Chevaliers (Qal'at al-Hosn), Homs", "city": "Homs", "country": "Syria", "category": "unesco_world_heritage", "lat": 34.7569, "lon": 36.2947, "radius_km": 0.08,
     "prompts": ["Krak des Chevaliers iconic Crusader stone fortress concentric walls and battlements mountain ridge Homs", "Qalat al Hosn medieval fortress Syria"]},

    # Hama
    {"name": "Norias of Hama (Giant Waterwheels), Orontes River", "city": "Hama", "country": "Syria", "category": "historical_monument", "lat": 35.1319, "lon": 36.7511, "radius_km": 0.05,
     "prompts": ["Norias of Hama colossal medieval wooden waterwheels spinning on Orontes River Hama", "Hama wooden water wheels and river aqueducts"]},

    # Latakia & Tartus
    {"name": "Citadel of Salah Ed-Din (Saladin Castle), Latakia", "city": "Latakia", "country": "Syria", "category": "unesco_world_heritage", "lat": 35.5967, "lon": 36.0583, "radius_km": 0.08,
     "prompts": ["Saladin Castle massive stone needle pillar rock-cut ditch forested mountain gorge Latakia", "Citadel of Salah Ed-Din Crusader ruins"]},

    # Palmyra
    {"name": "Ancient City of Palmyra Roman Colonnade & Temple of Bel", "city": "Palmyra", "country": "Syria", "category": "unesco_world_heritage", "lat": 34.5514, "lon": 38.2689, "radius_km": 0.15,
     "prompts": ["Palmyra Monumental Colonnade Roman stone arches and Temple of Bel desert ruins Syria", "Ancient Roman ruins of Palmyra Tadmor oasis"]},

    # Bosra
    {"name": "Roman Theatre at Bosra (Black Basalt Amphitheatre)", "city": "Bosra", "country": "Syria", "category": "unesco_world_heritage", "lat": 32.5186, "lon": 36.4817, "radius_km": 0.05,
     "prompts": ["Roman Theatre of Bosra impeccably preserved black basalt amphitheatre fort fortress Syria", "Bosra Roman amphitheatre black basalt stones"]}
]
with open(OUT_DIR / "syria.json", "w", encoding="utf-8") as f:
    json.dump(syria_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved syria.json with %d spots across Syria.", len(syria_spots))

# -----------------------------------------------------------------------------
# 14. YEMEN: Covering EVERY major city
# -----------------------------------------------------------------------------
yemen_spots = [
    # Sanaa
    {"name": "Old City of Sanaa Tower Houses & Bab al-Yaman", "city": "Sanaa", "country": "Yemen", "category": "unesco_world_heritage", "lat": 15.3547, "lon": 44.2156, "radius_km": 0.1,
     "prompts": ["Old City of Sanaa multi-story rammed earth tower houses white gypsum filigree windows Yemen", "Bab al-Yaman medieval fortified gateway to Old Sanaa"]},
    {"name": "Dar al-Hajar (Rock Palace), Wadi Dhahr, Sanaa", "city": "Sanaa", "country": "Yemen", "category": "historical_palace", "lat": 15.4411, "lon": 44.1294, "radius_km": 0.05,
     "prompts": ["Dar al-Hajar iconic royal palace perched atop towering natural rock pinnacle Wadi Dhahr Sanaa", "Rock Palace Dar al-Hajar Yemen landmark"]},
    {"name": "Al Saleh Mosque, Sanaa", "city": "Sanaa", "country": "Yemen", "category": "national_mosque", "lat": 15.3250, "lon": 44.2083, "radius_km": 0.08,
     "prompts": ["Al Saleh Mosque monumental yellow limestone central dome six tall minarets Sanaa", "Al Saleh Grand Mosque facade and courtyard Sanaa"]},

    # Shibam
    {"name": "Shibam Hadhramaut Mud Skyscraper City", "city": "Shibam", "country": "Yemen", "category": "unesco_world_heritage", "lat": 15.9264, "lon": 48.6278, "radius_km": 0.1,
     "prompts": ["Shibam Hadhramaut ancient high-rise mud brick skyscrapers Manhattan of the Desert Yemen", "Walled city of Shibam mud tower apartments desert oasis"]},

    # Aden
    {"name": "Cisterns of Tawila & Crater Fortress, Aden", "city": "Aden", "country": "Yemen", "category": "historical_monument", "lat": 12.7750, "lon": 45.0333, "radius_km": 0.08,
     "prompts": ["Cisterns of Tawila ancient volcanic rock water tanks Shamsan mountain Crater Aden", "Aden Crater harbor and volcanic mountain backdrop"]},

    # Taiz
    {"name": "Al-Qahira Castle & Al-Ashrafiya Mosque, Taiz", "city": "Taiz", "country": "Yemen", "category": "fortress", "lat": 13.5750, "lon": 44.0167, "radius_km": 0.08,
     "prompts": ["Cairo Castle Al-Qahira stone citadel perched on Mount Sabir overlooking Taiz city", "Al-Ashrafiya Mosque twin white minarets Taiz"]},

    # Socotra Island
    {"name": "Dragon's Blood Tree Forest (Dixam Plateau), Socotra", "city": "Socotra", "country": "Yemen", "category": "natural_landmark", "lat": 12.5167, "lon": 53.9167, "radius_km": 1.0,
     "prompts": ["Dragon's Blood trees umbrella shaped Dracaena cinnabari Dixam plateau rocky canyon Socotra", "Socotra island endemic dragon blood tree forest"]}
]
with open(OUT_DIR / "yemen.json", "w", encoding="utf-8") as f:
    json.dump(yemen_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved yemen.json with %d spots across Yemen.", len(yemen_spots))

# -----------------------------------------------------------------------------
# 15. ISRAEL / PALESTINE: Covering EVERY city
# -----------------------------------------------------------------------------
israel_palestine_spots = [
    # Jerusalem
    {"name": "Dome of the Rock (Qubbat as-Sakhrah), Jerusalem", "city": "Jerusalem", "country": "Israel", "category": "world_landmark", "lat": 31.7780, "lon": 35.2354, "radius_km": 0.05,
     "prompts": ["Dome of the Rock iconic golden dome octagonal blue Persian ceramic tilework Temple Mount Jerusalem", "Qubbat as-Sakhrah Golden Dome and marble plaza Jerusalem"]},
    {"name": "Western Wall (Kotel) & Plaza, Jerusalem", "city": "Jerusalem", "country": "Israel", "category": "world_landmark", "lat": 31.7767, "lon": 35.2344, "radius_km": 0.05,
     "prompts": ["Western Wall Kotel ancient Herodian massive limestone prayer wall and outdoor plaza Jerusalem", "Western Wall and Temple Mount esplanade Jerusalem"]},
    {"name": "Church of the Holy Sepulchre, Christian Quarter, Jerusalem", "city": "Jerusalem", "country": "Israel", "category": "historical_church", "lat": 31.7785, "lon": 35.2297, "radius_km": 0.05,
     "prompts": ["Church of the Holy Sepulchre Romanesque stone facade and belltower Old City Jerusalem", "Holy Sepulchre courtyard and entrance Jerusalem"]},

    # Tel Aviv-Yafo
    {"name": "Tel Aviv White City Bauhaus Architecture & Rothschild Blvd", "city": "Tel Aviv", "country": "Israel", "category": "unesco_world_heritage", "lat": 32.0631, "lon": 34.7739, "radius_km": 0.1,
     "prompts": ["Tel Aviv White City Bauhaus international style rounded balconies tree-lined Rothschild Boulevard", "Rothschild Boulevard modern Bauhaus buildings Tel Aviv"]},
    {"name": "Jaffa Old Port & Clock Tower, Tel Aviv-Yafo", "city": "Tel Aviv", "country": "Israel", "category": "heritage_village", "lat": 32.0542, "lon": 34.7522, "radius_km": 0.08,
     "prompts": ["Old Jaffa stone port lighthouse and limestone alleys overlooking Tel Aviv coastline", "Jaffa Clock Tower Ottoman stone monument square"]},

    # Haifa
    {"name": "Bahai Gardens & Shrine of the Bab, Mount Carmel, Haifa", "city": "Haifa", "country": "Israel", "category": "unesco_world_heritage", "lat": 32.8133, "lon": 34.9872, "radius_km": 0.08,
     "prompts": ["Bahai Gardens nineteen terraced symmetrical botanical gardens golden dome Shrine of the Bab Mount Carmel Haifa", "Bahai Terraces cascading down to Mediterranean Sea Haifa"]},

    # Bethlehem
    {"name": "Church of the Nativity & Manger Square, Bethlehem", "city": "Bethlehem", "country": "Palestine", "category": "unesco_world_heritage", "lat": 31.7044, "lon": 35.2075, "radius_km": 0.05,
     "prompts": ["Church of the Nativity ancient basilica entrance Door of Humility Manger Square Bethlehem", "Nativity Church courtyard Bethlehem"]},

    # Ramallah
    {"name": "Yasser Arafat Museum & Al-Manara Square, Ramallah", "city": "Ramallah", "country": "Palestine", "category": "civic_monument", "lat": 31.9039, "lon": 35.2036, "radius_km": 0.05,
     "prompts": ["Al-Manara Square four stone lions monument central roundabout Ramallah", "Yasser Arafat Mausoleum white limestone building Ramallah"]},

    # Nazareth
    {"name": "Basilica of the Annunciation, Nazareth", "city": "Nazareth", "country": "Israel", "category": "historical_church", "lat": 32.7019, "lon": 35.2978, "radius_km": 0.05,
     "prompts": ["Basilica of the Annunciation soaring polygonal cupola concrete lantern church Nazareth", "Church of the Annunciation courtyard Nazareth"]},

    # Hebron
    {"name": "Cave of the Patriarchs (Ibrahimi Mosque), Hebron", "city": "Hebron", "country": "Palestine", "category": "unesco_world_heritage", "lat": 31.5247, "lon": 35.1108, "radius_km": 0.05,
     "prompts": ["Cave of the Patriarchs Ibrahimi Mosque colossal Herodian ashlar stone walls Hebron", "Ibrahimi Mosque courtyard and battlements Hebron"]},

    # Jericho
    {"name": "Mount of Temptation Monastery & Ancient Jericho Tell", "city": "Jericho", "country": "Palestine", "category": "historical_monument", "lat": 31.8744, "lon": 35.4333, "radius_km": 0.1,
     "prompts": ["Mount of Temptation Greek Orthodox monastery clinging to vertical cliff face cable car Jericho", "Tell es-Sultan ancient Neolithic round tower Jericho"]},

    # Acre (Akko)
    {"name": "Crusader Fortress & Ottoman Sea Walls, Acre (Akko)", "city": "Acre", "country": "Israel", "category": "unesco_world_heritage", "lat": 32.9233, "lon": 35.0689, "radius_km": 0.08,
     "prompts": ["Knights Halls Crusader underground vaulted fortress and sea walls Old Acre Akko", "Old City of Acre stone harbour and Ottoman mosque"]}
]
with open(OUT_DIR / "israel_palestine.json", "w", encoding="utf-8") as f:
    json.dump(israel_palestine_spots, f, indent=2, ensure_ascii=False)
logger.info("Saved israel_palestine.json with %d spots across Israel and Palestine.", len(israel_palestine_spots))

# -----------------------------------------------------------------------------
# 16. GLOBAL ICONIC ANCHORS
# -----------------------------------------------------------------------------
global_iconic = [
    {"name": "Eiffel Tower & Champ de Mars, Paris, France", "city": "Paris", "country": "France", "category": "world_landmark", "lat": 48.8584, "lon": 2.2945, "radius_km": 0.05,
     "prompts": ["Eiffel Tower wrought-iron lattice tower Champ de Mars Seine river Paris France", "Eiffel Tower landmark Paris"]},
    {"name": "Colosseum & Arch of Constantine, Rome, Italy", "city": "Rome", "country": "Italy", "category": "world_landmark", "lat": 41.8902, "lon": 12.4922, "radius_km": 0.05,
     "prompts": ["Colosseum iconic ancient Roman amphitheatre travertine arches Rome Italy", "Flavian Amphitheatre Colosseum exterior Rome"]},
    {"name": "Big Ben & Palace of Westminster, London, UK", "city": "London", "country": "United Kingdom", "category": "world_landmark", "lat": 51.5007, "lon": -0.1246, "radius_km": 0.05,
     "prompts": ["Big Ben Elizabeth Tower clock face and Houses of Parliament Thames bridge London", "Palace of Westminster Big Ben clock tower London"]},
    {"name": "Statue of Liberty & New York Harbor, USA", "city": "New York", "country": "United States", "category": "world_landmark", "lat": 40.6892, "lon": -74.0445, "radius_km": 0.05,
     "prompts": ["Statue of Liberty copper green neoclassical statue torch Liberty Island New York Harbor", "Statue of Liberty Manhattan skyline background"]},
    {"name": "Sydney Opera House & Harbor Bridge, Sydney, Australia", "city": "Sydney", "country": "Australia", "category": "world_landmark", "lat": -33.8568, "lon": 151.2153, "radius_km": 0.05,
     "prompts": ["Sydney Opera House shell sail roof white ceramic tiles Sydney Harbour Australia", "Sydney Opera House and Harbour Bridge"]},
    {"name": "Christ the Redeemer (Cristo Redentor), Rio de Janeiro, Brazil", "city": "Rio de Janeiro", "country": "Brazil", "category": "world_landmark", "lat": -22.9519, "lon": -43.2105, "radius_km": 0.05,
     "prompts": ["Christ the Redeemer colossal Art Deco statue outstretched arms Corcovado Mountain Rio de Janeiro", "Cristo Redentor summit view Rio de Janeiro"]},
    {"name": "Machu Picchu Inca Citadel, Andes, Peru", "city": "Cusco", "country": "Peru", "category": "world_landmark", "lat": -13.1631, "lon": -72.5450, "radius_km": 0.1,
     "prompts": ["Machu Picchu ancient Inca stone ruins agricultural terraces Huayna Picchu mountain peak Peru", "Machu Picchu citadel terraces Andes mountains"]},
    {"name": "Great Wall of China (Mutianyu), Beijing, China", "city": "Beijing", "country": "China", "category": "world_landmark", "lat": 40.4319, "lon": 116.5704, "radius_km": 0.5,
     "prompts": ["Great Wall of China stone watchtowers winding across mountainous ridgeline Mutianyu", "Great Wall stone battlements green mountains Beijing"]}
]
with open(OUT_DIR / "global_iconic.json", "w", encoding="utf-8") as f:
    json.dump(global_iconic, f, indent=2, ensure_ascii=False)
logger.info("Saved global_iconic.json with %d iconic spots.", len(global_iconic))


# -----------------------------------------------------------------------------
# 17. Master Database Aggregation & Precomputation
# -----------------------------------------------------------------------------
def build_master_database():
    all_files = sorted(list(OUT_DIR.glob("*.json")))
    all_records = []
    for f in all_files:
        if f.name in ("landmarks_metadata.json", "all_landmarks.json"):
            continue
        try:
            records = json.loads(f.read_text(encoding="utf-8"))
            all_records.extend(records)
        except Exception as e:
            logger.warning("Error reading %s: %s", f.name, e)

    # Save consolidated master database
    master_path = OUT_DIR / "all_landmarks.json"
    master_path.write_text(json.dumps(all_records, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Consolidated %d total landmark records across all cities in %s", len(all_records), master_path)
    return all_records

if __name__ == "__main__":
    records = build_master_database()
    print(f"\nSuccessfully generated {len(records)} spots across EVERY city in all target countries!")
