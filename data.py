locations_trip = {
    1: ("Radolfzell am Bodensee", (47.7452, 8.9669)),
    2: ("Bad Ursach", (48.4931, 9.4042)),
    3: ("Gomadingen", (48.400280, 9.389230)),
}

restaurants = [
    {   "trip_id": 1,
        "name": "Levante Restaurant",
        "address": "Löwengasse 30, 78315 Radolfzell, Germany",
        "description": "Arabische Küche",
        "gmap_url": "https://maps.app.goo.gl/fU6LNySwc2DGJUJHA",
    },
    {   "trip_id": 1,
        "name": "MERAKI Modern Greek Taverna",
        "address": "Höristraße 2, 78315 Radolfzell am Bodensee",
        "description": "Griechische Küche",
        "gmap_url": "https://maps.app.goo.gl/Y9YrNnowydxTvBCH9",
    },
     {  "trip_id": 1,
        "name": "Safran - BioBistro",
        "address": "Löwengasse 22, 78315 Radolfzell am Bodensee",
        "description": "Vegane Küche",
        "gmap_url": "https://maps.app.goo.gl/eimF6ooZwK7DrM3z5",
    },
    {  "trip_id": 2,
        "name": "Kesselhaus",
        "address": "Pfählerstraße 7, 72574 Bad Urach",
        "description": "Restaurant",
        "gmap_url": "https://maps.app.goo.gl/H4rwnHZr5KzsiD8D9",
    },
     {  "trip_id": 2,
        "name": "Taj Mahal Bad Urach",
        "address": "Pfählhof 2, 72574 Bad Urach",
        "description": "Indisches Restaurant",
        "gmap_url": "https://maps.app.goo.gl/pGoznQRcyBpb97AWA",
    },
    {  "trip_id": 3,
        "name": "Lagerhaus an der Lauter",
        "address": "Lautertalstraße 65, 72532 Gomadingen",
        "description": "Cafè, Kaffeerösterei, Konditorei, Chocolaterie, Seifenmanufaktur",
        "gmap_url": "https://maps.app.goo.gl/rBRg9Q4RrLXSQJxy6",
    },
    
]


POIs = [
    {   "trip_id": 1,
        "name": "Pfahlbauten",
        "address": "Strandpromenade 6, 88690 Uhldingen-Mühlhofen",
        "description": "Die Pfahlbauten verkörpern eine ungewohnte Welt mit ihren Holz- und Schilfkonstruktionen – natürlich, vertraut, faszinierend.",
        "gmap_url": "https://maps.app.goo.gl/hu1dv5QsqTDTb5756",
    },
    {   "trip_id": 1,
        "name": "Insel Reichenau",
        "address": "Seestraße 2, 78479 Reichenau",
        "description": "malerisches, kulturhistorisch sehr bedeutendes Eiland im westlichen Bodensee.",
        "gmap_url": "https://maps.app.goo.gl/ftLmC3DZGVP2hNUE6",
    },
 
]

HIKES = [
    {   "trip_id": 1,
        "name": "Rehmhof-Weg",
        "file": "gpx/rehmhof-weg.gpx",  # Relative path to your GPX file
        "duration": "4h",
        "link": "https://www.bodman-ludwigshafen.de/de/Urlaub-am-See/Natur-und-aktiv/Wandern#/article/5d6a106a-fb31-462d-b126-b44ffc65021e"
    },
    {   "trip_id": 1,
        "name": "Rundweg Markelfingen - Wildpark - Mindelseee",
        "file": "gpx/t111836355_rundweg markelfingen-wild.gpx",  # Relative path to your GPX file
        "duration": "2h 40min",
        "link": "https://www.outdooractive.com/de/route/wanderung/bodensee-bw-/rundweg-markelfingen-wildpark-mindelsee/111836355/?utm_source=unknown&utm_medium=social&utm_campaign=user-shared-social-content#dmdtab=oax-tab1"
    },
    {   "trip_id": 2,
        "name": "Wasserfallsteig",
        "file": "gpx/wasserfallsteig.gpx",  # Relative path to your GPX file
        "duration": "3h 15",
        "link": "https://www.badurach-tourismus.de/tour/wasserfallsteig-694f35807b"
    },
     {   "trip_id": 3,
        "name": "Rund um den Sternberg",
        "file": "gpx/t31356257_rund um den sternberg.gpx",  # Relative path to your GPX file
        "duration": "3h 15min",
        "link": "https://www.outdooractive.com/de/route/wanderung/schwaebische-alb-mittelgebirge-/rund-um-den-sternberg/31356257"
    },
    {   "trip_id": 3,
        "name": "Tour hochgesprudelt Premiumwanderweg in Gomadingen",
        "file": "gpx/t27327224_hochgehberge - tour.gpx",  # Relative path to your GPX file
        "duration": "2h 45min",
        "link": "https://regio.outdooractive.com/oar-mythos-alb/de/tour/wanderung/hochgehberge-tour-hochgehsprudelt-premiumwanderweg-in-gomadingen/27327224/?utm_source=whatsapp&utm_medium=social&utm_campaign=user-shared-social-content"
    },
]

locations_home = {
    "Base MM": (49.2951, 8.6989), 
    "Base Plappermaul Paul": (47.488789, 10.718650),  # Example: Reute in Baden-Württemberg
    "Base KAF": (49.1427, 9.2109),
    "Base MRS": (47.4125, 9.7417),
    "Base ST": (49.0069, 8.4037)
}