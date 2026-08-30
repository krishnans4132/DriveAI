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
|  Driver Webcam |------->| Eye + Mouth Crops |------->| MobileNetV3-Small  |
|  (Video Feed)  |        | (MediaPipe/OpenCV)|        | Trained Models     |
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

The current comparison uses the processed YawDD and UTA-RLDD driver data with participant-disjoint train, validation, and test splits. Labels are provisional weak labels, so the reported results support a college prototype and still require independent human and real-driving validation.

The original videos, extracted frames, and local processed datasets are excluded from Git. See [Dataset Credits and Usage Notice](DATASET_CREDITS.md) for the required UTA-RLDD citation, the YawDD dataset and paper citations, official download links, privacy considerations, and the third-party licensing boundary.

## Team Model Ownership

| Member | Model | Why it was selected | Project purpose |
|---|---|---|---|
| **CB.SC.U4CSE23628** | **MobileNetV3-Small** | Smallest checkpoint and parameter count, with strong eye and mouth results | Deployment model for the live webcam demonstration |
| **CB.SC.U4CSE23603** | **EfficientNet-B0** | Efficient compound scaling provides a stronger accuracy/capacity comparison | Middle-weight accuracy-efficiency challenger |
| **CB.SC.U4CSE23717** | **ResNet-18** | A well-established residual CNN makes the experiment easy to explain and reproduce | Heavier reference model and accuracy ceiling |

## Locked Test Comparison

| Model | Parameters | Eye balanced accuracy | Mouth balanced accuracy | Deployment decision |
|---|---:|---:|---:|---|
| **MobileNetV3-Small** | **1.52 M** | 96.93% | 94.41% | **Selected for the webcam demo** |
| **EfficientNet-B0** | 4.01 M | 96.53% | 94.07% | Comparison challenger |
| **ResNet-18** | 11.18 M | **97.88%** | **95.57%** | Accuracy reference |

MobileNetV3-Small is deployed because it uses roughly 7.4× fewer parameters than ResNet-18 while remaining close on balanced accuracy. The comparison window also shows AP, recall, specificity, precision, F1, locked thresholds, checkpoint sizes, and per-member ownership.

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

### Backend Setup (Local Inference)

1. From the project root, use the existing environment:
   ```bash
   ./ml-env/bin/python backend/app.py
   ```
2. If recreating the environment, install the backend dependencies first:
   ```bash
   python -m pip install -r backend/requirements.txt
   ```
3. Then run the local API:
   ```bash
   python backend/app.py
   ```

Keep the backend terminal running, start the frontend in a second terminal with `npm run dev`, open the local address shown by Vite, and allow webcam access. Speed and continuous-drive time are intentionally simulated examiner controls. Rest-stop navigation uses a hardcoded offline demonstration map.

## Demo Safety Note

DriveAlert AI is a college prototype, not a certified automotive or medical safety device. The model results use provisional labels; the driver remains responsible for stopping safely and following applicable driving-hours rules.

## License

Original project code and documentation are available under the [MIT License](LICENSE). Third-party datasets are not included and are not covered by this license; see [Dataset Credits and Usage Notice](DATASET_CREDITS.md).
