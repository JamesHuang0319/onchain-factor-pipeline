from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from src.models.base import BaseModel


class _CNNLSTMNet(nn.Module):
    def __init__(
        self,
        input_dim: int,
        conv_channels: int,
        kernel_size: int,
        hidden_dim: int,
        num_layers: int,
        dropout: float,
        task: str,
    ) -> None:
        super().__init__()
        pad = kernel_size // 2
        self.conv = nn.Sequential(
            nn.Conv1d(input_dim, conv_channels, kernel_size=kernel_size, padding=pad),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        lstm_dropout = dropout if num_layers > 1 else 0.0
        self.lstm = nn.LSTM(
            input_size=conv_channels,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
        )
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_dim, 1)
        self.task = task

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.transpose(1, 2)
        x = self.conv(x)
        x = x.transpose(1, 2)
        out, _ = self.lstm(x)
        last = self.dropout(out[:, -1, :])
        logits = self.head(last).squeeze(-1)
        if self.task == "classification":
            return torch.sigmoid(logits)
        return logits


class CNNLSTMModel(BaseModel):
    name = "cnn_lstm"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.task = str(self.config.get("task", "regression")).lower()
        self.timesteps = int(self.config.get("timesteps", 10))
        self.conv_channels = int(self.config.get("conv_channels", 32))
        self.kernel_size = int(self.config.get("kernel_size", 3))
        self.hidden_dim = int(self.config.get("hidden_dim", 64))
        self.num_layers = int(self.config.get("num_layers", 1))
        self.dropout = float(self.config.get("dropout", 0.1))
        self.batch_size = int(self.config.get("batch_size", 64))
        self.max_epochs = int(self.config.get("max_epochs", 40))
        self.patience = int(self.config.get("early_stopping_patience", 8))
        self.learning_rate = float(self.config.get("learning_rate", 1e-3))
        self.weight_decay = float(self.config.get("weight_decay", 0.0))
        self.device = torch.device("cpu")
        self.scaler = StandardScaler()
        self.feature_cols: list[str] = []
        self._history_tail: np.ndarray | None = None
        self._input_dim: int | None = None

    def _to_2d(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        arr = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
        if arr.ndim != 2:
            raise ValueError(f"CNNLSTMModel expects 2D input, got shape={arr.shape}")
        return arr.astype(np.float32, copy=False)

    def _build_sequences(
        self,
        X_scaled: np.ndarray,
        y: np.ndarray | None = None,
        prefix: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        if prefix is not None and len(prefix):
            full_X = np.vstack([prefix, X_scaled])
        else:
            full_X = X_scaled
        seqs: list[np.ndarray] = []
        targets: list[float] = []
        start = 0 if prefix is None else len(prefix)
        for i in range(start, len(full_X)):
            left = max(0, i - self.timesteps + 1)
            seq = full_X[left:i + 1]
            if len(seq) < self.timesteps:
                pad = np.repeat(seq[:1], self.timesteps - len(seq), axis=0)
                seq = np.vstack([pad, seq])
            seqs.append(seq)
            if y is not None:
                targets.append(float(y[i - start]))
        seq_arr = np.asarray(seqs, dtype=np.float32)
        if y is None:
            return seq_arr, None
        return seq_arr, np.asarray(targets, dtype=np.float32)

    def _fit_loader(self, loader: DataLoader, criterion, optimizer) -> float:
        self._model.train()
        losses = []
        for xb, yb in loader:
            xb = xb.to(self.device)
            yb = yb.to(self.device)
            optimizer.zero_grad()
            pred = self._model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))
        return float(np.mean(losses)) if losses else float("inf")

    def _eval_loader(self, loader: DataLoader, criterion) -> float:
        self._model.eval()
        losses = []
        with torch.no_grad():
            for xb, yb in loader:
                xb = xb.to(self.device)
                yb = yb.to(self.device)
                pred = self._model(xb)
                loss = criterion(pred, yb)
                losses.append(float(loss.detach().cpu().item()))
        return float(np.mean(losses)) if losses else float("inf")

    def fit(
        self,
        X_train: pd.DataFrame | np.ndarray,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame | np.ndarray | None = None,
        y_val: pd.Series | np.ndarray | None = None,
    ) -> "CNNLSTMModel":
        torch.manual_seed(int(self.config.get("random_state", 42)))
        np.random.seed(int(self.config.get("random_state", 42)))

        X_train_arr = self._to_2d(X_train)
        y_train_arr = np.asarray(y_train, dtype=np.float32)
        self.feature_cols = list(X_train.columns) if isinstance(X_train, pd.DataFrame) else []
        X_train_scaled = self.scaler.fit_transform(X_train_arr).astype(np.float32)
        self._input_dim = X_train_scaled.shape[1]
        train_seq, train_y = self._build_sequences(X_train_scaled, y_train_arr)

        prefix = X_train_scaled[-(self.timesteps - 1):] if self.timesteps > 1 else None
        val_seq = val_y = None
        if X_val is not None and y_val is not None and len(X_val):
            X_val_scaled = self.scaler.transform(self._to_2d(X_val)).astype(np.float32)
            val_seq, val_y = self._build_sequences(
                X_val_scaled,
                np.asarray(y_val, dtype=np.float32),
                prefix=prefix,
            )
            history_source = np.vstack([X_train_scaled, X_val_scaled])
        else:
            history_source = X_train_scaled
        self._history_tail = history_source[-(self.timesteps - 1):] if self.timesteps > 1 else None

        self._model = _CNNLSTMNet(
            input_dim=self._input_dim,
            conv_channels=self.conv_channels,
            kernel_size=self.kernel_size,
            hidden_dim=self.hidden_dim,
            num_layers=self.num_layers,
            dropout=self.dropout,
            task=self.task,
        ).to(self.device)
        criterion = nn.BCELoss() if self.task == "classification" else nn.MSELoss()
        optimizer = torch.optim.Adam(
            self._model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )

        train_loader = DataLoader(
            TensorDataset(torch.from_numpy(train_seq), torch.from_numpy(train_y)),
            batch_size=self.batch_size,
            shuffle=False,
        )
        val_loader = None
        if val_seq is not None and val_y is not None:
            val_loader = DataLoader(
                TensorDataset(torch.from_numpy(val_seq), torch.from_numpy(val_y)),
                batch_size=self.batch_size,
                shuffle=False,
            )

        best_state = None
        best_loss = float("inf")
        stale = 0
        for _ in range(self.max_epochs):
            self._fit_loader(train_loader, criterion, optimizer)
            current = self._eval_loader(val_loader, criterion) if val_loader is not None else self._eval_loader(train_loader, criterion)
            if current < best_loss:
                best_loss = current
                best_state = {k: v.detach().cpu().clone() for k, v in self._model.state_dict().items()}
                stale = 0
            else:
                stale += 1
                if stale >= self.patience:
                    break

        if best_state is not None:
            self._model.load_state_dict(best_state)
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        if self._model is None or self._input_dim is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        X_scaled = self.scaler.transform(self._to_2d(X)).astype(np.float32)
        seqs, _ = self._build_sequences(X_scaled, prefix=self._history_tail)
        self._model.eval()
        with torch.no_grad():
            pred = self._model(torch.from_numpy(seqs).to(self.device)).detach().cpu().numpy()
        return pred.astype(float)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "state_dict": self._model.state_dict(),
                    "config": self.config,
                    "scaler_mean": self.scaler.mean_,
                    "scaler_scale": self.scaler.scale_,
                    "feature_cols": self.feature_cols,
                    "history_tail": self._history_tail,
                    "input_dim": self._input_dim,
                },
                f,
            )

    @classmethod
    def load(cls, path: str | Path) -> "CNNLSTMModel":
        with open(path, "rb") as f:
            payload = pickle.load(f)
        obj = cls(config=payload["config"])
        obj.feature_cols = payload.get("feature_cols", [])
        obj._history_tail = payload.get("history_tail")
        obj._input_dim = int(payload["input_dim"])
        obj.scaler.mean_ = np.asarray(payload["scaler_mean"], dtype=np.float64)
        obj.scaler.scale_ = np.asarray(payload["scaler_scale"], dtype=np.float64)
        obj.scaler.var_ = obj.scaler.scale_ ** 2
        obj.scaler.n_features_in_ = obj._input_dim
        obj._model = _CNNLSTMNet(
            input_dim=obj._input_dim,
            conv_channels=int(obj.config.get("conv_channels", 32)),
            kernel_size=int(obj.config.get("kernel_size", 3)),
            hidden_dim=int(obj.config.get("hidden_dim", 64)),
            num_layers=int(obj.config.get("num_layers", 1)),
            dropout=float(obj.config.get("dropout", 0.1)),
            task=str(obj.config.get("task", "regression")).lower(),
        ).to(obj.device)
        obj._model.load_state_dict(payload["state_dict"])
        obj._model.eval()
        return obj
