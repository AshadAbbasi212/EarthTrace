"""Generate comprehensive multi-city landmark datasets for Pakistan and prioritized regional countries.
Each city has multiple distinct spots (with Islamabad having 100 spots), accurate coordinates, and visual CLIP prompts.
"""
import json
from pathlib import Path

OUT_DIR = Path("data/landmarks")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# 1. PAKISTAN (Islamabad 100 spots + Lahore + Karachi + Rawalpindi + all cities)
# --------------------------------------------------------------------------
islamabad_spots = [
    # 1-10: Iconic National & Religious Landmarks
    {"name": "Faisal Mosque, Islamabad", "city": "Islamabad", "category": "national_mosque", "lat": 33.7296, "lon": 73.0372, "radius_km": 0.05,
     "prompts": ["Faisal Mosque white tent architectural minarets Margalla foothills Islamabad", "Faisal Mosque courtyard and white marble minarets Islamabad"]},
    {"name": "Pakistan Monument, Shakarparian, Islamabad", "city": "Islamabad", "category": "national_monument", "lat": 33.6934, "lon": 73.0684, "radius_km": 0.05,
     "prompts": ["Pakistan Monument blooming petal granite architecture Shakarparian Islamabad", "Pakistan Monument petal dome Shakarparian hills Islamabad"]},
    {"name": "Daman-e-Koh Margalla Viewpoint, Islamabad", "city": "Islamabad", "category": "viewpoint", "lat": 33.7389, "lon": 73.0583, "radius_km": 0.1,
     "prompts": ["Daman-e-Koh Margalla hills viewpoint terrace overlooking Islamabad city", "Daman-e-Koh garden terrace Margalla ridge view Islamabad"]},
    {"name": "Pir Sohawa & Monal Ridge, Margalla Hills, Islamabad", "city": "Islamabad", "category": "viewpoint", "lat": 33.7483, "lon": 73.0583, "radius_km": 0.15,
     "prompts": ["Monal restaurant terrace dining Pir Sohawa Margalla mountain ridge Islamabad", "Pir Sohawa Margalla crest viewpoint restaurant overlooking Islamabad"]},
    {"name": "Centaurus Mall & Towers, Blue Area, Islamabad", "city": "Islamabad", "category": "commercial_towers", "lat": 33.7077, "lon": 73.0503, "radius_km": 0.05,
     "prompts": ["Centaurus Mall three curved glass skyscraper towers Jinnah Avenue Islamabad", "Centaurus towers modern high-rise architecture Blue Area Islamabad"]},
    {"name": "Rawal Lake & Lake View Park, Islamabad", "city": "Islamabad", "category": "park", "lat": 33.7022, "lon": 73.1250, "radius_km": 0.2,
     "prompts": ["Rawal Lake water reservoir promenade and Lake View Park Islamabad", "Lake View Park gardens and boat jetty Rawal Dam Islamabad"]},
    {"name": "Lok Virsa Heritage Museum, Shakarparian, Islamabad", "city": "Islamabad", "category": "museum", "lat": 33.6917, "lon": 73.0708, "radius_km": 0.05,
     "prompts": ["Lok Virsa heritage museum traditional ethnic architecture Shakarparian Islamabad", "Lok Virsa National Heritage Museum courtyard Islamabad"]},
    {"name": "Saidpur Heritage Village, Margalla Foothills, Islamabad", "city": "Islamabad", "category": "heritage_village", "lat": 33.7417, "lon": 73.0686, "radius_km": 0.08,
     "prompts": ["Saidpur historic stone village restaurants and Hindu temple Margalla foothills Islamabad", "Saidpur village courtyard and traditional brick alleyways Islamabad"]},
    {"name": "Fatima Jinnah Park (F-9 Park), Islamabad", "city": "Islamabad", "category": "park", "lat": 33.7000, "lon": 73.0167, "radius_km": 0.3,
     "prompts": ["Fatima Jinnah Park F-9 solar canopy grand promenade pathways Islamabad", "F-9 Park expansive lawns walking trails and recreational pavilions Islamabad"]},
    {"name": "Parliament House & Constitution Avenue, Islamabad", "city": "Islamabad", "category": "government", "lat": 33.7314, "lon": 73.0967, "radius_km": 0.05,
     "prompts": ["Parliament House white facade Constitution Avenue Islamabad", "Majlis-e-Shoora Parliament building and Constitution Avenue Islamabad"]},

    # 11-20: State Institutions, Courts & Diplomatic Enclave
    {"name": "Supreme Court of Pakistan, Islamabad", "city": "Islamabad", "category": "government", "lat": 33.7303, "lon": 73.0983, "radius_km": 0.05,
     "prompts": ["Supreme Court of Pakistan white marble neoclassical building Constitution Avenue Islamabad", "Supreme Court courthouse portico Islamabad"]},
    {"name": "President House (Aiwan-e-Sadr), Islamabad", "city": "Islamabad", "category": "government", "lat": 33.7342, "lon": 73.1000, "radius_km": 0.08,
     "prompts": ["Aiwan-e-Sadr President House grand white palace Constitution Avenue Islamabad", "President House ceremonial gates and lawns Islamabad"]},
    {"name": "Prime Minister Secretariat, Islamabad", "city": "Islamabad", "category": "government", "lat": 33.7375, "lon": 73.1017, "radius_km": 0.08,
     "prompts": ["Prime Minister Secretariat executive building Red Zone Constitution Avenue Islamabad", "PM Secretariat complex Islamabad"]},
    {"name": "Islamabad High Court IHC Building, G-5, Islamabad", "city": "Islamabad", "category": "government", "lat": 33.7220, "lon": 73.0880, "radius_km": 0.05,
     "prompts": ["Islamabad High Court red-and-white courthouse building Sector G-5 Islamabad", "IHC High Court of Islamabad main building"]},
    {"name": "National Art Gallery NAG, F-5, Islamabad", "city": "Islamabad", "category": "museum", "lat": 33.7289, "lon": 73.0867, "radius_km": 0.05,
     "prompts": ["National Art Gallery modern brick-and-terracotta cultural building Sector F-5 Islamabad", "NAG National Art Gallery exhibition halls Islamabad"]},
    {"name": "Pakistan Museum of Natural History PMNH, Shakarparian, Islamabad", "city": "Islamabad", "category": "museum", "lat": 33.6939, "lon": 73.0722, "radius_km": 0.05,
     "prompts": ["Pakistan Museum of Natural History blue whale skeleton Shakarparian Islamabad", "PMNH Natural History Museum building Islamabad"]},
    {"name": "Convention Centre Islamabad, Club Road", "city": "Islamabad", "category": "civic_building", "lat": 33.7139, "lon": 73.1028, "radius_km": 0.08,
     "prompts": ["Jinnah Convention Centre grand dome architecture Club Road Islamabad", "Convention Centre Islamabad entrance and flagpoles"]},
    {"name": "Diplomatic Enclave Gate 1 & Chancery Row, Islamabad", "city": "Islamabad", "category": "embassy_zone", "lat": 33.7214, "lon": 73.1111, "radius_km": 0.2,
     "prompts": ["Diplomatic Enclave security gate chanceries Sector G-5 Islamabad", "Diplomatic Enclave embassy boulevard Islamabad"]},
    {"name": "US Embassy Compound, Diplomatic Enclave, Islamabad", "city": "Islamabad", "category": "embassy", "lat": 33.7225, "lon": 73.1186, "radius_km": 0.1,
     "prompts": ["United States Embassy compound modern chancery Diplomatic Enclave Islamabad", "US Embassy diplomatic chancery buildings Islamabad"]},
    {"name": "British High Commission, Diplomatic Enclave, Islamabad", "city": "Islamabad", "category": "embassy", "lat": 33.7258, "lon": 73.1147, "radius_km": 0.08,
     "prompts": ["British High Commission chancery gates Diplomatic Enclave Islamabad", "British High Commission diplomatic building Islamabad"]},

    # 21-30: Universities & Academic Campuses
    {"name": "Quaid-e-Azam University campus academic buildings, Islamabad", "city": "Islamabad", "category": "university_campus", "lat": 33.7489, "lon": 73.1369, "radius_km": 0.2,
     "prompts": ["Quaid-e-Azam University campus academic buildings faculty blocks Islamabad", "QAU Islamabad campus faculty buildings Margalla foothills"]},
    {"name": "NUST H-12 Campus Main Library & Gate, Islamabad", "city": "Islamabad", "category": "university_campus", "lat": 33.6425, "lon": 72.9904, "radius_km": 0.2,
     "prompts": ["National University of Sciences and Technology NUST H-12 campus central library Islamabad", "NUST H-12 main university gate and academic squares Islamabad"]},
    {"name": "FAST-NUCES Islamabad Campus, H-9", "city": "Islamabad", "category": "university_campus", "lat": 33.6567, "lon": 73.0167, "radius_km": 0.1,
     "prompts": ["FAST National University of Computer and Emerging Sciences H-9 campus Islamabad", "FAST-NUCES Islamabad academic building and lawns"]},
    {"name": "COMSATS University Islamabad Campus, Park Road, Chak Shahzad", "city": "Islamabad", "category": "university_campus", "lat": 33.6517, "lon": 73.1561, "radius_km": 0.15,
     "prompts": ["COMSATS University Islamabad campus faculty blocks Park Road Chak Shahzad", "COMSATS Institute of Information Technology main campus Islamabad"]},
    {"name": "International Islamic University IIUI New Campus, H-10, Islamabad", "city": "Islamabad", "category": "university_campus", "lat": 33.6583, "lon": 73.0250, "radius_km": 0.2,
     "prompts": ["International Islamic University IIUI grand mosque and academic blocks Sector H-10 Islamabad", "IIUI H-10 university campus buildings Islamabad"]},
    {"name": "National Defence University NDU, E-9, Islamabad", "city": "Islamabad", "category": "university_campus", "lat": 33.7250, "lon": 73.0250, "radius_km": 0.1,
     "prompts": ["National Defence University NDU main military academic block Sector E-9 Islamabad", "NDU Islamabad campus entrance Margalla foothills"]},
    {"name": "Air University Islamabad Campus, PAF Complex E-9", "city": "Islamabad", "category": "university_campus", "lat": 33.7167, "lon": 73.0278, "radius_km": 0.08,
     "prompts": ["Air University main academic building Sector E-9 PAF Complex Islamabad", "Air University campus square Islamabad"]},
    {"name": "Bahria University Islamabad Campus, E-8", "city": "Islamabad", "category": "university_campus", "lat": 33.7222, "lon": 73.0361, "radius_km": 0.08,
     "prompts": ["Bahria University campus modern building Naval Complex Sector E-8 Islamabad", "Bahria University Islamabad gate and blocks"]},
    {"name": "Allama Iqbal Open University AIOU Central Campus, H-8, Islamabad", "city": "Islamabad", "category": "university_campus", "lat": 33.6806, "lon": 73.0611, "radius_km": 0.1,
     "prompts": ["Allama Iqbal Open University AIOU central academic block Sector H-8 Islamabad", "AIOU main campus administration building Islamabad"]},
    {"name": "Higher Education Commission HEC Headquarters, H-9, Islamabad", "city": "Islamabad", "category": "civic_building", "lat": 33.6694, "lon": 73.0472, "radius_km": 0.05,
     "prompts": ["Higher Education Commission HEC headquarters glass building Sector H-9 Islamabad", "HEC head office building Islamabad"]},

    # 31-40: Commercial Hubs, Sectors & Shopping Centers
    {"name": "Blue Area Jinnah Avenue Commercial Strip, Islamabad", "city": "Islamabad", "category": "commercial_district", "lat": 33.7125, "lon": 73.0650, "radius_km": 0.2,
     "prompts": ["Blue Area Jinnah Avenue commercial boulevard skyscrapers Islamabad", "Blue Area financial and retail high-rises Islamabad"]},
    {"name": "Saudi Pak Tower, Blue Area, Islamabad", "city": "Islamabad", "category": "commercial_towers", "lat": 33.7128, "lon": 73.0628, "radius_km": 0.05,
     "prompts": ["Saudi Pak Tower brutalist Islamic modern high-rise Blue Area Jinnah Avenue Islamabad", "Saudi Pak Tower office building Islamabad"]},
    {"name": "Islamabad Stock Exchange ISE Towers, Blue Area", "city": "Islamabad", "category": "commercial_towers", "lat": 33.7139, "lon": 73.0656, "radius_km": 0.05,
     "prompts": ["Islamabad Stock Exchange ISE Towers twin glass skyscrapers Blue Area Islamabad", "ISE Towers financial center Jinnah Avenue Islamabad"]},
    {"name": "Telecom Tower, Blue Area, Islamabad", "city": "Islamabad", "category": "commercial_towers", "lat": 33.7153, "lon": 73.0694, "radius_km": 0.05,
     "prompts": ["PTCL Telecom Tower tall curved office building Blue Area Islamabad", "Telecom Tower modern glass facade Jinnah Avenue Islamabad"]},
    {"name": "Safa Gold Mall, F-7 Markaz (Jinnah Super), Islamabad", "city": "Islamabad", "category": "shopping_mall", "lat": 33.7225, "lon": 73.0567, "radius_km": 0.05,
     "prompts": ["Safa Gold Mall multistory shopping center F-7 Markaz Jinnah Super Islamabad", "Safa Gold Mall retail entrance Sector F-7 Islamabad"]},
    {"name": "Giga Mall & World Trade Center, DHA Phase 2, Islamabad", "city": "Islamabad", "category": "shopping_mall", "lat": 33.5283, "lon": 73.1617, "radius_km": 0.1,
     "prompts": ["Giga Mall World Trade Center grand shopping atrium GT Road DHA Phase 2 Islamabad", "Giga Mall hypermarket and retail towers Islamabad"]},
    {"name": "F-6 Super Market Commercial Square, Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.7294, "lon": 73.0767, "radius_km": 0.08,
     "prompts": ["F-6 Super Market open commercial square bookshops and cafes Sector F-6 Islamabad", "Super Market F-6 Islamabad retail plaza"]},
    {"name": "Kohsar Market, Sector F-6/3, Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.7336, "lon": 73.0728, "radius_km": 0.05,
     "prompts": ["Kohsar Market outdoor upscale dining cafes and gourmet stores Sector F-6 Islamabad", "Kohsar Market restaurant patio Sector F-6/3 Islamabad"]},
    {"name": "F-7 Jinnah Super Market Roundabout & Plaza, Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.7208, "lon": 73.0556, "radius_km": 0.08,
     "prompts": ["Jinnah Super Market circular commercial plaza Sector F-7 Islamabad", "F-7 Markaz Jinnah Super shops and restaurants Islamabad"]},
    {"name": "Beverly Centre, Blue Area / F-6, Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.7189, "lon": 73.0689, "radius_km": 0.05,
     "prompts": ["Beverly Centre trendy restaurants and retail shops Nazim-ud-din Road Islamabad", "Beverly Centre commercial arcade Sector F-6 Islamabad"]},

    # 41-50: Sector Markazes & Commercial Hubs
    {"name": "F-8 Markaz (Ayub Market), Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.7111, "lon": 73.0389, "radius_km": 0.08,
     "prompts": ["F-8 Markaz commercial square shops restaurants Sector F-8 Islamabad", "Ayub Market F-8 Markaz retail plaza Islamabad"]},
    {"name": "F-10 Markaz (Sumbal Market), Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.6972, "lon": 73.0125, "radius_km": 0.08,
     "prompts": ["F-10 Markaz buzzing commercial square retail towers Sector F-10 Islamabad", "F-10 Markaz round shopping plaza Islamabad"]},
    {"name": "F-11 Markaz (Fehmida Market), Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.6847, "lon": 72.9889, "radius_km": 0.08,
     "prompts": ["F-11 Markaz modern high-rise apartments and shopping arcade Sector F-11 Islamabad", "F-11 Markaz commercial center Islamabad"]},
    {"name": "G-9 Markaz (Karachi Company), Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.6903, "lon": 73.0306, "radius_km": 0.1,
     "prompts": ["G-9 Karachi Company bustling commercial marketplace and bus terminal Sector G-9 Islamabad", "Karachi Company G-9 Markaz bazaar Islamabad"]},
    {"name": "G-11 Markaz, Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.6736, "lon": 72.9986, "radius_km": 0.08,
     "prompts": ["G-11 Markaz commercial plaza residential towers Sector G-11 Islamabad", "G-11 Markaz shopping arcade Islamabad"]},
    {"name": "I-8 Markaz (Tipu Market), Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.6681, "lon": 73.0764, "radius_km": 0.08,
     "prompts": ["I-8 Markaz pedestrian food street and shopping center Sector I-8 Islamabad", "I-8 Markaz commercial avenue Islamabad"]},
    {"name": "I-9 Markaz & Industrial Area, Islamabad", "city": "Islamabad", "category": "industrial_district", "lat": 33.6556, "lon": 73.0611, "radius_km": 0.15,
     "prompts": ["Sector I-9 Industrial Area commercial warehouses and factories Islamabad", "I-9 Markaz commercial zone Islamabad"]},
    {"name": "I-10 Markaz, Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.6444, "lon": 73.0389, "radius_km": 0.08,
     "prompts": ["I-10 Markaz commercial marketplace retail stores Sector I-10 Islamabad", "I-10 Markaz shopping square Islamabad"]},
    {"name": "G-8 Markaz (Babri Market), Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.7000, "lon": 73.0417, "radius_km": 0.08,
     "prompts": ["G-8 Markaz commercial plaza shops near PIMS Hospital Sector G-8 Islamabad", "G-8 Markaz market Islamabad"]},
    {"name": "G-7 Markaz (Sitara Market), Islamabad", "city": "Islamabad", "category": "commercial_market", "lat": 33.7069, "lon": 73.0611, "radius_km": 0.08,
     "prompts": ["Sitara Market Sector G-7 commercial shops and municipal offices Islamabad", "G-7 Markaz Sitara Market plaza Islamabad"]},

    # 51-60: Luxury Hospitality, Clubs & Golf Courses
    {"name": "Serena Hotel Islamabad, Club Road", "city": "Islamabad", "category": "luxury_hotel", "lat": 33.7194, "lon": 73.1028, "radius_km": 0.05,
     "prompts": ["Islamabad Serena Hotel traditional Islamic palace architecture and water gardens", "Serena Hotel luxury courtyard and banquet lawns Islamabad"]},
    {"name": "Islamabad Marriott Hotel, Sector F-5/1", "city": "Islamabad", "category": "luxury_hotel", "lat": 33.7292, "lon": 73.0903, "radius_km": 0.05,
     "prompts": ["Marriott Hotel Islamabad white facade near Constitution Avenue Sector F-5", "Islamabad Marriott Hotel entrance driveway and security gates"]},
    {"name": "Islamabad Club & Polo Ground, Shakarparian", "city": "Islamabad", "category": "sports_club", "lat": 33.7083, "lon": 73.1056, "radius_km": 0.15,
     "prompts": ["Islamabad Club polo ground clubhouse and manicured green lawns Murree Road Islamabad", "Islamabad Club equestrian pavilion and sports facilities"]},
    {"name": "Islamabad Golf Club, Shakarparian / Rawal Lake", "city": "Islamabad", "category": "sports_club", "lat": 33.6972, "lon": 73.0917, "radius_km": 0.2,
     "prompts": ["Islamabad Golf Club 18-hole fairway rolling hills and lake view Shakarparian Islamabad", "Islamabad Golf Club fairways and clubhouse"]},
    {"name": "Gun & Country Club Islamabad, Shakarparian", "city": "Islamabad", "category": "sports_club", "lat": 33.7000, "lon": 73.0778, "radius_km": 0.1,
     "prompts": ["Gun and Country Club shooting range and recreational club Shakarparian Islamabad", "Gun and Country Club sporting grounds Islamabad"]},
    {"name": "Best Western Premier Hotel Islamabad, Club Road", "city": "Islamabad", "category": "hotel", "lat": 33.7150, "lon": 73.1067, "radius_km": 0.05,
     "prompts": ["Best Western Premier Hotel building Club Road near Rawal Lake Islamabad", "Best Western Hotel Islamabad entrance"]},
    {"name": "Ramada by Wyndham Islamabad, Club Road", "city": "Islamabad", "category": "hotel", "lat": 33.7111, "lon": 73.1111, "radius_km": 0.05,
     "prompts": ["Ramada Hotel Rawal Lake view Club Road Sector Islamabad", "Ramada Hotel building overlooking Rawal Dam reservoir Islamabad"]},
    {"name": "Pearl Continental PC Bhurban / Murree Gateway, Islamabad", "city": "Islamabad", "category": "luxury_hotel", "lat": 33.9556, "lon": 73.4514, "radius_km": 0.1,
     "prompts": ["Pearl Continental PC Hotel Bhurban pine tree valley and golf course Murree Hills", "PC Bhurban luxury mountain resort terrace"]},
    {"name": "Hotel Crown Plaza Islamabad, Blue Area", "city": "Islamabad", "category": "hotel", "lat": 33.7119, "lon": 73.0583, "radius_km": 0.05,
     "prompts": ["Hotel Crown Plaza high-rise building Jinnah Avenue Blue Area Islamabad", "Crown Plaza Hotel Islamabad facade"]},
    {"name": "Shelton Hotel & Guest House, F-8/3, Islamabad", "city": "Islamabad", "category": "hotel", "lat": 33.7150, "lon": 73.0450, "radius_km": 0.05,
     "prompts": ["Shelton boutique hotel and guest suites Sector F-8/3 Islamabad", "Shelton Hotel Islamabad entrance"]},

    # 61-70: Hospitals, Medical Complexes & Research Centers
    {"name": "Shifa International Hospital, H-8/4, Islamabad", "city": "Islamabad", "category": "hospital_complex", "lat": 33.6861, "lon": 73.0806, "radius_km": 0.08,
     "prompts": ["Shifa International Hospital grand medical complex red brick buildings Sector H-8/4 Islamabad", "Shifa Hospital main entrance and trauma tower Islamabad"]},
    {"name": "Pakistan Institute of Medical Sciences PIMS, G-8/3, Islamabad", "city": "Islamabad", "category": "hospital_complex", "lat": 33.7042, "lon": 73.0472, "radius_km": 0.1,
     "prompts": ["Pakistan Institute of Medical Sciences PIMS hospital campus and trauma center Sector G-8 Islamabad", "PIMS Hospital main emergency facade Islamabad"]},
    {"name": "Federal Government Polyclinic Hospital, G-6/2, Islamabad", "city": "Islamabad", "category": "hospital_complex", "lat": 33.7222, "lon": 73.0778, "radius_km": 0.05,
     "prompts": ["Polyclinic Hospital medical wards and outdoor patient department Sector G-6 Islamabad", "Federal Government Polyclinic building Islamabad"]},
    {"name": "Maroof International Hospital, F-10 Markaz, Islamabad", "city": "Islamabad", "category": "hospital_complex", "lat": 33.6944, "lon": 73.0111, "radius_km": 0.05,
     "prompts": ["Maroof International Hospital private medical facility Sector F-10 Markaz Islamabad", "Maroof Hospital glass building Islamabad"]},
    {"name": "Kulsum International Hospital, Blue Area, Islamabad", "city": "Islamabad", "category": "hospital_complex", "lat": 33.7094, "lon": 73.0528, "radius_km": 0.05,
     "prompts": ["Kulsum International Hospital tower Jinnah Avenue Blue Area Islamabad", "Kulsum Hospital facade Islamabad"]},
    {"name": "National Institute of Health NIH, Chak Shahzad, Islamabad", "city": "Islamabad", "category": "medical_research", "lat": 33.6722, "lon": 73.1389, "radius_km": 0.1,
     "prompts": ["National Institute of Health NIH research laboratories and campus Chak Shahzad Islamabad", "NIH Pakistan biomedical center Islamabad"]},
    {"name": "PAEC Nuclear Medicine Oncology & Radiotherapy NORI Hospital, G-8/3", "city": "Islamabad", "category": "hospital_complex", "lat": 33.7014, "lon": 73.0500, "radius_km": 0.05,
     "prompts": ["NORI Cancer Hospital PAEC medical facility Sector G-8/3 Islamabad", "NORI Hospital oncology tower Islamabad"]},
    {"name": "Quaid-e-Azam International Hospital QIH, Golra Mor, Islamabad", "city": "Islamabad", "category": "hospital_complex", "lat": 33.6278, "lon": 72.9667, "radius_km": 0.08,
     "prompts": ["Quaid-e-Azam International Hospital modern multi-story medical center Peshawar Road Golra Mor Islamabad", "QIH Hospital building Islamabad"]},
    {"name": "Ali Medical Centre, F-8 Markaz, Islamabad", "city": "Islamabad", "category": "hospital_complex", "lat": 33.7083, "lon": 73.0361, "radius_km": 0.05,
     "prompts": ["Ali Medical Centre private hospital building Sector F-8 Markaz Islamabad", "Ali Medical Centre entrance Islamabad"]},
    {"name": "Medicsi Hospital, F-10/4, Islamabad", "city": "Islamabad", "category": "hospital_complex", "lat": 33.6917, "lon": 73.0083, "radius_km": 0.05,
     "prompts": ["Medicsi private specialized hospital building Sector F-10/4 Islamabad", "Medicsi Hospital clinic Islamabad"]},

    # 71-80: Parks, Trails, Nature & Hiking
    {"name": "Margalla Hills Trail 3 Viewpoint, Islamabad", "city": "Islamabad", "category": "hiking_trail", "lat": 33.7444, "lon": 73.0611, "radius_km": 0.1,
     "prompts": ["Trail 3 Margalla Hills hiking track rocky ridge trail pine trees Islamabad", "Trail 3 viewpoint wooden benches overlooking Islamabad city"]},
    {"name": "Margalla Hills Trail 5 (Ghanghar Stream), Islamabad", "city": "Islamabad", "category": "hiking_trail", "lat": 33.7472, "lon": 73.0722, "radius_km": 0.1,
     "prompts": ["Trail 5 Margalla Hills natural freshwater stream rocky hiking track Islamabad", "Trail 5 trailhead picnic area and forest trail Islamabad"]},
    {"name": "Trail 2 (Daman-e-Koh to Zoo), Margalla Hills, Islamabad", "city": "Islamabad", "category": "hiking_trail", "lat": 33.7361, "lon": 73.0556, "radius_km": 0.1,
     "prompts": ["Trail 2 Margalla Hills dirt trail path winding from Marghazar to Daman-e-Koh Islamabad", "Trail 2 ridge hiking path Islamabad"]},
    {"name": "Rose & Jasmine Garden, Shakarparian, Islamabad", "city": "Islamabad", "category": "park", "lat": 33.6972, "lon": 73.0806, "radius_km": 0.08,
     "prompts": ["Rose and Jasmine Garden landscaped rose flowerbeds and walking path Shakarparian Islamabad", "Rose and Jasmine Garden seasonal flower exhibition lawns Islamabad"]},
    {"name": "Japanese Children Park, Margalla Road, Islamabad", "city": "Islamabad", "category": "park", "lat": 33.7333, "lon": 73.0611, "radius_km": 0.05,
     "prompts": ["Japanese Children Park wooden playground obstacle courses Sector F-6 Margalla Road Islamabad", "Japanese Park swings and green hillocks Islamabad"]},
    {"name": "Shah Allah Ditta Buddhist Caves, Margalla Foothills, Islamabad", "city": "Islamabad", "category": "heritage_site", "lat": 33.7194, "lon": 72.9194, "radius_km": 0.08,
     "prompts": ["Shah Allah Ditta historic Buddhist rock caves banyan trees Sadhu platform Margalla Islamabad", "Shah Allah Ditta ancient caves and freshwater spring Islamabad"]},
    {"name": "Korang River Valley & Promenade, Islamabad", "city": "Islamabad", "category": "river_valley", "lat": 33.6667, "lon": 73.1333, "radius_km": 0.15,
     "prompts": ["Korang River valley rocky stream banks and natural green basin Islamabad", "Korang riverbed crossing Chak Shahzad Islamabad"]},
    {"name": "Ankora / Simly Dam Reservoir, Islamabad", "city": "Islamabad", "category": "reservoir", "lat": 33.7917, "lon": 73.2833, "radius_km": 0.3,
     "prompts": ["Simly Dam reservoir blue water and concrete spillway hills Islamabad", "Simly Dam scenic lake and water filtration plant Islamabad"]},
    {"name": "Dino Valley Park, Monal Pir Sohawa Road, Margalla", "city": "Islamabad", "category": "theme_park", "lat": 33.7667, "lon": 73.0667, "radius_km": 0.08,
     "prompts": ["Dino Valley theme park dinosaur statues in pine forest Margalla Hills Islamabad", "Dino Valley family adventure park Pir Sohawa road Margalla"]},
    {"name": "Shahdara Picnic Spot & Freshwater Stream, Islamabad", "city": "Islamabad", "category": "natural_landmark", "lat": 33.7611, "lon": 73.1667, "radius_km": 0.15,
     "prompts": ["Shahdara Valley freshwater mountain stream charpoys in shallow water Margalla foothills Islamabad", "Shahdara picnic spot green hills and rocky stream Islamabad"]},

    # 81-90: Transport, Interchanges & Gateways
    {"name": "Islamabad International Airport IIAP Passenger Terminal", "city": "Islamabad", "category": "airport", "lat": 33.5489, "lon": 72.8250, "radius_km": 0.3,
     "prompts": ["Islamabad International Airport IIAP curved passenger terminal glass apron control tower", "New Islamabad Airport main departures concourse and runway"]},
    {"name": "Zero Point Interchange, Islamabad", "city": "Islamabad", "category": "interchange", "lat": 33.6889, "lon": 73.0611, "radius_km": 0.1,
     "prompts": ["Zero Point Interchange multi-level cloverleaf flyovers Kashmir Highway Faisal Avenue Islamabad", "Zero Point flyover network and landscaped green loops Islamabad"]},
    {"name": "Faizabad Interchange & Metro Station, Islamabad/Rawalpindi", "city": "Islamabad", "category": "interchange", "lat": 33.6639, "lon": 73.0778, "radius_km": 0.1,
     "prompts": ["Faizabad Interchange massive elevated flyovers and Metro Bus station boundary Islamabad Rawalpindi", "Faizabad junction connecting Murree Road and Expressway"]},
    {"name": "Golra Sharif Railway Station & Heritage Museum, Islamabad", "city": "Islamabad", "category": "railway_station", "lat": 33.6708, "lon": 72.9486, "radius_km": 0.05,
     "prompts": ["Golra Sharif historic colonial railway junction stone station and steam locomotive museum Islamabad", "Golra Railway Heritage Museum antique carriages and banyan tree platform"]},
    {"name": "Srinagar (Kashmir) Highway Corridor, Islamabad", "city": "Islamabad", "category": "highway", "lat": 33.6778, "lon": 73.0333, "radius_km": 0.2,
     "prompts": ["Srinagar Highway expansive multi-lane landscaped expressway pine trees Islamabad", "Kashmir Highway central artery connecting airport to Islamabad"]},
    {"name": "Islamabad Expressway Toll Plaza & Gulberg Interchange", "city": "Islamabad", "category": "highway", "lat": 33.5972, "lon": 73.1250, "radius_km": 0.15,
     "prompts": ["Islamabad Expressway multi-lane highway flyover Gulberg Greens entrance Islamabad", "Islamabad Expressway signal-free corridor and flyover bridges"]},
    {"name": "Metro Bus Saddar-Pak Secretariat Elevated Corridor, Islamabad", "city": "Islamabad", "category": "transit_corridor", "lat": 33.7111, "lon": 73.0583, "radius_km": 0.1,
     "prompts": ["Rawalpindi Islamabad Metro Bus red articulated bus on elevated dedicated flyover Blue Area", "Metro Bus station glass elevated platform Jinnah Avenue Islamabad"]},
    {"name": "Chaman / Rawal Road Interchange, Islamabad", "city": "Islamabad", "category": "interchange", "lat": 33.6806, "lon": 73.0972, "radius_km": 0.08,
     "prompts": ["Rawal Dam Chowk flyover and landscaped underpass Club Road Islamabad", "Rawal Dam junction interchange Islamabad"]},
    {"name": "Murree Expressway (N-75) Toll Plaza, Islamabad", "city": "Islamabad", "category": "highway", "lat": 33.7444, "lon": 73.1833, "radius_km": 0.1,
     "prompts": ["Murree Expressway N-75 toll booths and mountain foothills gateway Islamabad", "N-75 Expressway entry towards Murree Hills Islamabad"]},
    {"name": "G.T. Road Tarnol Interchange, Islamabad", "city": "Islamabad", "category": "highway", "lat": 33.6333, "lon": 72.9056, "radius_km": 0.1,
     "prompts": ["Tarnol GT Road flyover and railway overhead bridge western entrance Islamabad", "Tarnol junction commercial trucks and GT Road highway"]},

    # 91-100: Heritage, Shrines, Suburbs & Modern Developments
    {"name": "Shrine of Bari Imam (Hazrat Shah Abdul Latif Kazmi), Nurpur Shahan, Islamabad", "city": "Islamabad", "category": "shrine", "lat": 33.7472, "lon": 73.1194, "radius_km": 0.05,
     "prompts": ["Shrine of Bari Imam green dome complex marble courtyard Nurpur Shahan Islamabad", "Bari Imam shrine entrance and devotees plaza Margalla foothills"]},
    {"name": "Bahria Enclave Grand Jamia Mosque & Dancing Fountains, Islamabad", "city": "Islamabad", "category": "mosque", "lat": 33.6917, "lon": 73.2083, "radius_km": 0.08,
     "prompts": ["Bahria Enclave Grand Jamia Mosque Turkish ottoman architecture and commercial boulevard Islamabad", "Bahria Enclave fountain circle and modern residential sector Islamabad"]},
    {"name": "Gulberg Greens D-Markaz & Canal City, Islamabad", "city": "Islamabad", "category": "commercial_district", "lat": 33.5833, "lon": 73.1500, "radius_km": 0.15,
     "prompts": ["Gulberg Greens D-Markaz grand commercial square glass buildings and boulevard Islamabad", "Gulberg Greens palm tree avenues and waterfront boulevard Islamabad"]},
    {"name": "DHA Phase 2 Central Boulevard & Clock Tower, Islamabad", "city": "Islamabad", "category": "residential_district", "lat": 33.5167, "lon": 73.1500, "radius_km": 0.1,
     "prompts": ["DHA Phase 2 Islamabad main boulevard clock tower commercial square", "DHA Phase 2 entrance gates and landscaped roundabouts Islamabad"]},
    {"name": "Park View City Grand Mosque & Lake, Islamabad", "city": "Islamabad", "category": "residential_district", "lat": 33.6806, "lon": 73.1861, "radius_km": 0.1,
     "prompts": ["Park View City downtown lake and grand mosque Malot Margalla views Islamabad", "Park View City commercial downtown and residential hills Islamabad"]},
    {"name": "1965 War Memorial & Shakarparian Parade Ground, Islamabad", "city": "Islamabad", "category": "national_monument", "lat": 33.6861, "lon": 73.0833, "radius_km": 0.1,
     "prompts": ["Shakarparian National Parade Ground grandstands and military monument Islamabad", "Pakistan Day parade grandstand Shakarparian Islamabad"]},
    {"name": "Talhar & Gokina Village Pine Ridge, Margalla Hills, Islamabad", "city": "Islamabad", "category": "mountain_ridge", "lat": 33.7833, "lon": 73.0500, "radius_km": 0.2,
     "prompts": ["Gokina and Talhar village pine ridge viewpoints Margalla Hills behind Islamabad", "Margalla highland rural terraced fields and pine forests Islamabad"]},
    {"name": "Kenthla Dam & Reservoir, Margalla Basin, Islamabad", "city": "Islamabad", "category": "reservoir", "lat": 33.7833, "lon": 72.8667, "radius_km": 0.15,
     "prompts": ["Kenthla Dam scenic blue water reservoir nestled in Margalla hills Islamabad", "Kenthla Dam spillway and picnic ridge Islamabad"]},
    {"name": "Rawal Dam Spillway & Old Bridge, Islamabad", "city": "Islamabad", "category": "dam", "lat": 33.6944, "lon": 73.1194, "radius_km": 0.08,
     "prompts": ["Rawal Dam concrete masonry spillway gates and downstream canyon Islamabad", "Rawal Dam reservoir wall and observation tower Islamabad"]},
    {"name": "Saidpur Old Hindu Temple & Gurdwara Complex, Islamabad", "city": "Islamabad", "category": "historical_temple", "lat": 33.7422, "lon": 73.0692, "radius_km": 0.05,
     "prompts": ["Saidpur village ancient Hindu temple stone facade and step pond Margalla Islamabad", "Historic Rama Temple and Sikh gurdwara building Saidpur village Islamabad"]}
]

# --------------------------------------------------------------------------
# Pakistan - Lahore, Karachi, Rawalpindi, Peshawar, Quetta, Multan, Faisalabad, Abbottabad, Murree, Swat, Gilgit, Skardu, etc.
# --------------------------------------------------------------------------
other_pakistan_spots = [
    # Lahore
    {"name": "Badshahi Mosque, Lahore", "city": "Lahore", "category": "historical_mosque", "lat": 31.5881, "lon": 74.3108, "radius_km": 0.05,
     "prompts": ["Badshahi Mosque grand red sandstone Mughal courtyard and white marble domes Lahore", "Badshahi Mosque vast courtyard minarets Lahore"]},
    {"name": "Minar-e-Pakistan, Greater Iqbal Park, Lahore", "city": "Lahore", "category": "national_monument", "lat": 31.5925, "lon": 74.3094, "radius_km": 0.05,
     "prompts": ["Minar-e-Pakistan tall white memorial tower Greater Iqbal Park Lahore", "Minar-e-Pakistan tower and surrounding fountains Lahore"]},
    {"name": "Lahore Fort (Shahi Qila), Lahore", "city": "Lahore", "category": "unesco_world_heritage", "lat": 31.5881, "lon": 74.3153, "radius_km": 0.08,
     "prompts": ["Lahore Fort Shahi Qila Alamgiri Gate red sandstone Mughal fortress Lahore", "Lahore Fort Sheesh Mahal mirror palace and Diwan-e-Aam"]},
    {"name": "Wazir Khan Mosque, Walled City, Lahore", "city": "Lahore", "category": "historical_mosque", "lat": 31.5833, "lon": 74.3217, "radius_km": 0.05,
     "prompts": ["Wazir Khan Mosque intricate glazed tilework kashi-kari and minarets Old Lahore", "Wazir Khan Mosque courtyard vibrant fresco wall murals Lahore"]},
    {"name": "Shalimar Gardens (Shalamar Bagh), Lahore", "city": "Lahore", "category": "unesco_world_heritage", "lat": 31.5861, "lon": 74.3819, "radius_km": 0.08,
     "prompts": ["Shalimar Gardens Mughal terraced water cascades fountains and pavilions Lahore", "Shalimar Gardens historic Mughal water gardens Lahore"]},
    {"name": "Packages Mall, Walton Road, Lahore", "city": "Lahore", "category": "shopping_mall", "lat": 31.4722, "lon": 74.3542, "radius_km": 0.08,
     "prompts": ["Packages Mall grand modern shopping mall atrium Walton Road Lahore", "Packages Mall exterior facade and parking plaza Lahore"]},
    {"name": "Emporium Mall by Nishat, Johar Town, Lahore", "city": "Lahore", "category": "shopping_mall", "lat": 31.4678, "lon": 74.2667, "radius_km": 0.08,
     "prompts": ["Emporium Mall massive contemporary glass retail shopping complex Johar Town Lahore", "Emporium Mall interior atrium and Nishat Hotel Lahore"]},
    {"name": "Gaddafi Stadium (Lahore Cricket Stadium), Gulberg, Lahore", "city": "Lahore", "category": "stadium", "lat": 31.5133, "lon": 74.3333, "radius_km": 0.1,
     "prompts": ["Gaddafi Stadium red brick Mughal architectural arches cricket ground Lahore", "Gaddafi Stadium cricket arena and floodlights Lahore"]},
    {"name": "Liberty Market Roundabout, Gulberg 3, Lahore", "city": "Lahore", "category": "commercial_market", "lat": 31.5097, "lon": 74.3425, "radius_km": 0.08,
     "prompts": ["Liberty Market bustling roundabout illuminated shops Gulberg Lahore", "Liberty Market circular shopping plaza and fountain Lahore"]},
    {"name": "MM Alam Road Commercial Food Street, Gulberg, Lahore", "city": "Lahore", "category": "commercial_district", "lat": 31.5167, "lon": 74.3500, "radius_km": 0.1,
     "prompts": ["MM Alam Road upscale restaurants cafes and fashion boutiques Gulberg Lahore", "MM Alam Road evening street dining Lahore"]},
    {"name": "Wagah Border Flag Ceremony Arena, Lahore", "city": "Lahore", "category": "national_monument", "lat": 31.6050, "lon": 74.5728, "radius_km": 0.05,
     "prompts": ["Wagah Border stadium amphitheatre flag lowering ceremony Lahore Pakistan", "Wagah Border gate and national parade arena"]},
    {"name": "Tomb of Jahangir, Shahdara, Lahore", "city": "Lahore", "category": "unesco_world_heritage", "lat": 31.6225, "lon": 74.3033, "radius_km": 0.08,
     "prompts": ["Tomb of Jahangir sandstone and marble mausoleum minarets Shahdara Lahore", "Jahangir Tomb Persian gardens and marble mosaics Lahore"]},
    {"name": "Delhi Gate & Shahi Hammam, Walled City, Lahore", "city": "Lahore", "category": "heritage_site", "lat": 31.5833, "lon": 74.3250, "radius_km": 0.05,
     "prompts": ["Delhi Gate historic Mughal entrance gate and Shahi Hammam royal bathhouse Lahore", "Walled City of Lahore Delhi Gate bazaar"]},
    {"name": "Chauburji Monument & Metro Station, Multan Road, Lahore", "city": "Lahore", "category": "historical_monument", "lat": 31.5542, "lon": 74.3042, "radius_km": 0.05,
     "prompts": ["Chauburji historic four-towered Mughal gateway monument and Orange Line metro Lahore", "Chauburji monument tile mosaic towers Lahore"]},
    {"name": "Eiffel Tower Replica, Bahria Town, Lahore", "city": "Lahore", "category": "monument", "lat": 31.3653, "lon": 74.1889, "radius_km": 0.05,
     "prompts": ["Eiffel Tower replica steel monument illuminated Bahria Town Lahore", "Bahria Town Lahore Eiffel Tower park and boulevard"]},

    # Karachi
    {"name": "Mazar-e-Quaid (Jinnah Mausoleum), Karachi", "city": "Karachi", "category": "national_monument", "lat": 24.8753, "lon": 67.0408, "radius_km": 0.05,
     "prompts": ["Mazar-e-Quaid white marble modernist cube dome mausoleum Karachi", "Mazar-e-Quaid Quaid-e-Azam tomb illuminated gardens Karachi"]},
    {"name": "Clifton Beach & Sea View Promenade, Karachi", "city": "Karachi", "category": "coast", "lat": 24.7892, "lon": 67.0583, "radius_km": 0.2,
     "prompts": ["Clifton Sea View sandy beach Arabian Sea camels and promenade Karachi", "Sea View Clifton beach coastline sunset Karachi"]},
    {"name": "Mohatta Palace Museum, Clifton, Karachi", "city": "Karachi", "category": "historical_palace", "lat": 24.8142, "lon": 67.0322, "radius_km": 0.05,
     "prompts": ["Mohatta Palace Rajasthani pink Jodhpur sandstone palace museum Clifton Karachi", "Mohatta Palace gardens and stone domes Karachi"]},
    {"name": "Frere Hall & Gardens, Saddar, Karachi", "city": "Karachi", "category": "colonial_architecture", "lat": 24.8472, "lon": 67.0333, "radius_km": 0.05,
     "prompts": ["Frere Hall Venetian Gothic yellow limestone building Sadequain ceiling murals Karachi", "Frere Hall historic colonial library and lawns Karachi"]},
    {"name": "Port Grand Food Street & Old Railway Pier, Karachi", "city": "Karachi", "category": "commercial_district", "lat": 24.8444, "lon": 66.9889, "radius_km": 0.08,
     "prompts": ["Port Grand waterfront boardwalk restaurants old bridge harbor Native Jetty Karachi", "Port Grand Karachi evening food street along harbor"]},
    {"name": "PAF Museum, Shahrah-e-Faisal, Karachi", "city": "Karachi", "category": "aircraft_monument", "lat": 24.8876, "lon": 67.0984, "radius_km": 0.1,
     "prompts": ["PAF Museum outdoor aircraft display park fighter jets Pakistan Air Force Karachi", "Pakistan Air Force Museum Shahrah-e-Faisal Karachi military aircraft"]},
    {"name": "Dolmen Mall Clifton, Karachi", "city": "Karachi", "category": "shopping_mall", "lat": 24.8097, "lon": 67.0333, "radius_km": 0.05,
     "prompts": ["Dolmen Mall Clifton sea-facing luxury retail mall complex Karachi", "Dolmen Mall interior multi-level atrium Karachi"]},
    {"name": "Bahria Town Grand Jamia Mosque Karachi, Super Highway", "city": "Karachi", "category": "national_mosque", "lat": 25.0167, "lon": 67.3333, "radius_km": 0.1,
     "prompts": ["Grand Jamia Mosque Bahria Town Karachi massive white marble domes and minaret", "Bahria Town Karachi Grand Mosque architecture"]},
    {"name": "Empress Market, Saddar, Karachi", "city": "Karachi", "category": "colonial_architecture", "lat": 24.8614, "lon": 67.0306, "radius_km": 0.05,
     "prompts": ["Empress Market Victorian Gothic stone clock tower bazaar Saddar Karachi", "Empress Market heritage building and pedestrian plaza Karachi"]},
    {"name": "Do Darya Waterfront Dining, Phase 8 DHA, Karachi", "city": "Karachi", "category": "commercial_district", "lat": 24.7556, "lon": 67.0722, "radius_km": 0.1,
     "prompts": ["Do Darya coastal wooden deck restaurants overlooking Arabian Sea Phase 8 DHA Karachi", "Do Darya open-air seaside dining Karachi"]},

    # Rawalpindi
    {"name": "Ayub National Park, Rawalpindi", "city": "Rawalpindi", "category": "park", "lat": 33.5667, "lon": 73.0833, "radius_km": 0.15,
     "prompts": ["Ayub National Park lakes boating canals and military museum Rawalpindi", "Ayub Park green gardens and recreation grounds Rawalpindi"]},
    {"name": "Raja Bazaar & Dingi Khoyi, Rawalpindi", "city": "Rawalpindi", "category": "commercial_market", "lat": 33.6083, "lon": 73.0556, "radius_km": 0.08,
     "prompts": ["Raja Bazaar historic bustling marketplace old wooden carved balconies Rawalpindi", "Raja Bazaar narrow commercial alleys Rawalpindi"]},
    {"name": "Rawalpindi Cricket Stadium, Double Road", "city": "Rawalpindi", "category": "stadium", "lat": 33.6472, "lon": 73.0778, "radius_km": 0.08,
     "prompts": ["Rawalpindi Cricket Stadium international cricket pavilion and floodlights", "Rawalpindi Stadium turf and grandstands"]},
    {"name": "PAF Aircraft Monument, Rawalpindi, Chandni Chowk / Old Airport", "city": "Rawalpindi", "category": "aircraft_monument", "lat": 33.5950, "lon": 73.0800, "radius_km": 0.05,
     "prompts": ["Pakistan Air Force F-86 Sabre fighter jet monument Rawalpindi Chandni Chowk Old Airport Road", "PAF fighter jet on display pedestal Rawalpindi"]},

    # Peshawar
    {"name": "Islamia College University, Peshawar", "city": "Peshawar", "category": "university_campus", "lat": 33.9986, "lon": 71.4756, "radius_km": 0.08,
     "prompts": ["Islamia College Peshawar iconic Oriental Gothic red brick architecture and clock tower", "Islamia College main building and manicured gardens Peshawar"]},
    {"name": "Bala Hissar Fort, Peshawar", "city": "Peshawar", "category": "fortress", "lat": 34.0117, "lon": 71.5714, "radius_km": 0.08,
     "prompts": ["Bala Hissar Fort massive historic brick bastion fortress overlooking Peshawar city", "Bala Hissar Fort frontier corps battlements Peshawar"]},
    {"name": "Qissa Khwani Bazaar, Peshawar", "city": "Peshawar", "category": "commercial_market", "lat": 34.0100, "lon": 71.5667, "radius_km": 0.05,
     "prompts": ["Qissa Khwani Bazaar Storytellers Market brass teapots and historic street Peshawar", "Qissa Khwani traditional street market Peshawar"]},
    {"name": "Mahabat Khan Mosque, Peshawar", "city": "Peshawar", "category": "historical_mosque", "lat": 34.0114, "lon": 71.5706, "radius_km": 0.05,
     "prompts": ["Mahabat Khan Mosque white marble Mughal courtyard and tall minarets Old Peshawar", "Mahabat Khan Mosque interior tilework and prayer hall Peshawar"]},
    {"name": "Bab-e-Khyber (Khyber Pass Gateway), Jamrud / Peshawar", "city": "Peshawar", "category": "national_monument", "lat": 33.9972, "lon": 71.3917, "radius_km": 0.05,
     "prompts": ["Bab-e-Khyber stone arch gateway monument to Khyber Pass Jamrud Peshawar", "Bab-e-Khyber arch across the highway"]},

    # Quetta
    {"name": "Hanna Lake & Urrak Valley, Quetta", "city": "Quetta", "category": "reservoir", "lat": 30.2500, "lon": 67.1000, "radius_km": 0.15,
     "prompts": ["Hanna Lake turquoise water reservoir surrounded by arid brown mountains Quetta", "Hanna Lake bridge and picnic pavilion Quetta"]},
    {"name": "Quaid-e-Azam Residency, Ziarat, Balochistan", "city": "Quetta", "category": "historical_building", "lat": 30.3853, "lon": 67.7269, "radius_km": 0.05,
     "prompts": ["Quaid-e-Azam Residency wooden colonial heritage architecture pine trees Ziarat Balochistan", "Ziarat Residency historic wooden building"]},

    # Multan
    {"name": "Tomb of Shah Rukn-e-Alam, Multan", "city": "Multan", "category": "historical_shrine", "lat": 30.1983, "lon": 71.4722, "radius_km": 0.05,
     "prompts": ["Tomb of Shah Rukn-e-Alam octagonal red brick and blue glazed ceramic dome Multan", "Shah Rukn-e-Alam shrine high mound fortress Multan"]},
    {"name": "Shrine of Bahauddin Zakariya, Multan", "city": "Multan", "category": "historical_shrine", "lat": 30.1994, "lon": 71.4736, "radius_km": 0.05,
     "prompts": ["Shrine of Bahauddin Zakariya white and blue tiled dome Multan Fort", "Bahauddin Zakariya tomb courtyard Multan"]},

    # Faisalabad
    {"name": "Clock Tower (Ghanta Ghar), Faisalabad", "city": "Faisalabad", "category": "civic_monument", "lat": 31.4186, "lon": 73.0789, "radius_km": 0.05,
     "prompts": ["Clock Tower Ghanta Ghar Victorian stone tower center of eight bazaars Faisalabad", "Ghanta Ghar Faisalabad clock tower roundabout"]},

    # Abbottabad, Galyat & Mountains
    {"name": "Mushkpuri Peak, Nathia Gali, KPK, Pakistan", "city": "Abbottabad", "category": "mountain_peak", "lat": 34.0625, "lon": 73.4358, "radius_km": 10.0,
     "prompts": ["Mushkpuri Peak green mountain meadow ridge Nathia Gali Galyat Abbottabad", "Mushkpuri summit pine trees and alpine meadow trail"]},
    {"name": "Miranjani Peak, Nathia Gali, KPK, Pakistan", "city": "Abbottabad", "category": "mountain_peak", "lat": 34.1167, "lon": 73.4333, "radius_km": 10.0,
     "prompts": ["Miranjani Peak highest summit in Galyat pine forest ridge Nathia Gali", "Miranjani mountain trail overlooking Hazara and Kashmir"]},
    {"name": "Ilyasi Mosque, Abbottabad", "city": "Abbottabad", "category": "mosque", "lat": 34.1667, "lon": 73.2333, "radius_km": 0.05,
     "prompts": ["Ilyasi Mosque grand white facade over freshwater natural spring Abbottabad", "Ilyasi Mosque famous pakora bazaar and mountain spring Abbottabad"]},
    {"name": "Thandiani Hill Station, Abbottabad", "city": "Abbottabad", "category": "mountain_ridge", "lat": 34.2333, "lon": 73.3500, "radius_km": 0.2,
     "prompts": ["Thandiani pine forest hill station ridge clouds Abbottabad", "Thandiani mountain summit viewpoint overlooking Pir Panjal"]},

    # Murree
    {"name": "Mall Road Murree, Murree Hills", "city": "Murree", "category": "commercial_street", "lat": 33.9070, "lon": 73.3943, "radius_km": 0.08,
     "prompts": ["Mall Road Murree pedestrian mountain hill station shopping street shops hotels", "Murree Mall Road bustling evening street"]},
    {"name": "Patriata New Murree Chairlift & Cable Car", "city": "Murree", "category": "viewpoint", "lat": 33.8821, "lon": 73.4562, "radius_km": 0.1,
     "prompts": ["Patriata New Murree cable car gondola and chairlift riding over pine tree canopy", "Patriata hill station ridge chairlift Murree"]},
    {"name": "PAF Aircraft Monument, Lower Topa, Murree, Pakistan", "city": "Murree", "category": "aircraft_monument", "lat": 33.9115, "lon": 73.4150, "radius_km": 0.05,
     "prompts": ["Pakistan Air Force Sabre F-86 fighter aircraft monument Lower Topa Murree", "PAF aircraft monument installed roundabout Lower Topa Murree"]},

    # Swat Valley
    {"name": "Malam Jabba Ski Resort & Chairlift, Swat", "city": "Swat", "category": "mountain_resort", "lat": 34.7997, "lon": 72.5714, "radius_km": 0.1,
     "prompts": ["Malam Jabba ski resort hotel slopes and chairlift snow mountains Swat Valley", "Malam Jabba alpine mountain chairlift Swat"]},
    {"name": "White Palace Marghazar, Swat", "city": "Swat", "category": "historical_palace", "lat": 34.7167, "lon": 72.3333, "radius_km": 0.05,
     "prompts": ["White Palace Marghazar white marble heritage residence foothills Swat", "Sufed Mahal White Palace hotel and gardens Swat"]},

    # Gilgit & Hunza
    {"name": "Baltit Fort, Karimabad, Hunza Valley", "city": "Gilgit", "category": "fortress", "lat": 36.3267, "lon": 74.6711, "radius_km": 0.05,
     "prompts": ["Baltit Fort ancient Tibetan-style fortress wooden balconies overlooking Hunza Valley", "Baltit Fort Karimabad snow mountain background"]},
    {"name": "Passu Cones & Cathedral Peaks, Hunza", "city": "Gilgit", "category": "mountain_peak", "lat": 36.4680, "lon": 74.8870, "radius_km": 5.0,
     "prompts": ["Passu Cones Cathedral needle rock peaks Karakoram Highway Hunza", "Passu Cones pointed mountain spires Hunza Valley"]},
    {"name": "Attabad Lake Turquoise Waters, Hunza", "city": "Gilgit", "category": "reservoir", "lat": 36.3333, "lon": 74.8667, "radius_km": 0.3,
     "prompts": ["Attabad Lake vivid turquoise blue water and sheer rocky canyon walls Karakoram", "Attabad Lake boats cruising Karakoram Highway tunnel"]},

    # Skardu
    {"name": "Shangrila Resort & Lower Kachura Lake, Skardu", "city": "Skardu", "category": "mountain_resort", "lat": 35.4222, "lon": 75.4472, "radius_km": 0.08,
     "prompts": ["Shangrila Resort Chinese-style red pagoda chalets around heart-shaped Kachura Lake Skardu", "Shangrila Resort Lower Kachura Lake Skardu Baltistan"]},
    {"name": "Deosai National Park Plains (Land of Giants), Skardu", "city": "Skardu", "category": "national_park", "lat": 35.0500, "lon": 75.4500, "radius_km": 15.0,
     "prompts": ["Deosai Plains high altitude alpine plateau wildflowers green rolling tundra Skardu", "Deosai National Park wide open plains and snow peaks"]},
    {"name": "Katpana Cold Desert Dunes, Skardu", "city": "Skardu", "category": "desert", "lat": 35.3333, "lon": 75.5833, "radius_km": 0.5,
     "prompts": ["Katpana cold desert white sand dunes surrounded by snow-capped mountains Skardu", "Katpana cold sand desert Indus river Skardu"]},

    # Other historic spots
    {"name": "PAF F-86 Sabre Monument, Sargodha, Pakistan", "city": "Sargodha", "category": "aircraft_monument", "lat": 32.0620, "lon": 72.6710, "radius_km": 0.05,
     "prompts": ["PAF Base Sargodha Club Chowk F-86 Sabre fighter aircraft monument Pakistan", "PAF Sabre jet monument roundabout Sargodha"]},
    {"name": "Noor Mahal Palace, Bahawalpur, Punjab", "city": "Bahawalpur", "category": "historical_palace", "lat": 29.3972, "lon": 71.6669, "radius_km": 0.05,
     "prompts": ["Noor Mahal Italian chateau style palace Corinthian columns Bahawalpur", "Noor Mahal illuminated palace facade Bahawalpur"]},
    {"name": "Lansdowne Bridge & Sukkur Barrage, Sukkur, Sindh", "city": "Sukkur", "category": "bridge", "lat": 27.7000, "lon": 68.8833, "radius_km": 0.1,
     "prompts": ["Lansdowne Bridge historic steel cantilever railway bridge over Indus River Sukkur", "Sukkur Barrage arches and Lansdowne Bridge"]}
]

all_pakistan = islamabad_spots + other_pakistan_spots
with open(OUT_DIR / "pakistan.json", "w", encoding="utf-8") as f:
    json.dump(all_pakistan, f, indent=2, ensure_ascii=False)
print(f"Saved pakistan.json with {len(all_pakistan)} spots ({len(islamabad_spots)} in Islamabad).")

# --------------------------------------------------------------------------
# 2. TURKEY (Istanbul, Ankara, Izmir, Antalya, Bursa, Konya, Trabzon, Cappadocia, Gaziantep)
# --------------------------------------------------------------------------
turkey_spots = [
    # Istanbul
    {"name": "Hagia Sophia (Ayasofya-i Kebir Cami-i Serifi), Istanbul", "city": "Istanbul", "category": "historical_mosque", "lat": 41.0086, "lon": 28.9802, "radius_km": 0.05,
     "prompts": ["Hagia Sophia grand Byzantine dome and Ottoman minarets Sultanahmet Istanbul", "Ayasofya Hagia Sophia mosque exterior courtyard Istanbul"]},
    {"name": "Blue Mosque (Sultanahmet Camii), Istanbul", "city": "Istanbul", "category": "historical_mosque", "lat": 41.0054, "lon": 28.9768, "radius_km": 0.05,
     "prompts": ["Blue Mosque Sultanahmet six slender minarets cascading domes Istanbul", "Sultan Ahmed Mosque Blue Mosque courtyard Istanbul"]},
    {"name": "Galata Tower (Galata Kulesi), Beyoglu, Istanbul", "city": "Istanbul", "category": "historical_monument", "lat": 41.0256, "lon": 28.9742, "radius_km": 0.05,
     "prompts": ["Galata Tower medieval cylindrical stone tower cone roof Beyoglu Istanbul", "Galata Kulesi observation balcony overlooking Golden Horn Istanbul"]},
    {"name": "Topkapi Palace (Topkapi Sarayi), Istanbul", "city": "Istanbul", "category": "historical_palace", "lat": 41.0115, "lon": 28.9833, "radius_km": 0.08,
     "prompts": ["Topkapi Palace Ottoman imperial gate courtyards and Imperial Council Istanbul", "Topkapi Sarayi harem and Bosphorus view pavilion Istanbul"]},
    {"name": "Bosphorus Bridge (15 July Martyrs Bridge), Istanbul", "city": "Istanbul", "category": "bridge", "lat": 41.0456, "lon": 29.0344, "radius_km": 0.2,
     "prompts": ["Bosphorus Bridge 15 July Martyrs suspension bridge spanning Europe and Asia Istanbul", "Bosphorus strait suspension bridge Ortakoy view Istanbul"]},
    {"name": "Grand Bazaar (Kapalicarsi), Fatih, Istanbul", "city": "Istanbul", "category": "commercial_market", "lat": 41.0106, "lon": 28.9681, "radius_km": 0.08,
     "prompts": ["Grand Bazaar Kapalicarsi vaulted painted ceiling corridors and lantern shops Istanbul", "Grand Bazaar historic covered market arched entrance Istanbul"]},
    {"name": "Taksim Square & Republic Monument, Beyoglu, Istanbul", "city": "Istanbul", "category": "civic_monument", "lat": 41.0369, "lon": 28.9850, "radius_km": 0.05,
     "prompts": ["Taksim Square Republic Monument and red vintage nostalgic tramway Istanbul", "Taksim Square pedestrian plaza and Ataturk Cultural Centre Istanbul"]},
    {"name": "Dolmabahce Palace (Dolmabahce Sarayi), Besiktas, Istanbul", "city": "Istanbul", "category": "historical_palace", "lat": 41.0392, "lon": 29.0003, "radius_km": 0.08,
     "prompts": ["Dolmabahce Palace grand Baroque neoclassical waterfront facade clock tower Bosphorus Istanbul", "Dolmabahce Sarayi imperial gate along Bosphorus"]},
    {"name": "Maiden's Tower (Kiz Kulesi), Uskudar, Istanbul", "city": "Istanbul", "category": "historical_monument", "lat": 41.0211, "lon": 29.0042, "radius_km": 0.05,
     "prompts": ["Maiden's Tower Kiz Kulesi historic lighthouse islet Bosphorus strait Uskudar Istanbul", "Kiz Kulesi sunset silhouette on Bosphorus water"]},
    {"name": "Grand Camlica Mosque, Uskudar, Istanbul", "city": "Istanbul", "category": "national_mosque", "lat": 41.0344, "lon": 29.0708, "radius_km": 0.08,
     "prompts": ["Camlica Mosque massive modern neo-Ottoman dome and six minarets Camlica Hill Istanbul", "Buyuk Camlica Camii courtyard and panoramic Istanbul overlook"]},
    {"name": "Ortakoy Mosque (Buyuk Mecidiye Camii), Besiktas, Istanbul", "city": "Istanbul", "category": "historical_mosque", "lat": 41.0472, "lon": 29.0269, "radius_km": 0.05,
     "prompts": ["Ortakoy Mosque Baroque waterfront mosque under Bosphorus Bridge Istanbul", "Ortakoy Camii square and Bosphorus strait view"]},
    {"name": "Suleymaniye Mosque, Fatih, Istanbul", "city": "Istanbul", "category": "historical_mosque", "lat": 41.0161, "lon": 28.9639, "radius_km": 0.08,
     "prompts": ["Suleymaniye Mosque Mimar Sinan masterpiece grand dome courtyard overlooking Golden Horn Istanbul", "Suleymaniye Camii imperial complex Istanbul"]},

    # Ankara
    {"name": "Anitkabir (Ataturk Mausoleum), Cankaya, Ankara", "city": "Ankara", "category": "national_monument", "lat": 39.9250, "lon": 32.8369, "radius_km": 0.08,
     "prompts": ["Anitkabir Ataturk mausoleum ceremonial Lion Road and colonnaded Hall of Honor Ankara", "Anitkabir grand plaza and limestone colonnade Ankara"]},
    {"name": "Ankara Castle (Ankara Kalesi), Altindag, Ankara", "city": "Ankara", "category": "fortress", "lat": 39.9406, "lon": 32.8647, "radius_km": 0.05,
     "prompts": ["Ankara Castle medieval hilltop stone citadel walls overlooking red tile roofs Ankara", "Ankara Kalesi historic citadel bastions"]},
    {"name": "Atakule Tower, Cankaya, Ankara", "city": "Ankara", "category": "commercial_towers", "lat": 39.8864, "lon": 32.8556, "radius_km": 0.05,
     "prompts": ["Atakule communications and observation tower with revolving dome restaurant Cankaya Ankara", "Atakule tower shopping mall plaza Ankara"]},
    {"name": "Kocatepe Mosque, Kizilay, Ankara", "city": "Ankara", "category": "national_mosque", "lat": 39.9167, "lon": 32.8608, "radius_km": 0.08,
     "prompts": ["Kocatepe Mosque monumental neo-classical Ottoman four minaret mosque Kizilay Ankara", "Kocatepe Camii grand dome and illuminated minarets Ankara"]},

    # Izmir
    {"name": "Izmir Clock Tower (Saat Kulesi), Konak Square, Izmir", "city": "Izmir", "category": "civic_monument", "lat": 38.4189, "lon": 27.1286, "radius_km": 0.05,
     "prompts": ["Izmir Clock Tower ornate Ottoman marble clock tower Konak Square Aegean Sea Izmir", "Saat Kulesi Konak Meydani pigeons and palm trees Izmir"]},
    {"name": "Tarihi Asansor (Historical Elevator), Karatas, Izmir", "city": "Izmir", "category": "historical_monument", "lat": 38.4086, "lon": 27.1172, "radius_km": 0.05,
     "prompts": ["Tarihi Asansor brick elevator tower cliffside viewpoint Gulf of Izmir", "Historical Elevator terrace and Dario Moreno street Izmir"]},
    {"name": "Kemeralti Bazaar & Hisar Mosque, Konak, Izmir", "city": "Izmir", "category": "commercial_market", "lat": 38.4194, "lon": 27.1333, "radius_km": 0.08,
     "prompts": ["Kemeralti historic open-air market streets and Ottoman caravanserais Izmir", "Kemeralti Carsisi bustling spice market Izmir"]},

    # Antalya
    {"name": "Hadrian's Gate (Uckapilar), Kaleici, Antalya", "city": "Antalya", "category": "historical_monument", "lat": 36.8853, "lon": 30.7086, "radius_km": 0.05,
     "prompts": ["Hadrian's Gate triple-arched Roman white marble triumphal gate Kaleici Antalya", "Uckapilar Hadrian Gate Antalya old town"]},
    {"name": "Kaleici Historic Old Town & Marina, Antalya", "city": "Antalya", "category": "heritage_village", "lat": 36.8833, "lon": 30.7042, "radius_km": 0.1,
     "prompts": ["Kaleici historic Roman harbour yachts stone walls and Ottoman timber houses Antalya", "Antalya Old City Marina Mediterranean cliffside"]},
    {"name": "Duden Waterfalls (Lower Duden Falls), Lara, Antalya", "city": "Antalya", "category": "natural_landmark", "lat": 36.8517, "lon": 30.7833, "radius_km": 0.08,
     "prompts": ["Lower Duden Waterfall cascading off sheer coastal cliffs directly into Mediterranean Sea Antalya", "Duden Selalesi waterfall cliffside park Antalya"]},

    # Bursa
    {"name": "Grand Mosque of Bursa (Bursa Ulu Cami), Bursa", "city": "Bursa", "category": "historical_mosque", "lat": 40.1833, "lon": 29.0617, "radius_km": 0.05,
     "prompts": ["Grand Mosque of Bursa Ulu Cami twenty domes interior ablution fountain and calligraphic murals", "Bursa Ulu Camii monumental early Ottoman mosque"]},
    {"name": "Green Tomb (Yesil Turbe), Bursa", "city": "Bursa", "category": "historical_shrine", "lat": 40.1817, "lon": 29.0750, "radius_km": 0.05,
     "prompts": ["Green Tomb Yesil Turbe turquoise glazed hexagonal tiled mausoleum Sultan Mehmed I Bursa", "Yesil Turbe Green Mosque complex Bursa"]},

    # Konya
    {"name": "Mevlana Museum & Rumi Shrine, Konya", "city": "Konya", "category": "historical_shrine", "lat": 37.8708, "lon": 32.5056, "radius_km": 0.05,
     "prompts": ["Mevlana Museum turquoise fluted dome shrine of Jalal ad-Din Muhammad Rumi Konya", "Mevlana Celaleddin Rumi tomb and dervish museum Konya"]},

    # Trabzon
    {"name": "Sumela Monastery, Altindere Valley, Trabzon", "city": "Trabzon", "category": "unesco_world_heritage", "lat": 40.6900, "lon": 39.6583, "radius_km": 0.08,
     "prompts": ["Sumela Monastery ancient Greek Orthodox rock-hewn monastery clinging to vertical cliff Pontic Mountains Trabzon", "Sumela Monastery cliffside frescoes Trabzon"]},
    {"name": "Uzungol Alpine Lake & Mosque, Trabzon", "city": "Trabzon", "category": "natural_landmark", "lat": 40.6186, "lon": 40.2922, "radius_km": 0.1,
     "prompts": ["Uzungol alpine mountain lake white minaret mosque lush green pine mountain valley Trabzon", "Uzungol lake reflection and forest mountains Trabzon"]},

    # Cappadocia
    {"name": "Goreme Fairy Chimneys & Cave Dwellings, Cappadocia", "city": "Cappadocia", "category": "unesco_world_heritage", "lat": 38.6431, "lon": 34.8289, "radius_km": 0.5,
     "prompts": ["Goreme Fairy Chimneys volcanic tuff rock spires hot air balloons sunrise Cappadocia", "Cappadocia Goreme cave hotels and sandstone rock formations"]},
    {"name": "Uchisar Castle Rock Citadel, Cappadocia", "city": "Cappadocia", "category": "fortress", "lat": 38.6300, "lon": 34.8056, "radius_km": 0.08,
     "prompts": ["Uchisar Castle massive perforated volcanic rock fortress hill overlooking Cappadocia valleys", "Uchisar Castle rock pinnacle viewpoint Cappadocia"]},

    # Gaziantep
    {"name": "Zeugma Mosaic Museum, Sehitkamil, Gaziantep", "city": "Gaziantep", "category": "museum", "lat": 37.0750, "lon": 37.3861, "radius_km": 0.05,
     "prompts": ["Zeugma Mosaic Museum Gypsy Girl mosaic and Roman antiquities Gaziantep", "Zeugma Mosaic Museum modern building Gaziantep"]},
    {"name": "Gaziantep Castle (Gaziantep Kalesi), Sahinbey", "city": "Gaziantep", "category": "fortress", "lat": 37.0664, "lon": 37.3831, "radius_km": 0.05,
     "prompts": ["Gaziantep Castle stone hilltop fortress round bastions overlooking historic city Gaziantep", "Gaziantep Kalesi citadel walls"]},
]

with open(OUT_DIR / "turkey.json", "w", encoding="utf-8") as f:
    json.dump(turkey_spots, f, indent=2, ensure_ascii=False)
print(f"Saved turkey.json with {len(turkey_spots)} spots.")

# --------------------------------------------------------------------------
# 3. UNITED ARAB EMIRATES (Dubai, Abu Dhabi, Sharjah, Al Ain, Ras Al Khaimah, Fujairah, Ajman)
# --------------------------------------------------------------------------
uae_spots = [
    # Dubai
    {"name": "Burj Khalifa & Observation Deck, Downtown Dubai", "city": "Dubai", "category": "world_landmark", "lat": 25.1972, "lon": 55.2744, "radius_km": 0.05,
     "prompts": ["Burj Khalifa tallest skyscraper tiered spire glass facade Downtown Dubai", "Burj Khalifa tower rising above Dubai Mall fountain lake"]},
    {"name": "Burj Al Arab Luxury Sail Hotel, Jumeirah, Dubai", "city": "Dubai", "category": "luxury_hotel", "lat": 25.1412, "lon": 55.1853, "radius_km": 0.05,
     "prompts": ["Burj Al Arab iconic sail-shaped luxury hotel island helipad Jumeirah beach Dubai", "Burj Al Arab hotel white sail architecture Arabian Gulf"]},
    {"name": "Museum of the Future, Sheikh Zayed Road, Dubai", "city": "Dubai", "category": "museum", "lat": 25.2192, "lon": 55.2819, "radius_km": 0.05,
     "prompts": ["Museum of the Future stainless steel torus ring building Arabic calligraphy Sheikh Zayed Road Dubai", "Museum of the Future unique oval architectural landmark Dubai"]},
    {"name": "Dubai Frame, Zabeel Park, Dubai", "city": "Dubai", "category": "civic_monument", "lat": 25.2347, "lon": 25.2347, "radius_km": 0.05,
     "prompts": ["Dubai Frame giant golden picture frame architectural monument Zabeel Park Dubai", "The Dubai Frame observation bridge and glass bridge walkway"]},
    {"name": "The Dubai Mall & Dubai Fountain Lake, Downtown Dubai", "city": "Dubai", "category": "shopping_mall", "lat": 25.1986, "lon": 55.2797, "radius_km": 0.08,
     "prompts": ["The Dubai Mall grand shopping promenade and dancing fountain lake Downtown Dubai", "Dubai Mall fountain boardwalk and waterfront restaurants"]},
    {"name": "Palm Jumeirah & Atlantis The Palm, Dubai", "city": "Dubai", "category": "resort", "lat": 25.1303, "lon": 55.1172, "radius_km": 0.1,
     "prompts": ["Atlantis The Palm Arabian arch pink palace resort tip of Palm Jumeirah crescent Dubai", "Palm Jumeirah fronds luxury villas and Atlantis resort"]},
    {"name": "Dubai Marina Walk & Yacht Promenade, Dubai", "city": "Dubai", "category": "marina", "lat": 25.0789, "lon": 55.1389, "radius_km": 0.1,
     "prompts": ["Dubai Marina skyscrapers reflection luxury yachts waterway promenade Dubai", "Dubai Marina Walk high-rise residential towers waterfront"]},
    {"name": "Ain Dubai Giant Observation Wheel, Bluewaters Island, Dubai", "city": "Dubai", "category": "theme_park", "lat": 25.0797, "lon": 55.1214, "radius_km": 0.05,
     "prompts": ["Ain Dubai world's largest Ferris wheel Bluewaters Island JBR coastline Dubai", "Ain Dubai giant observation wheel steel legs and cabins"]},
    {"name": "Dubai Miracle Garden Floral Sculptures, Al Barsha, Dubai", "city": "Dubai", "category": "park", "lat": 25.0600, "lon": 55.2444, "radius_km": 0.08,
     "prompts": ["Dubai Miracle Garden colorful flower sculptures floral Emirates A380 airplane Dubai", "Dubai Miracle Garden vibrant floral arches and pathways"]},
    {"name": "Global Village Cultural Pavilions, Dubailand, Dubai", "city": "Dubai", "category": "theme_park", "lat": 25.0675, "lon": 55.3003, "radius_km": 0.15,
     "prompts": ["Global Village illuminated world pavilions facade replicas carnival park Dubai", "Global Village night lights and cultural pavilions Dubai"]},
    {"name": "Al Fahidi Historic District & Dubai Creek, Bur Dubai", "city": "Dubai", "category": "heritage_village", "lat": 25.2631, "lon": 55.3000, "radius_km": 0.08,
     "prompts": ["Al Fahidi historic windtower gypsum buildings narrow alleyways Bur Dubai Creek", "Bastakiya Al Fahidi heritage neighborhood and abras on Dubai Creek"]},

    # Abu Dhabi
    {"name": "Sheikh Zayed Grand Mosque, Abu Dhabi", "city": "Abu Dhabi", "category": "national_mosque", "lat": 24.4128, "lon": 54.4750, "radius_km": 0.08,
     "prompts": ["Sheikh Zayed Grand Mosque eighty-two white marble domes reflective pools Abu Dhabi", "Sheikh Zayed Grand Mosque grand floral courtyard and minarets Abu Dhabi"]},
    {"name": "Louvre Abu Dhabi Museum Dome, Saadiyat Island, Abu Dhabi", "city": "Abu Dhabi", "category": "museum", "lat": 24.5336, "lon": 54.3986, "radius_km": 0.08,
     "prompts": ["Louvre Abu Dhabi Jean Nouvel silver floating dome rain of light Arabian sea Saadiyat", "Louvre Abu Dhabi museum water promenade and geometric dome"]},
    {"name": "Qasr Al Watan Presidential Palace, Abu Dhabi", "city": "Abu Dhabi", "category": "historical_palace", "lat": 24.4633, "lon": 54.3056, "radius_km": 0.08,
     "prompts": ["Qasr Al Watan grand presidential palace white granite marble dome The Great Hall Abu Dhabi", "Qasr Al Watan presidential palace courtyard and fountain promenade"]},
    {"name": "Emirates Palace Mandarin Oriental, Corniche, Abu Dhabi", "city": "Abu Dhabi", "category": "luxury_hotel", "lat": 24.4617, "lon": 54.3175, "radius_km": 0.08,
     "prompts": ["Emirates Palace luxury Arabian palace hotel golden domes landscaped gardens Abu Dhabi", "Emirates Palace grand facade and triumphal archway Abu Dhabi"]},
    {"name": "Ferrari World Abu Dhabi Red Roof, Yas Island", "city": "Abu Dhabi", "category": "theme_park", "lat": 24.4836, "lon": 54.6075, "radius_km": 0.1,
     "prompts": ["Ferrari World iconic red aerodynamic curved roof yellow prancing horse logo Yas Island Abu Dhabi", "Ferrari World Abu Dhabi theme park exterior Yas Island"]},
    {"name": "Qasr Al Hosn Fort (White Fort), Abu Dhabi", "city": "Abu Dhabi", "category": "fortress", "lat": 24.4822, "lon": 54.3550, "radius_km": 0.05,
     "prompts": ["Qasr Al Hosn historic white coral stone watchtower and fortress Abu Dhabi", "Qasr Al Hosn oldest stone heritage building Abu Dhabi"]},
    {"name": "Abu Dhabi Corniche Beach & Skyline Promenade", "city": "Abu Dhabi", "category": "coast", "lat": 24.4694, "lon": 54.3417, "radius_km": 0.15,
     "prompts": ["Abu Dhabi Corniche beach turquoise Persian Gulf and modern skyscraper skyline", "Corniche road promenade and beach parks Abu Dhabi"]},

    # Sharjah
    {"name": "Al Noor Mosque, Buhaira Corniche, Sharjah", "city": "Sharjah", "category": "mosque", "lat": 25.3475, "lon": 55.3850, "radius_km": 0.05,
     "prompts": ["Al Noor Mosque Ottoman Turkish style cascading domes and two minarets Khaled Lagoon Sharjah", "Al Noor Mosque waterfront Buhaira Corniche Sharjah"]},
    {"name": "Al Majaz Waterfront & Musical Fountain, Sharjah", "city": "Sharjah", "category": "park", "lat": 25.3308, "lon": 55.3853, "radius_km": 0.08,
     "prompts": ["Al Majaz Waterfront palm promenades dining pavilions and musical fountain Khaled Lagoon Sharjah", "Al Majaz park waterfront skyline Sharjah"]},
    {"name": "Sharjah Central Souq (Blue Souk), Sharjah", "city": "Sharjah", "category": "commercial_market", "lat": 25.3486, "lon": 55.3889, "radius_km": 0.08,
     "prompts": ["Sharjah Central Souq Blue Souk twin traditional Islamic barrel vaulted buildings ceramic blue tiles", "Blue Souk Sharjah historic market buildings"]},

    # Al Ain
    {"name": "Jebel Hafeet Mountain Summit & Highway, Al Ain", "city": "Al Ain", "category": "mountain_peak", "lat": 24.0583, "lon": 55.7778, "radius_km": 1.0,
     "prompts": ["Jebel Hafeet winding mountain highway rocky desert limestone ridge Al Ain Abu Dhabi", "Jebel Hafeet summit viewpoint overlooking desert plains Al Ain"]},
    {"name": "Al Jahili Fort, Al Ain", "city": "Al Ain", "category": "fortress", "lat": 24.2167, "lon": 55.7528, "radius_km": 0.05,
     "prompts": ["Al Jahili Fort mud-brick battlements multi-tiered circular watchtower palm oasis Al Ain", "Al Jahili Fort courtyard and historic earthen towers Al Ain"]},

    # Ras Al Khaimah
    {"name": "Jebel Jais Mountain & Viewing Deck Park, Ras Al Khaimah", "city": "Ras Al Khaimah", "category": "mountain_peak", "lat": 25.9525, "lon": 56.1417, "radius_km": 1.0,
     "prompts": ["Jebel Jais highest mountain summit in UAE steep rocky switchback highway Ras Al Khaimah", "Jebel Jais Viewing Deck Park cliffs and canyons RAK"]},

    # Fujairah
    {"name": "Al Bidyah Mosque (Oldest UAE Mosque), Fujairah", "city": "Fujairah", "category": "historical_mosque", "lat": 25.4392, "lon": 56.3539, "radius_km": 0.05,
     "prompts": ["Al Bidyah Mosque ancient mud and stone four-domed mosque watchtowers Fujairah", "Al Bidyah oldest mosque in United Arab Emirates"]},
    {"name": "Fujairah Fort & Heritage Village, Fujairah", "city": "Fujairah", "category": "fortress", "lat": 25.1389, "lon": 56.3250, "radius_km": 0.05,
     "prompts": ["Fujairah Fort historic mud-brick castle and round watchtower rocky mound Fujairah", "Fujairah Fort and palm tree plantations"]}
]

with open(OUT_DIR / "uae.json", "w", encoding="utf-8") as f:
    json.dump(uae_spots, f, indent=2, ensure_ascii=False)
print(f"Saved uae.json with {len(uae_spots)} spots.")

# --------------------------------------------------------------------------
# 4. SAUDI ARABIA (Mecca, Medina, Riyadh, Jeddah, Dammam/Khobar, AlUla, Abha, Taif, Tabuk)
# --------------------------------------------------------------------------
saudi_spots = [
    # Mecca
    {"name": "The Kaaba & Masjid al-Haram, Mecca", "city": "Mecca", "category": "world_landmark", "lat": 21.4225, "lon": 39.8262, "radius_km": 0.05,
     "prompts": ["The Holy Kaaba black cloth kiswah mataf marble courtyard Masjid al-Haram Mecca", "Masjid al-Haram Grand Mosque marble courtyard and Kaaba Mecca"]},
    {"name": "Abraj Al Bait Makkah Clock Royal Tower, Mecca", "city": "Mecca", "category": "commercial_towers", "lat": 21.4189, "lon": 39.8256, "radius_km": 0.05,
     "prompts": ["Abraj Al Bait Makkah Clock Tower giant four-faced illuminated clock spire towering over Kaaba", "Makkah Royal Clock Tower skyscraper Mecca"]},
    {"name": "Mount Arafat (Jabal al-Rahmah), Mecca", "city": "Mecca", "category": "historical_monument", "lat": 21.3547, "lon": 39.9842, "radius_km": 0.1,
     "prompts": ["Jabal al-Rahmah Mount of Mercy stone pillar granite hill plains of Arafat Mecca", "Mount Arafat white pillar monument during Hajj pilgrimage"]},
    {"name": "Jabal al-Nour & Hira Cave, Mecca", "city": "Mecca", "category": "mountain_peak", "lat": 21.4578, "lon": 39.8592, "radius_km": 0.1,
     "prompts": ["Jabal al-Nour Mountain of Light rugged rocky mountain peak Hira Cave Mecca", "Jabal al-Nour crest and rocky trail overlooking Mecca city"]},

    # Medina
    {"name": "Al-Masjid an-Nabawi (Prophet's Mosque Green Dome), Medina", "city": "Medina", "category": "world_landmark", "lat": 24.4672, "lon": 39.6111, "radius_km": 0.05,
     "prompts": ["Al-Masjid an-Nabawi Prophet's Mosque iconic Green Dome and giant folding umbrella courtyard Medina", "Prophet's Mosque marble plaza Green Dome and minarets Medina"]},
    {"name": "Quba Mosque, Medina", "city": "Medina", "category": "historical_mosque", "lat": 24.4394, "lon": 39.6172, "radius_km": 0.05,
     "prompts": ["Quba Mosque first mosque in Islam white domes four minarets palm courtyard Medina", "Masjid Quba white marble portico Medina"]},
    {"name": "Mount Uhud & Archers Hill (Jabal al-Rumat), Medina", "city": "Medina", "category": "mountain_peak", "lat": 24.5033, "lon": 39.6125, "radius_km": 0.2,
     "prompts": ["Mount Uhud red volcanic mountain ridge and Archers Hill cemetery Medina", "Jabal Uhud rocky mountain backdrop Medina"]},

    # Riyadh
    {"name": "Kingdom Centre & Sky Bridge, Riyadh", "city": "Riyadh", "category": "commercial_towers", "lat": 24.7114, "lon": 46.6744, "radius_km": 0.05,
     "prompts": ["Kingdom Centre skyscraper inverted parabolic arch and illuminated Sky Bridge Riyadh", "Kingdom Tower modern reflective skyscraper Olaya Riyadh"]},
    {"name": "Al Faisaliyah Centre, Olaya, Riyadh", "city": "Riyadh", "category": "commercial_towers", "lat": 24.6903, "lon": 46.6853, "radius_km": 0.05,
     "prompts": ["Al Faisaliyah Centre pyramid skyscraper golden glass sphere top King Fahd Road Riyadh", "Al Faisaliyah Tower modern high-rise Riyadh"]},
    {"name": "Historic Diriyah & At-Turaif District, Riyadh", "city": "Riyadh", "category": "unesco_world_heritage", "lat": 24.7333, "lon": 46.5750, "radius_km": 0.1,
     "prompts": ["At-Turaif UNESCO World Heritage district mud-brick palaces Wadi Hanifa Diriyah Riyadh", "Diriyah mud-brick fortress and heritage buildings Riyadh"]},
    {"name": "Masmak Fortress (Al Masmak Palace), Deira, Riyadh", "city": "Riyadh", "category": "fortress", "lat": 24.6311, "lon": 46.7133, "radius_km": 0.05,
     "prompts": ["Al Masmak Fortress clay and mud-brick citadel four conical watchtowers historic Riyadh", "Masmak Palace fortress wooden door Riyadh"]},
    {"name": "King Abdullah Financial District (KAFD) Towers, Riyadh", "city": "Riyadh", "category": "commercial_district", "lat": 24.7667, "lon": 46.6389, "radius_km": 0.15,
     "prompts": ["KAFD King Abdullah Financial District futuristic geometric crystal skyscrapers Riyadh", "KAFD financial towers skyline Riyadh"]},
    {"name": "Edge of the World (Jabal Fihrayn), Riyadh Province", "city": "Riyadh", "category": "natural_landmark", "lat": 24.9458, "lon": 45.9908, "radius_km": 0.5,
     "prompts": ["Edge of the World Jabal Fihrayn dramatic sheer vertical limestone cliff drop Tuwaiq Escarpment Riyadh", "Edge of the World cliff edge panoramic desert view"]},

    # Jeddah
    {"name": "King Fahd's Fountain, Jeddah Corniche", "city": "Jeddah", "category": "civic_monument", "lat": 21.5161, "lon": 39.1464, "radius_km": 0.05,
     "prompts": ["King Fahd Fountain world's tallest seawater fountain jet Red Sea Jeddah Corniche", "Jeddah fountain water plume illuminated evening Red Sea"]},
    {"name": "Al-Balad Historic District (Old Jeddah), Jeddah", "city": "Jeddah", "category": "unesco_world_heritage", "lat": 21.4858, "lon": 39.1878, "radius_km": 0.08,
     "prompts": ["Historic Al-Balad coral stone tower houses intricate carved wooden roshan balconies Jeddah", "Al-Balad Old Jeddah ancient street and wooden latticework"]},
    {"name": "Al-Rahmah Floating Mosque, Jeddah Corniche", "city": "Jeddah", "category": "mosque", "lat": 21.5906, "lon": 39.1103, "radius_km": 0.05,
     "prompts": ["Al-Rahmah Floating Mosque white turquoise domed mosque built on stilts over Red Sea Jeddah", "Floating Mosque Jeddah Red Sea promenade"]},

    # Al Khobar & Dammam
    {"name": "King Abdulaziz Center for World Culture (Ithra), Dhahran", "city": "Dammam", "category": "museum", "lat": 26.3350, "lon": 50.1200, "radius_km": 0.08,
     "prompts": ["Ithra King Abdulaziz Center smooth pebble-shaped stainless steel architecture Dhahran Dammam", "Ithra cultural center monumental modern landmark"]},
    {"name": "Khobar Water Tower & Corniche, Al Khobar", "city": "Dammam", "category": "civic_monument", "lat": 26.2867, "lon": 50.2217, "radius_km": 0.05,
     "prompts": ["Khobar Water Tower modern illuminated beacon Corniche Arabian Gulf Al Khobar", "Al Khobar water tower and seafront park"]},

    # AlUla
    {"name": "Hegra (Madain Salih - Tomb of Lihyan son of Kuza), AlUla", "city": "AlUla", "category": "unesco_world_heritage", "lat": 26.8000, "lon": 37.9500, "radius_km": 0.2,
     "prompts": ["Hegra Madain Salih Qasr al-Farid carved Nabataean tomb sandstone monolith desert AlUla", "Qasr al-Farid lonely tomb Hegra UNESCO AlUla"]},
    {"name": "Elephant Rock (Jabal AlFil), AlUla", "city": "AlUla", "category": "natural_landmark", "lat": 26.6869, "lon": 37.9897, "radius_km": 0.08,
     "prompts": ["Elephant Rock Jabal AlFil natural elephant-shaped red sandstone arch desert AlUla", "Elephant Rock AlUla illuminated at night"]},
    {"name": "Maraya Concert Hall (Mirror Building), Ashar Valley, AlUla", "city": "AlUla", "category": "civic_building", "lat": 26.7028, "lon": 37.8972, "radius_km": 0.05,
     "prompts": ["Maraya Concert Hall giant mirrored cube building reflecting red canyon desert Ashar Valley AlUla", "Maraya mirror building AlUla"]},

    # Abha & Asir
    {"name": "Rijal Almaa Heritage Village, Asir Province, Abha", "city": "Abha", "category": "unesco_world_heritage", "lat": 18.2167, "lon": 42.3167, "radius_km": 0.08,
     "prompts": ["Rijal Almaa gingerbread multi-story stone castles white painted windows Asir mountains Abha", "Rijal Almaa traditional stone fortress village"]},
    {"name": "Green Mountain (Jabal Thera), Abha", "city": "Abha", "category": "viewpoint", "lat": 18.2100, "lon": 42.5028, "radius_km": 0.05,
     "prompts": ["Green Mountain Jabal Thera illuminated emerald green peak cable car Abha", "Jabal Thera Green Mountain overlook Abha"]}
]

with open(OUT_DIR / "saudi_arabia.json", "w", encoding="utf-8") as f:
    json.dump(saudi_spots, f, indent=2, ensure_ascii=False)
print(f"Saved saudi_arabia.json with {len(saudi_spots)} spots.")

# --------------------------------------------------------------------------
# 5. QATAR, KUWAIT, BAHRAIN, OMAN, EGYPT, INDIA, IRAN, IRAQ, YEMEN, SYRIA, ISRAEL_PALESTINE & GLOBAL
# --------------------------------------------------------------------------
# (Generating each respective regional catalog)
qatar_spots = [
    {"name": "Museum of Islamic Art (MIA), Doha, Qatar", "city": "Doha", "category": "museum", "lat": 25.2953, "lon": 51.5392, "radius_km": 0.05,
     "prompts": ["Museum of Islamic Art I.M. Pei geometric limestone cube architecture Doha harbor Qatar", "MIA Museum of Islamic Art dhow boats and Doha skyline"]},
    {"name": "Souq Waqif Heritage Bazaar, Doha, Qatar", "city": "Doha", "category": "commercial_market", "lat": 25.2867, "lon": 51.5333, "radius_km": 0.08,
     "prompts": ["Souq Waqif mud-rendered traditional market buildings spice stalls falcon souq Doha", "Souq Waqif bustling evening street dining Doha"]},
    {"name": "Katara Cultural Village & Amphitheatre, Doha, Qatar", "city": "Doha", "category": "civic_building", "lat": 25.3589, "lon": 51.5258, "radius_km": 0.08,
     "prompts": ["Katara Cultural Village classical Greco-Roman amphitheatre pigeon towers Doha", "Katara Cultural Village mosque and promenade Doha"]},
    {"name": "The Pearl-Qatar Luxury Island Marina, Doha, Qatar", "city": "Doha", "category": "marina", "lat": 25.3700, "lon": 51.5500, "radius_km": 0.1,
     "prompts": ["The Pearl Qatar artificial island luxury yacht marina Mediterranean pastel towers Doha", "The Pearl Porto Arabia promenade Doha"]},
    {"name": "National Museum of Qatar (Desert Rose), Doha", "city": "Doha", "category": "museum", "lat": 25.2881, "lon": 51.5486, "radius_km": 0.05,
     "prompts": ["National Museum of Qatar Jean Nouvel interlocking desert rose disk architecture Doha", "NMoQ National Museum of Qatar exterior curved disks"]},
    {"name": "Lusail Iconic Stadium & Katara Towers, Lusail, Qatar", "city": "Lusail", "category": "stadium", "lat": 25.4206, "lon": 51.4903, "radius_km": 0.1,
     "prompts": ["Lusail Iconic Stadium golden bowl World Cup arena and Katara crescent towers Lusail", "Lusail Stadium golden woven bowl facade Qatar"]}
]
with open(OUT_DIR / "qatar.json", "w", encoding="utf-8") as f:
    json.dump(qatar_spots, f, indent=2, ensure_ascii=False)

kuwait_spots = [
    {"name": "Kuwait Towers, Arabian Gulf Street, Kuwait City", "city": "Kuwait City", "category": "national_monument", "lat": 29.3897, "lon": 48.0033, "radius_km": 0.05,
     "prompts": ["Kuwait Towers three slender towers blue-green enameled steel spheres Arabian Gulf Street Kuwait City", "Kuwait Towers landmark observation spheres and gulf coastline"]},
    {"name": "Grand Mosque of Kuwait (Al-Masjid Al-Kabir), Kuwait City", "city": "Kuwait City", "category": "national_mosque", "lat": 29.3789, "lon": 47.9750, "radius_km": 0.05,
     "prompts": ["Grand Mosque of Kuwait traditional Islamic architecture central dome and minaret Kuwait City", "Al-Masjid Al-Kabir Grand Mosque Kuwait interior dome"]},
    {"name": "The Avenues Mall, Al-Rai, Kuwait", "city": "Kuwait City", "category": "shopping_mall", "lat": 29.3039, "lon": 47.9356, "radius_km": 0.1,
     "prompts": ["The Avenues Mall Kuwait Grand Avenue transparent glass arched roof palm trees shopping district", "The Avenues Mall interior European street promenade Kuwait"]},
    {"name": "Al Shaheed Park & Constitution Monument, Kuwait City", "city": "Kuwait City", "category": "park", "lat": 29.3667, "lon": 47.9944, "radius_km": 0.08,
     "prompts": ["Al Shaheed Park modern urban botanical park reflection pools Kuwait City", "Al Shaheed Park monument and green gardens Kuwait"]}
]
with open(OUT_DIR / "kuwait.json", "w", encoding="utf-8") as f:
    json.dump(kuwait_spots, f, indent=2, ensure_ascii=False)

bahrain_spots = [
    {"name": "Bab Al Bahrain & Manama Souq, Manama, Bahrain", "city": "Manama", "category": "civic_monument", "lat": 26.2344, "lon": 50.5756, "radius_km": 0.05,
     "prompts": ["Bab Al Bahrain historic arched gateway building entrance to Manama Souq Bahrain", "Bab Al Bahrain twin arches and Customs square Manama"]},
    {"name": "Bahrain World Trade Center, Manama, Bahrain", "city": "Manama", "category": "commercial_towers", "lat": 26.2394, "lon": 50.5819, "radius_km": 0.05,
     "prompts": ["Bahrain World Trade Center twin sail-shaped skyscraper towers three wind turbines Manama", "Bahrain WTC towers wind turbines Manama skyline"]},
    {"name": "Al Fateh Grand Mosque, Manama, Bahrain", "city": "Manama", "category": "national_mosque", "lat": 26.2192, "lon": 50.5981, "radius_km": 0.05,
     "prompts": ["Al Fateh Grand Mosque world's largest fiberglass dome twin minarets Manama Bahrain", "Al Fateh Mosque white marble courtyard and domes"]},
    {"name": "Qal'at al-Bahrain (Bahrain Fort), Karbabad, Bahrain", "city": "Manama", "category": "unesco_world_heritage", "lat": 26.2339, "lon": 50.5208, "radius_km": 0.08,
     "prompts": ["Qal'at al-Bahrain ancient Portuguese stone fort on sea coastline UNESCO Bahrain", "Bahrain Fort stone bastions overlooking modern skyline"]}
]
with open(OUT_DIR / "bahrain.json", "w", encoding="utf-8") as f:
    json.dump(bahrain_spots, f, indent=2, ensure_ascii=False)

oman_spots = [
    {"name": "Sultan Qaboos Grand Mosque, Muscat, Oman", "city": "Muscat", "category": "national_mosque", "lat": 23.5839, "lon": 58.3889, "radius_km": 0.08,
     "prompts": ["Sultan Qaboos Grand Mosque Indian sandstone central dome five minarets Persian carpet Muscat", "Sultan Qaboos Grand Mosque marble courtyard and archways Muscat"]},
    {"name": "Mutrah Corniche & Souq, Muscat, Oman", "city": "Muscat", "category": "commercial_market", "lat": 23.6231, "lon": 58.5636, "radius_km": 0.08,
     "prompts": ["Mutrah Corniche harbor waterfront traditional dhows giant incense burner monument Muscat", "Mutrah Souq ornate stained glass lattice entrance Muscat"]},
    {"name": "Al Alam Palace & Twin Portuguese Forts, Old Muscat", "city": "Muscat", "category": "historical_palace", "lat": 23.6158, "lon": 58.5947, "radius_km": 0.05,
     "prompts": ["Al Alam Palace Sultan's ceremonial palace gold and blue mushroom columns Old Muscat", "Al Alam Palace facade and Al Jalali Fort background Muscat"]},
    {"name": "Nizwa Fort & Round Tower, Nizwa, Oman", "city": "Nizwa", "category": "fortress", "lat": 22.9333, "lon": 57.5306, "radius_km": 0.05,
     "prompts": ["Nizwa Fort massive circular stone tower battlements and surrounding date palm oasis Oman", "Nizwa Fort cannon parapet and Old Souq Oman"]},
    {"name": "Jebel Shams (Grand Canyon of Arabia), Al Hamra, Oman", "city": "Nizwa", "category": "mountain_peak", "lat": 23.2389, "lon": 57.2647, "radius_km": 1.0,
     "prompts": ["Jebel Shams mountain Balcony Walk sheer vertical canyon abyss Grand Canyon of Oman", "Jebel Shams summit rocky cliffs overlooking deep wadi"]}
]
with open(OUT_DIR / "oman.json", "w", encoding="utf-8") as f:
    json.dump(oman_spots, f, indent=2, ensure_ascii=False)

egypt_spots = [
    {"name": "Great Pyramid of Giza & Sphinx, Giza, Cairo, Egypt", "city": "Cairo", "category": "world_landmark", "lat": 29.9792, "lon": 31.1342, "radius_km": 0.1,
     "prompts": ["Great Pyramid of Giza Khufu limestone pyramid and Great Sphinx desert Cairo Egypt", "Pyramids of Giza Khafre pyramid casing stone and Sphinx"]},
    {"name": "Grand Egyptian Museum (GEM), Giza, Egypt", "city": "Cairo", "category": "museum", "lat": 29.9950, "lon": 31.1200, "radius_km": 0.08,
     "prompts": ["Grand Egyptian Museum GEM triangular translucent alabaster facade Ramesses II statue Giza", "Grand Egyptian Museum grand staircase and entrance Giza"]},
    {"name": "Citadel of Saladin & Mosque of Muhammad Ali, Cairo", "city": "Cairo", "category": "historical_mosque", "lat": 30.0289, "lon": 31.2597, "radius_km": 0.08,
     "prompts": ["Citadel of Saladin and Mosque of Muhammad Ali alabaster twin minarets overlooking Cairo", "Muhammad Ali Alabaster Mosque courtyard and dome Cairo Citadel"]},
    {"name": "Khan el-Khalili Historic Bazaar, Islamic Cairo", "city": "Cairo", "category": "commercial_market", "lat": 30.0475, "lon": 31.2622, "radius_km": 0.08,
     "prompts": ["Khan el-Khalili historic medieval bazaar brass lamps spices Mamluk arches Cairo", "Khan el-Khalili narrow stone shopping street Islamic Cairo"]},
    {"name": "Citadel of Qaitbay, Alexandria, Egypt", "city": "Alexandria", "category": "fortress", "lat": 31.2139, "lon": 29.8856, "radius_km": 0.05,
     "prompts": ["Citadel of Qaitbay 15th-century stone defensive fortress Pharos lighthouse site Alexandria", "Qaitbay Citadel Mediterranean sea fortress Alexandria"]},
    {"name": "Karnak Temple Complex & Hypostyle Hall, Luxor, Egypt", "city": "Luxor", "category": "unesco_world_heritage", "lat": 25.7189, "lon": 32.6572, "radius_km": 0.1,
     "prompts": ["Karnak Temple Great Hypostyle Hall 134 colossal sandstone papyrus columns Luxor", "Karnak Temple avenue of ram-headed sphinxes Luxor Egypt"]},
    {"name": "Abu Simbel Sun Temples of Ramesses II, Aswan, Egypt", "city": "Aswan", "category": "unesco_world_heritage", "lat": 22.3369, "lon": 31.6256, "radius_km": 0.05,
     "prompts": ["Abu Simbel four colossal seated statues of Ramesses II rock-cut temple Lake Nasser Aswan", "Abu Simbel grand rock temple facade Egypt"]}
]
with open(OUT_DIR / "egypt.json", "w", encoding="utf-8") as f:
    json.dump(egypt_spots, f, indent=2, ensure_ascii=False)

india_spots = [
    {"name": "Taj Mahal & Yamuna River, Agra, India", "city": "Agra", "category": "world_landmark", "lat": 27.1750, "lon": 78.0422, "radius_km": 0.05,
     "prompts": ["Taj Mahal white marble Mughal mausoleum dome reflecting pool and minarets Agra India", "Taj Mahal symmetry gardens and central dome Yamuna river"]},
    {"name": "India Gate & Kartavya Path, New Delhi, India", "city": "Delhi", "category": "national_monument", "lat": 28.6128, "lon": 77.2294, "radius_km": 0.05,
     "prompts": ["India Gate triumphal war memorial sandstone arch Kartavya Path New Delhi", "India Gate canopy and ceremonial avenue Delhi"]},
    {"name": "Red Fort (Lal Qila), Old Delhi, India", "city": "Delhi", "category": "unesco_world_heritage", "lat": 28.6561, "lon": 77.2411, "radius_km": 0.08,
     "prompts": ["Red Fort Lal Qila red sandstone Mughal fortress Lahore Gate Old Delhi", "Red Fort massive defensive walls and battlements Delhi"]},
    {"name": "Qutub Minar & Iron Pillar, Mehrauli, Delhi, India", "city": "Delhi", "category": "unesco_world_heritage", "lat": 28.5244, "lon": 77.1856, "radius_km": 0.05,
     "prompts": ["Qutub Minar fluted red sandstone minaret tower balcony carvings Mehrauli Delhi", "Qutub Minar complex and Quwwat-ul-Islam mosque"]},
    {"name": "Lotus Temple (Bahai House of Worship), New Delhi", "city": "Delhi", "category": "temple", "lat": 28.5533, "lon": 77.2589, "radius_km": 0.05,
     "prompts": ["Lotus Temple white marble lotus flower petal architecture reflection ponds New Delhi", "Lotus Temple Bahai prayer hall gardens Delhi"]},
    {"name": "Gateway of India & Taj Mahal Palace Hotel, Mumbai", "city": "Mumbai", "category": "national_monument", "lat": 18.9220, "lon": 72.8347, "radius_km": 0.05,
     "prompts": ["Gateway of India basalt triumphal arch and Taj Mahal Palace Hotel Mumbai harbor", "Gateway of India waterfront monument Colaba Mumbai"]},
    {"name": "Hawa Mahal (Palace of Winds), Jaipur, Rajasthan", "city": "Jaipur", "category": "historical_palace", "lat": 26.9239, "lon": 75.8267, "radius_km": 0.05,
     "prompts": ["Hawa Mahal Palace of Winds pink honeycomb sandstone facade jharokha windows Jaipur", "Hawa Mahal five-story pink palace street view Jaipur"]},
    {"name": "Golden Temple (Harmandir Sahib), Amritsar, Punjab", "city": "Amritsar", "category": "temple", "lat": 31.6200, "lon": 74.8764, "radius_km": 0.05,
     "prompts": ["Golden Temple Harmandir Sahib gold-plated gurdwara surrounded by sacred Amrit Sarovar lake Amritsar", "Golden Temple illuminated at night reflecting in holy pool"]},
    {"name": "Varanasi Ghats & Kashi Vishwanath Temple, Varanasi", "city": "Varanasi", "category": "heritage_site", "lat": 25.3108, "lon": 83.0106, "radius_km": 0.1,
     "prompts": ["Dashashwamedh Ghat Ganga Aarti ceremony steps holy Ganges river Varanasi", "Varanasi ghats ancient riverfront temples and boats Ganges"]}
]
with open(OUT_DIR / "india.json", "w", encoding="utf-8") as f:
    json.dump(india_spots, f, indent=2, ensure_ascii=False)

iran_spots = [
    {"name": "Azadi Tower (Freedom Monument), Tehran, Iran", "city": "Tehran", "category": "national_monument", "lat": 35.6997, "lon": 51.3381, "radius_km": 0.05,
     "prompts": ["Azadi Tower white marble inverted Y-shaped monument Azadi Square Tehran", "Shahyad Azadi Tower fountain plaza Tehran"]},
    {"name": "Milad Tower, Tehran, Iran", "city": "Tehran", "category": "commercial_towers", "lat": 35.7447, "lon": 51.3753, "radius_km": 0.05,
     "prompts": ["Milad Tower sixth-tallest telecommunications tower head pod Alborz mountains Tehran", "Milad Tower observation deck overlooking Tehran skyline"]},
    {"name": "Naqsh-e Jahan Square & Shah Mosque, Isfahan, Iran", "city": "Isfahan", "category": "unesco_world_heritage", "lat": 32.6575, "lon": 51.6778, "radius_km": 0.1,
     "prompts": ["Naqsh-e Jahan Square vast Safavid royal plaza turquoise Shah Mosque reflection pool Isfahan", "Shah Mosque Imam Mosque seven-colored tilework entrance portal Isfahan"]},
    {"name": "Nasir al-Mulk (Pink Mosque), Shiraz, Iran", "city": "Shiraz", "category": "historical_mosque", "lat": 29.6083, "lon": 52.5486, "radius_km": 0.05,
     "prompts": ["Nasir al-Mulk Pink Mosque kaleidoscope stained glass windows casting rainbow light Persian carpets Shiraz", "Pink Mosque Shiraz interior colorful morning sun"]},
    {"name": "Persepolis (Takht-e Jamshid), Shiraz, Fars", "city": "Shiraz", "category": "unesco_world_heritage", "lat": 29.9353, "lon": 52.8914, "radius_km": 0.15,
     "prompts": ["Persepolis Takht-e Jamshid ancient Achaemenid ceremonial capital stone columns Gate of All Nations", "Persepolis ruins monumental stairways and bas-reliefs Shiraz"]}
]
with open(OUT_DIR / "iran.json", "w", encoding="utf-8") as f:
    json.dump(iran_spots, f, indent=2, ensure_ascii=False)

iraq_spots = [
    {"name": "Al-Mustansiriya Madrasah & Tigris River, Baghdad", "city": "Baghdad", "category": "historical_building", "lat": 33.3381, "lon": 44.3889, "radius_km": 0.05,
     "prompts": ["Mustansiriya Madrasah medieval Abbasid brick arched university on Tigris riverbank Baghdad", "Mustansiriya courtyard and geometric brickwork Baghdad"]},
    {"name": "Swords of Qadisiyah (Hands of Victory), Baghdad, Iraq", "city": "Baghdad", "category": "national_monument", "lat": 33.3058, "lon": 44.3833, "radius_km": 0.05,
     "prompts": ["Hands of Victory Swords of Qadisiyah massive crossed bronze swords archway parade ground Baghdad", "Swords of Qadisiyah triumphal arch Baghdad"]},
    {"name": "Imam Ali Holy Shrine, Najaf, Iraq", "city": "Najaf", "category": "historical_shrine", "lat": 31.9961, "lon": 44.3142, "radius_km": 0.05,
     "prompts": ["Imam Ali Holy Shrine pure gold dome and minarets grand tiled courtyard Najaf Iraq", "Imam Ali Shrine golden dome and pilgrims plaza Najaf"]},
    {"name": "Imam Husayn Holy Shrine, Karbala, Iraq", "city": "Karbala", "category": "historical_shrine", "lat": 32.6161, "lon": 44.0325, "radius_km": 0.05,
     "prompts": ["Imam Husayn Holy Shrine illuminated golden dome and minarets Karbala Iraq", "Imam Husayn and Al-Abbas holy shrines pedestrian plaza Karbala"]},
    {"name": "Erbil Citadel (Hawler Citadel), Erbil, Kurdistan, Iraq", "city": "Erbil", "category": "unesco_world_heritage", "lat": 36.1911, "lon": 44.0092, "radius_km": 0.08,
     "prompts": ["Erbil Citadel ancient fortified tell mound continuous mud-brick perimeter wall Erbil", "Hawler Citadel entrance gate and central fountains Erbil"]}
]
with open(OUT_DIR / "iraq.json", "w", encoding="utf-8") as f:
    json.dump(iraq_spots, f, indent=2, ensure_ascii=False)

yemen_spots = [
    {"name": "Old City of Sanaa Tower Houses & Bab al-Yaman, Yemen", "city": "Sanaa", "category": "unesco_world_heritage", "lat": 15.3547, "lon": 44.2156, "radius_km": 0.1,
     "prompts": ["Old City of Sanaa multi-story rammed earth tower houses white gypsum filigree windows Yemen", "Bab al-Yaman medieval fortified gateway to Old Sanaa"]},
    {"name": "Dar al-Hajar (Rock Palace), Wadi Dhahr, Sanaa", "city": "Sanaa", "category": "historical_palace", "lat": 15.4411, "lon": 44.1294, "radius_km": 0.05,
     "prompts": ["Dar al-Hajar iconic royal palace perched atop towering natural rock pinnacle Wadi Dhahr Sanaa", "Rock Palace Dar al-Hajar Yemen landmark"]},
    {"name": "Shibam Hadhramaut Mud Skyscraper City, Yemen", "city": "Shibam", "category": "unesco_world_heritage", "lat": 15.9264, "lon": 48.6278, "radius_km": 0.1,
     "prompts": ["Shibam Hadhramaut ancient high-rise mud brick skyscrapers Manhattan of the Desert Yemen", "Walled city of Shibam mud tower apartments desert oasis"]}
]
with open(OUT_DIR / "yemen.json", "w", encoding="utf-8") as f:
    json.dump(yemen_spots, f, indent=2, ensure_ascii=False)

syria_spots = [
    {"name": "Umayyad Mosque (Great Mosque of Damascus), Syria", "city": "Damascus", "category": "unesco_world_heritage", "lat": 33.5119, "lon": 36.3067, "radius_km": 0.05,
     "prompts": ["Umayyad Mosque marble courtyard golden mosaic pavilions and three minarets Old Damascus", "Great Mosque of Damascus Umayyad courtyard and Barada mosaics"]},
    {"name": "Citadel of Aleppo, Aleppo, Syria", "city": "Aleppo", "category": "unesco_world_heritage", "lat": 36.1992, "lon": 37.1628, "radius_km": 0.08,
     "prompts": ["Citadel of Aleppo massive medieval limestone fortress stone bridge and moat hill Aleppo", "Aleppo Citadel grand fortified entrance gateway"]},
    {"name": "Ancient City of Palmyra Roman Colonade, Syria", "city": "Palmyra", "category": "unesco_world_heritage", "lat": 34.5514, "lon": 38.2689, "radius_km": 0.15,
     "prompts": ["Palmyra Monumental Colonnade Roman stone arches and Temple of Bel desert ruins Syria", "Ancient Roman ruins of Palmyra Tadmor oasis"]}
]
with open(OUT_DIR / "syria.json", "w", encoding="utf-8") as f:
    json.dump(syria_spots, f, indent=2, ensure_ascii=False)

israel_palestine_spots = [
    {"name": "Dome of the Rock (Qubbat as-Sakhrah), Jerusalem", "city": "Jerusalem", "category": "world_landmark", "lat": 31.7780, "lon": 35.2354, "radius_km": 0.05,
     "prompts": ["Dome of the Rock iconic golden dome octagonal blue Persian ceramic tilework Temple Mount Jerusalem", "Qubbat as-Sakhrah Golden Dome and marble plaza Jerusalem"]},
    {"name": "Western Wall (Kotel) & Plaza, Jerusalem", "city": "Jerusalem", "category": "world_landmark", "lat": 31.7767, "lon": 35.2344, "radius_km": 0.05,
     "prompts": ["Western Wall Kotel ancient Herodian massive limestone prayer wall and outdoor plaza Jerusalem", "Western Wall and Temple Mount esplanade Jerusalem"]},
    {"name": "Church of the Holy Sepulchre, Christian Quarter, Jerusalem", "city": "Jerusalem", "category": "historical_church", "lat": 31.7785, "lon": 35.2297, "radius_km": 0.05,
     "prompts": ["Church of the Holy Sepulchre Romanesque stone facade and belltower Old City Jerusalem", "Holy Sepulchre courtyard and entrance Jerusalem"]},
    {"name": "Tel Aviv White City Bauhaus Architecture & Rothschild Blvd", "city": "Tel Aviv", "category": "unesco_world_heritage", "lat": 32.0631, "lon": 34.7739, "radius_km": 0.1,
     "prompts": ["Tel Aviv White City Bauhaus international style rounded balconies tree-lined Rothschild Boulevard", "Rothschild Boulevard modern Bauhaus buildings Tel Aviv"]},
    {"name": "Jaffa Old Port & Clock Tower, Tel Aviv-Yafo", "city": "Tel Aviv", "category": "heritage_village", "lat": 32.0542, "lon": 34.7522, "radius_km": 0.08,
     "prompts": ["Old Jaffa stone port lighthouse and limestone alleys overlooking Tel Aviv coastline", "Jaffa Clock Tower Ottoman stone monument square"]}
]
with open(OUT_DIR / "israel_palestine.json", "w", encoding="utf-8") as f:
    json.dump(israel_palestine_spots, f, indent=2, ensure_ascii=False)

global_iconic = [
    {"name": "Eiffel Tower & Champ de Mars, Paris, France", "city": "Paris", "category": "world_landmark", "lat": 48.8584, "lon": 2.2945, "radius_km": 0.05,
     "prompts": ["Eiffel Tower wrought-iron lattice tower Champ de Mars Seine river Paris France", "Eiffel Tower landmark Paris"]},
    {"name": "Colosseum & Arch of Constantine, Rome, Italy", "city": "Rome", "category": "world_landmark", "lat": 41.8902, "lon": 12.4922, "radius_km": 0.05,
     "prompts": ["Colosseum iconic ancient Roman amphitheatre travertine arches Rome Italy", "Flavian Amphitheatre Colosseum exterior Rome"]},
    {"name": "Big Ben & Palace of Westminster, London, UK", "city": "London", "category": "world_landmark", "lat": 51.5007, "lon": -0.1246, "radius_km": 0.05,
     "prompts": ["Big Ben Elizabeth Tower clock face and Houses of Parliament Thames bridge London", "Palace of Westminster Big Ben clock tower London"]},
    {"name": "Statue of Liberty & New York Harbor, USA", "city": "New York", "category": "world_landmark", "lat": 40.6892, "lon": -74.0445, "radius_km": 0.05,
     "prompts": ["Statue of Liberty copper green neoclassical statue torch Liberty Island New York Harbor", "Statue of Liberty Manhattan skyline background"]},
    {"name": "Sydney Opera House & Harbor Bridge, Sydney, Australia", "city": "Sydney", "category": "world_landmark", "lat": -33.8568, "lon": 151.2153, "radius_km": 0.05,
     "prompts": ["Sydney Opera House shell sail roof white ceramic tiles Sydney Harbour Australia", "Sydney Opera House and Harbour Bridge"]},
    {"name": "Christ the Redeemer (Cristo Redentor), Rio de Janeiro, Brazil", "city": "Rio de Janeiro", "category": "world_landmark", "lat": -22.9519, "lon": -43.2105, "radius_km": 0.05,
     "prompts": ["Christ the Redeemer colossal Art Deco statue outstretched arms Corcovado Mountain Rio de Janeiro", "Cristo Redentor summit view Rio de Janeiro"]},
    {"name": "Machu Picchu Inca Citadel, Andes, Peru", "city": "Cusco", "category": "world_landmark", "lat": -13.1631, "lon": -72.5450, "radius_km": 0.1,
     "prompts": ["Machu Picchu ancient Inca stone ruins agricultural terraces Huayna Picchu mountain peak Peru", "Machu Picchu citadel terraces Andes mountains"]},
    {"name": "Great Wall of China (Mutianyu), Beijing, China", "city": "Beijing", "category": "world_landmark", "lat": 40.4319, "lon": 116.5704, "radius_km": 0.5,
     "prompts": ["Great Wall of China stone watchtowers winding across mountainous ridgeline Mutianyu", "Great Wall stone battlements green mountains Beijing"]}
]
with open(OUT_DIR / "global_iconic.json", "w", encoding="utf-8") as f:
    json.dump(global_iconic, f, indent=2, ensure_ascii=False)

print("\nAll 16 landmark JSON files generated successfully in data/landmarks/")
