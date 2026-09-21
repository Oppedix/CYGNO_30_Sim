"""Read the published source specification and constructed quantities.

No jobs are launched here. Run scheduling, completion and primary accounting
belong to the study runner. Only the published matrix schema is accepted.
"""
import csv
import json
import math
from pathlib import Path

LAYOUTS = {'legacy-25x3', 'cygno-5x5x3-v1'}
COMPONENTS = {
    'GEMsCore': ('Acrylic', 'GEMs'), 'GEMsOuter': ('EFCu', 'GEMs'),
    'RingSupports': ('Acrylic', 'Field Cage'), 'RingStrips': ('EFCu', 'Field Cage'),
    'Cathodes': ('EFCu', 'Cathodes'), 'Vessel': ('EFCu', 'Vessel'),
    'Lens': ('Suprasil', 'Camera Lenses'), 'Sensors': ('Silicon', 'Camera Sensors'),
    'Resistors': ('Al2O3', 'Resistors'),
}
IONS = {'U238': (92, 238), 'Th232': (90, 232), 'K40': (19, 40),
        'U235': (92, 235), 'Ra226': (88, 226), 'Th228': (90, 228)}


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
    require(matrix.get('matrix_id') == 'thesis-table7.1-v1', 'Unsupported source matrix')
    require(matrix.get('seconds_per_year') == 31536000, 'Study year convention changed')
    require(matrix.get('quantity_policy') == 'constructed-component-mass-kg-or-placement-count', 'Invalid quantity policy')
    provenance = matrix.get('provenance', {})
    require(provenance.get('table') == '7.1' and len(provenance.get('sha256', '')) == 64,
            'Missing Table 7.1 provenance')
    rows = matrix.get('contributions', [])
    seen = set()
    for row in rows:
        component = row.get('component')
        require(component in COMPONENTS, 'Unknown/ambiguous source component')
        material, category = COMPONENTS[component]
        require((row.get('assay_material'), row.get('category')) == (material, category), 'Wrong assay/category mapping')
        isotope = ion_name(row.get('chain_start'))
        key = (component, isotope)
        require(key not in seen and row.get('id') == '_'.join(key), 'Duplicate or malformed contribution ID')
        seen.add(key)
        require(positive(row.get('activity')), 'Activity must be finite and positive; omit x entries')
        require(row.get('activity_unit') == ('Bq/piece' if component == 'Resistors' else 'Bq/kg'), 'Wrong activity unit')
        require(row.get('activity_basis') == ('upper-limit-used-as-value' if material == 'Acrylic' else 'table-value'), 'Wrong activity interpretation')
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
    expected = {(component, isotope) for component, (material, _) in COMPONENTS.items()
                for isotope in (IONS if component == 'Resistors' else
                                ('U238', 'Th232') if material == 'EFCu' else ('U238', 'Th232', 'K40'))}
    require(seen == expected and len(rows) == 26, 'Expected exactly 26 Table 7.1 contributions; no missing/extra chains')
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
    require(layout in LAYOUTS and model == 'code-compatible', 'Unsupported constructed detector')
    lines = Path(path).read_text().splitlines()
    headers = {}
    for line in lines:
        if line.startswith('# '):
            key, value = line[2:].split(':', 1)
            require(key not in headers, 'Duplicate quantities metadata')
            headers[key] = value.strip()
    for key, expected in {'layout': layout, 'detector-model': model,
                          'source-policy': 'historical', 'geometry-hash': geometry_hash}.items():
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
