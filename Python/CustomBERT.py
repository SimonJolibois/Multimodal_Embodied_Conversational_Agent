from transformers import BertForSequenceClassification, BertModel
import torch.nn as nn


class CustomBert(nn.Module):
    def __init__(self, pretrained_model_name, num_labels):
        super(CustomBert, self).__init__()
        self.num_labels = num_labels

        # Load the pre-trained BERT model
        self.bert = BertForSequenceClassification.from_pretrained(
            pretrained_model_name,
            num_labels=num_labels,
            output_attentions=True,
            output_hidden_states=True
        )
        self.bert = BertModel.from_pretrained(pretrained_model_name)

        # Custom dense layer for multi-label classification
        self.classifier = nn.Sequential(
            nn.Dropout(0.1),
            nn.Linear(768, num_labels),
            nn.Sigmoid()
        )

    def forward(self, input_ids, attention_mask=None, token_type_ids=None, labels=None):
        outputs = self.bert(input_ids,
                            attention_mask=attention_mask,
                            token_type_ids=token_type_ids)

        sequence_output = outputs[1]
        logits = self.classifier(sequence_output)
        return logits


# Initialize your custom model
# modelE = CustomBert("name", len(labels_to_use))

