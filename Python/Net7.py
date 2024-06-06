import torch
import torch.nn as nn
import torch.nn.functional as F


class Net7(nn.Module):
    """Multi-Layer Perceptron with 7 outputs"""

    def __init__(self):
        __slot__ = "fc1", "fc2", "fc3", "fc4"

        super().__init__()
        self.fc1 = nn.Linear(17, 15)
        self.fc2 = nn.Linear(15, 12)
        self.fc3 = nn.Linear(12, 10)
        self.fc4 = nn.Linear(10, 7)

    def forward(self, x):
        x = torch.flatten(x).float()  # flatten all dimensions except batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return x
