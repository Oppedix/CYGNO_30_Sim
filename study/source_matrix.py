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
V1_COMPONENTS = {
    'GEMsPolyimide': ('300ELJPolyimide', 'GEMs'), 'GEMsCopper': ('LaminateCopper', 'GEMs'),
    'RingSupports': ('Acrylic', 'Field Cage'), 'RingStrips': ('EFCu', 'Field Cage'),
    'CathodesPolyimide': ('300ELJPolyimide', 'Cathodes'),
    'CathodesCopper': ('LaminateCopper', 'Cathodes'), 'Vessel': ('EFCu', 'Vessel'),
    'Lens': ('Suprasil', 'Camera Lenses'), 'Sensors': ('Silicon', 'Camera Sensors'),
    'Resistors': ('Al2O3', 'Resistors'),
}
IONS = {'U238': (92, 238), 'Th232': (90, 232), 'K40': (19, 40),
        'U235': (92, 235), 'Ra226': (88, 226), 'Th228': (90, 228)}
MATRIX_MODELS = {'cygno-300elj-radioassay-v2': 'cygno-300elj-v2',
                 'cygno-300elj-radioassay-v3': 'cygno-acrylic-v3'}


# Arnquist et al., arXiv:1910.04317v1, sec. 2.2: specific activities in
# Bq/g of isotope (U/Th) or natural potassium (K, already includes abundance).
# These published conversion constants define this matrix version.
SPECIFIC_ACTIVITIES_BQ_G = {'U238': 12400.0, 'Th232': 4060.0, 'K40': 30.5}
ASSAYS = {
    '300ELJPolyimide': {'U238': [5.58, 0.16], 'Th232': [6.82, 0.09], 'K40': [108, 38]},
    'LaminateCopper': {'U238': [12, 13], 'Th232': [12, 12], 'K40': [130, 180]},
}
RETAINED_ACTIVITIES = {'Acrylic': {'U238': 0.000296, 'Th232': 5.69e-05, 'K40': 7.12e-05}, 'EFCu': {'U238': 1.31e-07, 'Th232': 3.4e-08}, 'Silicon': {'U238': 0.002, 'Th232': 0.0028, 'K40': 0.009}, 'Suprasil': {'U238': 0.000123, 'Th232': 4.07e-05, 'K40': 0.0003}, 'Al2O3': {'U238': 1e-06, 'Th232': 1.4e-07, 'K40': 1.2e-06, 'U235': 4e-08, 'Ra226': 1.8e-07, 'Th228': 1.3e-07}}
# v1 remains readable only through explicit historical validation.
COMPONENTS = V1_COMPONENTS | {
    'RingSupports': ('RadiopurePMMA', 'Field Cage'),
    'Resistors': ('CompletedMBNLResistor', 'Resistors'),
}
ACRYLIC_COMPONENTS = COMPONENTS | {
    'GEMsPolyimide': ('Acrylic', 'GEMs'), 'GEMsCopper': ('EFCu', 'GEMs'),
    'CathodesPolyimide': ('Acrylic', 'Cathodes'), 'CathodesCopper': ('EFCu', 'Cathodes'),
}
HISTORICAL_LAYERS = {
    'reference_matrix_id': 'thesis-table7.1-v1',
    'reference_matrix_sha256': 'de7eddc44076f0697d36a693894eb0d927da964770dc9762f684b34eb0a65836',
    'core_activity_Bq_kg': {'U238': .000296, 'Th232': 5.69e-5, 'K40': 7.12e-5},
    'copper_activity_Bq_kg': {'U238': 1.31e-7, 'Th232': 3.4e-8},
    'core_transport': 'PMMA, 1.190 g/cm3, 50 um; both GEM and cathode',
    'extension': 'Table 7.1 GEMsCore Acrylic also assigned to the cathode core; historical cathode was solid copper',
    'copper_K40': 'omitted table x; not a measured zero',
    'scope': 'new internal transport campaign required; not a normalization override for v2 ROOT files',
}
PMMA_ACTIVITIES = {'U238': 9.05e-6, 'Th232': 5.05e-6, 'K40': 71.2e-6}
RESISTOR_ASSAY = {'U238': [4.30, .20], 'Th232': [2.00, .16], 'K40': [7.90, .20]}
REFERENCE_RESISTOR = dict(length_mm=17., outer_diameter_mm=6., inner_diameter_mm=4., density_g_cm3=2.20)
PMMA_PROVENANCE = {
    'title': 'Mass Spectrometric Assay of High Radiopurity Solid Polymer Materials for Parts in Radiation and Rare Event Physics Detectors',
    'citation': 'I.J. Arnquist et al., NIM A 943 (2019) 162443',
    'doi': '10.1016/j.nima.2019.162443',
    'table': '1', 'manuscript_page': 7,
    'row': 'second Pre- set, sample 3, 0.1527 g (ninth data row)',
    'sample': 'UVT acrylic, Reynolds Polymer Technology, Inc.; solid 4 x 12 x 12 inch block',
    'form': 'finished solid stock; clean band-saw cubes, not raw precursor',
    'method': 'clean machining; detergent/DI/6M HNO3/DI cleaning; dry ashing in ULB EF-Cu boats; isotope-dilution ICP-MS with pre-ashing tracer',
    'U238': {'pg_g': .730, 'uBq_kg': 9.05, 'uncertainty': None, 'upper_limit': False},
    'Th232': {'pg_g': 1.23, 'uBq_kg': 5.05, 'uncertainty': None, 'upper_limit': False},
    'interpretation': 'central measurements, uncertainties not reported for this row; conservative replicate envelope: same row has maxima for both U and Th across all 12 Cu-boat determinations; adopt published activity columns without re-rounding their concentrations',
    'alternatives': 'Table 1 includes measured U 3.03-9.05 and Th 1.13-5.05 uBq/kg plus limits; Table 2 post-ashing agrees, pre-ashing quartz values are inflated by tracer loss (section 3.2 pp.6-8)',
    'K40': {'measured': False, 'uBq_kg': 71.2, 'basis': 'conservative-old-K-proxy', 'reference': 'retained thesis Table 7.1 Acrylic'},
    'design_status': 'adopted radiopure PMMA design material; not an assay of Samuele acrylic or the installed support batch',
}
RESISTOR_PROVENANCE = {
    'title': 'Novel High-Radiopurity Doped Amorphous Silicon Resistors for Low-Background Detectors',
    'citation': 'A. Anker et al., arXiv:2601.05985v2',
    'table': '9', 'page': 19, 'row': 'Prototype 2 MBNL - 2024, Completed',
    'radioassay_title': 'The nEXO Radioassay Program',
    'radioassay_citation': 'R. MacLellan et al., arXiv:2604.15406v1',
    'radioassay_table': 'IV', 'radioassay_page': 10, 'radioassay_row': 60,
    'sample': 'MBNL Heraeus Suprasil 300, aSi CVD at 550 C, Ti and Pd end metalized',
    'method': 'PNNL ICP-MS after full dissolution; uncertainties are analytical precision (Anker section 6 pp.17-19)',
    'concentrations': RESISTOR_ASSAY,
    'units': {'U238': 'ppt, early chain', 'Th232': 'ppt', 'K40': 'ppb natural K'},
    'sample_correspondence': 'same completed MBNL component technology and matching U/Th results; Anker reference 22 explicitly points to nEXO Table IV items 55-60. No unique specimen or batch identifier establishes identity. Composite publication basis; all U/Th/K are available together in nEXO row 60, with Anker providing geometry/process context',
    'chain_assumption': 'secular equilibrium for U/Th is a modelling assumption, not demonstrated by ICP-MS chain-head assays',
    'reference_geometry': REFERENCE_RESISTOR,
    'normalization': 'Bq/kg completed-component concentration times nominal reference tube mass -> effective Bq/reference-piece assigned to each compact CYGNO surrogate; coating and metal masses omitted',
    'transport_approximation': '1.6 x 0.55 x 3.2 mm fused-silica box at 2.20 g/cm3; not mechanically identical to nEXO tube; uniform source location cannot partition silica/aSi/metallization contamination',
}



def assay_activity(isotope, concentration):
    """pg/g U/Th or ng/g natural K -> Bq/kg; no thickness rescaling."""
    require(isotope in SPECIFIC_ACTIVITIES_BQ_G and positive(concentration), 'Invalid assay concentration')
    return concentration * (1e-6 if isotope == 'K40' else 1e-9) * SPECIFIC_ACTIVITIES_BQ_G[isotope]


def reference_resistor_mass_kg():
    r = REFERENCE_RESISTOR
    return math.pi*(r['outer_diameter_mm']**2-r['inner_diameter_mm']**2)/4*r['length_mm']*r['density_g_cm3']*1e-6


def resistor_activity(isotope):
    return assay_activity(isotope, RESISTOR_ASSAY[isotope][0])*reference_resistor_mass_kg()


def vessel_material_comparison(vessel_mass_kg, copper_density_g_cm3, pmma_density_g_cm3):
    """Use the actual constructed shell volume; same-volume replacement only."""
    require(all(positive(v) for v in (vessel_mass_kg, copper_density_g_cm3, pmma_density_g_cm3)), 'Invalid vessel comparison')
    volume_cm3 = vessel_mass_kg*1000/copper_density_g_cm3
    pmma_mass = volume_cm3*pmma_density_g_cm3/1000
    crossover = {i: RETAINED_ACTIVITIES['EFCu'][i]*vessel_mass_kg/pmma_mass for i in ('U238', 'Th232')}
    return dict(volume_cm3=volume_cm3, copper_mass_kg=vessel_mass_kg, pmma_mass_kg=pmma_mass,
                crossover_Bq_kg=crossover,
                pmma_clears_both=all(PMMA_ACTIVITIES[i]<crossover[i] for i in crossover),
                pmma_K_measured=PMMA_PROVENANCE['K40']['measured'], selected_material='EFCu')


def expected_contributions(*, historical=False, acrylic=False):
    components = V1_COMPONENTS if historical else ACRYLIC_COMPONENTS if acrylic else COMPONENTS
    return {(component, isotope) for component, (material, _) in components.items()
            for isotope in (PMMA_ACTIVITIES if material == 'RadiopurePMMA' else RESISTOR_ASSAY
                            if material == 'CompletedMBNLResistor' else ASSAYS.get(material) or RETAINED_ACTIVITIES[material])}


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


def validate_matrix(matrix, *, historical=False):
    v1 = historical and matrix.get('matrix_id') == 'cygno-300elj-radioassay-v1'
    acrylic = matrix.get('matrix_id') == 'cygno-300elj-radioassay-v3'
    components = V1_COMPONENTS if v1 else ACRYLIC_COMPONENTS if acrylic else COMPONENTS
    expected = expected_contributions(historical=v1, acrylic=acrylic)
    require(matrix.get('schema_version') == 1, 'Unsupported matrix schema')
    require(matrix.get('matrix_id') in ({'cygno-300elj-radioassay-v1'} if v1 else MATRIX_MODELS), 'Unsupported source matrix')
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
    if not v1:
        require(provenance.get('pmma') == PMMA_PROVENANCE and provenance.get('completed_resistor') == RESISTOR_PROVENANCE, 'Missing/changed v2 material provenance')
    if acrylic:
        require(provenance.get('historical_layers') == HISTORICAL_LAYERS, 'Missing/changed v3 layer provenance')
    rows = matrix.get('contributions', [])
    seen = set()
    for row in rows:
        component = row.get('component')
        require(component in components, 'Unknown/ambiguous source component')
        material, category = components[component]
        require((row.get('assay_material'), row.get('category')) == (material, category), 'Wrong assay/category mapping')
        isotope = ion_name(row.get('chain_start'))
        key = (component, isotope)
        require(key in expected, 'Unsupported component isotope')
        require(key not in seen and row.get('id') == '_'.join(key), 'Duplicate or malformed contribution ID')
        seen.add(key)
        require(positive(row.get('activity')), 'Activity must be finite and positive; omit x entries')
        require(row.get('activity_unit') == ('Bq/piece' if component == 'Resistors' else 'Bq/kg'), 'Wrong activity unit')
        require(row.get('activity_basis') == ('separate-material-assay' if material in ASSAYS else
                'upper-limit-used-as-value' if material == 'Acrylic' else
                'conservative-old-K-proxy' if material == 'RadiopurePMMA' and isotope == 'K40' else
                'measured-solid-pmma-conservative-replicate' if material == 'RadiopurePMMA' else
                'effective-completed-component-per-piece' if material == 'CompletedMBNLResistor' else 'table-value'), 'Wrong activity interpretation')
        expected_activity = (assay_activity(isotope, ASSAYS[material][isotope][0]) if material in ASSAYS
                             else PMMA_ACTIVITIES[isotope] if material == 'RadiopurePMMA'
                             else resistor_activity(isotope) if material == 'CompletedMBNLResistor'
                             else RETAINED_ACTIVITIES[material].get(isotope))
        require(expected_activity is not None and row['activity'] == expected_activity, 'Wrong nominal assay activity')
        require(row.get('full_chain') is True, 'Chain transport must be enabled, including split segments')
        stop = row.get('stop_before')
        expected_stop = {'U238': 'Ra226', 'Th232': 'Th228'}.get(isotope) if v1 and component == 'Resistors' else None
        require((ion_name(stop) if stop is not None else None) == expected_stop, 'Wrong stop-before boundary')
        policy = ('upper-segment' if expected_stop else 'lower-segment' if isotope in ('Ra226', 'Th228')
                  else 'single-parent' if isotope == 'K40' else 'equilibrium')
        require(row.get('chain_policy') == policy, 'Wrong chain policy')
        daughters = ([{'U238': 'Ra226', 'Th232': 'Th228'}[isotope]]
                     if (not v1 or component != 'Resistors') and isotope in ('U238', 'Th232') else [])
        require(row.get('equilibrium_daughters') == daughters, 'Equilibrium daughters must not become separate jobs')
    require(seen == expected, 'Missing/extra canonical source contributions')
    return matrix


def read_matrix(path, *, historical=False):
    return validate_matrix(json.loads(Path(path).read_text()), historical=historical)


def validate_matrix_model(matrix, model):
    require(MATRIX_MODELS.get(matrix['matrix_id']) == model, 'Source matrix/transport model mismatch; use a new matching campaign')


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
    require(layout in LAYOUTS and model in MATRIX_MODELS.values(), 'Unsupported constructed detector')
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
        if model == 'cygno-acrylic-v3' and component in ('GEMsPolyimide', 'CathodesPolyimide'):
            require(row['geometry_material'] == 'PMMA', 'v3 core transport must be PMMA')
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
