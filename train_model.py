import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle

# Load dataset
df = pd.read_csv("loan.csv")

# Strip spaces from column names
df.columns = df.columns.str.strip()

# Preprocess categorical columns
df['education'] = df['education'].apply(lambda x: 1 if x.lower() == "graduate" else 0)
df['self_employed'] = df['self_employed'].apply(lambda x: 1 if x.lower() == "yes" else 0)

# Features and target
X = df[['no_of_dependents', 'education', 'self_employed',
        'income_annum', 'loan_amount', 'loan_term', 'cibil_score',
        'residential_assets_value','commercial_assets_value',
        'luxury_assets_value','bank_asset_value']]
y = df['loan_status']

# Split dataset into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Evaluate model
accuracy = model.score(X_test, y_test)
print(f"Test Accuracy: {accuracy:.2f}")

# Save model
with open("loan_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved successfully!")
