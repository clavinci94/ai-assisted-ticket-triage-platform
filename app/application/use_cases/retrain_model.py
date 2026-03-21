from pathlib import Path

from app.infrastructure.ai.train_model import train_model


class RetrainModelUseCase:
    def execute(self) -> Path:
        return train_model()
