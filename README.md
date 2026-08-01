# DriveAlert AI
**Real-Time Driver Fatigue and Microsleep Detection for Commercial Transport Safety**

DriveAlert AI is a proactive cognitive co-pilot designed to monitor commercial drivers for fatigue and microsleep incidents in real-time. Moving beyond traditional hardware-heavy infrared monitoring, DriveAlert AI leverages a software-first approach using standard dashcams and webcams to dynamically assess driver state and intervene before accidents occur.

## Key Features & Novelties
1. **Proactive Cognitive Co-Pilot with Dynamic Rest-Rerouting:** Verbal text-to-speech intervention and automatic rest-stop navigation upon fatigue detection.
2. **Speed-Adaptive Risk Thresholding (Velocity-Context Filter):** Dynamic adjustment of eye-closure thresholds based on vehicle speed.
3. **Dynamic Continuous-Drive Sensitivity Shift:** Automatic multiplier on fatigue sensitivity based on continuous hours driven.

## System Architecture

```
+----------------+        +-------------------+        +--------------------+
|                |        |                   |        |                    |
|  Driver Webcam |------->|  Face/Eye Tracker |------->| Fatigue Detection  |
|  (Video Feed)  |        |  (EAR & PERCLOS)  |        | Model (MobileNet)  |
|                |        |                   |        |                    |
+----------------+        +-------------------+        +---------+----------+
                                                                 |
+----------------+        +-------------------+                  |
|                |        |                   |                  |
|  Vehicle Speed |------->| Velocity Context  |<-----------------+
|  (Telemetry)   |        | Filter            |                  |
|                |        |                   |                  |
+----------------+        +-------------------+                  |
                                                                 v
+----------------+        +-------------------+        +--------------------+
|                |        |                   |        |                    |
| Drive Time     |------->| Sensitivity Shift |------->| Proactive Co-Pilot |
| (Shift Clock)  |        | Multiplier        |        | (TTS & Navigation) |
|                |        |                   |        |                    |
+----------------+        +-------------------+        +--------------------+
```

## Dataset Details
The models have been trained and evaluated on three primary benchmark datasets for fatigue detection:
- **YawDD (Yawning Detection Dataset):** Video clips of various drivers yawning under different conditions.
- **UTA-RLDD (Real-Life Drowsiness Dataset):** Multi-stage drowsiness classification (Alert, Low Vigilance, Drowsy).
- **DDD (Drowsiness Detection Dataset):** Diverse lighting and occlusion scenarios, critical for night-time and glasses-wearing driver detection.

## Model Evaluation Benchmarks

| Model             | Accuracy | Inference Time (ms) | Params (M) | Notes                        |
|-------------------|----------|---------------------|------------|------------------------------|
| **MobileNetV2**   | 94.2%    | 12.5                | 3.4        | **Selected (Optimal Edge)**  |
| **EfficientNet-B0**| 95.8%   | 18.2                | 5.3        | High accuracy, slightly slower|
| **ResNet-18**     | 93.5%    | 25.1                | 11.2       | Baseline architecture        |

## Installation & Setup

### Prerequisites
- Node.js (v18+)
- Python (3.9+)

### Frontend Setup (Simulator Dashboard)
1. Navigate to the project root directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

### Backend Setup (Microservice)
1. Navigate to the `backend/` directory.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API service:
   ```bash
   python app.py
   ```
