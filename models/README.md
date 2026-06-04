# Models

## forecaster_v1.pkl
Prophet-based per-signal forecaster. Trained on cached coordinate histories.
Retrain: `python scripts/retrain_forecaster.py`
W&B project: `chronos-forecaster`

## Versioning
Model artifacts are tracked in W&B and DVC. `.pkl` files are gitignored.
To fetch latest: `dvc pull models/`
