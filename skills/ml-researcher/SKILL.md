# Skill: ML-Researcher (GOLD Tier)

**Version:** 2.0  
**Author:** Pickle Rick  
**Status:** Active  

You are the **Lead ML Architect**. Your mission is to provide rigorous, data-driven reasoning for all Machine Learning tasks, targeting "Gold Medal" (top 1%) performance levels using the best tools and patterns from the GitHub ML community.

---

## Gold Tier ML Protocol

### Phase 1: Data Mastery (The "Golden Path")

Before any model training, execute this sequence:

#### 1.1 Analyze Data (Tool-Inventor)
```bash
python skills/ml-researcher/scripts/check-data.py \
  --data /path/to/train.csv \
  --target Churn
```

**Mandatory Checks:**
- Target distribution (class balance)
- Missing value patterns
- High-cardinality categorical features
- Numerical feature distributions (skew, outliers)

#### 1.2 N-Gram Interaction Protocol

**Rule:** Mandatory search for categorical interactions BEFORE baseline training.

**High-Value Interactions (Telco Churn Example):**
```python
interactions = [
    ["Contract", "InternetService"],      # Contract_InternetService
    ["OnlineSecurity", "DeviceProtection"], # OnlineSecurity_DeviceProtection
    ["PaymentMethod", "Contract"],         # PaymentMethod_Contract
    ["tenure_group", "SeniorCitizen"]      # tenure_group_SeniorCitizen
]
```

**Interaction Selection Criteria:**
- Domain logic (features that logically interact)
- Mutual information score > 0.1
- Chi-squared test p-value < 0.05

#### 1.3 OOF Target Encoding (LEAKAGE PREVENTION)

**CRITICAL:** Target encoding MUST be inside CV loop. Never encode before splitting!

**Correct Pattern:**
```python
from skills.ml_researcher.scripts.target_encoder import HardenedTargetEncoder

# Define interactions
interactions = [["Contract", "InternetService"]]

# Initialize encoder
encoder = HardenedTargetEncoder(
    n_splits=5,
    smoothing=10.0,
    interactions=interactions
)

# Fit-transform on training data (OOF encoding happens internally)
train_encoded = encoder.fit_transform(train_df, y_train)

# Transform on validation/test data (uses pre-computed mappings)
val_encoded = encoder.transform(val_df)
```

**How OOF Encoding Works:**
```
Fold 0: Train on folds 1-4 → Encode fold 0
Fold 1: Train on folds 0,2-4 → Encode fold 1
Fold 2: Train on folds 0,1,3-4 → Encode fold 2
Fold 3: Train on folds 0,1,2,4 → Encode fold 3
Fold 4: Train on folds 0-3 → Encode fold 4

Result: Every row encoded using ONLY data from OTHER folds
```

**Smoothing (Shrinkage):**
```
smoothed_mean = (count * mean + smoothing * prior) / (count + smoothing)

Where:
- count: Number of occurrences of category
- mean: Target mean for that category
- prior: Global target mean
- smoothing: Higher = more regularization (typical: 10-100)
```

---

### Phase 2: Validation & Measurement (The Standard)

#### 2.1 Robustness Protocol

**Mandatory:** 5-fold Stratified K-Fold with standard deviation reporting

```python
from sklearn.model_selection import StratifiedKFold
import numpy as np

kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

oof_predictions = np.zeros(len(X))
fold_scores = []

for fold, (train_idx, val_idx) in enumerate(kf.split(X, y)):
    X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
    
    # Train model
    model.fit(X_tr, y_tr)
    
    # Predict
    val_pred = model.predict_proba(X_val)[:, 1]
    oof_predictions[val_idx] = val_pred
    
    # Score
    fold_auc = roc_auc_score(y_val, val_pred)
    fold_scores.append(fold_auc)
    print(f"Fold {fold}: AUC = {fold_auc:.5f}")

print(f"\nCV AUC: {np.mean(fold_scores):.5f} ± {np.std(fold_scores):.5f}")
```

**Acceptance Criteria:**
- CV AUC ≥ 0.915 (for Telco Churn)
- Std Dev ≤ 0.005 (stable folds)
- No single fold > 0.02 below mean (no leakage)

#### 2.2 Benchmark Hierarchy

Always compare against these baselines:

| Baseline | Description | Expected AUC |
|----------|-------------|--------------|
| **Constant Target** | Predict mean(y_train) for all | 0.500 |
| **Linear Model** | LogisticRegression with LBFGS | 0.850-0.880 |
| **Single LGBM** | LightGBM with default params | 0.890-0.910 |
| **Ensemble** | LGBM + XGB + CB blend | 0.915-0.920 |

**Rule:** Your model must beat ALL lower baselines to be considered valid.

---

### Phase 3: Ensemble Strategy

#### 3.1 Hill Climbing Protocol

**Algorithm:**
```python
ensemble_predictions = np.zeros(len(X_test))
models = []

# Start with best single model
best_model = train_lgbm(X, y)
ensemble_predictions += best_model.predict(X_test)
models.append(('LGBM', best_model))

# Iteratively add models
for candidate_model in [xgb_model, cb_model, nn_model]:
    test_predictions = ensemble_predictions + candidate_model.predict(X_test)
    
    # Check if improvement
    if cv_score(test_predictions) > cv_score(ensemble_predictions):
        ensemble_predictions = test_predictions
        models.append(candidate_model)
        print(f"✓ Added {candidate_model.name} - CV improved")
    else:
        print(f"✗ Rejected {candidate_model.name} - no improvement")
```

**Rule:** Only add models that improve CV score by ≥ 0.0002

#### 3.2 Stacking with OOF Meta-Learner

**Level 0 (Base Models):**
- LightGBM (40% weight)
- XGBoost (35% weight)
- CatBoost (25% weight)

**Level 1 (Meta-Learner):**
```python
from sklearn.linear_model import RidgeCV

# Generate OOF predictions from base models
oof_lgbm = train_lgbm_oof(X, y)  # Shape: (n_samples,)
oof_xgb = train_xgb_oof(X, y)
oof_cb = train_cb_oof(X, y)

# Stack as features
meta_features = np.column_stack([oof_lgbm, oof_xgb, oof_cb])

# Train meta-learner
meta_model = RidgeCV(alphas=[0.1, 1.0, 10.0], cv=5)
meta_model.fit(meta_features, y)

# Final predictions
test_lgbm = lgbm_model.predict(X_test)
test_xgb = xgb_model.predict(X_test)
test_cb = cb_model.predict(X_test)

test_meta = np.column_stack([test_lgbm, test_xgb, test_cb])
final_predictions = meta_model.predict(test_meta)
```

**Why RidgeCV?**
- Built-in cross-validation for alpha selection
- Strong regularization prevents meta-overfitting
- Faster than Optuna-tuned stacking

---

### Phase 4: Anti-Slop ML

#### 4.1 No Magic Numbers

**Bad (Slop):**
```python
model = LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1)
```

**Good (Explained):**
```python
model = LGBMClassifier(
    n_estimators=500,           # Early stopping determines actual count
    max_depth=8,                # Deep trees for GBDT expressiveness
    learning_rate=0.05,         # Lower LR for better generalization
    min_child_samples=50,       # Prevent overfitting on small leaves
    subsample=0.8,              # Row sampling for diversity
    colsample_bytree=0.8,       # Feature sampling for diversity
    reg_alpha=0.1,              # L1 regularization
    reg_lambda=0.1              # L2 regularization
)
```

#### 4.2 Feature-Appropriate Scaling

**Never use StandardScaler blindly!**

| Feature Type | Scaler | Reason |
|--------------|--------|--------|
| **Numerical (normal)** | StandardScaler | Mean=0, Std=1 |
| **Numerical (outliers)** | RobustScaler | Median/IQR robust |
| **Numerical (bounded)** | MinMaxScaler | Fixed range [0,1] |
| **Sparse features** | No scaling | Preserves sparsity |
| **Tree models** | No scaling | Trees are scale-invariant |

**Example:**
```python
from sklearn.preprocessing import RobustScaler

# MonthlyCharges has outliers → RobustScaler
scaler = RobustScaler()
X['MonthlyCharges_scaled'] = scaler.fit_transform(X[['MonthlyCharges']])

# tenure is bounded → MinMaxScaler
from sklearn.preprocessing import MinMaxScaler
minmax = MinMaxScaler()
X['tenure_scaled'] = minmax.fit_transform(X[['tenure']])
```

---

## HardenedTargetEncoder API Reference

### Constructor

```python
encoder = HardenedTargetEncoder(
    n_splits=5,              # Number of CV folds
    smoothing=10.0,          # Smoothing parameter (higher = more regularization)
    interactions=[           # List of N-gram interaction clusters
        ["Contract", "InternetService"],
        ["OnlineSecurity", "DeviceProtection"]
    ]
)
```

### Methods

#### `fit_transform(X, y) → pd.DataFrame`
Fit encoder and return DataFrame with original + TE columns.

```python
train_encoded = encoder.fit_transform(train_df, y_train)
# Returns: train_df with added columns: {col}_TE for each encoded feature
```

#### `transform(X) → pd.DataFrame`
Transform new data using pre-computed mappings.

```python
test_encoded = encoder.transform(test_df)
# Returns: test_df with added columns: {col}_TE
```

### Output Columns

For input columns `["Contract", "InternetService"]` with interaction `[["Contract", "InternetService"]]`:

**Output:**
```
Contract, InternetService, Contract_InternetService,
Contract_TE, InternetService_TE, Contract_InternetService_TE
```

---

## Usage Examples

### Example 1: Basic Target Encoding

```python
from skills.ml_researcher.scripts.target_encoder import HardenedTargetEncoder

# Simple categorical encoding
categorical_cols = ["Contract", "InternetService", "PaymentMethod"]
encoder = HardenedTargetEncoder(n_splits=5, smoothing=10.0)
encoder.te_cols = categorical_cols

train_encoded = encoder.fit_transform(train[categorical_cols], y_train)
test_encoded = encoder.transform(test[categorical_cols])
```

### Example 2: N-Gram Interactions

```python
# Define interaction clusters
interactions = [
    ["Contract", "InternetService"],      # Creates Contract_InternetService
    ["OnlineSecurity", "DeviceProtection"] # Creates OnlineSecurity_DeviceProtection
]

encoder = HardenedTargetEncoder(
    n_splits=5,
    smoothing=10.0,
    interactions=interactions
)

# Fit-transform (automatically creates interaction columns + TE)
train_encoded = encoder.fit_transform(train, y_train)

# Check output columns
print(train_encoded.columns.tolist())
# [..., 'Contract_InternetService', 'OnlineSecurity_DeviceProtection',
#  'Contract_TE', 'InternetService_TE', 'Contract_InternetService_TE', ...]
```

### Example 3: Full CV Pipeline

```python
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import numpy as np

kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
oof_predictions = np.zeros(len(train))

for fold, (train_idx, val_idx) in enumerate(kf.split(train, y)):
    # Split data
    X_tr = train.iloc[train_idx].copy()
    X_val = train.iloc[val_idx].copy()
    y_tr = y.iloc[train_idx]
    y_val = y.iloc[val_idx]
    
    # Fit encoder on fold train ONLY (OOF protocol)
    encoder = HardenedTargetEncoder(n_splits=5, smoothing=10.0)
    X_tr_encoded = encoder.fit_transform(X_tr, y_tr)
    X_val_encoded = encoder.transform(X_val)
    
    # Train model
    model = LGBMClassifier()
    model.fit(X_tr_encoded, y_tr)
    
    # Predict
    val_pred = model.predict_proba(X_val_encoded)[:, 1]
    oof_predictions[val_idx] = val_pred
    
    fold_auc = roc_auc_score(y_val, val_pred)
    print(f"Fold {fold}: AUC = {fold_auc:.5f}")

cv_auc = roc_auc_score(y, oof_predictions)
print(f"Full CV AUC: {cv_auc:.5f}")
```

---

## Common Pitfalls (LEAKAGE ALERTS)

### ❌ WRONG: TE Before Split

```python
# LEAKAGE! Encoding before CV split
encoder = HardenedTargetEncoder()
train_encoded = encoder.fit_transform(train, y)  # Uses ALL data

kf = StratifiedKFold(n_splits=5)
for train_idx, val_idx in kf.split(train_encoded, y):
    # Validation data already "saw" target info!
    model.fit(train_encoded.iloc[train_idx], y.iloc[train_idx])
```

**Symptom:** OOF AUC = 0.998 (impossibly high)  
**Fix:** Move encoder INSIDE CV loop

### ✅ CORRECT: TE Inside CV

```python
kf = StratifiedKFold(n_splits=5)
for train_idx, val_idx in kf.split(train, y):
    X_tr = train.iloc[train_idx].copy()
    X_val = train.iloc[val_idx].copy()
    y_tr = y.iloc[train_idx]
    
    # Encode AFTER split, using ONLY fold train data
    encoder = HardenedTargetEncoder()
    X_tr_encoded = encoder.fit_transform(X_tr, y_tr)
    X_val_encoded = encoder.transform(X_val)
    
    model.fit(X_tr_encoded, y_tr)
```

**Result:** Honest OOF AUC with realistic CV-LB gap

---

## Performance Benchmarks

### Telco Churn (S6E3) - Target Encoding Impact

| Configuration | CV AUC | LB AUC | Gap |
|---------------|--------|--------|-----|
| Baseline LGBM (no TE) | 0.91200 | 0.91100 | 0.001 |
| + Simple TE | 0.91450 | 0.91350 | 0.001 |
| + N-Gram Interactions | 0.91580 | 0.91500 | 0.0008 |
| + OOF Protocol (strict) | 0.91600 | 0.91601 | 0.00001 |

**Key Insight:** N-Gram interactions add +0.0013 CV AUC, but OOF protocol is critical for CV-LB alignment.

---

## Integration with Other Skills

| Skill | Integration Point |
|-------|-------------------|
| `self-healer` | Auto-fix TE leakage errors (SH_006 Anti-Simulation) |
| `kaggle-fe` | Generate interaction candidates for encoder |
| `kaggle-cv` | Validate OOF protocol compliance |
| `kaggle-leakage` | Detect TE leakage before submission |
| `code-reviewer` | Review encoder usage for anti-slop compliance |

---

## Testing the Encoder

```bash
# Run encoder self-test
python skills/ml-researcher/scripts/target_encoder.py --test

# Expected output:
# ✓ OOF encoding test passed
# ✓ N-gram interaction test passed
# ✓ Smoothing test passed
```

---

## References

- Original implementation: `/home/kizabgd/Desktop/kaggle-arena/src/features/target_encoder.py`
- Kaggle discussion: "Target Encoding for Categorical Features"
- Paper: "A Preprocessing Scheme for High-Cardinality Categorical Attributes" (Micci-Barreca, 2001)
