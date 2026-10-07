"""Read the published source specification and constructed quantities.

No jobs are launched here. Run scheduling, completion and primary accounting
belong to the study runner. Only the published matrix schema is accepted.
"""
import csv
import json
import math
from pathlib import Path

# Counts are the Python file-validation contract; C++ derives placement counts.
LAYOUT_MODULE_COUNTS = {'legacy-25x3': 75, 'cygno-5x5x3-v1': 75, 'cygno-11x7-v1': 77}
LAYOUTS = set(LAYOUT_MODULE_COUNTS)
COMPONENTS = {
    'GEMsPolyimide': ('300ELJPolyimide', 'GEMs'), 'GEMsCopper': ('LaminateCopper', 'GEMs'),
    'RingSupports': ('Acrylic', 'Field Cage'), 'RingStrips': ('EFCu', 'Field Cage'),
    'CathodesPolyimide': ('300ELJPolyimide', 'Cathodes'),
    'CathodesCopper': ('LaminateCopper', 'Cathodes'), 'Vessel': ('EFCu', 'Vessel'),
    'Lens': ('Suprasil', 'Camera Lenses'), 'Sensors': ('Silicon', 'Camera Sensors'),
    'Resistors': ('Al2O3', 'Resistors'),
}
IONS = {'U238': (92, 238), 'Th232': (90, 232), 'K40': (19, 40),
        'U235': (92, 235), 'Ra226': (88, 226), 'Th228': (90, 228)}


# Arnquist et al., arXiv:1910.04317v1, sec. 2.2: specific activities in
# Bq/g of isotope (U/Th) or natural potassium (K, already includes abundance).
# These published conversion constants define this matrix version.
SPECIFIC_ACTIVITIES_BQ_G = {'U238': 12400.0, 'Th232': 4060.0, 'K40': 30.5}
ASSAYS = {
    '300ELJPolyimide': {'U238': [5.58, 0.16], 'Th232': [6.82, 0.09], 'K40': [108, 38]},
    'LaminateCopper': {'U238': [12, 13], 'Th232': [12, 12], 'K40': [130, 180]},
}
RETAINED_ACTIVITIES = {'Acrylic': {'U238': 0.000296, 'Th232': 5.69e-05, 'K40': 7.12e-05}, 'EFCu': {'U238': 1.31e-07, 'Th232': 3.4e-08}, 'Silicon': {'U238': 0.002, 'Th232': 0.0028, 'K40': 0.009}, 'Suprasil': {'U238': 0.000123, 'Th232': 4.07e-05, 'K40': 0.0003}, 'Al2O3': {'U238': 1e-06, 'Th232': 1.4e-07, 'K40': 1.2e-06, 'U235': 4e-08, 'Ra226': 1.8e-07, 'Th228': 1.3e-07}}


def assay_activity(isotope, concentration):
    """pg/g U/Th or ng/g natural K -> Bq/kg; no thickness rescaling."""
    require(isotope in SPECIFIC_ACTIVITIES_BQ_G and positive(concentration), 'Invalid assay concentration')
    return concentration * (1e-6 if isotope == 'K40' else 1e-9) * SPECIFIC_ACTIVITIES_BQ_G[isotope]


def expected_contributions():
    return {(component, isotope) for component, (material, _) in COMPONENTS.items()
            for isotope in (ASSAYS.get(material) or RETAINED_ACTIVITIES[material])}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def ion_name(ion):
    require(isinstance(ion, dict), 'Missing nucleus record')
    name = ion.get('name')
    require(name in IONS and (ion.get('Z'), ion.get('A')) == IONS[name], 'Invalid nucleus Z/A')
    return name


def validate_matrix(matrix):
    require(matrix.get('schema_version') == 1, 'Unsupported matrix schema')
    require(matrix.get('matrix_id') == 'cygno-300elj-radioassay-v1', 'Unsupported source matrix')
    require(matrix.get('seconds_per_year') == 31536000, 'Study year convention changed')
    require(matrix.get('quantity_policy') == 'constructed-component-mass-kg-or-placement-count', 'Invalid quantity policy')
    provenance = matrix.get('provenance', {})
    require(provenance.get('assay_reference') == 'https://arxiv.org/abs/1910.04317v1' and
            provenance.get('assay_table') == '5' and provenance.get('separate_assays') == ASSAYS and
            provenance.get('specific_activities_Bq_g') == SPECIFIC_ACTIVITIES_BQ_G,
            'Missing/changed separate assay provenance or conversion constants')
    require(provenance.get('retained_reference', {}).get('matrix_id') == 'thesis-table7.1-v1' and
            provenance['retained_reference'].get('sha256') == 'de7eddc44076f0697d36a693894eb0d927da964770dc9762f684b34eb0a65836',
            'Missing retained Table 7.1 matrix provenance')
    rows = matrix.get('contributions', [])
    seen = set()
    for row in rows:
        component = row.get('component')
        require(component in COMPONENTS, 'Unknown/ambiguous source component')
        material, category = COMPONENTS[component]
        require((row.get('assay_material'), row.get('category')) == (material, category), 'Wrong assay/category mapping')
        isotope = ion_name(row.get('chain_start'))
        key = (component, isotope)
        require(key in expected_contributions(), 'Unsupported component isotope')
        require(key not in seen and row.get('id') == '_'.join(key), 'Duplicate or malformed contribution ID')
        seen.add(key)
        require(positive(row.get('activity')), 'Activity must be finite and positive; omit x entries')
        require(row.get('activity_unit') == ('Bq/piece' if component == 'Resistors' else 'Bq/kg'), 'Wrong activity unit')
        require(row.get('activity_basis') == ('separate-material-assay' if material in ASSAYS else
                'upper-limit-used-as-value' if material == 'Acrylic' else 'table-value'), 'Wrong activity interpretation')
        expected_activity = (assay_activity(isotope, ASSAYS[material][isotope][0]) if material in ASSAYS
                             else RETAINED_ACTIVITIES[material].get(isotope))
        require(expected_activity is not None and row['activity'] == expected_activity, 'Wrong nominal assay activity')
        require(row.get('full_chain') is True, 'Chain transport must be enabled, including split segments')
        stop = row.get('stop_before')
        expected_stop = {'U238': 'Ra226', 'Th232': 'Th228'}.get(isotope) if component == 'Resistors' else None
        require((ion_name(stop) if stop is not None else None) == expected_stop, 'Wrong stop-before boundary')
        policy = ('upper-segment' if expected_stop else 'lower-segment' if isotope in ('Ra226', 'Th228')
                  else 'single-parent' if isotope == 'K40' else 'equilibrium')
        require(row.get('chain_policy') == policy, 'Wrong chain policy')
        daughters = ([{'U238': 'Ra226', 'Th232': 'Th228'}[isotope]]
                     if component != 'Resistors' and isotope in ('U238', 'Th232') else [])
        require(row.get('equilibrium_daughters') == daughters, 'Equilibrium daughters must not become separate jobs')
    require(seen == expected_contributions(), 'Missing/extra canonical source contributions')
    return matrix


def read_matrix(path):
    return validate_matrix(json.loads(Path(path).read_text()))


def decay_commands(row):
    """Controls only; explicitly reset a previous split-chain boundary to 0/0.

    stop_before kills the ground-state boundary ion BEFORE its radioactive
    decay; inherited excited-state de-excitation is retained. No isotope
    lifetimes, branching probabilities, time thresholds or datasets are changed.
    """
    start = row['chain_start']
    stop = row['stop_before'] or {'Z': 0, 'A': 0}
    return [f"/detector/RadElement {row['component']}",
            f"/isotope/AtomicNumber {start['Z']}", f"/isotope/MassNumber {start['A']}",
            '/rdecay01/fullChain true', f"/stopChain/ZStopDecay {stop['Z']}",
            f"/stopChain/AStopDecay {stop['A']}"]


def read_quantities(path, *, layout, model, geometry_hash):
    require(layout in LAYOUTS and model == 'cygno-300elj-v1', 'Unsupported constructed detector')
    lines = Path(path).read_text().splitlines()
    headers = {}
    for line in lines:
        if line.startswith('# '):
            key, value = line[2:].split(':', 1)
            require(key not in headers, 'Duplicate quantities metadata')
            headers[key] = value.strip()
    for key, expected in {'layout': layout, 'detector-model': model,
                          'source-policy': 'uniform-volume-v1', 'geometry-hash': geometry_hash}.items():
        require(headers.get(key) == expected, f'Quantities {key} mismatch')
    require(headers.get('provenance'), 'Missing constructed quantities provenance')
    result = {}
    for row in csv.DictReader((line for line in lines if not line.startswith('#')), delimiter='\t'):
        component = row['component']
        require(component in COMPONENTS and component not in result, 'Unknown/duplicate quantity component')
        mass, pieces = float(row['mass_kg']), int(row['pieces'])
        require(positive(mass) and pieces > 0 and row['geometry_material'], 'Invalid constructed quantity')
        result[component] = dict(mass_kg=mass, pieces=pieces, geometry_material=row['geometry_material'])
    require(result.keys() == COMPONENTS.keys(), 'Incomplete constructed quantities')
    return result


def quantity_for(row, quantities):
    """Select units, never use a resistor mass as its number of pieces."""
    unit = row['activity_unit']
    require(unit in ('Bq/kg', 'Bq/piece'), 'Unsupported activity unit')
    return quantities[row['component']]['mass_kg' if unit == 'Bq/kg' else 'pieces']


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('matrix', type=Path)
    args = parser.parse_args()
    matrix = read_matrix(args.matrix)
    print(f"Validated {matrix['matrix_id']}: {len(matrix['contributions'])} contributions; no jobs launched")
