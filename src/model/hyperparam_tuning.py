import numpy as np
from hyperopt import hp,STATUS_OK, fmin, tpe, Trials
from hyperopt.pyll.base import scope
from sklearn.metrics import root_mean_squared_error

class SearchSpace:
    search_space = dict()
    search_choice = dict()
    search_int = dict()
    ### LGBMRegerssor
    search_space['LGBMRegressor'] = {
        'num_leaves': scope.int(hp.quniform('num_leaves', 20, 150, 1)),
        'max_depth': scope.int(hp.quniform('max_depth', 3, 15, 1)),
        'learning_rate': hp.qloguniform('learning_rate', np.log(0.01), np.log(0.2), 0.01),
        'n_estimators': scope.int(hp.quniform('n_estimators', 500, 5000, 100)),
        'min_child_samples': scope.int(hp.quniform('min_child_samples', 20, 500, 5)),
        'subsample': hp.quniform('subsample', 0.5, 0.95, 0.05),
        'colsample_bytree': hp.quniform('colsample_bytree', 0.5, 1.0, 0.05),
        'reg_alpha': hp.qloguniform('reg_alpha', np.log(1e-8), np.log(10.0), 0.01),
        'reg_lambda': hp.qloguniform('reg_lambda', np.log(1e-8), np.log(10.0), 0.01),
        'min_split_gain': hp.qloguniform('min_split_gain', np.log(1e-8), np.log(1.0), 0.01),
        'boosting_type': hp.choice('boosting_type', ['gbdt', 'dart', 'goss']),
        'objective':hp.choice('objective',['regression','huber','fair'])
    }
    search_int['LGBMRegressor'] = [
        'num_leaves','max_depth','n_estimators','min_child_samples'
    ]
    search_choice['LGBMRegressor'] = {
        'boosting_type':['gbdt', 'dart', 'goss'],
        'objective':['regression','huber','fair','gamma']
    }
    ### CatBoostRegressor
    search_space['CatBoostRegressor'] = {
        'iterations': scope.int(hp.quniform('n_estimators', 500, 5000, 100)),
        'depth': scope.int(hp.quniform('depth', 4, 10, 1)),
        'learning_rate': hp.qloguniform('learning_rate', np.log(0.01), np.log(0.3), 0.01),
        'l2_leaf_reg': hp.qloguniform('l2_leaf_reg', np.log(1), np.log(20), 1),
        'border_count': scope.int(hp.quniform('border_count', 32, 255, 1)),
        'random_strength': scope.int(hp.quniform('random_strength', 1, 20, 1)),
        'min_data_in_leaf': scope.int(hp.quniform('min_data_in_leaf', 1, 20, 1)),
        'leaf_estimation_iterations': hp.quniform('leaf_estimation_iterations', 1, 20, 1),
        'leaf_estimation_method': hp.choice('leaf_estimation_method', ['Newton', 'Gradient']),
        'grow_policy': hp.choice('grow_policy', ['SymmetricTree', 'Depthwise']),
        'bootstrap_type': hp.choice('bootstrap_type', ['Bayesian', 'Bernoulli', 'MVS'])
    }
    search_int['CatBoostRegressor'] = [
        'iterations','depth','border_count','random_strength','min_data_in_leaf',
    ]
    search_choice['CatBoostRegressor'] = {
        'leaf_estimation_method': ['Newton', 'Gradient'],
        'grow_policy': ['SymmetricTree', 'Depthwise'],
        'bootstrap_type': ['Bayesian', 'Bernoulli', 'MVS'],
    }


def hyperparameter_tuning(model_card, fold_datasets, max_evals=10):
    ss = SearchSpace
    search_space = ss.search_space.get(model_card.name, None)
    search_choice = ss.search_choice.get(model_card.name, False)
    search_int = ss.search_int.get(model_card.name, False)
    if search_space is None:
        raise ValueError(f"Hyperparameter Search space of {model_card.name} model is not defined.")
    
    def objective(params):
        if search_int:
            for si in search_int:
                params[si] = int(params[si])
        model_card.init_model(params)

        # cross-validation
        scores = []
        for train_dataset, val_dataset in fold_datasets:
            model_card.train(train_dataset, val_dataset)
            preds = model_card.inference(val_dataset)
            rmse = root_mean_squared_error(val_dataset.target, preds)
            scores.append(rmse)
        return {'loss':np.mean(scores), 'status':STATUS_OK}
    trials = Trials()
    best = fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=max_evals,
        trials=trials,
        rstate=np.random.default_rng(model_card.random_seed)
    )
    if search_int:
        for si in search_int:
            best[si] = int(best[si])
    if search_choice:
        for sc in search_choice:
            best[sc] = search_choice.get(sc)[best[sc]]
    # best hyper parameter로 모델 초기화
    model_card.params = best
    model_card.init_model(best)
    # ✅ mean score 계산
    all_scores = [trial['result']['loss'] for trial in trials.trials]
    mean_val_score = np.mean(all_scores)
    return model_card, mean_val_score