# Model card

## Intended use

The XGBoost model ranks simulated card transactions for analyst review. It is an educational baseline for streaming ML infrastructure, not a production underwriting or payment-denial model.

## Training data

`app.train` generates 25,000 synthetic examples from documented statistical distributions. Fraud labels derive from amount, velocity, amount deviation, rapid travel, device novelty, country change, and card presence. These relationships are intentionally learnable and do not represent real fraud prevalence.

## Metrics

The training command prints a held-out classification report. Live labeled decisions are measured separately through `app.evaluate`. A production release gate should include time-based validation, probability calibration, precision at review capacity, cost-weighted recall, geographic/customer slices, and stability across multiple time windows.

## Risks

Synthetic data cannot reveal real bias, leakage, adversarial adaptation, or delayed-label behavior. Device and location signals can create accessibility and geographic disparities. Analysts need explanations, an appeal process, and safeguards against automation bias.

