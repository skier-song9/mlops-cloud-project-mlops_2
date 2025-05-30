import numpy as np
from sklearn.metrics import root_mean_squared_error

def cross_validation(model_card, fold_datasets):
    # cross-validation
    scores = []
    for train_dataset, val_dataset in fold_datasets:
        model_card.train(train_dataset, val_dataset)
        preds = model_card.inference(val_dataset)
        rmse = root_mean_squared_error(val_dataset.target, preds)
        scores.append(rmse)
    mean_val_score = np.mean(scores)
    return model_card, mean_val_score