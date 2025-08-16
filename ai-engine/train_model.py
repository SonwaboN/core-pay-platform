import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# Load the dataset
data = pd.read_csv('synthetic_transactions.csv')

# --- Feature Engineering ---
# One-hot encode the 'device_type' column
categorical_features = ['device_type']
data = pd.get_dummies(data, columns=categorical_features, drop_first=True)

# Define features (X) and target (y)
features = ['amount', 'transactions_per_hour', 'device_type_mobile']
target = 'is_fraud'

X = data[features]
y = data[target]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# --- Model Training ---
# Initialize and train the RandomForestClassifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# --- Model Evaluation ---
y_pred = model.predict(X_test)
print(f"Model Accuracy: {accuracy_score(y_test, y_pred):.2f}")

# --- Save the Model ---
# Save the trained model to a file
joblib.dump(model, 'fraud_detection_model.joblib')

print("Model trained and saved as 'fraud_detection_model.joblib'")
