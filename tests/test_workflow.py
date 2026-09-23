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
                calls.append(label)
                if label=='environment':
                    return '\n'.join('CYGNO_ENV '+k+' '+v for k,v in env.items())
                if label=='quantities':
                    Path(command[1]).write_bytes((fixture/'quantities.tsv').read_bytes())
                    Path(command[3]).write_bytes((fixture/'geometry.json').read_bytes())
                    return ''
                return fake_invoke(command,cwd,label,timeout,**options)
            def preflight(build,output):
                output.mkdir()
                rt.save(output/'preflight.json',rt.read(fixture/'preflight/preflight.json'))
                return 0
            args=simulate.parser().parse_args(['--build',str(build),'--output',str(base/'one-million'),
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
                self.assertEqual(campaign['coverage'],'1/26')
                self.assertEqual(campaign['identity']['config']['primaries_per_job'],1_000_000)
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
