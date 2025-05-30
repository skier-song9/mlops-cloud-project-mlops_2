from enum import Enum

from src.model.model_cards import LGBMRegressorCard, CatBoostRegressorCard

class CustomEnum(Enum):
    @classmethod
    def names(cls):
        return [member.name for member in list(cls)]

    @classmethod
    def validation(cls, name: str):
        names = [name.lower() for name in cls.names()]
        if name.lower() in names:
            return True
        else:
            raise ValueError(f"Invalid argument. Must be one of {cls.names()}")


class Models(CustomEnum):
    LGBMREGRESSOR = LGBMRegressorCard  # python main.py train --model_name movie_predictor
    CATBOOSTREGRESSOR = CatBoostRegressorCard
