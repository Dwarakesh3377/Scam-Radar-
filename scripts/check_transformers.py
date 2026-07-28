from transformers import TrainingArguments
import torch
import inspect

def check():
    print(f"Torch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    # Check TrainingArguments init signature
    sig = inspect.signature(TrainingArguments.__init__)
    params = sig.parameters.keys()
    
    print("\nTrainingArguments Parameters:")
    for p in sorted(params):
        if p in ['eval_strategy', 'evaluation_strategy', 'no_cuda', 'fp16']:
            print(f"Found: {p}")

if __name__ == "__main__":
    check()
