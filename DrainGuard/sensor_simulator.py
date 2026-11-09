import csv
import random

random.seed(42)

zones = [f"Zone-{i}" for i in range(1, 7)]

with open("drainage_data.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "zone", "water_level", "flow_rate",
        "rainfall", "pressure", "risk"
    ])

    for zone in zones:
        for _ in range(100):
            rainfall = random.uniform(0, 100)
            water = random.uniform(10, 100)
            flow = random.uniform(5, 100)
            pressure = random.uniform(10, 80)

            if water > 75 and flow < 25:
                risk = "Critical"
            elif water > 60 and flow < 40:
                risk = "High"
            elif water > 45 and rainfall > 70:
                risk = "Moderate"
            else:
                risk = "Normal"

            writer.writerow([
                zone, round(water, 2), round(flow, 2),
                round(rainfall, 2), round(pressure, 2), risk
            ])

print("DrainGuard sensor data generated!")
print("Zones:", len(zones))
print("Total readings:", len(zones) * 100)
print("Output: drainage_data.csv")