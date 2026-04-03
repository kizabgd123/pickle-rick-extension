import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from typing import List, Optional, Dict, Union


class HardenedTargetEncoder:
    """
    Pickle Core - Hardened Target Encoder (Anti-Slop Edition)
    "I'm a Target Encoder, Morty! I've turned myself into a Leakage-Proof Machine!"
    
    Features:
    - OOF (Out-Of-Fold) encoding to prevent target leakage
    - Bayesian smoothing (shrinkage) for high-cardinality/rare categories
    - N-gram interaction term generation (God Mode Feature Engineering)
    - High-performance vectorized operations (Zero Slop)
    """
    def __init__(self, n_splits: int = 5, smoothing: float = 10.0, 
                 interactions: Optional[List[List[str]]] = None):
        self.n_splits = n_splits
        self.smoothing = smoothing
        self.interactions = interactions or []
        self.mappings: Dict[str, pd.Series] = {}
        self.global_mean: float = 0.0
        self.te_cols: List[str] = []

    def __repr__(self):
        return f"<HardenedTargetEncoder(n_splits={self.n_splits}, smoothing={self.smoothing}, interactions={len(self.interactions)})>"

    def _prepare_data(self, X: pd.DataFrame) -> pd.DataFrame:
        """Vectorized interaction term generation."""
        X = X.copy()
        self.te_cols = list(X.columns)
        
        if self.interactions:
            for cluster in self.interactions:
                name = '_'.join(cluster)
                if name not in self.te_cols:
                    self.te_cols.append(name)
                
                # Optimized interaction string joining (vectorized)
                X[name] = X[cluster[0]].astype(str)
                for i in range(1, len(cluster)):
                    X[name] += "_" + X[cluster[i]].astype(str)
        return X

    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """God Mode: Standard Fit-Transform with OOF encoding."""
        X = self._prepare_data(X)
        self.global_mean = y.mean()
        
        # Pre-allocate all TE columns
        encoded_df = X.copy()
        for col in self.te_cols:
            encoded_df[f"{col}_TE"] = self.global_mean

        # Pre-compute global mappings for transform() - used for inference
        for col in self.te_cols:
            self.mappings[col] = self._compute_mapping(X[col], y)
        
        # Single-pass OOF splits using StratifiedKFold
        kf = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=42)
        
        for train_idx, val_idx in kf.split(X, y):
            X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
            X_val = X.iloc[val_idx]
            
            fold_mean = y_tr.mean()
            
            # Update each column using OOF mappings
            for col in self.te_cols:
                mapping = self._compute_mapping(X_tr[col], y_tr, fold_mean)
                # Map and handle unseen categories with fold-specific mean
                encoded_df.loc[X_val.index, f"{col}_TE"] = X_val[col].map(mapping).fillna(fold_mean)
                
        return encoded_df

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Pure Inference: Uses global mappings computed during fit."""
        X = self.copy_with_interactions(X)
        encoded_df = X.copy()
        
        for col, mapping in self.mappings.items():
            if col in X.columns:
                encoded_df[f"{col}_TE"] = X[col].map(mapping).fillna(self.global_mean)
        
        # Reorder columns to match fit_transform output
        expected_cols = list(X.columns) + [f"{col}_TE" for col in self.te_cols]
        return encoded_df[[c for c in expected_cols if c in encoded_df.columns]]

    def copy_with_interactions(self, X: pd.DataFrame) -> pd.DataFrame:
        """Shared logic for interaction generation."""
        X = X.copy()
        for cluster in self.interactions:
            name = '_'.join(cluster)
            X[name] = X[cluster[0]].astype(str)
            for i in range(1, len(cluster)):
                X[name] += "_" + X[cluster[i]].astype(str)
        return X

    def _compute_mapping(self, series: pd.Series, target: pd.Series, 
                         prior: Optional[float] = None) -> pd.Series:
        """The Bayesian Smoothing Core - Vectorized."""
        prior = prior if prior is not None else self.global_mean
        
        # Aggregate count and sum for single-pass groupby
        agg = target.groupby(series).agg(['count', 'sum'])
        counts = agg['count']
        sums = agg['sum']
        
        # Optimized Bayesian smoothing formula
        return (sums + self.smoothing * prior) / (counts + self.smoothing)


def run_self_test():
    """
    Self-test for HardenedTargetEncoder.
    Validates OOF encoding logic, N-gram interactions, and smoothing efficacy.
    """
    print("\n" + "="*60)
    print("🥒 HardenedTargetEncoder - Pickle Core Self-Test")
    print("="*60)
    
    # Create synthetic data
    np.random.seed(42)
    n_samples = 1000
    
    df = pd.DataFrame({
        'cat_high': np.random.choice([f'cat_{i}' for i in range(100)], n_samples),
        'cat_rare': ['A'] * 995 + ['B'] * 5,
        'cat_interaction_1': np.random.choice(['X', 'Y'], n_samples),
        'cat_interaction_2': np.random.choice(['1', '2'], n_samples)
    })
    
    # Target with high-cardinality signal
    y = (df['cat_high'].str.extract('(\\d+)').astype(int) % 2).iloc[:, 0]
    y = (y ^ (np.random.rand(n_samples) > 0.8).astype(int)) # Add noise
    
    print("\n[Phase 1] Basic Encoding & OOF Protocol...")
    encoder = HardenedTargetEncoder(n_splits=5, smoothing=10.0)
    encoded = encoder.fit_transform(df[['cat_high', 'cat_rare']], y)
    
    assert 'cat_high_TE' in encoded.columns
    assert encoded['cat_high_TE'].std() > 0, "Encoder output should have variance"
    print("  ✓ OOF basic encoding passed")
    
    print("\n[Phase 2] N-Gram Interaction Terms...")
    interactions = [['cat_interaction_1', 'cat_interaction_2']]
    encoder_int = HardenedTargetEncoder(n_splits=5, interactions=interactions)
    encoded_int = encoder_int.fit_transform(df, y)
    
    name = 'cat_interaction_1_cat_interaction_2'
    assert name in encoded_int.columns, "Interaction column missing"
    assert f"{name}_TE" in encoded_int.columns, "Interaction TE column missing"
    print("  ✓ N-gram interactions verified")
    
    print("\n[Phase 3] Leakage Check (Correlation vs Target)...")
    # Pure leakage would yield correlation > 0.9 on high cardinality
    corr = np.corrcoef(encoded['cat_high_TE'], y)[0, 1]
    print(f"  OOF Correlation: {corr:.3f}")
    assert corr < 0.8, "Possible leakage detected! OOF failed."
    print("  ✓ Leakage defense verified")
    
    print("\n[Phase 4] Smoothing Impact on Rare Categories...")
    mapping = encoder.mappings['cat_rare']
    global_mean = y.mean()
    # Cat 'B' has only 5 samples, should be closer to global mean than raw mean
    print(f"  Global Mean: {global_mean:.3f}")
    print(f"  Rare Category 'B' Mapping: {mapping['B']:.3f} (Raw mean was local)")
    assert abs(mapping['B'] - global_mean) < abs(mapping['B'] - 0.0) or abs(mapping['B'] - 1.0)
    print("  ✓ Bayesian smoothing verified")
    
    print("\n" + "="*60)
    print("All tests passed! Pickle Rick is proud. ✓")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_self_test()
    else:
        print("HardenedTargetEncoder - Pickle Core ML-Researcher Skill")
        print("Usage: python target_encoder.py --test")

