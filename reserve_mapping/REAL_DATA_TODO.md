# Real-mode data: what's still missing

`geological_labels_template.csv` only has headers - real mode (`--mode real`)
has never actually been run, only demo mode has. This is the one part of
Reserve Mapping that isn't finished by writing more code; it needs actual
validated points.

## What's needed
At least a few rows of **validated** mineralized and barren observations for
the Balaghat study area, in the schema `geo_labels.py` enforces:
`obs_id, lat, lon, label_class (mineralized|barren), evidence_type, source, [mn_pct], [notes]`.

You need **both** classes with real coordinates - `step3_train_model.py` can't
train a classifier on one class only.

## Leads on the "mineralized" side (need verification, not ready to use as-is)
Public sources (a 2024-25 Ministry of Steel reply on steel.gov.in, and MOIL's
own filings) confirm MOIL operates four mines in the Balaghat Parliamentary
Constituency - Balaghat, Tirodi, Sitapatore and Ukwa - plus mines in
neighbouring Nagpur/Bhandara districts (Kandri, Munsar, Beldongri, Gumgaon,
Chikla, Dongri Buzurg). An active/historic mine working is reasonable
`evidence_type` for a mineralized point - but I did not find precise,
citable lat/lon for each mine site in general web search, so I have **not**
added these as rows in the CSV. Putting in approximate coordinates and
labelling them "validated" would undermine exactly the evidence discipline
this module is built around (see `geo_labels.py`'s docstring).

To finish this properly:
1. Pull precise coordinates for each mine's lease/pit area from GSI Bhukosh
   (bhukosh.gsi.gov.in), MOIL's environmental clearance filings (mine
   boundaries are usually given as lease-area coordinates), or Google Earth
   by locating the visible pit/headgear at each named mine.
2. For **barren** points, you need actual tested-and-negative ground -
   borehole logs or mapped traverses outside the ore body. This typically
   isn't public; it would come from MOIL/GSI exploration reports if the team
   has access, or from a geology-team member who can read a published
   geological map of the belt and pick genuinely off-belt control points.
3. Fill the rows into `geological_labels_template.csv` (copy it to
   `data/geological_labels.csv`), then run:
   `python run_pipeline.py --mode real --labels data/geological_labels.csv`
   (needs Member 1's `data/features.csv` to exist too).

If real points can't be sourced in time, demo mode is a legitimate fallback
for the jury demo - just keep saying "prospectivity" and keep the DEMO banner
visible, which the code already does automatically.
