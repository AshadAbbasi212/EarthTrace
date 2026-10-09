"""Curated Landmark, Heritage, and Architectural Vision Perception Database.

Provides high-precision zero-shot vision-language landmark recognition
for world heritage sites, historical fortresses, national monuments,
famous buildings, and university campuses.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
from PIL import Image

logger = logging.getLogger("geolocator.pipeline.landmarks")

# (Prompt text, Canonical Name, Lat, Lon, Category)
LANDMARK_DATABASE: List[Tuple[str, str, float, float, str]] = [
    # --- Pakistan: Historical Forts & UNESCO Heritage Sites ---
    ("Kot Diji Fort Khairpur Sindh", "Kot Diji Fort (Fort Ahmadabad), Khairpur, Sindh", 27.345524, 68.706691, "fortress"),
    ("Ranikot Fort Jamshoro The Great Wall of Sindh", "Ranikot Fort, Jamshoro, Sindh", 25.897368, 67.902264, "fortress"),
    ("Rohtas Fort Jhelum Punjab", "Rohtas Fort, Jhelum, Punjab", 32.966389, 73.576944, "unesco_world_heritage"),
    ("Lahore Fort Shahi Qila Sheesh Mahal", "Lahore Fort (Shahi Qila), Lahore", 31.587823, 74.315056, "unesco_world_heritage"),
    ("Derawar Fort Cholistan Desert Bahawalpur", "Derawar Fort, Cholistan Desert, Bahawalpur", 28.767500, 71.334167, "fortress"),
    ("Attock Fort Indus River", "Attock Fort, Attock, Punjab", 33.890667, 72.238500, "fortress"),
    ("Bala Hissar Fort Peshawar", "Bala Hissar Fort, Peshawar, Khyber Pakhtunkhwa", 34.013611, 71.571944, "fortress"),
    ("Baltit Fort Karimabad Hunza Valley", "Baltit Fort, Hunza Valley, Gilgit-Baltistan", 36.326389, 74.671389, "fortress"),
    ("Altit Fort Hunza Valley", "Altit Fort, Hunza Valley, Gilgit-Baltistan", 36.314722, 74.690833, "fortress"),
    ("Hiran Minar Sheikhupura Mughal hunting park", "Hiran Minar, Sheikhupura, Punjab", 31.748611, 73.951944, "monument"),
    ("Mohenjo-daro Buddhist stupa Indus Valley Civilization", "Mohenjo-daro Archaeological Ruins, Larkana, Sindh", 27.328333, 68.138611, "unesco_world_heritage"),
    ("Harappa Archaeological Ruins Indus Valley", "Harappa Archaeological Ruins, Sahiwal, Punjab", 30.630000, 72.864167, "archaeological_ruins"),
    ("Taxila Dharmarajika Buddhist Stupa ruins", "Dharmarajika Stupa, Taxila, Punjab", 33.746667, 72.846389, "unesco_world_heritage"),
    ("Taxila Jaulian Buddhist monastery ruins", "Jaulian Buddhist Monastery, Taxila, Punjab", 33.760000, 72.871944, "unesco_world_heritage"),
    ("Taxila Sirkap ancient Greco-Bactrian city ruins", "Sirkap City Ruins, Taxila, Punjab", 33.743611, 72.831389, "unesco_world_heritage"),
    ("Takht-i-Bahi Buddhist monastery ruins Mardan", "Takht-i-Bahi Buddhist Complex, Mardan, KPK", 34.319722, 71.979444, "unesco_world_heritage"),
    ("Chaukhandi Tombs sandstone necropolis Karachi", "Chaukhandi Tombs, Karachi, Sindh", 24.866155, 67.271397, "historical_necropolis"),
    ("Makli Necropolis Thatta Sindh historical tombs", "Makli Necropolis, Thatta, Sindh", 24.755833, 67.901667, "unesco_world_heritage"),
    ("Shah Jahan Mosque Thatta blue glazed tilework", "Shah Jahan Mosque, Thatta, Sindh", 24.747222, 67.927222, "historical_mosque"),
    ("Katas Raj Temples sacred pond Chakwal", "Katas Raj Temples, Chakwal, Punjab", 32.724722, 72.951667, "historical_temple"),

    # --- Pakistan: Famous Religious, National & Civic Monuments ---
    ("Badshahi Mosque red sandstone Lahore", "Badshahi Mosque, Lahore", 31.588056, 74.310833, "historical_mosque"),
    ("Faisal Mosque Islamabad white tent architecture Margalla", "Faisal Mosque, Islamabad", 33.729600, 73.037200, "national_mosque"),
    ("Wazir Khan Mosque fresco tilework Lahore", "Wazir Khan Mosque, Walled City, Lahore", 31.583333, 74.321667, "historical_mosque"),
    ("Minar-e-Pakistan Iqbal Park Lahore", "Minar-e-Pakistan, Lahore", 31.592500, 74.309444, "national_monument"),
    ("Pakistan Monument blooming petal Shakarparian Islamabad", "Pakistan Monument, Islamabad", 33.693400, 73.068400, "national_monument"),
    ("Mazar-e-Quaid white marble mausoleum Karachi", "Mazar-e-Quaid (Jinnah Mausoleum), Karachi", 24.875278, 67.040833, "national_monument"),
    ("Tomb of Jahangir Shahdara Lahore", "Tomb of Jahangir, Lahore", 31.622500, 74.303333, "historical_monument"),
    ("Shalimar Gardens Mughal terraces Lahore", "Shalimar Gardens, Lahore", 31.586111, 74.381944, "unesco_world_heritage"),
    ("Tomb of Shah Rukn-e-Alam Multan blue glazed dome", "Tomb of Shah Rukn-e-Alam, Multan, Punjab", 30.198333, 71.472222, "historical_shrine"),
    ("Shrine of Bahauddin Zakariya Multan", "Shrine of Bahauddin Zakariya, Multan, Punjab", 30.199444, 71.473611, "historical_shrine"),
    ("Ziarat Residency Quaid-e-Azam wooden architecture Balochistan", "Quaid-e-Azam Residency, Ziarat, Balochistan", 30.385278, 67.726944, "historical_building"),
    ("Clock Tower Ghanta Ghar Faisalabad", "Clock Tower (Ghanta Ghar), Faisalabad", 31.418611, 73.078889, "civic_monument"),
    ("Sharda Peeth ancient Hindu temple Neelum Valley Azad Kashmir", "Sharda Peeth, Neelum Valley, AJK", 34.793056, 74.190278, "historical_temple"),
    ("Pir Chinasi shrine viewpoint Azad Kashmir Muzaffarabad", "Pir Chinasi Shrine, Muzaffarabad, AJK", 34.372738, 73.523538, "viewpoint_shrine"),

    # --- Pakistan: Palaces, Colonial & Institutional Architecture ---
    ("Government College University GCU Gothic Clock Tower Lahore", "Government College University (GCU), Lahore", 31.573152, 74.308354, "university_campus"),
    ("King Edward Medical University Patiala Block Lahore", "King Edward Medical University, Lahore", 31.572400, 74.316800, "university_campus"),
    ("Aitchison College colonial brick architecture Lahore", "Aitchison College, Lahore", 31.536111, 74.347222, "educational_campus"),
    ("Islamia College University Peshawar Oriental Gothic architecture", "Islamia College University, Peshawar", 33.998611, 71.475556, "university_campus"),
    ("Punjab University Old Campus Allama Iqbal Campus Lahore", "Punjab University Old Campus, Lahore", 31.568611, 74.311667, "university_campus"),
    ("University of the Punjab New Campus Canal Road Lahore", "University of the Punjab (New Campus), Lahore", 31.503400, 74.300500, "university_campus"),
    ("University of Engineering and Technology UET GT Road Lahore", "UET Lahore Main Campus, Lahore", 31.579400, 74.356200, "university_campus"),
    ("LUMS Lahore University of Management Sciences DHA Lahore", "LUMS Campus, DHA Phase 5, Lahore", 31.470556, 74.410833, "university_campus"),
    ("Quaid-e-Azam University Islamabad QAU Margalla foothills", "Quaid-e-Azam University, Islamabad", 33.748889, 73.136944, "university_campus"),
    ("NUST National University of Sciences and Technology Islamabad", "NUST H-12 Campus, Islamabad", 33.642500, 72.990400, "university_campus"),
    ("Noor Mahal Italian chateau palace Bahawalpur", "Noor Mahal, Bahawalpur, Punjab", 29.397222, 71.666944, "historical_palace"),
    ("Darbar Mahal royal palace Bahawalpur", "Darbar Mahal, Bahawalpur, Punjab", 29.400556, 71.684167, "historical_palace"),
    ("Mohatta Palace Rajasthani stone palace Clifton Karachi", "Mohatta Palace, Clifton, Karachi", 24.814167, 67.032222, "historical_palace"),
    ("Frere Hall Venetian Gothic building Saddar Karachi", "Frere Hall, Civil Lines, Karachi", 24.846667, 67.032778, "civic_building"),
    ("Empress Market Indo-Gothic clock tower Saddar Karachi", "Empress Market, Saddar, Karachi", 24.861667, 67.027222, "civic_market"),
    ("Saint Patrick Cathedral Roman Catholic Gothic Karachi", "St. Patrick's Cathedral, Saddar, Karachi", 24.859167, 67.032500, "cathedral"),
    ("Lahore High Court Mall Road colonial architecture", "Lahore High Court, Mall Road, Lahore", 31.562000, 74.314200, "government_building"),
    ("Supreme Court of Pakistan Constitution Avenue Islamabad", "Supreme Court of Pakistan, Islamabad", 33.729700, 73.093400, "government_building"),
    ("Parliament House National Assembly Islamabad", "Parliament House of Pakistan, Islamabad", 33.731400, 73.095500, "government_building"),
    ("Prime Minister Secretariat Constitution Avenue Islamabad", "Prime Minister Secretariat, Islamabad", 33.738000, 73.097000, "government_building"),
    ("Mayo Hospital Lahore historic brick medical building", "Mayo Hospital, Lahore", 31.572400, 74.312000, "hospital_complex"),
    ("Services Hospital Jail Road Lahore", "Services Hospital, Lahore", 31.539800, 74.336400, "hospital_complex"),
    ("Children Hospital Ferozepur Road Lahore", "The Children's Hospital, Lahore", 31.482000, 74.343500, "hospital_complex"),

    # --- World Iconic Landmarks & UNESCO World Heritage ---
    ("Taj Mahal white marble mausoleum Agra India", "Taj Mahal, Agra, India", 27.175145, 78.042142, "unesco_world_heritage"),
    ("Red Fort Lal Qila sandstone Delhi India", "Red Fort, Delhi, India", 28.656159, 77.241020, "unesco_world_heritage"),
    ("Qutub Minar brick minaret complex Delhi India", "Qutub Minar, Delhi, India", 28.524428, 77.185456, "unesco_world_heritage"),
    ("India Gate war memorial Rajpath New Delhi", "India Gate, New Delhi, India", 28.612912, 77.229510, "national_monument"),
    ("Eiffel Tower Champ de Mars Paris France", "Eiffel Tower, Paris, France", 48.858370, 2.294481, "world_landmark"),
    ("Louvre Museum glass pyramid Paris France", "Louvre Museum, Paris, France", 48.860611, 2.337644, "museum"),
    ("Notre-Dame Cathedral Gothic Paris France", "Notre-Dame Cathedral, Paris, France", 48.852968, 2.349902, "cathedral"),
    ("Arc de Triomphe Place Charles de Gaulle Paris France", "Arc de Triomphe, Paris, France", 48.873792, 2.295028, "monument"),
    ("Colosseum amphitheatre Rome Italy", "Colosseum, Rome, Italy", 41.890210, 12.492231, "unesco_world_heritage"),
    ("Pantheon Roman temple dome Rome Italy", "Pantheon, Rome, Italy", 41.898611, 12.476944, "unesco_world_heritage"),
    ("Leaning Tower of Pisa Piazza dei Miracoli Italy", "Leaning Tower of Pisa, Pisa, Italy", 43.722952, 10.396597, "world_landmark"),
    ("Duomo Santa Maria del Fiore Florence Italy", "Florence Cathedral (Duomo), Florence, Italy", 43.773133, 11.255960, "cathedral"),
    ("Big Ben Elizabeth Tower Houses of Parliament London UK", "Big Ben (Elizabeth Tower), London, UK", 51.500729, -0.124625, "world_landmark"),
    ("Tower Bridge bascule suspension bridge London UK", "Tower Bridge, London, UK", 51.505456, -0.075356, "bridge"),
    ("Buckingham Palace London UK", "Buckingham Palace, London, UK", 51.501364, -0.141890, "palace"),
    ("Stonehenge prehistoric monument Wiltshire England", "Stonehenge, Wiltshire, UK", 51.178882, -1.826215, "unesco_world_heritage"),
    ("Parthenon Acropolis Athens Greece", "Parthenon, Acropolis of Athens, Greece", 37.971532, 23.726647, "unesco_world_heritage"),
    ("Hagia Sophia dome Istanbul Turkey", "Hagia Sophia, Istanbul, Turkey", 41.008583, 28.980175, "unesco_world_heritage"),
    ("Blue Mosque Sultan Ahmed Mosque Istanbul Turkey", "Blue Mosque (Sultan Ahmed), Istanbul, Turkey", 41.005389, 28.976806, "historical_mosque"),
    ("Sagrada Familia Gaudi basilica Barcelona Spain", "Basílica de la Sagrada Família, Barcelona, Spain", 41.403629, 2.174356, "cathedral"),
    ("Alhambra Moorish palace Granada Spain", "Alhambra Palace, Granada, Spain", 37.176078, -3.588141, "unesco_world_heritage"),
    ("Statue of Liberty Liberty Island New York USA", "Statue of Liberty, New York, USA", 40.689249, -74.044500, "national_monument"),
    ("Empire State Building Art Deco skyscraper Manhattan New York", "Empire State Building, New York, USA", 40.748817, -73.985428, "landmark_building"),
    ("Golden Gate Bridge San Francisco California", "Golden Gate Bridge, San Francisco, USA", 37.819929, -122.478255, "bridge"),
    ("Pyramids of Giza Great Pyramid Khufu Cairo Egypt", "Great Pyramid of Giza, Giza, Egypt", 29.979167, 31.134167, "unesco_world_heritage"),
    ("Great Sphinx of Giza limestone statue Egypt", "Great Sphinx of Giza, Giza, Egypt", 29.975278, 31.137500, "ancient_monument"),
    ("Petra Treasury Al-Khazneh rock-cut architecture Jordan", "Al-Khazneh (The Treasury), Petra, Jordan", 30.322222, 35.451667, "unesco_world_heritage"),
    ("Burj Khalifa skyscraper Downtown Dubai UAE", "Burj Khalifa, Dubai, UAE", 25.197197, 55.274376, "landmark_building"),
    ("Sheikh Zayed Grand Mosque white marble Abu Dhabi UAE", "Sheikh Zayed Grand Mosque, Abu Dhabi, UAE", 24.412822, 54.474964, "grand_mosque"),
    ("Kaaba Sacred Mosque Masjid al-Haram Mecca Saudi Arabia", "Kaaba, Masjid al-Haram, Mecca, Saudi Arabia", 21.422487, 39.826206, "sacred_site"),
    ("Al-Masjid an-Nabawi Prophet Mosque Medina Saudi Arabia", "Al-Masjid an-Nabawi, Medina, Saudi Arabia", 24.467222, 39.611111, "sacred_site"),
    ("Dome of the Rock golden dome Temple Mount Jerusalem", "Dome of the Rock, Jerusalem", 31.778056, 35.235556, "sacred_site"),
    ("Great Wall of China Mutianyu Badaling stone fortifications", "Great Wall of China (Mutianyu), Beijing, China", 40.431908, 116.570374, "unesco_world_heritage"),
    ("Forbidden City Imperial Palace Beijing China", "Forbidden City, Beijing, China", 39.916345, 116.397155, "unesco_world_heritage"),
    ("Sydney Opera House Bennelong Point Sydney Australia", "Sydney Opera House, Sydney, Australia", -33.856784, 151.215297, "unesco_world_heritage"),
    ("Machu Picchu Inca citadel Andes Mountains Peru", "Machu Picchu, Cusco Region, Peru", -13.163141, -72.544963, "unesco_world_heritage"),
    ("Christ the Redeemer Art Deco statue Corcovado Rio de Janeiro", "Christ the Redeemer, Rio de Janeiro, Brazil", -22.951916, -43.210487, "world_landmark"),
    ("Chichen Itza El Castillo Mayan pyramid Yucatan Mexico", "El Castillo (Temple of Kukulcan), Chichen Itza, Mexico", 20.684285, -88.567783, "unesco_world_heritage"),
]


class LandmarkMatcher:
    """High-accuracy zero-shot landmark recognition and exact mark geocoding."""

    def __init__(self):
        self._prompts = [f"a photo of {lm[0]}" for lm in LANDMARK_DATABASE]

    def match(
        self,
        image: Image.Image,
        clip_model: Any,
        clip_proc: Any,
        device: str = "cuda",
        min_confidence: float = 0.12,
    ) -> Optional[Dict[str, Any]]:
        """Run batched zero-shot classification against landmark database.
        
        Returns exact candidate metadata if confidence exceeds threshold, else None.
        """
        inputs = clip_proc(text=self._prompts, images=image, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            out = clip_model(**inputs)
            probs = out.logits_per_image.softmax(dim=-1).cpu().numpy()[0]

        top_idx = int(np.argmax(probs))
        top_prob = float(probs[top_idx])
        top_lm = LANDMARK_DATABASE[top_idx]

        # Uniform baseline probability across N items
        uniform_baseline = 1.0 / len(LANDMARK_DATABASE)
        # Margin over second place
        sorted_probs = np.sort(probs)
        margin = top_prob - float(sorted_probs[-2]) if len(sorted_probs) > 1 else top_prob

        logger.info(
            "[landmark_matcher] Top match: '%s' (conf=%.4f, baseline=%.4f, margin=%.4f)",
            top_lm[1], top_prob, uniform_baseline, margin
        )

        # Trigger if confidence exceeds min_threshold OR is 3x higher than uniform baseline with positive margin
        is_significant = (top_prob >= min_confidence) or (top_prob >= uniform_baseline * 3.0 and margin >= 0.04)

        if not is_significant:
            return None

        prompt_text, canonical_name, lat, lon, category = top_lm
        calibrated_radius_km = 0.05 if top_prob >= 0.30 else (0.10 if top_prob >= 0.20 else 0.25)

        return {
            "name": canonical_name,
            "category": category,
            "latitude": lat,
            "longitude": lon,
            "confidence": top_prob,
            "margin": margin,
            "tier": "T1",
            "radius_km": calibrated_radius_km,
            "rationale": f"High-confidence visual perception match against landmark database for {canonical_name}",
        }
