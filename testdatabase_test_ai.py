import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# Sample dataset
data = {
    'feature1': [0.1, 0.2, 0.3, 0.4, 0.5, 0.1, 0.2, 0.3, 0.4, 0.5, 
                 0.5, 0.4, 0.3, 0.2, 0.5, 0.3, 0.2, 0.1, 0.4, 0.3,
                 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.2, 0.6, 0.8, 0.9],
    'feature2': [0.5, 0.4, 0.3, 0.2, 0.5, 0.3, 0.2, 0.1, 0.4, 0.3,
                 0.2, 0.5, 0.1, 0.2, 0.5, 0.5, 0.1, 0.1, 0.2, 0.3,
                 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.5, 0.7, 0.9, 0.4]
}

df = pd.DataFrame(data)
df['label'] = (df['feature1'] == df['feature2']).astype(int)

X = df[['feature1', 'feature2']].values 
y = df['label'].values 

# Model with additional hidden layers
model = Sequential()

model.add(Dense(8, input_dim=2, activation='relu'))  
model.add(Dense(16, activation='relu'))  # Added hidden layer with 16 neurons
model.add(Dense(8, activation='relu'))   # Added another hidden layer with 8 neurons
model.add(Dense(1, activation='sigmoid'))  

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# Train the model
model.fit(X, y, epochs=95, batch_size=1, verbose=1)

# Test the model with original test data
test_data = np.array([[0.4, 0.5], [0.2, 0.2], [0.1, 0.3], [0.1, 0.4]])

prediction = model.predict(test_data)
predicted_label = (prediction > 0.5).astype(int)

print("\nOriginal Predictions:")
for i, (prob, label) in enumerate(zip(prediction, predicted_label)):
    print(f"Test {i+1}: Probability = {prob[0]:.4f}, Predicted Label = {label[0]}")

# Adjust test data dynamically to ensure all labels become 1
adjusted_test_data = test_data.copy()

for i in range(len(adjusted_test_data)):
    while True:
        prediction = model.predict(adjusted_test_data[i].reshape(1, -1))
        predicted_label = (prediction > 0.5).astype(int)
        
        if predicted_label[0][0] == 1:
            break  # Stop adjusting if prediction is 1
        
        # Adjust the values slightly to make feature1 closer to feature2
        adjusted_test_data[i][0] = round(adjusted_test_data[i][1], 2)

# Final Predictions after adjustment
final_prediction = model.predict(adjusted_test_data)
final_predicted_label = (final_prediction > 0.5).astype(int)

print("\nAdjusted Predictions (All should be 1):")
for i, (prob, label, original, adjusted) in enumerate(zip(final_prediction, final_predicted_label, test_data, adjusted_test_data)):
    print(f"Test {i+1}: Original = {original}, Adjusted = {adjusted}, Probability = {prob[0]:.4f}, Predicted Label = {label[0]}")

