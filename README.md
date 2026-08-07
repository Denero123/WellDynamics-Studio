# PyMudCement-Optima

PENG 258 Drilling Engineering 1 capstone implementation.

## Current scope

This Streamlit version implements the engineering functions directly supported by the supplied project specification:

- Hydrostatic pressure
- Required mud density for formation-pressure balance
- Mud-weight conversion to ppg
- Safe mud-density window from pore/fracture gradients
- Bingham-plastic shear stress
- Annular volume
- Open-hole excess
- Spacer/flush/displacement volume calculations
- ECD from supplied circulating pressure loss
- **ECD calculated directly from geometry and flow rate** via a Bingham-plastic
  annular friction model (`src/engineering/rheology.py`) -- annular velocity,
  Reynolds number, laminar/transitional/turbulent classification, frictional
  pressure drop, and a cuttings-transport screening check
- **Safe mud-weight window evaluated across a full depth-indexed pore-pressure /
  fracture-gradient profile** (`src/engineering/mud_weight_window.py`), not just
  a single depth -- linear interpolation between profile points, with
  OK/WARNING/CRITICAL severity grading against configurable safety margins
- Input validation
- Unit tests (36, all passing)

New capability is wired into `app.py` as two additional pages:
**"Annular Hydraulics (Physics-Based ECD)"** and **"MW Window (Depth Profile)"**.
The original five pages are unchanged.

## Important scope boundary

The project PDF requests dynamic pressure-drop modelling and live ECD tracking,
but does not specify one required pressure-loss correlation. This implementation
now offers both options: `hydraulics.py` still accepts a user-supplied
circulating pressure loss for anyone with measured/simulated data, while
`rheology.py` calculates that loss internally using a standard oilfield
Bingham-plastic annular friction model, so ECD can be produced from wellbore
geometry and flow rate alone.

The cuttings-transport check in `rheology.py` is a conservative screening
heuristic (higher YP -> lower minimum velocity), not a full slip-velocity
(e.g. Moore) correlation -- call this out as a stated modelling limitation in
the technical report rather than presenting it as rigorous.

Likewise, the PDF mentions an additive database, plug bumping pressure and P&A plug calculations, but does not provide the required database values or mathematical correlations. Those should be added only when validated project/company data or explicit equations are available.

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

## Tests

```bash
pytest -q
```

## Recommended production architecture

For the final project, keep the Streamlit UI thin and put engineering calculations in `src/engineering`. This makes the calculation layer independently testable and allows a future FastAPI/React interface to reuse the same validated engineering services.
