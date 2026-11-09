
import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load generated drainage sensor data
data = pd.read_csv("drainage_data.csv")

# Features used for prediction
X = data[[
    "water_level",
    "flow_rate",
    "rainfall",
    "pressure"
]]

# Target risk category
y = data["risk"]

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train Random Forest model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate model
predictions = model.predict(X_test)

print("\n===== DRAINGUARD ML RESULTS =====")
print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))
print("Model accuracy:", round(accuracy_score(y_test, predictions) * 100, 2), "%")

print("\nClassification Report:")
print(classification_report(y_test, predictions, zero_division=0))

# Save trained model
with open("drain_model.pkl", "wb") as file:
    pickle.dump(model, file)

print("\nModel saved as drain_model.pkl")

# Predict a sample drainage condition
sample = pd.DataFrame([{
    "water_level": 85,
    "flow_rate": 15,
    "rainfall": 90,
    "pressure": 65
}])

result = model.predict(sample)[0]

print("\nSample drainage prediction:", result)
