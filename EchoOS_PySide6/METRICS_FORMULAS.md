# Performance Metrics Formulas & Validation Methods

## 📐 Formulas for Calculating Metrics

### 1. Speech Recognition Metrics

#### Word Error Rate (WER)
**Formula:**
```
WER = (S + D + I) / N × 100%

Where:
- S = Number of substitutions
- D = Number of deletions  
- I = Number of insertions
- N = Total number of words in reference
```

**How to Validate:**
- Use standard test datasets (TEDLIUM, LibriSpeech)
- Compare predicted text with reference text
- Calculate edit distance (Levenshtein distance)

**Code Example:**
```python
from jiwer import wer

reference = "lock screen"
hypothesis = "lock screen"
error_rate = wer(reference, hypothesis) * 100  # Returns WER%
```

#### Recognition Latency
**Formula:**
```
Recognition Time = Processing Time + Model Latency
Average Latency = Σ(Individual Latencies) / N
```

**How to Measure:**
```python
import time

start = time.perf_counter()
text = model.recognize(audio)
end = time.perf_counter()
latency_ms = (end - start) * 1000
```

---

### 2. Command Execution Metrics

#### Command Success Rate
**Formula:**
```
Success Rate = (Successful Commands / Total Commands) × 100%
Error Rate = (Failed Commands / Total Commands) × 100%
```

**How to Calculate:**
```python
total_commands = len(test_commands)
successful = sum(1 for cmd, result in results if result == True)
success_rate = (successful / total_commands) * 100
```

#### Execution Time by Category
**Formula:**
```
Average Execution Time = Σ(Execution Times) / N
Standard Deviation = √(Σ(xi - μ)² / N)
```

**How to Measure:**
```python
execution_times = {
    'system': [],
    'file': [],
    'app': [],
    'media': []
}

for command in commands:
    start = time.perf_counter()
    result = executor.execute_command(command)
    end = time.perf_counter()
    
    category = categorize_command(command)
    execution_times[category].append((end - start) * 1000)
```

---

### 3. End-to-End Latency

#### Pipeline Latency Breakdown
**Formula:**
```
E2E Latency = T_audio + T_recognition + T_parsing + T_auth + T_execution

Where:
- T_audio = Audio capture time (4 seconds default)
- T_recognition = Speech recognition time (~150ms)
- T_parsing = Command parsing time (~50ms)
- T_auth = Authentication check time (~10ms)
- T_execution = Command execution time (varies)
```

**How to Measure:**
```python
def measure_e2e_latency(command):
    # Audio capture
    t0 = time.perf_counter()
    audio = record_audio(4)  # 4 seconds
    t1 = time.perf_counter()
    audio_time = (t1 - t0) * 1000
    
    # Recognition
    t1 = time.perf_counter()
    text = recognize(audio)
    t2 = time.perf_counter()
    recognition_time = (t2 - t1) * 1000
    
    # Parsing
    t2 = time.perf_counter()
    parsed = parse_command(text)
    t3 = time.perf_counter()
    parsing_time = (t3 - t2) * 1000
    
    # Auth check
    t3 = time.perf_counter()
    if not check_auth():
        return None
    t4 = time.perf_counter()
    auth_time = (t4 - t3) * 1000
    
    # Execution
    t4 = time.perf_counter()
    execute(parsed)
    t5 = time.perf_counter()
    execution_time = (t5 - t4) * 1000
    
    total_time = (t5 - t0) * 1000
    
    return {
        'total': total_time,
        'breakdown': {
            'audio': audio_time,
            'recognition': recognition_time,
            'parsing': parsing_time,
            'auth': auth_time,
            'execution': execution_time
        }
    }
```

---

### 4. Authentication Metrics

#### Accuracy, Precision, Recall, F1-Score
**Formulas:**
```
Accuracy = (TP + TN) / (TP + TN + FP + FN) × 100%

Precision = TP / (TP + FP) × 100%

Recall = TP / (TP + FN) × 100%

F1-Score = 2 × (Precision × Recall) / (Precision + Recall)
```

**Confusion Matrix:**
```
                Predicted
               Accept  Reject
Actual Accept    TP     FN
       Reject    FP     TN
```

**How to Calculate:**
```python
def calculate_auth_metrics(results):
    """
    results: List of (actual, predicted) tuples
    where actual=True means genuine user, predicted=True means accepted
    """
    tp = sum(1 for actual, pred in results if actual and pred)
    tn = sum(1 for actual, pred in results if not actual and not pred)
    fp = sum(1 for actual, pred in results if not actual and pred)
    fn = sum(1 for actual, pred in results if actual and not pred)
    
    total = len(results)
    
    accuracy = ((tp + tn) / total) * 100 if total > 0 else 0
    precision = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0
    recall = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'confusion_matrix': {'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn}
    }
```

#### False Acceptance Rate (FAR) / False Rejection Rate (FRR)
**Formulas:**
```
FAR = FP / (FP + TN) × 100%  (Imposters accepted)
FRR = FN / (FN + TP) × 100%  (Genuine users rejected)
EER = Point where FAR = FRR  (Equal Error Rate)
```

---

### 5. Resource Usage Metrics

#### Memory Usage
**Formula:**
```
Average Memory = Σ(Memory Samples) / N
Peak Memory = Max(Memory Samples)
```

**How to Measure:**
```python
import psutil
import os

process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
```

#### CPU Usage
**Formula:**
```
Average CPU = Σ(CPU Samples) / N
Peak CPU = Max(CPU Samples)
```

**How to Measure:**
```python
cpu_percent = process.cpu_percent(interval=1)
```

---

## 📊 Statistical Analysis Methods

### 1. Confidence Intervals
**Formula:**
```
95% CI = Mean ± (1.96 × (SD / √N))

Where:
- SD = Standard Deviation
- N = Sample Size
```

**Code:**
```python
import scipy.stats as stats

mean = statistics.mean(data)
std = statistics.stdev(data)
n = len(data)
ci = stats.t.interval(0.95, n-1, loc=mean, scale=std/np.sqrt(n))
```

### 2. Statistical Significance Testing
**t-test for comparing means:**
```python
from scipy.stats import ttest_ind

group1_times = [...]
group2_times = [...]

t_stat, p_value = ttest_ind(group1_times, group2_times)
# p_value < 0.05 indicates significant difference
```

---

## 📈 Graph Generation Formulas

### 1. Histogram Bins
**Sturges' Rule:**
```
Number of Bins = 1 + log₂(N)

Where N = Number of data points
```

### 2. Box Plot Statistics
```
Q1 = 25th percentile
Median = 50th percentile  
Q3 = 75th percentile
IQR = Q3 - Q1
Outliers = Values outside [Q1 - 1.5×IQR, Q3 + 1.5×IQR]
```

---

## 🧪 Testing Methodology

### 1. Test Dataset Requirements
- **Speech Recognition**: Minimum 100 test phrases
- **Command Execution**: All command categories represented
- **Authentication**: Minimum 50 genuine + 50 impostor attempts
- **Resource Usage**: Minimum 30 samples over 10 minutes

### 2. Reproducibility
- Use fixed random seeds
- Document hardware specifications
- Record software versions
- Control environmental factors (noise, lighting)

### 3. Validation Protocol
1. **Baseline Measurement**: Establish baseline performance
2. **Controlled Testing**: Test under controlled conditions
3. **Real-World Testing**: Test in natural usage scenarios
4. **Statistical Analysis**: Apply statistical tests
5. **Graph Generation**: Visualize results

---

## 📝 Example Test Script

See `test_performance.py` for complete implementation of all metrics calculations and graph generation.

**To run tests:**
```bash
cd EchoOS_PySide6
pip install matplotlib numpy scipy jiwer psutil
python test_performance.py
```

This will generate:
- `test_results.json` - All metrics data
- `graphs/recognition_time.png` - Recognition latency distribution
- `graphs/command_execution.png` - Execution times by category
- `graphs/e2e_latency.png` - End-to-end latency breakdown
- `graphs/auth_confusion_matrix.png` - Authentication confusion matrix
- `graphs/success_rate.png` - Command success rate
- `graphs/resource_usage.png` - Memory/CPU over time

---

## 📚 References for Research Paper

### Standard Metrics
- **WER**: Standard metric from speech recognition research
- **FAR/FRR**: ISO/IEC 19795 biometric evaluation standards
- **Precision/Recall**: Standard classification metrics

### Benchmark Datasets
- **TEDLIUM**: Speech recognition benchmark
- **LibriSpeech**: Standard ASR test corpus
- **LFW** (adapted): Face recognition benchmark (for comparison)

---

**Note**: Always include error bars, confidence intervals, and statistical significance tests in your research paper graphs!

