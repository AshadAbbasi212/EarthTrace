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
    ("Karachi Gymkhana Club cricket ground lawn Club Road Karachi", "Karachi Gymkhana Club, Club Road, Karachi", 24.851000, 67.029000, "sports_club"),
    ("Pearl Continental Hotel PC Hotel Karachi Club Road PIDC", "Pearl Continental Hotel (PC Hotel), Karachi", 24.852500, 67.031500, "luxury_hotel"),
    ("Movenpick Hotel Karachi luxury hotel Club Road PIDC", "Mövenpick Hotel Karachi, Club Road, Karachi", 24.851900, 67.030800, "luxury_hotel"),
    ("Lahore High Court Mall Road colonial architecture", "Lahore High Court, Mall Road, Lahore", 31.562000, 74.314200, "government_building"),
    ("Supreme Court of Pakistan Constitution Avenue Islamabad", "Supreme Court of Pakistan, Islamabad", 33.729700, 73.093400, "government_building"),
    ("Parliament House National Assembly Islamabad", "Parliament House of Pakistan, Islamabad", 33.731400, 73.095500, "government_building"),
    ("Prime Minister Secretariat Constitution Avenue Islamabad", "Prime Minister Secretariat, Islamabad", 33.738000, 73.097000, "government_building"),

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
    ("Tokyo Tower red and white lattice communications tower Tokyo Japan", "Tokyo Tower, Tokyo, Japan", 35.658581, 139.745433, "world_landmark"),
    ("Bixby Creek Bridge open-spandrel arch bridge Big Sur California", "Bixby Creek Bridge, Big Sur, California, USA", 36.371389, -121.901944, "bridge"),
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

    # --- World Iconic Natural Landmarks, Mountains & Valleys ---
    ("Matterhorn pyramid peak Zermatt Swiss Alps", "Matterhorn Peak, Zermatt, Switzerland", 45.976300, 7.748000, "mountain_peak"),
    ("Mount Fuji snow capped volcanic cone Japan", "Mount Fuji, Honshu, Japan", 35.360600, 138.727400, "mountain_peak"),
    ("Denali Mount McKinley Alaska mountain range", "Denali (Mount McKinley), Alaska, USA", 63.069200, -151.007000, "mountain_peak"),
    ("Mount Cook Aoraki Southern Alps New Zealand", "Aoraki / Mount Cook, South Island, New Zealand", -43.595000, 170.141800, "mountain_peak"),
    ("Mount Aconcagua Andes mountain peak Argentina", "Mount Aconcagua, Mendoza, Argentina", -32.653200, -70.010900, "mountain_peak"),
    ("Mount Kilimanjaro volcanic peak Tanzania Africa", "Mount Kilimanjaro, Tanzania", -3.067400, 37.355600, "mountain_peak"),
    ("Yosemite Valley El Capitan Half Dome California", "Yosemite Valley, California, USA", 37.745600, -119.593600, "national_park"),
    ("Lauterbrunnen Valley waterfalls Swiss Alps", "Lauterbrunnen Valley, Bernese Oberland, Switzerland", 46.593600, 7.909100, "alpine_valley"),
    ("Sacred Valley of the Incas Urubamba Peru", "Sacred Valley of the Incas, Cusco, Peru", -13.333300, -72.083300, "historical_valley"),
    ("Great Rift Valley Kenya East Africa", "Great Rift Valley Viewpoint, Kenya", -0.366700, 36.083300, "rift_valley"),
    ("Capertee Valley sandstone canyon New South Wales Australia", "Capertee Valley, NSW, Australia", -33.150000, 150.050000, "canyon_valley"),

    # --- World Deserts, Coasts, Waters & Islands ---
    ("Erg Chebbi sand dunes Sahara Desert Merzouga Morocco", "Erg Chebbi Dunes, Merzouga, Morocco", 31.149200, -4.011700, "desert_dunes"),
    ("Death Valley Badwater Basin salt flats California", "Death Valley (Badwater Basin), California, USA", 36.532300, -116.932500, "desert_basin"),
    ("Atacama Desert salt flats and volcanic peaks Chile", "Atacama Desert, Antofagasta, Chile", -23.863400, -69.132800, "arid_desert"),
    ("Wadi Rum red sandstone desert monoliths Jordan", "Wadi Rum Protected Area, Jordan", 29.573300, 35.433300, "desert_valley"),
    ("Simpson Desert red sand ridges Outback Australia", "Simpson Desert, Northern Territory, Australia", -24.570000, 137.420000, "desert_dunes"),
    ("Rub al Khali Empty Quarter sand dunes Oman", "Rub' al Khali (Empty Quarter), Oman", 20.000000, 50.000000, "desert_dunes"),
    ("Big Sur Pacific coastal cliffs California highway", "Big Sur Coastal Highway, California, USA", 36.270400, -121.808100, "coastal_cliffs"),
    ("Algarve sandstone sea cliffs and caves Portugal", "Algarve Coast (Ponta da Piedade), Portugal", 37.089100, -8.243600, "coastal_cliffs"),
    ("Twelve Apostles limestone sea stacks Great Ocean Road Australia", "Twelve Apostles, Victoria, Australia", -38.665800, 143.104400, "coastal_stacks"),
    ("Cape Point Cape of Good Hope cliffs South Africa", "Cape Point (Cape of Good Hope), South Africa", -34.357200, 18.497500, "coastal_cape"),
    ("Ha Long Bay emerald water limestone karst islands Vietnam", "Ha Long Bay, Quang Ninh, Vietnam", 20.910100, 107.183900, "coastal_karst"),
    ("Giants Causeway interlocking basalt columns Northern Ireland", "Giant's Causeway, County Antrim, UK", 55.240800, -6.511600, "coastal_basalt"),
    ("Lake Como alpine lake and villas Lombardy Italy", "Lake Como, Lombardy, Italy", 45.986700, 9.257200, "alpine_lake"),
    ("Lake Tahoe clear blue water Sierra Nevada USA", "Lake Tahoe, California/Nevada, USA", 39.096800, -120.032400, "alpine_lake"),
    ("Lake Baikal deep freshwater lake Siberia Russia", "Lake Baikal, Irkutsk, Russia", 53.558700, 108.165000, "lake"),
    ("Lake Titicaca high altitude Andean lake Bolivia Peru", "Lake Titicaca, Bolivia/Peru", -15.925400, -69.335400, "lake"),
    ("Lake Wakatipu Queenstown alpine lake New Zealand", "Lake Wakatipu, Otago, New Zealand", -45.050000, 168.650000, "alpine_lake"),
    ("Victoria Falls Mosi-oa-Tunya waterfall Zambezi Zimbabwe Zambia", "Victoria Falls, Zimbabwe/Zambia", -17.924300, 25.855900, "waterfall"),
    ("Black Forest evergreen woodland Baden-Wurttemberg Germany", "Black Forest (Schwarzwald), Germany", 48.300000, 8.150000, "forest"),
    ("Redwood National Park giant coastal redwoods California", "Redwood National and State Parks, California, USA", 41.213200, -124.004600, "forest"),
    ("Amazon Rainforest tropical river basin Manaus Brazil", "Amazon Rainforest, Manaus, Brazil", -3.119000, -60.021700, "rainforest"),
    ("Yakushima ancient cedar temperate rainforest Japan", "Yakushima Primeval Forest, Kagoshima, Japan", 30.358500, 130.528600, "rainforest"),
    ("Daintree Rainforest tropical coastal canopy Queensland Australia", "Daintree Rainforest, Queensland, Australia", -16.280000, 145.416700, "rainforest"),
    ("Svalbard Arctic tundra mountains Spitsbergen Norway", "Svalbard Archipelago, Norway", 78.223200, 15.626700, "arctic_tundra"),
    ("Franz Josef Glacier temperate glacier South Island New Zealand", "Franz Josef Glacier, New Zealand", -43.466700, 170.183300, "glacier"),
    ("Columbia Icefield Athabasca Glacier Canadian Rockies Alberta", "Columbia Icefield, Alberta, Canada", 52.216700, -117.216700, "glacier"),
    ("Perito Moreno Glacier ice wall Lake Argentino Patagonia", "Perito Moreno Glacier, Santa Cruz, Argentina", -50.483300, -73.050000, "glacier"),
    ("Santorini white caldera cliff houses Cyclades Greece", "Santorini (Thira), Cyclades, Greece", 36.393200, 25.461500, "volcanic_island"),
    ("Maui tropical volcanic beaches Hawaii USA", "Maui, Hawaiian Islands, USA", 20.798400, -156.331900, "volcanic_island"),
    ("Galapagos Islands volcanic archipelago Ecuador", "Galápagos Islands, Ecuador", -0.953800, -90.965600, "volcanic_island"),
    ("Bora Bora turquoise barrier reef French Polynesia", "Bora Bora, French Polynesia", -16.500400, -151.741500, "atoll_island"),
    ("Zanzibar tropical spice island beaches Tanzania", "Zanzibar Archipelago, Tanzania", -6.165900, 39.202600, "island"),
    ("Vestmannaeyjar volcanic cliffs Westman Islands Iceland", "Vestmannaeyjar (Westman Islands), Iceland", 63.438900, -20.273600, "volcanic_island"),

    # --- Global Metropolises & Urban Hubs ---
    ("Tokyo Skytree Shinjuku Shibuya skyline Japan", "Tokyo Metropolis, Japan", 35.689500, 139.691700, "urban_metropolis"),
    ("Obelisco de Buenos Aires Avenida 9 de Julio Argentina", "Buenos Aires (Obelisco), Argentina", -34.603700, -58.381600, "urban_metropolis"),
    ("Kenyatta International Convention Centre KICC Nairobi Kenya", "Nairobi City Center, Kenya", -1.286400, 36.817200, "urban_metropolis"),

    # --- Famous World Highways & Scenic Corridors ---
    ("Glencoe A82 Scottish Highlands mountain pass Scotland UK", "Glencoe A82 Valley, Scottish Highlands, UK", 56.666700, -4.983300, "scenic_corridor"),
    ("Route 66 historic highway Arizona desert Southwest USA", "Route 66 Historic Corridor, Arizona, USA", 35.325800, -112.874200, "scenic_corridor"),
    ("Ruta 40 Patagonia highway steppe mountains Argentina", "Ruta 40 Corridor, Patagonia, Argentina", -47.166700, -70.916700, "scenic_corridor"),
    ("Stuart Highway Outback red desert Northern Territory Australia", "Stuart Highway, Outback, Australia", -23.700000, 133.880000, "scenic_corridor"),
    ("Pamir Highway high altitude mountain pass Pamir Mountains Tajikistan", "Pamir Highway, GBAO, Tajikistan", 38.535800, 73.136100, "scenic_corridor"),
    ("Garden Route coastal scenic road Western Cape South Africa", "Garden Route, Western Cape, South Africa", -34.035100, 23.046500, "scenic_corridor"),

    # --- Famous Global Farmlands & Agricultural Landscapes ---
    ("Val d'Orcia rolling hills cypress trees Tuscany Italy", "Val d'Orcia, Tuscany, Italy", 43.064200, 11.606700, "agricultural_landscape"),
    ("Iowa cornfields Midwest agricultural plains USA", "Iowa Cornfields, Midwest, USA", 41.878000, -93.097700, "agricultural_landscape"),
    ("Pampas fertile agricultural plains cattle ranching Argentina", "Pampas Agricultural Plains, Argentina", -36.616700, -64.283300, "agricultural_landscape"),
    ("Hokkaido agricultural rolling fields Biei Furano Japan", "Hokkaido Plains, Hokkaido, Japan", 43.583300, 142.466700, "agricultural_landscape"),
    ("Alentejo cork oak groves rolling farmland Portugal", "Alentejo Farmlands, Portugal", 38.016700, -7.866700, "agricultural_landscape"),
    ("Canterbury Plains braided rivers pastoral farmland New Zealand", "Canterbury Plains, South Island, New Zealand", -43.616700, 172.116700, "agricultural_landscape"),

    # --- Unique Valleys, Wilderness, and Polar Stations ---
    ("Barun Valley Makalu Barun National Park Himalayas Nepal", "Barun Valley, Himalayas, Nepal", 27.700000, 87.100000, "himalayan_valley"),
    ("Bwindi Impenetrable National Park mountain rainforest Uganda", "Bwindi Impenetrable Forest, Uganda", -1.050000, 29.616700, "rainforest"),
    ("McMurdo Station scientific research base Ross Island Antarctica", "McMurdo Station, Ross Island, Antarctica", -77.846300, 166.668200, "polar_research_station"),
    ("Zanskar frozen river Chadar Trek ice gorge Ladakh India", "Zanskar Frozen Gorge, Ladakh, India", 33.780000, 76.920000, "polar_frozen_river"),
]


NEGATIVE_PROMPTS = [
    "an ordinary street, road, or intersection without famous landmarks",
    "an ordinary residential house, apartment building, or residential neighborhood",
    "an ordinary commercial building, shop, or retail storefront",
    "a generic natural landscape, hill, field, or countryside without famous landmarks",
    "a photo of ordinary people, vehicles, cars, or everyday objects",
    "an indoor room, office, or domestic interior",
    "ordinary agricultural farmland, rural pasture, or wild forest without landmarks",
    "a close up photo or non-scenic view",
    "an ordinary desert town, mudbrick village, clay houses, or arid settlement without famous landmarks",
    "an ordinary rural road or country highway through trees or hills without landmarks",
    "an ordinary outback town, country street, or regional settlement without famous landmarks",
]


class LandmarkMatcher:
    """High-accuracy zero-shot landmark recognition and exact mark geocoding."""

    def __init__(self):
        self._prompts = [f"a photo of {lm[0]}" for lm in LANDMARK_DATABASE] + NEGATIVE_PROMPTS

    def match(
        self,
        image: Image.Image,
        clip_model: Any,
        clip_proc: Any,
        device: Optional[str] = None,
        min_confidence: float = 0.35,
        candidate_countries: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Run batched zero-shot classification against landmark database.
        
        Returns exact candidate metadata ONLY if confident and clearly exceeding negative background prompts.
        """
        model_device = getattr(clip_model, "device", None) or (device or ("cuda" if torch.cuda.is_available() else "cpu"))
        inputs = clip_proc(text=self._prompts, images=image, return_tensors="pt", padding=True).to(model_device)
        with torch.no_grad():
            out = clip_model(**inputs)
            probs = out.logits_per_image.softmax(dim=-1).cpu().numpy()[0]

        top_idx = int(np.argmax(probs))
        top_prob = float(probs[top_idx])

        # 1. If highest match is any negative/generic prompt, reject immediately
        if top_idx >= len(LANDMARK_DATABASE):
            logger.info(
                "[landmark_matcher] Matched negative/generic scene: '%s' (conf=%.4f) -> No landmark",
                NEGATIVE_PROMPTS[top_idx - len(LANDMARK_DATABASE)], top_prob
            )
            return None

        top_lm = LANDMARK_DATABASE[top_idx]
        neg_probs = probs[len(LANDMARK_DATABASE):]
        max_neg_prob = float(np.max(neg_probs)) if len(neg_probs) > 0 else 0.0

        # Margin over the best negative prompt
        neg_margin = top_prob - max_neg_prob

        # Margin over second place landmark
        lm_probs = probs[:len(LANDMARK_DATABASE)]
        sorted_lm_probs = np.sort(lm_probs)
        lm_margin = top_prob - float(sorted_lm_probs[-2]) if len(sorted_lm_probs) > 1 else top_prob

        logger.info(
            "[landmark_matcher] Candidate match: '%s' (conf=%.4f, lm_margin=%.4f, neg_margin=%.4f, max_neg=%.4f)",
            top_lm[1], top_prob, lm_margin, neg_margin, max_neg_prob
        )

        # A real landmark must:
        # 1. Substantially beat the highest negative class (neg_margin >= 0.20)
        # 2. Have clear lead over other landmarks and substantial absolute probability
        is_significant = (top_prob >= 0.55 and neg_margin >= 0.20) or (top_prob >= 0.40 and lm_margin >= 0.15 and neg_margin >= 0.25)

        if not is_significant:
            logger.info("[landmark_matcher] Match '%s' rejected (failed significance thresholds)", top_lm[1])
            return None

        # Country consistency verification: Reject if candidate country is strongly known and doesn't match landmark
        if candidate_countries:
            from geolocator.pipeline.geo_utils import get_country_candidate
            lm_country = get_country_candidate(top_lm[2], top_lm[3]) or ""
            lm_text = f"{top_lm[0]} {top_lm[1]} {lm_country}".lower()
            norm_cand_countries = [c.strip().lower() for c in candidate_countries if c.strip()]
            country_matched = any(c in lm_text for c in norm_cand_countries)
            if not country_matched and top_prob < 0.90:
                logger.info(
                    "[landmark_matcher] Match '%s' rejected due to country mismatch with candidate countries %s (conf=%.4f < 0.90)",
                    top_lm[1], candidate_countries, top_prob
                )
                return None

        prompt_text, canonical_name, lat, lon, category = top_lm
        if category in ("monument", "national_monument", "fortress", "unesco_world_heritage", "world_landmark", "landmark_building", "cathedral", "grand_mosque", "national_mosque", "historical_mosque", "palace", "museum", "university_campus", "hospital_complex", "civic_building", "civic_market", "luxury_hotel", "hotel", "sports_club", "hospitality"):
            calibrated_radius_km = 0.05 if top_prob >= 0.25 else 0.10
            tier = "T1"
        elif category in ("urban_metropolis", "scenic_corridor", "coastal_cliffs", "coastal_stacks", "coastal_cape", "bridge"):
            calibrated_radius_km = 5.0
            tier = "T2"
        elif category in ("mountain_peak", "alpine_valley", "himalayan_valley", "rift_valley", "desert_dunes", "desert_basin", "arid_desert", "desert_valley", "alpine_lake", "lake", "waterfall", "glacier", "volcanic_island", "atoll_island", "island", "polar_research_station"):
            calibrated_radius_km = 10.0
            tier = "T2"
        else:
            calibrated_radius_km = 15.0
            tier = "T3"

        return {
            "name": canonical_name,
            "category": category,
            "latitude": lat,
            "longitude": lon,
            "confidence": top_prob,
            "margin": lm_margin,
            "tier": tier,
            "radius_km": calibrated_radius_km,
            "rationale": f"High-confidence visual perception match against landmark database for {canonical_name}",
        }

