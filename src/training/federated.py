"""
Federated Learning Implementation (FedAvg, FedProx)
"""


class FederatedTrainer:
    """
    Simulates federated learning across multiple stations.
    """

    def __init__(self, stations: list, model_class, data_splits: list):
        self.stations = stations
        self.model_class = model_class
        self.data_splits = data_splits
        # TODO: Initialize models, optimizers per station

    def run_round(self):
        # TODO: Local training, aggregation, DP-SGD
        pass

    def fit(self, rounds: int):
        for r in range(rounds):
            self.run_round()
            # TODO: Log metrics, communication cost
