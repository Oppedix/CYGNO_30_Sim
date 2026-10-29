"""Exercise the actual Stage A CLI orchestration with synthetic transport only."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from study import runtime as rt, simulate
from study.source_matrix import read_matrix
from fixtures import campaign_fixture, environment, fake_invoke


class WorkflowTests(unittest.TestCase):
    def test_archived_analysis_source_without_git(self):
        from study.analyze import analysis_source_state
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source/'study').mkdir()
            (source/'study/analyze.py').write_text('# isolated source fixture\n')
            with patch.object(rt, 'REPO', source), patch.object(rt, 'source_state', side_effect=AssertionError('Git must not run')):
                provenance = analysis_source_state()
            self.assertIsNone(provenance['revision'])
            self.assertEqual(provenance['files_sha256'], {'study/analyze.py': rt.digest(source/'study/analyze.py')})

    def test_v4_and_historical_cli_select_matching_matrix_and_transport(self):
        for model,matrix_id,count in [('cygno-copper-cathode-v4','cygno-radioassay-v4',23),
                                      ('cygno-acrylic-v3','cygno-300elj-radioassay-v3',26)]:
            with tempfile.TemporaryDirectory() as d:
                base=Path(d);template=base/'template'
                config,_,_=campaign_fixture(template,model)
                config_path=base/'config.json';rt.save(config_path,config)
                build=base/'build';build.mkdir()
                for name in ('rdecay01','geometry_quantities','CMakeCache.txt'):
                    (build/name).write_text('fixture')
                env=environment();seen=[]
                def invoke(command,cwd,label,timeout,**options):
                    self.assertEqual(command[-2:],['--model',model])
                    seen.append(label)
                    if label=='environment':return '\n'.join('CYGNO_ENV '+k+' '+v for k,v in env.items())
                    if label=='quantities':
                        Path(command[1]).write_bytes((template/'quantities.tsv').read_bytes())
                        Path(command[3]).write_bytes((template/'geometry.json').read_bytes())
                        return ''
                    return fake_invoke(command,cwd,label,timeout,**options)
                def preflight(build,output,model):
                    self.assertEqual(model,config['model'])
                    output.mkdir();rt.save(output/'preflight.json',rt.read(template/'preflight/preflight.json'))
                    return 0
                args=simulate.parser().parse_args(['--config',str(config_path),'--build',str(build),
                    '--output',str(base/'campaign'),'--only','Lens_K40'])
                with patch.object(rt,'invoke',side_effect=invoke),patch.object(rt,'dataset_state',return_value={}), \
                     patch.object(rt,'source_state',return_value={'files_sha256':{}}), \
                     patch.object(rt,'compiled_source_hash',return_value=env['source_hash']), \
                     patch('study.preflight.check',side_effect=preflight):
                    self.assertEqual(simulate.run(args),2)
                document=rt.read(args.output/'campaign.json')
                self.assertEqual(document['coverage'],f'1/{count}')
                self.assertEqual(document['identity']['matrix']['matrix_id'],matrix_id)
                self.assertEqual(seen,['environment','quantities','simulation'])

    def test_cli_statistics_resume_identity_and_gate(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            fixture=base/'template';campaign_fixture(fixture)
            build=base/'build';build.mkdir()
            for name in ('rdecay01','geometry_quantities','CMakeCache.txt'):
                (build/name).write_text('test fixture')
            env=environment()
            calls=[]
            def invoke(command,cwd,label,timeout,**options):
                self.assertEqual(command[-2:],['--model','cygno-300elj-v2'])
                calls.append(label)
                if label=='environment':
                    return '\n'.join('CYGNO_ENV '+k+' '+v for k,v in env.items())
                if label=='quantities':
                    Path(command[1]).write_bytes((fixture/'quantities.tsv').read_bytes())
                    Path(command[3]).write_bytes((fixture/'geometry.json').read_bytes())
                    return ''
                return fake_invoke(command,cwd,label,timeout,**options)
            def preflight(build,output,model):
                self.assertEqual(model,'cygno-300elj-v2')
                output.mkdir()
                rt.save(output/'preflight.json',rt.read(fixture/'preflight/preflight.json'))
                return 0
            args=simulate.parser().parse_args(['--config',str(rt.REPO/'config/study/historical/smoke-A-v2.json'),'--build',str(build),'--output',str(base/'one-million'),
                                              '--primaries','1000000','--only','Lens_K40'])
            with patch.object(rt,'invoke',side_effect=invoke), patch.object(rt,'dataset_state',return_value={}), \
                 patch.object(rt,'source_state',return_value={'files_sha256':{}}), \
                 patch.object(rt,'compiled_source_hash',return_value=env['source_hash']), \
                 patch('study.preflight.check',side_effect=preflight):
                self.assertEqual(simulate.run(args),2)  # one contribution remains partial
                self.assertEqual(calls.count('simulation'),1)
                self.assertEqual(simulate.run(args),2)
                self.assertEqual(calls.count('simulation'),1)  # reused
                campaign=rt.read(args.output/'campaign.json')
                self.assertEqual(campaign['coverage'],'1/28')
                self.assertEqual(campaign['identity']['config']['primaries_per_job'],1_000_000)
                args.primaries=1000000
                for mode in ('compact','both'):
                    args.output_mode=mode
                    with self.assertRaisesRegex(ValueError,'identity changed'): simulate.run(args)
                args.output_mode='raw'
                args.primaries=2
                with self.assertRaisesRegex(ValueError,'identity changed'): simulate.run(args)
                args.output=base/'failed-preflight'
                failed=rt.read(fixture/'preflight/preflight.json')
                failed['checks']['th232-full']['status']='failed'
                rt.save(fixture/'preflight/preflight.json',failed)
                with self.assertRaisesRegex(ValueError,'preflight failed'): simulate.run(args)
                self.assertEqual(rt.read(args.output/'campaign.json')['status'],'preflight_failed')
                self.assertFalse((args.output/'jobs').exists())

if __name__ == '__main__': unittest.main()
