import csv
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from typing import Dict, List, Any, Optional
import random

class DataCollector:
    """Collect and manage scam detection data"""
    
    def __init__(self, data_dir='dataset'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # File paths
        self.scam_file = os.path.join(data_dir, 'scam_data.csv')
        self.legit_file = os.path.join(data_dir, 'legit_data.csv')
        self.reviews_file = os.path.join(data_dir, 'negative_reviews.csv')
        self.metadata_file = os.path.join(data_dir, 'metadata.json')
        
        # Initialize data structures
        self.scam_data = []
        self.legit_data = []
        self.reviews_data = []
        self.metadata = {
            'total_samples': 0,
            'scam_count': 0,
            'legit_count': 0,
            'reviews_count': 0,
            'last_updated': None,
            'languages': set(),
            'categories': set()
        }
    
    def load_data(self):
        """Load existing data from files"""
        try:
            # Load scam data
            if os.path.exists(self.scam_file):
                self.scam_data = self._load_csv(self.scam_file)
                self.metadata['scam_count'] = len(self.scam_data)
            
            # Load legit data
            if os.path.exists(self.legit_file):
                self.legit_data = self._load_csv(self.legit_file)
                self.metadata['legit_count'] = len(self.legit_data)
            
            # Load reviews data
            if os.path.exists(self.reviews_file):
                self.reviews_data = self._load_csv(self.reviews_file)
                self.metadata['reviews_count'] = len(self.reviews_data)
            
            # Load metadata
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    loaded_metadata = json.load(f)
                    # Convert sets from lists
                    if 'languages' in loaded_metadata:
                        loaded_metadata['languages'] = set(loaded_metadata['languages'])
                    if 'categories' in loaded_metadata:
                        loaded_metadata['categories'] = set(loaded_metadata['categories'])
                    self.metadata.update(loaded_metadata)
            
            self.metadata['total_samples'] = self.metadata['scam_count'] + self.metadata['legit_count']
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
    
    def save_data(self):
        """Save data to files"""
        try:
            # Save scam data
            if self.scam_data:
                self._save_csv(self.scam_file, self.scam_data)
            
            # Save legit data
            if self.legit_data:
                self._save_csv(self.legit_file, self.legit_data)
            
            # Save reviews data
            if self.reviews_data:
                self._save_csv(self.reviews_file, self.reviews_data)
            
            # Save metadata (convert sets to lists)
            metadata_to_save = self.metadata.copy()
            metadata_to_save['languages'] = list(metadata_to_save.get('languages', []))
            metadata_to_save['categories'] = list(metadata_to_save.get('categories', []))
            metadata_to_save['last_updated'] = datetime.utcnow().isoformat()
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_to_save, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"Error saving data: {str(e)}")
    
    def add_scam_sample(self, text: str, metadata: Dict = None, language: str = 'en'):
        """Add a scam sample to dataset"""
        sample = {
            'id': self._generate_id('scam'),
            'text': text,
            'label': 1,
            'language': language,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat(),
            'source': 'user_submission',
            'verified': False
        }
        
        self.scam_data.append(sample)
        self.metadata['scam_count'] += 1
        self.metadata['total_samples'] += 1
        self.metadata['languages'].add(language)
        
        if metadata and 'category' in metadata:
            self.metadata['categories'].add(metadata['category'])
    
    def add_legit_sample(self, text: str, metadata: Dict = None, language: str = 'en'):
        """Add a legitimate sample to dataset"""
        sample = {
            'id': self._generate_id('legit'),
            'text': text,
            'label': 0,
            'language': language,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat(),
            'source': 'user_submission',
            'verified': True  # Legitimate samples are usually verified
        }
        
        self.legit_data.append(sample)
        self.metadata['legit_count'] += 1
        self.metadata['total_samples'] += 1
        self.metadata['languages'].add(language)
        
        if metadata and 'category' in metadata:
            self.metadata['categories'].add(metadata['category'])
    
    def add_review(self, review_data: Dict):
        """Add a negative review to dataset"""
        review = {
            'id': self._generate_id('review'),
            'company_name': review_data.get('company_name', ''),
            'company_domain': review_data.get('company_domain', ''),
            'job_title': review_data.get('job_title', ''),
            'rating': review_data.get('rating', 1),
            'comment': review_data.get('comment', ''),
            'category': review_data.get('category', 'job_scam'),
            'evidence': json.dumps(review_data.get('evidence', {})),
            'location': review_data.get('location', ''),
            'financial_loss': review_data.get('financial_loss', 0),
            'tags': ','.join(review_data.get('tags', [])),
            'created_at': datetime.utcnow().isoformat(),
            'username': review_data.get('username', 'Anonymous'),
            'helpful_count': 0,
            'verified': False
        }
        
        self.reviews_data.append(review)
        self.metadata['reviews_count'] += 1
        self.metadata['categories'].add(review['category'])
    
    def get_training_data(self, balance: bool = True, test_size: float = 0.2):
        """Get data for training in a balanced way"""
        # Combine and shuffle data
        all_data = self.scam_data + self.legit_data
        
        if not all_data:
            return [], [], [], []
        
        # Balance dataset if requested
        if balance:
            scam_count = len(self.scam_data)
            legit_count = len(self.legit_data)
            
            if scam_count > legit_count:
                # Undersample scam data
                sampled_scam = random.sample(self.scam_data, legit_count)
                all_data = sampled_scam + self.legit_data
            elif legit_count > scam_count:
                # Undersample legit data
                sampled_legit = random.sample(self.legit_data, scam_count)
                all_data = self.scam_data + sampled_legit
        
        # Shuffle data
        random.shuffle(all_data)
        
        # Split features and labels
        texts = [item['text'] for item in all_data]
        labels = [item['label'] for item in all_data]
        
        # Split into train/test
        split_idx = int(len(texts) * (1 - test_size))
        
        X_train = texts[:split_idx]
        y_train = labels[:split_idx]
        X_test = texts[split_idx:]
        y_test = labels[split_idx:]
        
        return X_train, y_train, X_test, y_test
    
    def get_reviews_by_company(self, company_name: str, limit: int = 10) -> List[Dict]:
        """Get reviews for a specific company"""
        company_reviews = []
        
        for review in self.reviews_data:
            if review['company_name'].lower() == company_name.lower():
                # Parse evidence JSON
                try:
                    review['evidence'] = json.loads(review['evidence'])
                except:
                    review['evidence'] = {}
                
                # Convert tags string to list
                review['tags'] = review['tags'].split(',') if review['tags'] else []
                
                company_reviews.append(review)
        
        # Sort by helpful count and date
        company_reviews.sort(key=lambda x: (x['helpful_count'], x['created_at']), reverse=True)
        
        return company_reviews[:limit]
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics"""
        stats = self.metadata.copy()
        
        # Convert sets to lists for JSON serialization
        stats['languages'] = list(stats.get('languages', []))
        stats['categories'] = list(stats.get('categories', []))
        
        # Calculate additional statistics
        stats['scam_ratio'] = round(stats['scam_count'] / max(stats['total_samples'], 1), 2)
        stats['legit_ratio'] = round(stats['legit_count'] / max(stats['total_samples'], 1), 2)
        
        # Language distribution
        stats['language_distribution'] = {}
        for data in [self.scam_data, self.legit_data]:
            for sample in data:
                lang = sample.get('language', 'unknown')
                stats['language_distribution'][lang] = stats['language_distribution'].get(lang, 0) + 1
        
        # Category distribution for reviews
        stats['review_category_distribution'] = {}
        for review in self.reviews_data:
            category = review.get('category', 'unknown')
            stats['review_category_distribution'][category] = stats['review_category_distribution'].get(category, 0) + 1
        
        return stats
    
    def generate_sample_data(self, num_samples: int = 1000):
        """Generate sample data for testing"""
        print(f"Generating {num_samples} sample data points...")
        
        # Scam examples
        scam_examples = [
            "URGENT HIRING! Work from home and earn $5000/month. No experience needed! Send $50 for training materials.",
            "Immediate Job Opportunity: Data entry jobs available. Earn $1000 weekly. Send your bank details to start.",
            "Government Job Guaranteed! Pay $200 for registration and get placed in top companies. Limited seats!",
            "Earn $300 daily from home! Just share your personal information and payment of $100 for startup kit.",
            "Get Rich Quick! Invest $500 and earn 10x returns. Bitcoin payments accepted. Contact us now!",
            "Work from home, earn money online. No skills required. Immediate payment. Send your details.",
            "Exclusive job offer for you! High salary, flexible hours. Pay small fee for processing.",
            "You've been selected for a special job position. Confidential offer. Reply immediately.",
            "Earn money by completing simple tasks. No interview. Start earning today!",
            "Part-time jobs with high income. Work anywhere. Send your CV and payment for verification."
        ]
        
        # Legitimate examples
        legit_examples = [
            "We are hiring Software Engineers at TechCorp. Requirements: 3+ years experience, B.Tech degree.",
            "Marketing Intern position available at StartupXYZ. Stipend: $1000/month. Duration: 6 months.",
            "Customer Service Representative needed. Full-time with benefits. Good communication skills required.",
            "Content Writers wanted for our blog. Work from office. Competitive salary based on experience.",
            "Data Analyst position. Remote work option. Requirements: SQL, Python, Statistics knowledge.",
            "Looking for experienced Project Manager. Must have PMP certification and 5+ years experience.",
            "Sales Executive position. Target-based salary with attractive commissions. MBA preferred.",
            "Web Developer needed for e-commerce platform. Skills: React, Node.js, MongoDB.",
            "Graphic Designer position. Create marketing materials. Portfolio required.",
            "Accountant needed for medium-sized firm. CPA certification and 3+ years experience required."
        ]
        
        # Generate scam samples
        for i in range(num_samples // 2):
            text = random.choice(scam_examples)
            # Add some variation
            text = text.replace('$5000', f'${random.randint(3000, 8000)}')
            text = text.replace('$50', f'${random.randint(30, 100)}')
            
            metadata = {
                'category': random.choice(['job_scam', 'internship_scam', 'phishing', 'financial_fraud']),
                'source': 'generated',
                'has_urgency': random.choice([True, False]),
                'has_money_mention': True,
                'language': 'en'
            }
            
            self.add_scam_sample(text, metadata, 'en')
        
        # Generate legitimate samples
        for i in range(num_samples // 2):
            text = random.choice(legit_examples)
            
            metadata = {
                'category': random.choice(['software', 'marketing', 'customer_service', 'content', 'data']),
                'source': 'generated',
                'has_urgency': False,
                'has_money_mention': random.choice([True, False]),
                'language': 'en'
            }
            
            self.add_legit_sample(text, metadata, 'en')
        
        # Generate sample reviews
        review_companies = ['FakeCorp', 'ScamInc', 'FraudLLC', 'PhishCo', 'SpamEnterprises']
        
        for company in review_companies:
            for i in range(5):
                review = {
                    'company_name': company,
                    'company_domain': f'{company.lower()}.xyz',
                    'job_title': random.choice(['Data Entry', 'Customer Service', 'Marketing', 'Sales']),
                    'rating': 1,
                    'comment': f"They asked for ${random.randint(50, 500)} upfront payment. Total scam!",
                    'category': 'job_scam',
                    'evidence': {'screenshots': [], 'urls': [f'https://{company.lower()}.xyz']},
                    'location': random.choice(['USA', 'India', 'UK', 'Canada', 'Australia']),
                    'financial_loss': random.randint(50, 1000),
                    'tags': ['scam', 'fraud', 'upfront_payment'],
                    'username': f'User{random.randint(1000, 9999)}'
                }
                
                self.add_review(review)
        
        self.save_data()
        print(f"Generated {num_samples} samples and {len(review_companies)*5} reviews")
    
    def _load_csv(self, filepath: str) -> List[Dict]:
        """Load data from CSV file"""
        data = []
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse JSON fields
                    for key in ['metadata', 'evidence']:
                        if key in row and row[key]:
                            try:
                                row[key] = json.loads(row[key])
                            except:
                                row[key] = {}
                    
                    data.append(row)
        
        return data
    
    def _save_csv(self, filepath: str, data: List[Dict]):
        """Save data to CSV file"""
        if not data:
            return
        
        # Convert complex fields to JSON strings
        processed_data = []
        for item in data:
            processed_item = item.copy()
            
            for key in ['metadata', 'evidence']:
                if key in processed_item and processed_item[key]:
                    if isinstance(processed_item[key], (dict, list)):
                        processed_item[key] = json.dumps(processed_item[key], ensure_ascii=False)
            
            processed_data.append(processed_item)
        
        # Write to CSV
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            if processed_data:
                fieldnames = processed_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(processed_data)
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
        return f"{prefix}_{timestamp}_{random_str}"
    
    def cleanup_old_data(self, days_old: int = 365):
        """Remove data older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Filter scam data
        self.scam_data = [
            item for item in self.scam_data
            if datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')) >= cutoff_date
        ]
        
        # Filter legit data
        self.legit_data = [
            item for item in self.legit_data
            if datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')) >= cutoff_date
        ]
        
        # Filter reviews
        self.reviews_data = [
            item for item in self.reviews_data
            if datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')) >= cutoff_date
        ]
        
        # Update metadata
        self.metadata['scam_count'] = len(self.scam_data)
        self.metadata['legit_count'] = len(self.legit_data)
        self.metadata['reviews_count'] = len(self.reviews_data)
        self.metadata['total_samples'] = self.metadata['scam_count'] + self.metadata['legit_count']
        
        self.save_data()
        print(f"Cleaned up data older than {days_old} days")