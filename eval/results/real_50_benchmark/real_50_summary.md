# Real 50-Photo Worldwide Geolocator Benchmark Report

**Date:** 2026-10-09 19:49:48
**Total Real Internet Photos Evaluated:** 50
**Total Execution Time:** 1333.0 s (26.66 s/photo)
**Peak VRAM Usage:** 2662.6 MB (Quadro M1200 safe, single resident GPU execution)

## 1. Overall Key Performance Indicators

| Metric | Value | Description |
|--------|-------|-------------|
| **Median Error** | **7.67 km** | 50th percentile localization error |
| **Mean Error** | **1067.76 km** | Average global error across all biomes |
| **Within 1 km (Exact Mark)** | **26.0%** | Cadastral / building / street level precision |
| **Within 25 km (Local Area)** | **66.0%** | City / mountain range / valley scale |
| **Within 200 km (Regional)** | **80.0%** | Province / state level accuracy |
| **Within 750 km (Sub-continental)** | **90.0%** | Sub-continental zone accuracy |
| **Within 2500 km (Continental)** | **92.0%** | Continental prior accuracy |
| **Honest Calibration Rate** | **36.0%** | Ground truth within predicted error radius |

## 2. Accuracy Breakdown by Biome / Category

| Biome / Category | Count | Median Error (km) | Mean Error (km) | <= 25 km (%) | <= 200 km (%) |
|------------------|-------|-------------------|-----------------|--------------|---------------|
| `coast` | 5 | 2.5 | 18.4 | 60.0% | 100.0% |
| `desert` | 4 | 114.1 | 2155.9 | 50.0% | 50.0% |
| `farmland` | 5 | 216.3 | 454.7 | 40.0% | 40.0% |
| `forest` | 4 | 19.6 | 27.5 | 50.0% | 100.0% |
| `island` | 4 | 3777.7 | 5478.8 | 50.0% | 50.0% |
| `lake_river` | 5 | 12.8 | 21.8 | 80.0% | 100.0% |
| `mountain` | 5 | 0.0 | 94.3 | 80.0% | 80.0% |
| `rural_road` | 5 | 3.3 | 54.7 | 60.0% | 80.0% |
| `snow_ice` | 4 | 9.2 | 4843.0 | 75.0% | 75.0% |
| `urban` | 5 | 0.0 | 0.2 | 100.0% | 100.0% |
| `valley` | 4 | 7.5 | 36.6 | 75.0% | 100.0% |

## 3. Four Evidence Types Modality Audit

| Modality | Used | Not Applicable | Not Available |
|----------|------|----------------|---------------|
| **OpenStreetMap Geometry** | 32 | 0 | 0 |
| **Elevation Skylines (DEM)** | 0 | 0 | 0 |
| **Satellite Imagery** | 50 | 0 | 0 |
| **Street-Level Imagery** | 35 | 0 | 0 |

## 4. Confidence Tier Distribution

| Tier | Definition | Count | Share (%) |
|------|------------|-------|-----------|
| **T1** | Exact building/cadastral (radius <= 1.5 km) | 49 | 98.0% |
| **T2** | Street corridor / Landmark (radius <= 10 km) | 0 | 0.0% |
| **T3** | City / Mountain valley (radius <= 25 km) | 1 | 2.0% |
| **T4** | Sub-region / Province (radius <= 150 km) | 0 | 0.0% |
| **T5** | Macro-region / Country (radius <= 1500 km) | 0 | 0.0% |
| **T6** | Unknown / Insufficient signal | 0 | 0.0% |

## 5. Detailed Test Sample Log (All 50 Real Photos)

| # | ID | Name | Category | Country | Ground Truth | Prediction | Error (km) | Tier | Calibrated? |
|---|---|------|----------|---------|--------------|------------|------------|------|-------------|
| 1 | `urb_01` | Eiffel Tower | `urban` | France | 48.8582, 2.2945 | 48.8583, 2.2945 | **0.0** | T1 | PASS |
| 2 | `urb_02` | Tokyo Tower | `urban` | Japan | 35.6586, 139.7456 | 35.6584, 139.7455 | **0.0** | T1 | PASS |
| 3 | `urb_03` | WNYC-FM | `urban` | USA | 40.7484, -73.9857 | 40.7578, -73.9861 | **1.0** | T3 | PASS |
| 4 | `urb_04` | Colosseum | `urban` | Italy | 41.8903, 12.4922 | 41.8909, 12.4919 | **0.1** | T1 | FAIL |
| 5 | `urb_05` | Sydney Opera House | `urban` | Australia | -33.8568, 151.2151 | -33.8572, 151.2151 | **0.0** | T1 | PASS |
| 6 | `rur_01` | Seligman, Arizona | `rural_road` | USA | 35.3269, -112.8722 | 35.3269, -112.8763 | **0.4** | T1 | FAIL |
| 7 | `rur_02` | Buachaille Etive Beag | `rural_road` | UK | 56.6382, -4.9707 | 56.6667, -4.9833 | **3.3** | T1 | PASS |
| 8 | `rur_03` | The Residency, Alice Spr | `rural_road` | Australia | -23.6987, 133.8821 | -23.6984, 133.8813 | **0.1** | T1 | FAIL |
| 9 | `rur_04` | Murghob | `rural_road` | Tajikistan | 38.1689, 73.9650 | 37.5328, 71.6576 | **214.6** | T1 | FAIL |
| 10 | `rur_05` | Knysna | `rural_road` | South Africa | -34.0356, 23.0489 | -33.9597, 22.4587 | **55.1** | T1 | FAIL |
| 11 | `far_01` | Castiglione d'Orcia | `farmland` | Italy | 43.0167, 11.6167 | 43.0110, 11.5686 | **4.0** | T1 | PASS |
| 12 | `far_02` | Ruan Center | `farmland` | USA | 41.5870, -93.6260 | 40.7484, -73.9857 | **1643.1** | T1 | FAIL |
| 13 | `far_03` | Pergamino | `farmland` | Argentina | -33.8833, -60.5667 | -34.6029, -58.3808 | **216.3** | T1 | FAIL |
| 14 | `far_04` | Biei, Hokkaido | `farmland` | Japan | 43.5833, 142.4667 | 43.5797, 142.4627 | **0.5** | T1 | FAIL |
| 15 | `far_05` | Cathedral of Évora | `farmland` | Portugal | 38.5718, -7.9066 | 37.1740, -3.5901 | **409.5** | T1 | FAIL |
| 16 | `cst_01` | Bixby Bridge | `coast` | USA | 36.3714, -121.9019 | 36.2231, -121.3877 | **48.9** | T1 | FAIL |
| 17 | `cst_02` | Loch Ard Gorge | `coast` | Australia | -38.6466, 143.0705 | -38.6603, 143.0934 | **2.5** | T1 | FAIL |
| 18 | `cst_03` | Igreja de Santo António  | `coast` | Portugal | 37.0994, -8.6714 | 37.0952, -8.2262 | **39.5** | T1 | FAIL |
| 19 | `cst_04` | Cape of Good Hope | `coast` | South Africa | -34.3581, 18.4756 | -34.3509, 18.4844 | **1.1** | T1 | FAIL |
| 20 | `cst_05` | Giant's Causeway | `coast` | UK | 55.2408, -6.5117 | 55.2407, -6.5115 | **0.0** | T1 | PASS |
| 21 | `lak_01` | Bellagio, Lombardy | `lake_river` | Italy | 45.9833, 9.2500 | 45.9918, 9.2649 | **1.5** | T1 | PASS |
| 22 | `lak_02` | Emerald Bay State Park | `lake_river` | USA | 38.9536, -120.0939 | 39.0885, -120.0504 | **15.5** | T1 | FAIL |
| 23 | `lak_03` | Olkhon Island | `lake_river` | Russia | 53.1567, 107.3836 | 53.6167, 108.1307 | **71.2** | T1 | FAIL |
| 24 | `lak_04` | Victoria Falls | `lake_river` | Zambia | -17.9244, 25.8567 | -17.8531, 25.8614 | **8.0** | T1 | FAIL |
| 25 | `lak_05` | Queenstown, New Zealand | `lake_river` | New Zealand | -45.0311, 168.6625 | -45.0888, 168.5211 | **12.8** | T1 | FAIL |
| 26 | `mtn_01` | Riffelhorn | `mountain` | Switzerland | 45.9813, 7.7583 | 45.9764, 7.6586 | **7.7** | T1 | PASS |
| 27 | `mtn_02` | Mount Fuji | `mountain` | Japan | 35.3608, 138.7275 | 35.3606, 138.7274 | **0.0** | T1 | PASS |
| 28 | `mtn_03` | Denali | `mountain` | USA | 63.0692, -151.0064 | 63.0691, -151.0062 | **0.0** | T1 | PASS |
| 29 | `mtn_04` | Aoraki / Mount Cook | `mountain` | New Zealand | -43.5950, 170.1419 | -43.5950, 170.1418 | **0.0** | T1 | PASS |
| 30 | `mtn_05` | Kilimanjaro National Par | `mountain` | Tanzania | -3.0667, 37.3667 | 0.6713, 35.5157 | **463.8** | T1 | FAIL |
| 31 | `val_01` | Yosemite Museum | `valley` | USA | 37.7486, -119.5880 | 37.7327, -119.6057 | **2.4** | T1 | FAIL |
| 32 | `val_02` | Lauterbrunnen | `valley` | Switzerland | 46.5950, 7.9074 | 46.5936, 7.9091 | **0.2** | T1 | PASS |
| 33 | `val_03` | Urubamba, Peru | `valley` | Peru | -13.3042, -72.1167 | -13.3594, -72.0152 | **12.6** | T1 | PASS |
| 34 | `val_04` | Nakuru | `valley` | Kenya | -0.3000, 36.0667 | -1.2312, 36.7947 | **131.4** | T1 | FAIL |
| 35 | `dst_01` | Erg Chebbi | `desert` | Morocco | 31.1667, -3.9833 | 31.1492, -4.0117 | **3.3** | T1 | PASS |
| 36 | `dst_02` | Death Valley | `desert` | USA | 36.2469, -116.8169 | -24.5563, -69.4226 | **8392.2** | T1 | FAIL |
| 37 | `dst_03` | Jabal Ram | `desert` | Jordan | 29.5833, 35.4000 | 29.5175, 35.3836 | **7.5** | T1 | PASS |
| 38 | `dst_04` | San Pedro de Atacama | `desert` | Chile | -22.9167, -68.2000 | -24.5563, -69.4226 | **220.7** | T1 | FAIL |
| 39 | `fst_01` | Humboldt Lagoons State P | `forest` | USA | 41.2306, -124.1028 | 41.4614, -124.0481 | **26.1** | T1 | FAIL |
| 40 | `fst_02` | Baden-Baden | `forest` | Germany | 48.7628, 8.2408 | 48.1413, 8.2144 | **69.1** | T1 | FAIL |
| 41 | `fst_03` | Manaus | `forest` | Brazil | -3.1189, -60.0217 | -3.1321, -60.0216 | **1.5** | T1 | FAIL |
| 42 | `fst_04` | Yakushima | `forest` | Japan | 30.3439, 130.5239 | 30.3902, 130.6511 | **13.2** | T1 | FAIL |
| 43 | `snw_01` | Longyearbyen | `snow_ice` | Norway | 78.2200, 15.6500 | -77.8463, 166.6682 | **19352.5** | T1 | FAIL |
| 44 | `snw_02` | Franz Josef Glacier | `snow_ice` | New Zealand | -43.4669, 170.1917 | -43.4757, 170.1981 | **1.1** | T1 | PASS |
| 45 | `snw_03` | Mount Athabasca | `snow_ice` | Canada | 52.1806, -117.2017 | 52.1609, -117.3087 | **7.6** | T1 | PASS |
| 46 | `snw_04` | Perito Moreno Glacier | `snow_ice` | Argentina | -50.5000, -73.1333 | -50.5759, -73.2292 | **10.8** | T1 | FAIL |
| 47 | `isl_01` | Therasia | `island` | Greece | 36.4300, 25.3300 | 36.3880, 25.4579 | **12.4** | T1 | FAIL |
| 48 | `isl_02` | Maui | `island` | USA | 20.8000, -156.3000 | -0.6288, -90.3639 | **7543.0** | T1 | FAIL |
| 49 | `isl_03` | Puerto Ayora | `island` | Ecuador | -0.7500, -90.3167 | -6.1669, 39.2011 | **14359.4** | T1 | FAIL |
| 50 | `isl_04` | Bora Bora | `island` | French Polynesia | -16.5010, -151.7400 | -16.5043, -151.7367 | **0.5** | T1 | FAIL |