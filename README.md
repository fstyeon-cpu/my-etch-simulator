# SiO2 Etch Process Simulator (Prototype)

## Included files
- `app.py`: Streamlit UI and charts
- `etch_model.py`: calculation functions and input validation
- `requirements.txt`: Python package dependencies

## Run on Windows
1. Install Python (recommended: a current Streamlit-supported Python version) and VS Code.
2. Open this folder in VS Code.
3. Open Terminal > New Terminal.
4. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

5. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

6. Start the app:

```bash
python -m streamlit run app.py
```

The app should open in a browser. Stop it with `Ctrl+C` in the terminal.

## Model
The etch-rate formula is the team's initial additive empirical model. The program restricts inputs to:
- RF Power: 500–700 W
- Pressure: 500–900 mTorr
- Etching time: 0.5–3.0 min

Etch depth is calculated as `etch rate * etching time`.

## Important limitations
This is a prototype, not a validated production process model. There are only five reported experimental points, and the additive assumption ignores RF-power/pressure interactions. The wafer non-uniformity and yield model are intentionally not implemented yet.
