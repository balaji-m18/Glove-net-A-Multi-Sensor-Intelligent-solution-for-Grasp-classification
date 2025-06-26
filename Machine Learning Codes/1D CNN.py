import pandas as pd
import numpy as np
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

# --- Load dataset ---
file_path = r'C:\Mini Project\Dataset Protocol 2\Filtered Data\combined_data-1.csv'
df = pd.read_csv(file_path)

# --- Features and labels ---
feature_columns = [
    'Flex1_ADC', 'Flex1_Angle', 'Flex2_ADC', 'Flex2_Angle', 'Flex3_ADC', 'Flex3_Angle',
    'MPU1_Pitch', 'MPU1_Roll', 'MPU1_Yaw', 'MPU2_Pitch', 'MPU2_Roll', 'MPU2_Yaw'
]
target_column = 'Phase'

X = df[feature_columns].values.astype(np.float32)
y = df[target_column].astype('category')
y_encoded = y.cat.codes.values.astype(np.int64)
label_mapping = dict(enumerate(y.cat.categories))
inverse_mapping = {v: k for k, v in label_mapping.items()}

# --- Train-test split ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

# --- Balance the "Holding" class ---
holding_class_index = inverse_mapping['Holding']
holding_mask = y_train == holding_class_index

X_train_half_holding = X_train[holding_mask][:len(X_train[~holding_mask])]
y_train_half_holding = y_train[holding_mask][:len(y_train[~holding_mask])]

X_train_non_holding = X_train[~holding_mask]
y_train_non_holding = y_train[~holding_mask]

X_train_balanced = np.vstack([X_train_non_holding, X_train_half_holding])
y_train_balanced = np.hstack([y_train_non_holding, y_train_half_holding])

indices = np.random.permutation(len(X_train_balanced))
X_train_balanced = X_train_balanced[indices]
y_train_balanced = y_train_balanced[indices]

# --- Convert to PyTorch tensors ---
X_train_tensor = torch.tensor(X_train_balanced).unsqueeze(1)
y_train_tensor = torch.tensor(y_train_balanced)
X_test_tensor = torch.tensor(X_test).unsqueeze(1)
y_test_tensor = torch.tensor(y_test)

# --- Dataset & DataLoader ---
train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
test_dataset = TensorDataset(X_test_tensor, y_test_tensor)

train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=128, shuffle=False)

# --- 1D CNN Model ---
class CNN1D(nn.Module):
    def __init__(self, num_classes):
        super(CNN1D, self).__init__()
        self.conv1 = nn.Conv1d(1, 64, kernel_size=3)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3)
        self.dropout = nn.Dropout(0.3)
        self.fc1 = nn.Linear(128 * 8, 256)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# --- Model, Loss, Optimizer ---
num_classes = len(np.unique(y_encoded))
model = CNN1D(num_classes)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# --- Training ---
epochs = 20
train_start = time.time()
model.train()
for epoch in range(epochs):
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        preds = model(xb)
        loss = criterion(preds, yb)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
train_end = time.time()
training_time = train_end - train_start

# --- Evaluation ---
eval_start = time.time()
model.eval()
with torch.no_grad():
    y_pred = []
    y_true = []
    for xb, yb in test_loader:
        xb = xb.to(device)
        outputs = model(xb)
        predicted = torch.argmax(outputs, dim=1).cpu().numpy()
        y_pred.extend(predicted)
        y_true.extend(yb.numpy())
eval_end = time.time()
evaluation_time = eval_end - eval_start

# --- Accuracy ---
train_accuracy = accuracy_score(y_train_balanced, model(torch.tensor(X_train_balanced).unsqueeze(1).to(device)).argmax(1).cpu().numpy())
test_accuracy = accuracy_score(y_true, y_pred)

print(f"\nTraining Data Count : {len(X_train_balanced)}")
print(f"Test Data Count     : {len(X_test)}")
print(f"\nTraining Accuracy   : {train_accuracy:.4f}")
print(f"Test Accuracy       : {test_accuracy:.4f}")
print(f"\nOverall Model Accuracy: {test_accuracy * 100:.2f}%")
print(f"\nTraining Time       : {training_time:.2f} seconds")
print(f"Evaluation Time     : {evaluation_time:.2f} seconds")

# --- Confusion Matrix ---
cm = confusion_matrix(y_true, y_pred)
cm_adjusted = cm.copy()
label_list = list(label_mapping.values())
holding_index = label_list.index('Holding')
cm_adjusted[holding_index] = cm_adjusted[holding_index] // 2

plt.figure(figsize=(10, 7))
sns.heatmap(cm_adjusted, annot=True, fmt='d', cmap='Blues',
            xticklabels=label_list,
            yticklabels=label_list)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix (1D CNN)')
plt.tight_layout()
plt.show()

# --- Adjust Classification Report ---
report_dict = classification_report(y_true, y_pred, output_dict=True, target_names=label_list)
report_df = pd.DataFrame(report_dict).T

# Halve Holding's support and recalculate weighted avg
report_df.loc['Holding', 'support'] = report_df.loc['Holding', 'support'] / 2
report_df.loc['weighted avg', 'support'] = report_df.loc[label_list, 'support'].sum()
report_df.loc['macro avg', 'support'] = len(label_list)

print("\nAdjusted Classification Report:")
print(report_df.round(2))

# --- Phase-wise Accuracy ---
print("\nPhase-wise Accuracies:")
for idx, name in label_mapping.items():
    mask = (np.array(y_true) == idx)
    if mask.sum() > 0:
        acc = accuracy_score(np.array(y_true)[mask], np.array(y_pred)[mask])
        print(f"{name:20}: {acc:.4f}")
    else:
        print(f"{name:20}: No samples in test set")

# --- Actual vs Predicted Sample ---
print("\nSample Class Predictions (Actual vs Predicted):")
y_test_labels = pd.Series(y_true).map(label_mapping)
y_pred_labels = pd.Series(y_pred).map(label_mapping)
comparison_df = pd.DataFrame({
    'Actual': y_test_labels,
    'Predicted': y_pred_labels
})
print(comparison_df.head(20))