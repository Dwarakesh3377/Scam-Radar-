"""
Excel Dataset Loader - Load data from Excel files
=================================================
Handles loading of scam/legitimate/suspicious datasets and negative reviews.
"""

import pandas as pd
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
import random

def clean_name(name):
    """
    Clean company name for matching by removing noise words and symbols.
    """
    if pd.isna(name): return ""
    name = str(name).lower().strip()
    
    # Remove common noise words
    noise = {
        'limited', 'ltd', 'pvt', 'private', 'solutions', 'services', 'inc', 'corp', 
        'india', 'technology', 'technologies', 'software', 'systems', 'enterprise', 
        'enterprises', 'group', 'groups', 'intl', 'international', 'co', 'company',
        'direct', 'hiring', 'recruitment', 'hr', 'careers', 'team', 'teams', 'work', 
        'home', 'remote', 'online', 'vacancy', 'vacancies', 'hiring', 'recruiter',
        'official', 'verified', 'support', 'helpdesk', 'pay', 'portal', 'opening',
        'openings', 'career', 'opportunity', 'opportunities', 'office', 'executive',
        'job', 'jobs'
    }
    
    # Handle hyphenated names like E-Jobs -> E-Jobs (keep the hyphen for part splitting but also try without)
    # We'll just replace with space to let parts logic handle it
    name_for_parts = name.replace('-', ' ')
    
    # Remove common symbols but keep alphanumeric characters
    cleaned = re.sub(r'[^\w\s]', ' ', name_for_parts)
    parts = cleaned.split()
    
    # Only remove noise if we have at least 2 non-noise parts OR if the name is long
    meaningful_parts = [p for p in parts if p not in noise]
    
    # CRITICAL: If noise removal makes it too short (<2 chars) or empty, ignore noise list
    if not meaningful_parts or (len(meaningful_parts) == 1 and len(meaningful_parts[0]) < 3):
        # Fallback to original parts but filter out only the most generic ones (ltd, pvt, india)
        # if and only if there are other parts.
        minimal_noise = {'limited', 'ltd', 'pvt', 'private', 'corp', 'inc'}
        meaningful_parts = [p for p in parts if p not in minimal_noise]
        
    # Final filter: remove only extremely short noise-like parts unless it's a very short name overall
    if len(meaningful_parts) > 1:
        meaningful_parts = [p for p in meaningful_parts if len(p) > 1]
        
    return " ".join(meaningful_parts).strip()


class ExcelDataLoader:
    """Load and query data from Excel datasets"""
    
    def __init__(self, dataset_dir: Optional[str] = None):
        """Initialize the Excel data loader"""
        if dataset_dir is None:
            # Robust path discovery: search parent directories for 'dataset' folder
            # This works both locally (d:/scam/backend/utils/loader) and in Docker (/app/utils/loader)
            base_dir = Path(__file__).resolve().parent
            found_dir = None
            for _ in range(4): # Check up to 4 levels up
                if (base_dir / 'dataset').exists():
                    found_dir = base_dir / 'dataset'
                    break
                base_dir = base_dir.parent
                
            if found_dir:
                self.dataset_dir = found_dir
                print(f"[DATASET] Found dataset directory at: {self.dataset_dir}")
            else:
                # Final fallbacks
                search_paths = [
                    '/app/dataset',
                    './dataset',
                    '../dataset',
                    '../../dataset',
                    'backend/dataset'
                ]
                for p in search_paths:
                    if os.path.exists(p):
                        self.dataset_dir = Path(p)
                        print(f"[DATASET] Found dataset via fallback at: {self.dataset_dir}")
                        break
                else:
                    self.dataset_dir = Path(__file__).parent.parent.parent / 'dataset'
        else:
            self.dataset_dir = Path(dataset_dir)
        
        # Dataset file paths
        self.files = {
            'legitimate_jobs': 'legitimate_jobs_final 2.0.xlsx',
            'legitimate_internships': 'legitimate_internships_final 2.0.xlsx',
            'suspicious_jobs': 'suspicious_jobs_final 2.0.xlsx',
            'suspicious_internships': 'suspicious_internships_final 2.0.xlsx',
            'scam_jobs': 'scam_jobs_final 2.0.xlsx',
            'scam_internships': 'scam_internships_final 2.0.xlsx',
            'negative_reviews': 'negative_reviews_final 2.0.xlsx'
        }
        
        # Cache for loaded data
        self._cache = {}
    
    def _load_excel(self, file_key: str) -> pd.DataFrame:
        """Load an Excel file and cache it"""
        if file_key in self._cache:
            return self._cache[file_key]
        
        file_path = self.dataset_dir / self.files.get(file_key, '')
        
        if not file_path.exists():
            print(f"Warning: Dataset file not found: {file_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_excel(file_path)
            self._cache[file_key] = df
            return df
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            return pd.DataFrame()
    
    def get_negative_reviews(self, company_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Get negative reviews from the dataset.
        
        Args:
            company_name: Filter by company name (fuzzy match)
            limit: Maximum number of reviews to return
            
        Returns:
            List of review dictionaries
        """
        df = self._load_excel('negative_reviews')
        
        if df.empty:
            return self._get_fallback_reviews()
        
        # Filter by company name if provided
        if company_name and company_name not in ['External Email', 'Unknown Company', 'None', '']:
            target = company_name.lower().strip()
            
            target_clean = clean_name(target)
            print(f"[REVIEWS] Searching for company: '{target}' (cleaned: '{target_clean}')")
            
            def is_match_internal(row_company):
                """Internal wrapper for matching logic"""
                return is_match(target, str(row_company))

            # Use refined matching
            mask = df['scam_company_name'].apply(is_match_internal)
            # Filter rows where match quality is strong or weak
            filtered_df = df[mask.isin(['strong', 'weak'])]
            
            if filtered_df.empty:
                print(f"[REVIEWS] No refined match found for: '{company_name}'. Trying substring fallback...")
                # Substring fallback
                mask = df['scam_company_name'].apply(lambda x: target_clean in clean_name(str(x)) or clean_name(str(x)) in target_clean)
                filtered_df = df[mask]
                
            if filtered_df.empty:
                print(f"[REVIEWS] No absolute or substring match found for: '{company_name}'")
                return []
        else:
            # If no company name provided or if we want general reviews
            print("[REVIEWS] No company name provided for review search. Returning general reviews...")
            return self._get_general_reviews(limit)
        
        # Convert to list of dictionaries
        reviews = []
        for _, row in filtered_df.head(limit).iterrows():
            review = {
                'id': len(reviews) + 1,
                'reviewer_name': row.get('reviewer_name', 'Anonymous'),
                'company_name': row.get('scam_company_name', 'Unknown Company'),
                'loss_type': row.get('loss_type', 'Unknown'),
                'loss_amount': row.get('loss_amount', 'Not specified'),
                'review_text': row.get('review_text', 'No details provided'),
                'review_date': str(row.get('review_date', '')),
            }
            reviews.append(review)
            
        if not reviews:
            print(f"[REVIEWS] No company-specific reviews found for: '{company_name}'. Returning general reviews...")
            return self._get_general_reviews(limit)
        
        print(f"[REVIEWS] Fetched {len(reviews)} reviews for company: {company_name}")
        return reviews

    def _get_general_reviews(self, limit: int = 10) -> List[Dict]:
        """Return a random sample of general scam reviews from the dataset"""
        df = self._load_excel('negative_reviews')
        if df.empty:
            return []
        
        # Sample random reviews
        sample_df = df.sample(min(len(df), limit)) if not df.empty else df
        
        reviews = []
        for i, (_, row) in enumerate(sample_df.iterrows()):
            review = {
                'id': i + 1,
                'reviewer_name': row.get('reviewer_name', 'Anonymous'),
                'company_name': row.get('scam_company_name', 'Reported Entity'),
                'loss_type': row.get('loss_type', 'Recruitment Scam'),
                'loss_amount': row.get('loss_amount', 'Not specified'),
                'review_text': row.get('review_text', 'Reported as a fraudulent hiring attempt.'),
                'review_date': str(row.get('review_date', '')),
            }
            reviews.append(review)
        return reviews
    
    def _get_fallback_reviews(self) -> List[Dict]:
        """Return empty list if dataset is missing - no dummy data"""
        return []
    
    
    def get_scam_patterns(self, input_type: str = 'job') -> pd.DataFrame:
        """Get scam patterns for training/comparison"""
        file_key = f'scam_{input_type}s' if input_type != 'internship' else 'scam_internships'
        return self._load_excel(file_key)
    
    def get_legitimate_patterns(self, input_type: str = 'job') -> pd.DataFrame:
        """Get legitimate patterns for training/comparison"""
        file_key = f'legitimate_{input_type}s' if input_type != 'internship' else 'legitimate_internships'
        return self._load_excel(file_key)
    
    def get_suspicious_patterns(self, input_type: str = 'job') -> pd.DataFrame:
        """Get suspicious patterns for training/comparison"""
        file_key = f'suspicious_{input_type}s' if input_type != 'internship' else 'suspicious_internships'
        return self._load_excel(file_key)
    
    def get_training_data(self, input_type: str = 'job') -> Dict[str, pd.DataFrame]:
        """Get all training data for a given input type"""
        return {
            'legitimate': self.get_legitimate_patterns(input_type),
            'suspicious': self.get_suspicious_patterns(input_type),
            'scam': self.get_scam_patterns(input_type)
        }

    def get_whitelist_companies(self) -> List[str]:
        """Get unique legitimate company names for whitelisting"""
        names = []
        for file_key in ['legitimate_jobs', 'legitimate_internships']:
            df = self._load_excel(file_key)
            if not df.empty:
                # Assuming the column name matches the data
                col = 'legitimate_company_name' if 'legitimate_company_name' in df.columns else df.columns[0]
                names.extend(df[col].dropna().unique().tolist())
        return sorted(list(set(names)))
    
    def get_known_scam_names(self) -> List[str]:
        """
        Returns all unique scam company names from the negative reviews dataset.
        Caches the result for performance.
        """
        cache_key = '_cached_scam_names'
        if cache_key in self._cache:
            return self._cache[cache_key]

        df = self._load_excel('negative_reviews')
        if df.empty or 'scam_company_name' not in df.columns:
            self._cache[cache_key] = []
            return []

        names = [str(n) for n in df['scam_company_name'].dropna().unique()]
        self._cache[cache_key] = sorted(list(set(names)))
        return self._cache[cache_key]
    
    def search_similar_scams(self, content: str, limit: int = 5) -> List[Dict]:
        """
        Search for similar scam patterns in the dataset.
        
        Args:
            content: The content to search for
            limit: Maximum number of results
            
        Returns:
            List of matching scam records
        """
        results = []
        
        # Search in both job and internship scam datasets
        for file_key in ['scam_jobs', 'scam_internships']:
            df = self._load_excel(file_key)
            if df.empty:
                continue
            
            # Simple keyword matching
            content_lower = content.lower()
            import itertools
            all_words = content_lower.split()
            keywords = list(itertools.islice(all_words, 5))  # Use first 5 words safely
            
            for _, row in df.iterrows():
                description = str(row.get('scam_job_description', '') or '').lower()
                if any(str(kw) in description for kw in keywords if kw and len(str(kw)) > 3):
                    results.append({
                        'company': row.get('scam_company_name', 'Unknown'),
                        'title': row.get('fake_job_title', 'Unknown'),
                        'description': "".join(itertools.islice(str(row.get('scam_job_description', '') or ''), 200)),
                        'payment_type': row.get('payment_request_type', ''),
                        'urgency': row.get('urgency_language', ''),
                    })
                    
                    if len(results) >= limit:
                        break
            
            if len(results) >= limit:
                break
        
        import itertools
        return list(itertools.islice(list(results), limit))


# Singleton instance
_data_loader = None

def get_data_loader() -> ExcelDataLoader:
    """Get the singleton instance of ExcelDataLoader"""
    global _data_loader
    if _data_loader is None:
        _data_loader = ExcelDataLoader()
    return _data_loader


# Convenience functions
def get_negative_reviews(company_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Get negative reviews from the dataset"""
    return get_data_loader().get_negative_reviews(company_name, limit)


def search_similar_scams(content: str, limit: int = 5) -> List[Dict]:
    """Search for similar scam patterns"""
    return get_data_loader().search_similar_scams(content, limit)


def fetch_reviews_from_db(company_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Alias for get_negative_reviews to fix ImportError"""
    return get_negative_reviews(company_name, limit)


def get_enriched_reviews(content: Any = None, company_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Alias for get_negative_reviews to fix ImportError"""
    return get_negative_reviews(company_name, limit)

def is_match(target: str, reference: str) -> str:
    """
    Refined matching logic that returns 'strong', 'weak', or 'none'.
    Used to distinguish legitimate companies from scam variants.
    """
    if not target or not reference:
        return "none"
        
    t = str(target).lower().strip()
    r = str(reference).lower().strip()
    
    # 1. Exact Match (Simple)
    if t == r: return "strong"
    
    # 2. Cleaned Match (Noise words removed)
    t_clean = clean_name(t)
    r_clean = clean_name(r)
    
    if not t_clean or not r_clean: return "none"
    if t_clean == r_clean: 
        return "strong"
    
    # 3. Substring Match (Fuzzy)
    # If one is a significant part of the other (e.g. "E-Jobs" in "E-Jobs India")
    if len(t_clean) > 3 and (t_clean in r_clean or r_clean in t_clean):
        return "weak"
    
    if t_clean.replace(" ", "") == r_clean.replace(" ", ""):
        return "strong"
        
    # 4. Normalized Match (No symbols)
    t_simple = re.sub(r'[^a-z0-9]', '', t_clean)
    r_simple = re.sub(r'[^a-z0-9]', '', r_clean)
    
    if t_simple and r_simple:
        if t_simple == r_simple: return "strong"
    
    # 4. Part Overlap
    t_parts = t_clean.split()
    r_parts = r_clean.split()
    
    # NEW: Check original parts (before cleaning) to see if one is significantly 
    # more specific than the other (e.g. "Accenture" vs "Accenture India Jobs")
    t_orig_parts = t.split()
    r_orig_parts = r.split()
    
    if not t_parts or not r_parts: return "none"
    
    common = set(t_parts) & set(r_parts)
    if not common: 
        # Check for substring match in joined simple strings for cases like "E-Jobs" vs "Ejobs"
        if t_simple and r_simple and (t_simple in r_simple or r_simple in t_simple):
            if len(t_simple) > 10 or len(r_simple) > 10:
                return "weak"
        return "none"
        
    # Single word target rules
    if len(t_parts) == 1:
        part = t_parts[0]
        if part in r_parts:
            # If the original word counts are very different, it's a weak match
            # e.g. "Accenture" vs "Accenture India Jobs Recruitment Team"
            if abs(len(t_orig_parts) - len(r_orig_parts)) >= 2:
                return "weak"
            if len(r_parts) > 1: return "weak"
            return "strong"
        return "none"
        
    # Multi-word overlap rules
    overlap_target = len(common) / len(t_parts)
    overlap_ref = len(common) / len(r_parts)
    
    # If target is almost fully contained in ref or vice versa
    if overlap_target >= 0.8 or overlap_ref >= 0.8:
        # If they are very similar in word count (original)
        if abs(len(t_orig_parts) - len(r_orig_parts)) <= 1:
            return "strong"
        return "weak"
        
    if overlap_target >= 0.4 or overlap_ref >= 0.4:
        return "weak"
    
    # Final substring check
    if t_simple in r_simple or r_simple in t_simple:
        if len(t_simple) > 4 and len(r_simple) > 4:
            return "weak"
        
    return "none"
