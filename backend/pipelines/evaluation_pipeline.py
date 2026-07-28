import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc,
    precision_recall_curve, average_precision_score
)
from backend.pipelines.inference_pipeline import InferencePipeline

class EvaluationPipeline:
    """Pipeline for evaluating model performance"""
    
    def __init__(self, test_data_path='test_data.csv'):
        self.test_data_path = test_data_path
        self.inference_pipeline = InferencePipeline()
        self.results = {}
        
        # Create results directory
        self.results_dir = 'evaluation_results/'
        os.makedirs(self.results_dir, exist_ok=True)
    
    def load_test_data(self):
        """Load test data for evaluation"""
        print("Loading test data...")
        
        if not os.path.exists(self.test_data_path):
            print(f"Test data not found at {self.test_data_path}")
            return None
        
        try:
            test_df = pd.read_csv(self.test_data_path)
            
            # Ensure required columns exist
            required_columns = ['text', 'label']
            for col in required_columns:
                if col not in test_df.columns:
                    print(f"Missing required column: {col}")
                    return None
            
            print(f"Loaded {len(test_df)} test samples")
            return test_df
            
        except Exception as e:
            print(f"Error loading test data: {str(e)}")
            return None
    
    def run_predictions(self, test_df, sample_size=None):
        """Run predictions on test data"""
        print("\nRunning predictions...")
        
        if sample_size and sample_size < len(test_df):
            test_df = test_df.sample(sample_size, random_state=42)
        
        texts = test_df['text'].tolist()
        true_labels = test_df['label'].tolist()
        
        # Get metadata if available
        metadata_list = []
        if 'metadata' in test_df.columns:
            metadata_list = test_df['metadata'].apply(lambda x: eval(x) if isinstance(x, str) else x).tolist()
        
        # Run predictions
        predictions = self.inference_pipeline.batch_analyze(texts, metadata_list)
        
        # Extract predicted scores and labels
        predicted_scores = [pred['score'] for pred in predictions]
        
        # Convert scores to binary labels (scam if > 60)
        predicted_labels = [1 if score > 60 else 0 for score in predicted_scores]
        
        # Store results
        self.results = {
            'true_labels': true_labels,
            'predicted_labels': predicted_labels,
            'predicted_scores': predicted_scores,
            'predictions': predictions,
            'sample_count': len(texts)
        }
        
        return self.results
    
    def calculate_metrics(self):
        """Calculate evaluation metrics"""
        print("\nCalculating metrics...")
        
        if not self.results:
            print("No results available. Run predictions first.")
            return None
        
        true_labels = self.results['true_labels']
        predicted_labels = self.results['predicted_labels']
        predicted_scores = self.results['predicted_scores']
        
        # Basic metrics
        accuracy = accuracy_score(true_labels, predicted_labels)
        precision = precision_score(true_labels, predicted_labels, zero_division=0)
        recall = recall_score(true_labels, predicted_labels, zero_division=0)
        f1 = f1_score(true_labels, predicted_labels, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(true_labels, predicted_labels)
        
        # ROC curve metrics
        try:
            fpr, tpr, thresholds = roc_curve(true_labels, predicted_scores)
            roc_auc = auc(fpr, tpr)
        except:
            fpr, tpr, thresholds = None, None, None
            roc_auc = 0
        
        # Precision-Recall curve
        try:
            precision_curve, recall_curve, _ = precision_recall_curve(true_labels, predicted_scores)
            pr_auc = average_precision_score(true_labels, predicted_scores)
        except:
            precision_curve, recall_curve = None, None
            pr_auc = 0
        
        metrics = {
            'accuracy': round(accuracy, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'roc_auc': round(roc_auc, 4),
            'pr_auc': round(pr_auc, 4),
            'confusion_matrix': cm.tolist(),
            'sample_count': len(true_labels),
            'scam_count': sum(true_labels),
            'legit_count': len(true_labels) - sum(true_labels),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Print results
        print("\n" + "=" * 50)
        print("EVALUATION METRICS")
        print("=" * 50)
        print(f"Accuracy:  {accuracy:.2%}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall:    {recall:.2%}")
        print(f"F1 Score:  {f1:.2%}")
        print(f"ROC AUC:   {roc_auc:.2%}")
        print(f"PR AUC:    {pr_auc:.2%}")
        print(f"\nSamples:   {len(true_labels)}")
        print(f"Scams:     {sum(true_labels)}")
        print(f"Legit:     {len(true_labels) - sum(true_labels)}")
        print("\nConfusion Matrix:")
        print(cm)
        print("\nClassification Report:")
        print(classification_report(true_labels, predicted_labels, target_names=['Legit', 'Scam']))
        
        return metrics
    
    def plot_results(self, metrics):
        """Create visualization plots"""
        print("\nGenerating plots...")
        
        true_labels = self.results['true_labels']
        predicted_scores = self.results['predicted_scores']
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Model Evaluation Results', fontsize=16)
        
        # 1. Score Distribution
        axes[0, 0].hist(predicted_scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].axvline(x=60, color='red', linestyle='--', label='Scam Threshold (60)')
        axes[0, 0].set_xlabel('Risk Score')
        axes[0, 0].set_ylabel('Count')
        axes[0, 0].set_title('Distribution of Predicted Risk Scores')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Confusion Matrix Heatmap
        cm = np.array(metrics['confusion_matrix'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=['Legit', 'Scam'],
                    yticklabels=['Legit', 'Scam'],
                    ax=axes[0, 1])
        axes[0, 1].set_xlabel('Predicted')
        axes[0, 1].set_ylabel('Actual')
        axes[0, 1].set_title('Confusion Matrix')
        
        # 3. ROC Curve
        if hasattr(self, 'roc_curve_data'):
            fpr, tpr, _ = self.roc_curve_data
            roc_auc = metrics['roc_auc']
            axes[1, 0].plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
            axes[1, 0].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            axes[1, 0].set_xlim([0.0, 1.0])
            axes[1, 0].set_ylim([0.0, 1.05])
            axes[1, 0].set_xlabel('False Positive Rate')
            axes[1, 0].set_ylabel('True Positive Rate')
            axes[1, 0].set_title('Receiver Operating Characteristic (ROC) Curve')
            axes[1, 0].legend(loc="lower right")
            axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Metric Comparison
        metric_names = ['Accuracy', 'Precision', 'Recall', 'F1 Score']
        metric_values = [
            metrics['accuracy'],
            metrics['precision'],
            metrics['recall'],
            metrics['f1_score']
        ]
        
        colors = ['skyblue', 'lightgreen', 'lightcoral', 'gold']
        bars = axes[1, 1].bar(metric_names, metric_values, color=colors, edgecolor='black')
        axes[1, 1].set_ylim([0, 1])
        axes[1, 1].set_ylabel('Score')
        axes[1, 1].set_title('Model Performance Metrics')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            axes[1, 1].text(bar.get_x() + bar.get_width()/2., height + 0.02,
                          f'{value:.2%}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.results_dir, 'evaluation_plots.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Plots saved to: {plot_path}")
        
        # Create score distribution by actual label
        self.plot_score_distribution_by_label()
        
        return plot_path
    
    def plot_score_distribution_by_label(self):
        """Plot score distribution separated by actual label"""
        true_labels = np.array(self.results['true_labels'])
        predicted_scores = np.array(self.results['predicted_scores'])
        
        # Separate scores by actual label
        scam_scores = predicted_scores[true_labels == 1]
        legit_scores = predicted_scores[true_labels == 0]
        
        plt.figure(figsize=(10, 6))
        
        # Create histogram
        plt.hist([legit_scores, scam_scores], 
                bins=20, 
                alpha=0.7, 
                color=['green', 'red'],
                label=['Legitimate', 'Scam'],
                edgecolor='black')
        
        plt.axvline(x=60, color='black', linestyle='--', linewidth=2, label='Scam Threshold (60)')
        
        plt.xlabel('Risk Score')
        plt.ylabel('Count')
        plt.title('Risk Score Distribution by Actual Label')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save plot
        plot_path = os.path.join(self.results_dir, 'score_distribution_by_label.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Score distribution plot saved to: {plot_path}")
    
    def analyze_errors(self):
        """Analyze false positives and false negatives"""
        print("\nAnalyzing errors...")
        
        if not self.results:
            print("No results available.")
            return None
        
        true_labels = self.results['true_labels']
        predicted_labels = self.results['predicted_labels']
        predictions = self.results['predictions']
        
        # Identify errors
        errors = {
            'false_positives': [],  # Predicted scam but actually legit
            'false_negatives': []   # Predicted legit but actually scam
        }
        
        for i, (true, pred) in enumerate(zip(true_labels, predicted_labels)):
            if true == 0 and pred == 1:  # False positive
                errors['false_positives'].append({
                    'index': i,
                    'score': predictions[i]['score'],
                    'risk_level': predictions[i]['risk_level']
                })
            elif true == 1 and pred == 0:  # False negative
                errors['false_negatives'].append({
                    'index': i,
                    'score': predictions[i]['score'],
                    'risk_level': predictions[i]['risk_level']
                })
        
        # Calculate error rates
        total = len(true_labels)
        fp_count = len(errors['false_positives'])
        fn_count = len(errors['false_negatives'])
        
        error_analysis = {
            'false_positive_rate': fp_count / max(total, 1),
            'false_negative_rate': fn_count / max(total, 1),
            'false_positives_count': fp_count,
            'false_negatives_count': fn_count,
            'total_errors': fp_count + fn_count,
            'error_details': errors
        }
        
        print(f"False Positives: {fp_count} ({fp_count/total:.2%})")
        print(f"False Negatives: {fn_count} ({fn_count/total:.2%})")
        print(f"Total Errors: {fp_count + fn_count} ({(fp_count + fn_count)/total:.2%})")
        
        return error_analysis
    
    def save_results(self, metrics, error_analysis):
        """Save evaluation results to files"""
        print("\nSaving results...")
        
        # Save metrics
        metrics_path = os.path.join(self.results_dir, 'evaluation_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Save error analysis
        if error_analysis:
            errors_path = os.path.join(self.results_dir, 'error_analysis.json')
            with open(errors_path, 'w') as f:
                json.dump(error_analysis, f, indent=2)
        
        # Save detailed predictions
        detailed_results = {
            'predictions': self.results['predictions'],
            'true_labels': self.results['true_labels'],
            'predicted_labels': self.results['predicted_labels'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        detailed_path = os.path.join(self.results_dir, 'detailed_predictions.json')
        with open(detailed_path, 'w') as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        print(f"Results saved to: {self.results_dir}")
    
    def run_complete_evaluation(self, sample_size=500):
        """Run complete evaluation pipeline"""
        print("=" * 50)
        print("MODEL EVALUATION PIPELINE")
        print("=" * 50)
        
        # Step 1: Load test data
        test_df = self.load_test_data()
        if test_df is None:
            print("Failed to load test data.")
            return
        
        # Step 2: Run predictions
        self.run_predictions(test_df, sample_size)
        
        # Step 3: Calculate metrics
        metrics = self.calculate_metrics()
        if metrics is None:
            print("Failed to calculate metrics.")
            return
        
        # Step 4: Analyze errors
        error_analysis = self.analyze_errors()
        
        # Step 5: Generate plots
        plot_path = self.plot_results(metrics)
        
        # Step 6: Save results
        self.save_results(metrics, error_analysis)
        
        print("\n" + "=" * 50)
        print("EVALUATION COMPLETE!")
        print("=" * 50)
        print(f"Results saved in: {self.results_dir}")
        print(f"Plots saved: {plot_path}")
        
        return metrics, error_analysis

# Main execution
if __name__ == "__main__":
    evaluator = EvaluationPipeline()
    
    # Run evaluation
    metrics, errors = evaluator.run_complete_evaluation(sample_size=200)
    
    # Print summary
    if metrics:
        print("\nSUMMARY:")
        print(f"Final Accuracy: {metrics['accuracy']:.2%}")
        print(f"Precision:      {metrics['precision']:.2%}")
        print(f"Recall:         {metrics['recall']:.2%}")
        print(f"F1 Score:       {metrics['f1_score']:.2%}")