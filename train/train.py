from src.services import transformerclass
from src.utils.model_functions import compute_evaluation_metrics
from . import data_splitter
from . import (config, etl_metadata, etl_metadata_serialized)

import numpy as np
from sklearn.pipeline import Pipeline
import xgboost as xgb
import pickle
import joblib
import json


class Train():

    def __init__(self) -> None:
        pass

    def run(self):
        print('Start training...')

        ds_data = joblib.load(f'data/processed/{etl_metadata.output_processed}')
        target = etl_metadata.target
        features = etl_metadata.features

        splitter = data_splitter.DataSplitter(ds_data)
        ds_train, ds_test = splitter.split_train_test(ds_data)

        X_train = ds_train[features]
        X_test = ds_test[features]
        y_train = ds_train[target]
        y_test = ds_test[target]

        transformer = transformerclass.Transformer(etl_metadata.features)
        X_train = transformer.scale_data(X_train)
        X_test = transformer.scale_data(X_test)

        X_train_c = np.concatenate((X_train, X_test), axis=0)
        y_train_c = np.concatenate((y_train, y_test), axis=0)

        print('Training model...')
        pipeline = self.get_model()
        pipeline.fit(X_train_c, y_train_c, model__verbose=10)

        print('Saving model...')
        model_name = self.__save_model(pipeline)

        y_pred = pipeline.predict(X_train_c)
        model_metrics = compute_evaluation_metrics(y_train_c,
                                                   y_pred, model_name)

        print('Saving metadata...')
        self.__save_metadata(model_name, model_metrics.to_json())

        print('Training model DONE SUCCESSFULLY')

    def __save_metadata(self, model_name, model_metrics):
        self.metadata = {
            'etl_version': config.etl_version,
            'train_version': config.version,
            'output_model': model_name,
            'metrics': model_metrics,
            'etl_metadata': etl_metadata_serialized
        }
        with open(f'train/metadata/metadata_v{config.version}.json', "w") as f:
            json.dump(self.metadata, f)

    def __save_model(self, model):
        version = config.version
        type = config.model.type
        identifier = config.model.identifier
        name = f'{type}_{identifier}_v{version}.dat'
        pickle.dump(model, open(f'models/{name}', "wb"))
        return name

    def get_model(self):

        model = xgb.XGBRegressor(
            n_estimators=27,
            max_depth=4,
            min_child_weight=1,
            eta=0.1,
            reg_lambda=0,
            objective='reg:squarederror',
            random_state=42)

        return Pipeline([
            ('model', model)
        ])