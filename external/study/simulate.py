#!/usr/bin/env python3
"""One environmental spectrum per immutable, resumable campaign; no ROOT dependency."""
import argparse
from pathlib import Path
import re
import shutil
import sys
import time
if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from external.study.config import load, validate, macro, rate, PHYSICS, REPO
from study import runtime as rt
from study.source_matrix import require
from study.campaign import inside


def environment(log):
    values={}
    for line in log.splitlines():
        if line.startswith('CYGNO_ENV '):
            _,key,value=line.split(' ',2)
            require(key not in values,'Duplicate environment marker')
            values[key]=value
    require(set(values)=={*rt.ENV_KEYS,'source_hash','geometry_hash','geant4','physics','radioactive_decay_time_threshold_s'}, 'Missing environment')
    require(values['physics']==PHYSICS+'+G4RadioactiveDecayPhysics' and all(values[k]!='UNRESOLVED' for k in rt.ENV_KEYS), 'Wrong external physics/datasets')
    radius=re.findall(r'^CYGNO_EXTERNAL radius_mm (\S+)$',log,re.M)
    hashes=re.findall(r'^CYGNO_EXTERNAL geometry_hash (\S+)$',log,re.M)
    require(len(radius)==len(hashes)==1,'Missing external geometry identity')
    return values,float(radius[0]),hashes[0]


def check_campaign(output):
    c=rt.read(output/'campaign.json')
    require(c['external_campaign_version']==1 and c['status']=='complete', 'Not a completed external campaign')
    identity=c['identity']; cfg=validate(identity['config'])
    require(c['fingerprint']==rt.object_digest(identity), 'External identity fingerprint mismatch')
    require(rt.read(output/'config.json')==cfg and rt.digest(output/'geometry.json')==c['geometry_sha256'], 'Snapshot mismatch')
    for name,checksum in identity['source']['files_sha256'].items():
        if checksum!='missing':
            require(rt.digest(inside(output/'source',name))==checksum,'Source snapshot mismatch: '+name)
    attempt=inside(output,c['attempt'])
    require(rt.read(attempt/'manifest.json')==c,'Attempt/campaign manifest mismatch')
    rt.check_artifacts(attempt,c)
    require((attempt/'run.mac').read_text()==macro(cfg), 'Macro/config mismatch')
    log=(attempt/'simulation.log').read_text(errors='replace')
    env,radius,geometry_hash=environment(log)
    require(env==identity['environment'] and radius==identity['source_radius_mm'] and geometry_hash==identity['external_geometry_hash'], 'Transport identity mismatch')
    accounting=rt.parse_accounting(log,cfg['primaries'])
    require(accounting==c['accounting'], 'Accounting mismatch')
    receipt=rt.read(attempt/'simulation.command.json')
    require(receipt.get('returncode')==0 and not receipt.get('interrupted') and not receipt.get('timed_out'), 'Incomplete transport receipt')
    data=inside(attempt,c['data_path'])
    require(data.parent==attempt/'outfiles_V2' and data.stat().st_size>0, 'Invalid output path')
    require(c['incident_rate_s']==rate(cfg,radius), 'Normalization mismatch')
    return c,data


def run(args):
    cfg=load(args.config)
    for key in ('primaries','seed','shield','output_mode'):
        if getattr(args,key) is not None:cfg[key]=getattr(args,key)
    validate(cfg)
    if args.dry_run:
        print(macro(cfg));return 0
    require(args.build and args.output,'--build and --output are required')
    build,output=args.build.resolve(),args.output.resolve()
    simulation,exporter=build/'rdecay01',build/'geometry_quantities'
    require(simulation.is_file() and exporter.is_file(),'Build the common Geant4 application first')
    with rt.locked(output):
        probe=output/'probes'/str(time.time_ns());probe.mkdir(parents=True)
        (probe/'probe.mac').write_text('/control/echo EXTERNAL_ENVIRONMENT_PROBE\n')
        options=['1','--mode','external','--shield',cfg['shield'],'--layout',cfg['layout'],'--output-mode',cfg['output_mode']]
        log=rt.invoke([simulation,probe/'probe.mac',*options],probe,'environment',120)
        env,radius,geometry_hash=environment(log)
        require(env['source_hash']==rt.compiled_source_hash() and env['geometry_hash']==rt.digest(REPO/'common/DetectorGeometry.hh') and
                geometry_hash==rt.digest(REPO/'common/ExternalGeometry.hh'), 'Stale binary; rebuild')
        identity=dict(config=cfg,environment=env,source_radius_mm=radius,external_geometry_hash=geometry_hash,
                      executable_sha256=rt.digest(simulation),source=rt.source_state(),datasets=rt.dataset_state(env))
        fingerprint=rt.object_digest(identity)
        path=output/'campaign.json'
        if path.exists():
            campaign=rt.read(path)
            require(campaign['fingerprint']==fingerprint and campaign['identity']==identity,'Campaign identity changed; use a new directory')
            if campaign['status']=='complete':
                check_campaign(output);print('Reused complete external campaign: '+str(output));return 0
            require(args.retry_failed,'Previous attempt retained; use --retry-failed to create a new attempt')
        else:
            rt.save(output/'config.json',cfg)
            rt.invoke([exporter,output/'quantities.tsv',cfg['layout'],output/'geometry.json'],probe,'geometry',120)
            geometry=rt.read(output/'geometry.json')
            require(geometry['source_hash']==env['source_hash'],'Stale geometry exporter')
            for name,checksum in identity['source']['files_sha256'].items():
                if checksum!='missing':
                    target=output/'source'/name;target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(REPO/name,target)
            campaign=dict(external_campaign_version=1,identity=identity,fingerprint=fingerprint,
                          geometry_sha256=rt.digest(output/'geometry.json'))
        number=max([int(p.name.split('-')[1]) for p in output.glob('attempt-*')] or [0])+1
        attempt=output/f'attempt-{number:04d}';attempt.mkdir()
        campaign.pop('error',None)
        campaign.update(status='running',attempt=attempt.name,incident_rate_s=rate(cfg,radius))
        rt.save(path,campaign)
        try:
            (attempt/'run.mac').write_text(macro(cfg))
            log=rt.invoke([simulation,attempt/'run.mac',*options],attempt,'simulation',cfg['timeout_seconds'],
                          contribution=cfg['id'],primaries=cfg['primaries'])
            require(environment(log)==(env,radius,geometry_hash),'Environment changed during transport')
            campaign['accounting']=rt.parse_accounting(log,cfg['primaries'])
            roots=list((attempt/'outfiles_V2').glob('*.root'))
            require(len(roots)==1 and roots[0].name in (cfg['output_mode']+'.root',cfg['output_mode']+'_t0.root') and roots[0].stat().st_size>0,'Expected one nonempty single-worker file')
            campaign.update(data_path=str(roots[0].relative_to(attempt)),status='complete')
        except (ValueError,RuntimeError,OSError,KeyboardInterrupt) as error:
            campaign.update(status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',error=str(error))
            raise
        finally:
            campaign['artifacts']=rt.artifacts(attempt)
            rt.save(attempt/'manifest.json',campaign);rt.save(path,campaign)
        check_campaign(output)
        print('External campaign complete; physical assumptions remain: '+cfg['scientific_status'])
        return 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--build',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--primaries',type=int);p.add_argument('--seed',type=int)
    p.add_argument('--shield',choices=('none','copper20'))
    p.add_argument('--output-mode',choices=('raw','compact','both'))
    p.add_argument('--retry-failed',action='store_true');p.add_argument('--dry-run',action='store_true')
    try:return run(p.parse_args())
    except KeyboardInterrupt:return 130
    except (ValueError,RuntimeError,OSError,KeyError) as e:
        print('External simulation: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
