# DriveAlert AI

**Real-time driver fatigue and microsleep monitoring with adaptive risk assessment and proactive rest intervention.**

DriveAlert AI is a college research prototype that uses a normal webcam, two trained MobileNetV3-Small classifiers, and a deterministic temporal safety engine to monitor eye closure and yawning. The system combines visual evidence with simulated vehicle speed and continuous-drive time, displays the progress toward each alert threshold, issues browser text-to-speech warnings, and offers a hardcoded demonstration route to a rest stop.

The repository also contains a controlled comparison of MobileNetV3-Small, EfficientNet-B0, and ResNet-18 using the same participant-disjoint evaluation protocol.

## Contents

- [Current project status](#current-project-status)
- [Key features and novelty](#key-features-and-novelty)
- [Team and model ownership](#team-and-model-ownership)
- [Model comparison](#model-comparison)
- [System architecture](#system-architecture)
- [Fatigue decision logic](#fatigue-decision-logic)
- [Installation](#installation)
- [Running the live demonstration](#running-the-live-demonstration)
- [Local API](#local-api)
- [Testing](#testing)
- [ML workflow and repository structure](#ml-workflow-and-repository-structure)
- [Datasets and attribution](#datasets-and-attribution)
- [Limitations and safety](#limitations-and-safety)
- [License](#license)

## Current Project Status

| Capability | Status | Notes |
|---|---|---|
| Three-model research comparison | Implemented | Interactive eye and mouth metric comparison |
| Real webcam capture | Implemented | Uses browser camera permission |
| Eye and mouth region extraction | Implemented | MediaPipe Face Mesh with an OpenCV fallback |
| MobileNetV3-Small live inference | Implemented | Separate eye-state and mouth-event checkpoints |
| Temporal fatigue engine | Implemented and tested | PERCLOS, sustained closure, repeated yawns, sensor validity |
| Speed-adaptive sensitivity | Implemented | Simulated speed changes temporal alert thresholds |
| Continuous-drive sensitivity | Implemented | Simulated drive duration increases vigilance |
| Alert queue monitor | Implemented | Shows current, next, and reached alert stages |
| Spoken warnings | Implemented | Browser text-to-speech; requires a user click to enable reliably |
| Rest-stop rerouting | Simulated | Hardcoded offline map to “Lakeside Rest Plaza” |
| Vehicle telemetry connection | Simulated | Speed and drive duration are examiner-controlled |

Only MobileNetV3-Small is loaded by the live application. EfficientNet-B0 and ResNet-18 remain research comparison models represented by their notebooks and compact evaluation reports.

## Key Features and Novelty

### 1. Proactive cognitive co-pilot

When live fatigue evidence reaches a warning or critical level, the interface presents an intervention, can speak the warning aloud, recommends a safe break, and offers a demonstration reroute to a predefined rest stop.

### 2. Velocity-context risk filter

Vehicle speed does not change the locked neural-network probability threshold. Instead, it increases the temporal safety-engine sensitivity so sustained eye closure and PERCLOS evidence trigger sooner in higher-risk driving contexts.

### 3. Continuous-drive sensitivity shift

The engine progressively increases sensitivity after two, four, and eight continuous driving hours. Speed and drive-time multipliers are combined, while safety floors prevent the effective thresholds from becoming unrealistically small.

### 4. Transparent alert queue

The live console displays continuous eye-closure duration, 60-second PERCLOS, five-minute yawn count, their effective thresholds, progress toward the next trigger, and the escalation sequence:

`Monitoring → Advisory → Warning → Critical`

### 5. Safe idle behavior

Vehicle speed defaults to `0 km/h`. At zero speed, frame inference and alert accumulation pause, the backend session resets, and the interface clearly reports that the fatigue model is idle.

## Team and Model Ownership

Each member trained and evaluated one architecture under the shared comparison protocol.

| Member ID | GitHub author | Model | Reason for selection | Role in the project |
|---|---|---|---|---|
| **CB.SC.U4CSE23628** | [krishnans4132](https://github.com/krishnans4132) | **MobileNetV3-Small** | Compact mobile architecture with strong results and the smallest runtime footprint | Selected deployment model for the webcam system |
| **CB.SC.U4CSE23603** | [Adwaith2207](https://github.com/Adwaith2207) | **EfficientNet-B0** | Compound scaling provides a meaningful accuracy-versus-efficiency challenger | Middle-weight research comparison |
| **CB.SC.U4CSE23717** | [Eric277-wq](https://github.com/Eric277-wq) | **ResNet-18** | Residual connections provide a strong, reproducible accuracy benchmark | Heavier reference model and accuracy ceiling |

## Model Comparison

### Experimental protocol

The comparison is designed around:

- the same participant-disjoint train, validation, and test splits;
- the same augmentation strategy and training budget;
- threshold selection using validation data only; and
- an untouched held-out test split for the reported comparison.

Two tasks are evaluated:

- **Eye state:** binary open-versus-closed classification.
- **Mouth event:** three-class not-yawn, talking, and yawn classification.

### Held-out test summary

| Architecture | Parameters | Eye ONNX | Eye balanced accuracy | Closed-eye recall | Mouth balanced accuracy | Yawn recall |
|---|---:|---:|---:|---:|---:|---:|
| **MobileNetV3-Small** | **1.52 M** | **5.80 MiB** | 96.93% | 97.31% | 94.41% | 91.04% |
| **EfficientNet-B0** | 4.01 M | 15.28 MiB | 96.53% | **98.39%** | 94.07% | 88.89% |
| **ResNet-18** | 11.18 M | 42.63 MiB | **97.88%** | **98.39%** | **95.57%** | **93.55%** |

The interactive comparison page additionally reports average precision, specificity, precision, F1, yawn balanced accuracy, validation-locked thresholds, checkpoint size, and model ownership.

### Deployment decision

MobileNetV3-Small is deployed because its 5.80 MiB eye ONNX model is approximately 7.3 times smaller than the ResNet-18 equivalent, while its held-out balanced accuracy remains close to the accuracy leader. This is the most practical accuracy, storage, and expected-latency tradeoff for a webcam demonstration on an ordinary laptop.

## System Architecture

```text
Browser webcam
      │ JPEG frame approximately every 700 ms
      ▼
Local HTTP API ──► MediaPipe Face Mesh / OpenCV fallback
      │                         │
      │                    eye and mouth crops
      ▼                         ▼
MobileNetV3-Small eye head + MobileNetV3-Small mouth head
      │
      │ probabilities + simulated speed + continuous-drive time
      ▼
Deterministic temporal fatigue engine
      │
      ├── sustained eye-closure duration
      ├── 60-second PERCLOS proxy
      ├── five-minute yawn-event count
      ├── sensor-validity monitoring
      └── speed and drive-time sensitivity scaling
      │
      ▼
Live dashboard ──► alert queue ──► spoken intervention ──► simulated rest route
```

### Main technologies

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Lucide icons, browser MediaDevices and Speech Synthesis APIs |
| Local API | Python standard-library HTTP server |
| Vision | MediaPipe, OpenCV, NumPy |
| Inference | PyTorch, TorchVision, MobileNetV3-Small |
| Evaluation | Jupyter notebooks, CSV histories, model cards, locked-threshold reports |

## Fatigue Decision Logic

The neural-network thresholds were selected on validation data and remain fixed during inference:

| Model signal | Locked threshold |
|---|---:|
| Eye closed probability | `0.060` |
| Yawn probability | `0.355` |

The temporal engine then evaluates the following configurable defaults:

| Temporal signal | Advisory/warning condition | Critical condition |
|---|---:|---:|
| Continuous eye closure | 1.50 seconds | 2.50 seconds |
| 60-second PERCLOS proxy | 15% | 25% |
| Yawn events in five minutes | 3 yawns | — |
| Minimum PERCLOS history | 20 seconds with at least 60% valid eye observations | — |
| Missing valid eye signal | Sensor unavailable after 2 seconds | — |

### Context sensitivity

- Speeds from `5` to `100 km/h` progressively increase the speed multiplier up to `1.35×`.
- Continuous driving applies `1.10×` from two hours, `1.25×` from four hours, and `1.40×` from eight hours.
- The combined multiplier reduces the required temporal duration and PERCLOS thresholds.
- Model probability thresholds stay locked; only the temporal decision policy adapts.

These values are engineering defaults for the prototype, not medical, legal, or automotive certification limits.

## Installation

### Prerequisites

- Node.js 18 or newer
- npm
- Python 3.10–3.12
- A webcam
- A modern browser with camera access; Chrome or Edge is recommended for the demonstration

### 1. Clone the repository

```bash
git clone https://github.com/krishnans4132/DriveAI.git
cd DriveAI
```

### 2. Install frontend dependencies

```bash
npm install
```

### 3. Create the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

The deployed MobileNet checkpoints are already stored under `ml/models/`. Raw datasets are not required to run the live demonstration.

## Running the Live Demonstration

### Terminal 1 — start the local inference API

```bash
source .venv/bin/activate
python backend/app.py
```

The backend starts at `http://127.0.0.1:5000` and loads the eye and mouth MobileNetV3-Small checkpoints once.

### Terminal 2 — start the frontend

```bash
npm run dev
```

Open the local address printed by Vite, normally `http://localhost:5173`.

### Demonstration sequence

1. Open **Launch Live Simulator** and allow webcam access.
2. Click **Enable voice alerts** once. This user interaction allows browser speech output and plays a confirmation message.
3. Notice that speed begins at `0 km/h` and the fatigue model is idle.
4. Increase the vehicle speed to begin frame inference.
5. Adjust continuous-drive time to demonstrate the sensitivity multiplier.
6. Watch the alert queue and the three live evidence bars approach their effective thresholds.
7. Use **Demo yawn alert** or **Demo microsleep** for a reliable examiner-controlled intervention.
8. Play or replay the spoken warning from the intervention window.
9. Choose **Start safe reroute** to activate the hardcoded offline route.
10. Use reset to return speed to zero, clear the session, and restore the idle state.

### Custom backend address

The frontend uses `http://127.0.0.1:5000` by default. To use another address, create `.env.local` in the project root:

```dotenv
VITE_API_URL=http://127.0.0.1:5000
```

Restart the Vite development server after changing this value.

### Common demonstration issues

| Problem | Resolution |
|---|---|
| “Start local API” appears | Start `python backend/app.py` and confirm port 5000 is available |
| Camera unavailable | Allow camera permission, close other apps using the webcam, and reload |
| No spoken warning | Click **Enable voice alerts**, check browser/system volume, and confirm Speech Synthesis support |
| Model remains idle | Increase the simulated vehicle speed above zero |
| Face signal unavailable | Face the camera directly and improve lighting or reduce occlusion |

## Local API

The backend accepts local JSON requests and enables CORS for the demonstration frontend.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/status` | Confirm runtime status, model metadata, and face-extraction backend |
| `POST` | `/api/analyze_frame` | Analyze one base64-encoded camera frame with telemetry context |
| `POST` | `/api/session/reset` | Clear accumulated temporal evidence for one session |

### Analyze-frame request

```json
{
  "session_id": "drivealert-demo",
  "frame": "data:image/jpeg;base64,...",
  "speed_kph": 60,
  "continuous_drive_minutes": 180
}
```

The response includes face status, normalized eye and mouth boxes, raw model probabilities and labels, temporal decision metrics, effective thresholds, alert reasons, recommended action, telemetry, and inference time.

## Testing

### Frontend production build

```bash
npm run build
```

### Backend unit and checkpoint tests

```bash
source .venv/bin/activate
python -m unittest discover -s backend/tests -v
```

The backend suite currently covers temporal accumulation, sustained-closure escalation, PERCLOS validity, yawn-event counting, non-monotonic timestamps, speed and drive-time sensitivity, preprocessing, checkpoint loading, and probability output.

## ML Workflow and Repository Structure

```text
DriveAI/
├── backend/
│   ├── app.py                 # Local HTTP inference service
│   ├── model_runtime.py       # MobileNet loading and prediction
│   ├── vision.py              # Face, eye, and mouth crop extraction
│   ├── fatigue_engine.py      # Temporal and context-aware decision policy
│   ├── detect_fatigue.py      # Compatibility facade
│   └── tests/                 # Backend unit and model-runtime tests
├── ml/
│   ├── notebooks/             # One training/comparison notebook per architecture
│   ├── models/                # Deployed MobileNet checkpoints and reports
│   ├── results/               # Compact EfficientNet and ResNet evaluation evidence
│   ├── scripts/               # Extraction, labeling, splitting, and packaging tools
│   ├── annotation_app.py      # Local review/annotation server
│   └── annotation_ui.html     # Annotation interface
├── src/
│   ├── components/            # Landing, comparison, webcam, telemetry, and alerts
│   ├── data/                  # Locked comparison values
│   └── utils/speech.js        # Browser text-to-speech helper
├── DATASET_CREDITS.md
├── LICENSE
└── README.md
```

### Reproducing the data workflow

The active `v2` scripts represent the current preprocessing flow:

1. `01_extract_features_v2.py` extracts face-derived features and model crops.
2. `02_build_annotation_queue_v2.py` creates a balanced manual-review queue.
3. `annotation_app.py` and `annotation_ui.html` support local label review.
4. `03_build_weak_labels_and_splits_v2.py` creates weak labels and participant-disjoint splits.
5. `04_package_kaggle_v2.py` packages local processed data for the training environment.
6. `build_comparison_notebooks.py` generates aligned architecture notebooks.

Use `python <script> --help` for supported arguments where available. Local dataset paths and generated packages are intentionally excluded from Git. The older non-`v2` scripts remain as historical pipeline references.

## Datasets and Attribution

The experiments use locally obtained data from:

- [UTA Real-Life Drowsiness Dataset (UTA-RLDD)](https://sites.google.com/view/utarldd/home)
- [Yawning Detection Dataset (YawDD)](https://ieee-dataport.org/open-access/yawdd-yawning-detection-dataset)

The original videos, extracted frames, processed datasets, and packaged export archives are not stored in this repository. The reported results use provisional weak labels and must not be presented as independently verified real-world performance.

See [DATASET_CREDITS.md](DATASET_CREDITS.md) for the required UTA-RLDD paper citation, YawDD dataset and paper citations, privacy notes, official download links, and the third-party licensing boundary.

## Limitations and Safety

- This is a college prototype, not a certified automotive, medical, or occupational-safety system.
- The project has not been validated in a moving vehicle or across production driving conditions.
- Speed and continuous-drive time are simulated and are not connected to a vehicle CAN bus, GPS receiver, or fleet platform.
- The rest-stop route is a hardcoded offline visual demonstration, not real navigation.
- Browser text-to-speech availability and voice selection depend on the operating system and browser.
- Webcam accuracy can degrade with poor lighting, extreme head pose, occlusion, camera blur, or missing faces.
- Dataset labels are provisional weak labels; independent human annotation and real-driving evaluation are required.
- The driver remains responsible for stopping safely and following applicable traffic and driving-hours rules.

## License

Original project code and documentation are released under the [MIT License](LICENSE).

Third-party datasets are not included and are not covered by the MIT License. Dataset access, use, and any redistribution of derived artifacts remain subject to the original providers’ current terms; see [DATASET_CREDITS.md](DATASET_CREDITS.md).
