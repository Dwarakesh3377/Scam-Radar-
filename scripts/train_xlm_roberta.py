import os
import torch
import pandas as pd
import numpy as np
from transformers import (
    XLMRobertaTokenizer, 
    XLMRobertaForSequenceClassification, 
    Trainer, 
    TrainingArguments,
    DataCollatorWithPadding
)
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

class ScamDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='weighted')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def prepare_text(row):
    """Concatenate relevant fields for richer context."""
    def get_val(key):
        val = row.get(key, '')
        if pd.isna(val):
            return ''
        return str(val).strip()

    title = get_val('job_title')
    company = get_val('company_name')
    desc = get_val('job_description')
    reqs = get_val('job_requirements')
    email = get_val('contact_email')
    website = get_val('company_website')
    
    # Combined text with separators
    text = f"Job: {title} | Company: {company} | Description: {desc} | Requirements: {reqs} | Contact: {email} | Website: {website}"
    return text

def train_xlm_roberta():
    # Dataset paths
    base_path = "d:/scam-risk-detection2/dataset"
    files = {
        "legitimate": os.path.join(base_path, "Multilingual_legitimate_dataset 2.0.xlsx"),
        "scam": os.path.join(base_path, "Multilingual_scam_dataset 2.0.xlsx"),
        "suspicious": os.path.join(base_path, "Multilingual_suspicious_dataset 2.0.xlsx")
    }

    dfs = []
    for label, path in files.items():
        if os.path.exists(path):
            print(f"Loading {label} dataset from {path}...")
            df = pd.read_excel(path)
            # Standardize labels just in case
            df['label'] = label
            dfs.append(df)
        else:
            print(f"Warning: {path} not found!")

    if not dfs:
        print("No datasets found!")
        return

    full_df = pd.concat(dfs, ignore_index=True)
    print(f"Total records loaded: {len(full_df)}")

    # Preprocess text
    print("Preparing text context...")
    full_df['combined_text'] = full_df.apply(prepare_text, axis=1)
    
    # Map labels to integers
    label_map = {"legitimate": 0, "suspicious": 1, "scam": 2}
    full_df['label_int'] = full_df['label'].map(label_map)
    
    # User requested to use full dataset (no sampling)
    print("Using full dataset for training (9000 records).")

    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        full_df['combined_text'].tolist(), full_df['label_int'].tolist(), test_size=0.1, random_state=42
    )

    # Initialize Tokenizer and Model
    model_name = "xlm-roberta-base"
    print(f"Initializing {model_name}...")
    tokenizer = XLMRobertaTokenizer.from_pretrained(model_name)
    model = XLMRobertaForSequenceClassification.from_pretrained(model_name, num_labels=3)

    # Tokenize
    print("Tokenizing data...")
    # Reduced max_length to 64 to significantly speed up CPU training (was 128)
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=64) 
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=64)

    # Create datasets
    train_dataset = ScamDataset(train_encodings, train_labels)
    val_dataset = ScamDataset(val_encodings, val_labels)

    # Training Arguments
    output_dir = "d:/scam-risk-detection2/ml_models/xlm_roberta_multilingual"
    os.makedirs(output_dir, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=1, 
        per_device_train_batch_size=2, # Increased for better CPU throughput
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=16, # Effective batch size = 32 (2 * 16)
        warmup_steps=50,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=5,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=50,
        save_total_limit=1,
        fp16=False,
        dataloader_num_workers=0,
    )

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer)
    )

    # Train (Resuming from last checkpoint if it exists)
    print("Starting/Resuming training (this may take a while on CPU)...")
    checkpoint_dir = "d:/scam-risk-detection2/ml_models/xlm_roberta_multilingual"
    latest_checkpoint = None
    
    # Check for existing checkpoints
    if os.path.exists(checkpoint_dir):
        checkpoints = [os.path.join(checkpoint_dir, d) for d in os.listdir(checkpoint_dir) if d.startswith("checkpoint-")]
        if checkpoints:
            latest_checkpoint = max(checkpoints, key=os.path.getmtime)
            print(f"--- Detected existing checkpoint: {latest_checkpoint}. Resuming... ---")

    trainer.train(resume_from_checkpoint=latest_checkpoint)

    # Save model and tokenizer
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")

if __name__ == "__main__":
    train_xlm_roberta()
