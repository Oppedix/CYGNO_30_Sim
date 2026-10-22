"""External source contract. Probabilities are bin integrals, never flux densities."""
import math
from pathlib import Path
import re
from study import runtime as rt
from study.source_matrix import require, LAYOUTS

REPO = rt.REPO
PROCESSING = 'external-track-volumes-v1'
PHYSICS = 'QGSP_BIC_HP_EMZ'
FIELDS = {'schema_version','mode','id','layout','shield','output_mode','primaries','seed',
          'timeout_seconds','scientific_status','particle','hall','flux_cm2_s','flux_convention',
          'energy_edges_MeV','bin_probabilities','shape_assumption','reference'}


def validate(config):
    require(set(config)==FIELDS and config['schema_version']==1 and config['mode']=='external', 'Invalid external config schema')
    require(isinstance(config['id'],str) and re.fullmatch(r'[a-zA-Z0-9_-]+',config['id']), 'Unsafe source ID')
    require(config['layout'] in LAYOUTS and config['shield'] in ('none','copper20'), 'Invalid layout/shield')
    require(config['output_mode'] in ('raw','compact','both') and config['particle'] in ('gamma','neutron'), 'Invalid source/output mode')
    for key,maximum in [('primaries',2147483647),('seed',2000000000),('timeout_seconds',2147483647)]:
        require(type(config[key]) is int and 1<=config[key]<=maximum, 'Invalid '+key)
    require(config['flux_convention'] in ('scalar','inward_current'), 'Specify scalar or inward_current flux')
    require(type(config['flux_cm2_s']) in (int,float) and math.isfinite(config['flux_cm2_s']) and config['flux_cm2_s']>0, 'Invalid flux')
    edges,weights=config['energy_edges_MeV'],config['bin_probabilities']
    require(isinstance(edges,list) and isinstance(weights,list) and 1<=len(weights)<=1023 and len(edges)==len(weights)+1, 'Invalid spectrum size')
    require(all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in edges+weights), 'Invalid spectrum value')
    require(all(a<b for a,b in zip(edges,edges[1:])) and edges[-1]<=2000, 'Invalid energy edges')
    require(math.isclose(sum(weights),1.,rel_tol=0,abs_tol=1e-12), 'Bin probabilities must sum to one')
    require(all(isinstance(config[k],str) and config[k].strip() for k in ('hall','scientific_status','shape_assumption','reference')), 'Missing physical provenance')
    require('\n' not in config['scientific_status'] and '\r' not in config['scientific_status'], 'Scientific status must be one macro-comment line')
    return config


def load(path):
    return validate(rt.read(Path(path)))


def macro(config):
    validate(config)
    seeds=rt.seeds_for(config['seed'],config['id'])
    lines=['# External source: '+config['id'], '# '+config['scientific_status'],
           '/run/verbose 0','/event/verbose 0','/tracking/verbose 0','/run/printProgress 10000',
           '/random/setSeeds '+' '.join(map(str,seeds)), '/output/OutFile '+config['output_mode'],
           '/gps/particle '+config['particle'], '/gps/ene/type User', '/gps/hist/type energy',
           '/gps/hist/point '+format(config['energy_edges_MeV'][0],'.17g')+' 0']
    # GPS User histogram weights are bin probabilities: widths have ALREADY been integrated.
    lines += [f'/gps/hist/point {edge:.17g} {weight:.17g}' for edge,weight in zip(config['energy_edges_MeV'][1:],config['bin_probabilities'])]
    return '\n'.join(lines+[f'/run/beamOn {config["primaries"]}',''])


def rate(config,radius_mm):
    require(math.isfinite(radius_mm) and radius_mm>0, 'Invalid source radius')
    area=4*math.pi*(radius_mm/10)**2
    return config['flux_cm2_s']*area/(4 if config['flux_convention']=='scalar' else 1)
