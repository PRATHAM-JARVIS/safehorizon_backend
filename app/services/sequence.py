import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from typing import Any, Dict, List, Optional, Tuple
from sklearn.preprocessing import MinMaxScaler
import joblib
from ..models.model_registry import save_model, load_model
from ..config import get_settings

settings = get_settings()


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2):
        super(LSTMAutoencoder, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Encoder
        self.encoder_lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        
        # Decoder
        self.decoder_lstm = nn.LSTM(hidden_size, hidden_size, num_layers, batch_first=True)
        self.decoder_output = nn.Linear(hidden_size, input_size)
        
    def forward(self, x):
        # Encoder
        encoded, (hidden, cell) = self.encoder_lstm(x)
        
        # Use the last hidden state as the encoded representation
        encoded_last = encoded[:, -1:, :]  # Keep sequence dimension
        
        # Decoder - repeat the encoded state for the sequence length
        seq_len = x.size(1)
        encoded_repeated = encoded_last.repeat(1, seq_len, 1)
        
        decoded, _ = self.decoder_lstm(encoded_repeated, (hidden, cell))
        output = self.decoder_output(decoded)
        
        return output


class SequenceAnomalyDetector:
    def __init__(self, sequence_length: int = 10):
        self.sequence_length = sequence_length
        self.model: Optional[LSTMAutoencoder] = None
        self.scaler: Optional[MinMaxScaler] = None
        self.feature_columns = ['latitude', 'longitude', 'speed', 'hour', 'day_of_week']
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def _load_models(self):
        """Load trained models from disk"""
        try:
            # Load PyTorch model
            model_path = f"{settings.models_dir}/lstm_autoencoder.pth"
            if torch.cuda.is_available():
                checkpoint = torch.load(model_path)
            else:
                checkpoint = torch.load(model_path, map_location='cpu')
            
            self.model = LSTMAutoencoder(
                input_size=len(self.feature_columns),
                hidden_size=checkpoint['hidden_size'],
                num_layers=checkpoint['num_layers']
            )
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            # Load scaler
            self.scaler = load_model("sequence_scaler")
        except (FileNotFoundError, KeyError):
            # Models not trained yet
            pass
    
    def _prepare_sequences(self, locations_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare location data as sequences for LSTM"""
        if len(locations_data) < self.sequence_length:
            return np.array([]), np.array([])
        
        df = pd.DataFrame(locations_data)
        
        # Convert timestamp to datetime features
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Fill missing values
        for col in self.feature_columns:
            if col in df.columns:
                df[col].fillna(df[col].mean() if col != 'day_of_week' else 0, inplace=True)
            else:
                df[col] = 0  # Default value
        
        # Select and order features
        features = df[self.feature_columns].values
        
        # Create sequences
        sequences = []
        for i in range(len(features) - self.sequence_length + 1):
            sequences.append(features[i:i + self.sequence_length])
        
        return np.array(sequences), features
    
    async def train(self, locations_data: List[Dict[str, Any]], epochs: int = 50) -> Dict[str, Any]:
        """Train the LSTM autoencoder"""
        if len(locations_data) < self.sequence_length * 5:
            return {
                "status": "insufficient_data", 
                "message": f"Need at least {self.sequence_length * 5} location points"
            }
        
        # Prepare sequences
        sequences, raw_features = self._prepare_sequences(locations_data)
        
        if len(sequences) == 0:
            return {"status": "error", "message": "No sequences generated"}
        
        # Scale features
        self.scaler = MinMaxScaler()
        # Fit scaler on all raw features, then transform sequences
        self.scaler.fit(raw_features)
        
        # Scale sequences
        scaled_sequences = np.zeros_like(sequences)
        for i, seq in enumerate(sequences):
            scaled_sequences[i] = self.scaler.transform(seq)
        
        # Convert to PyTorch tensors
        tensor_data = torch.FloatTensor(scaled_sequences).to(self.device)
        dataset = TensorDataset(tensor_data, tensor_data)  # Autoencoder: input = target
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        # Initialize model
        self.model = LSTMAutoencoder(
            input_size=len(self.feature_columns),
            hidden_size=64,
            num_layers=2
        ).to(self.device)
        
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
        # Training loop
        self.model.train()
        total_loss = 0
        
        for epoch in range(epochs):
            epoch_loss = 0
            for batch_data, batch_target in dataloader:
                optimizer.zero_grad()
                
                output = self.model(batch_data)
                loss = criterion(output, batch_target)
                
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Loss: {epoch_loss/len(dataloader):.6f}")
            
            total_loss += epoch_loss
        
        # Save models
        model_path = f"{settings.models_dir}/lstm_autoencoder.pth"
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'hidden_size': 64,
            'num_layers': 2,
            'input_size': len(self.feature_columns)
        }, model_path)
        
        save_model(self.scaler, "sequence_scaler")
        
        return {
            "status": "success",
            "message": f"Model trained on {len(sequences)} sequences",
            "epochs": epochs,
            "final_loss": total_loss / (epochs * len(dataloader))
        }
    
    async def score_sequence(self, points: List[Dict[str, Any]]) -> float:
        """Score a sequence of points for anomaly"""
        if not self.model or not self.scaler:
            self._load_models()
        
        if not self.model or not self.scaler:
            return 0.0  # No model trained yet
        
        if len(points) < self.sequence_length:
            return 0.0  # Not enough points for sequence
        
        # Prepare the sequence
        sequences, _ = self._prepare_sequences(points)
        
        if len(sequences) == 0:
            return 0.0
        
        # Use the last sequence
        last_sequence = sequences[-1]
        scaled_sequence = self.scaler.transform(last_sequence)
        
        # Convert to tensor
        tensor_input = torch.FloatTensor(scaled_sequence).unsqueeze(0).to(self.device)
        
        # Get reconstruction
        self.model.eval()
        with torch.no_grad():
            reconstruction = self.model(tensor_input)
        
        # Calculate reconstruction error
        mse = nn.MSELoss()(reconstruction, tensor_input).item()
        
        # Normalize score (higher MSE = more anomalous)
        # Typical MSE values are small, so we scale appropriately
        normalized_score = min(1.0, mse * 100)  # Scale factor may need tuning
        
        return float(normalized_score)


# Global instance
sequence_detector = SequenceAnomalyDetector()


async def score_sequence(points: List[Dict[str, Any]]) -> float:
    """Score a sequence of points for anomaly detection"""
    return await sequence_detector.score_sequence(points)


async def train_sequence_model(locations_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Train the sequence anomaly detection model"""
    return await sequence_detector.train(locations_data)
