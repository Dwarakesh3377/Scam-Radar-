#!/usr/bin/env python3
"""
Train BERT Model for Scam Detection (Pure PyTorch Loop)
=======================================================
Fine-tunes a BERT model on the scam/legitimate/suspicious datasets.
Re-written to avoid 'accelerate' dependency issues with Trainer.
"""

import os
import sys
import torch  # Move torch to top to avoid DLL conflicts
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from transformers import BertTokenizer, BertForSequenceClassification
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW

import warnings
warnings.filterwarnings('ignore')

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATASET_DIR = ROOT_DIR / 'dataset'
MODELS_DIR = ROOT_DIR / 'ml_models' / 'bert_model'

# Dataset files
DATASETS = {
    'scam_jobs': 'scam_jobs_final 2.0.xlsx',
    'scam_internships': 'scam_internships_final 2.0.xlsx',
    'legitimate_jobs': 'legitimate_jobs_final 2.0.xlsx',
    'legitimate_internships': 'legitimate_internships_final 2.0.xlsx',
    'suspicious_jobs': 'suspicious_jobs_final 2.0.xlsx',
    'suspicious_internships': 'suspicious_internships_final 2.0.xlsx',
}

def load_datasets():
    """Load all datasets and combine them."""
    print("Loading datasets...")
    
    all_texts = []
    all_labels = []
    
    for dataset_key, filename in DATASETS.items():
        filepath = DATASET_DIR / filename
        
        if not filepath.exists():
            print(f"  Warning: {filename} not found, skipping...")
            continue
        
        try:
            df = pd.read_excel(filepath)
            
            # Determine category and text column
            if 'scam' in dataset_key:
                label = 2  # Scam
                text_col = 'scam_job_description'
            elif 'legitimate' in dataset_key:
                label = 0  # Legitimate
                text_col = 'job_description'
            else:  
                label = 1  # Suspicious
                text_col = 'partial_job_description'
            
            # Extract texts
            if text_col in df.columns:
                texts = df[text_col].fillna('').astype(str).tolist()
                # Filter out empty texts
                texts = [t for t in texts if len(t) > 10]
                
                all_texts.extend(texts)
                all_labels.extend([label] * len(texts))
                print(f"  Loaded {len(texts)} samples from {filename} (Label: {label})")
            else:
                print(f"  Warning: Column '{text_col}' not found in {filename}")
                
        except Exception as e:
            print(f"  Error loading {filename}: {str(e)}")
    
    return all_texts, all_labels

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

def train():
    print("=" * 60)
    print("BERT MODEL TRAINING (Pure PyTorch)")
    print("=" * 60)
    
    # 1. Load Data
    texts, labels = load_datasets()
    
    if not texts:
        print("No data loaded. Exiting.")
        return

    # 2. Split Data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    print(f"\nTraining samples: {len(train_texts)}")
    print(f"Validation samples: {len(val_texts)}")
    
    # 3. Tokenizer
    print("\nTokenizing data...")
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=512)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=512)
    
    train_dataset = ScamDataset(train_encodings, train_labels)
    val_dataset = ScamDataset(val_encodings, val_labels)
    
    train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True) # Small batch for CPU
    val_loader = DataLoader(val_dataset, batch_size=8)
    
    # 4. Model
    print("\nInitializing BERT model...")
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print(f"Using device: {device}")
    
    model = BertForSequenceClassification.from_pretrained(
        'bert-base-uncased', 
        num_labels=3,
        id2label={0: 'LEGITIMATE', 1: 'SUSPICIOUS', 2: 'SCAM'},
        label2id={'LEGITIMATE': 0, 'SUSPICIOUS': 1, 'SCAM': 2}
    )
    model.to(device)
    
    # 5. Training Loop
    optimizer = AdamW(model.parameters(), lr=5e-5)
    epochs = 3
    
    print("\nStarting training...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        print(f"\nEpoch {epoch+1}/{epochs}")
        
        for step, batch in enumerate(train_loader):
            optimizer.zero_grad()
            
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            if (step + 1) % 10 == 0:
                print(f"  Step {step+1}/{len(train_loader)} - Loss: {loss.item():.4f}", end='\r')
            
            if (step + 1) % 50 == 0:
                avg_loss = total_loss / 50 # Corrected to divide by 50 steps
                print(f"\n  Step {step+1}/{len(train_loader)} - Loss: {avg_loss:.4f}")
                total_loss = 0.0 # Reset total_loss for the next 50 steps
                
                # Intermediate save
                model.save_pretrained(MODELS_DIR)
                tokenizer.save_pretrained(MODELS_DIR)
                print(f"  ✓ Intermediate save at step {step+1}")
        
        # Calculate average training loss for the remaining steps in the epoch
        # if total_loss is not 0 (i.e., len(train_loader) is not a multiple of 50)
        if total_loss > 0:
            remaining_steps = len(train_loader) % 50
            if remaining_steps == 0: # If len(train_loader) is a multiple of 50, total_loss would be 0
                remaining_steps = 50 # This case should not happen if total_loss > 0
            avg_train_loss = total_loss / remaining_steps
            print(f"\n  Average Training Loss (remaining steps): {avg_train_loss:.4f}")
        else:
            # If total_loss is 0, it means the last 50-step block was just processed
            # and its average was already printed.
            print(f"\n  Average Training Loss: (already reported in last 50-step block)")
        
        # Validation
        model.eval()
        val_loss = 0
        preds = []
        true_labels = []
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
                val_loss += outputs.loss.item()
                
                predictions = torch.argmax(outputs.logits, dim=-1)
                preds.extend(predictions.cpu().numpy())
                true_labels.extend(labels.cpu().numpy())
        
        avg_val_loss = val_loss / len(val_loader)
        accuracy = accuracy_score(true_labels, preds)
        print(f"  Validation Loss: {avg_val_loss:.4f}")
        print(f"  Validation Accuracy: {accuracy:.4f}")
        
        # Save checkpoint
        checkpoint_dir = MODELS_DIR / f'checkpoint-{epoch}'
        os.makedirs(checkpoint_dir, exist_ok=True)
        model.save_pretrained(checkpoint_dir)
        tokenizer.save_pretrained(checkpoint_dir)

    # 6. Save Final Model
    print(f"\nSaving final model to {MODELS_DIR}...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    model.save_pretrained(MODELS_DIR)
    tokenizer.save_pretrained(MODELS_DIR)
    
    print("\n" + "=" * 60)
    print("BERT TRAINING COMPLETE!")
    print("=" * 60)

if __name__ == '__main__':
    train()
