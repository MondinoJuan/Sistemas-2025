import requests


# Pruebo HERE
def test_here_api():
    bbox = "48.872,2.293;48.875,2.296"  # aprox. rotonda
    url = f"https://traffic.ls.hereapi.com/traffic/6.3/flow.json?bbox={bbox}&apiKey=TU_API_KEY"
    r = requests.get(url); r.raise_for_status()
    print(r.json())

# Pruebo TomTom
def test_tomtom_api():
    bbox = "48.872,2.293,48.875,2.296"
    url = f"https://api.tomtom.com/traffic/services/5/incidentDetails?bbox={bbox}&fields={{incidents{{...}}}}&key=TU_API_KEY"
    r = requests.get(url); r.raise_for_status()
    print(r.json())


# Pruebo Google Directions
def test_google_directions_api():
    origin = "48.8738,2.2946"; dest = "48.8738,2.2955"
    url = ("https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origin}&destination={dest}&departure_time=now&traffic_model=best_guess&key=TU_API_KEY")
    r = requests.get(url); r.raise_for_status()
    print(r.json()["routes"][0]["legs"][0]["duration_in_traffic"])


