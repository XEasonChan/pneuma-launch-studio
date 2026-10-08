"""Offline QC regressions. Run with skill/scripts/py <absolute path to this file>."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skill/scripts/qc'))
import qc


class ReadcheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ws = self.tmp.name
        self.vo = Path(self.ws) / 'stages/vo'
        self.vo.mkdir(parents=True)

    def row(self, outcomes, available=True, picked=1):
        takes = [dict(id='S01', lang='en', take=i, ok=ok) for i, ok in enumerate(outcomes, 1)]
        (self.vo / 'readcheck.json').write_text(json.dumps(dict(available=available, takes=takes)))
        (self.vo / 'lines.json').write_text(json.dumps([dict(id='S01', lang='en', take=picked)]))
        return qc.readcheck_row(self.ws, 'en-jasub')

    def test_failed_picked_take_fails_the_version(self):
        row = self.row([False])
        self.assertEqual(row['status'], 'fail')
        rec = dict(version='short-16x9-en', format='short-16x9', lang='en', file='out/roughcut/short-16x9-en.mp4',
                   audio_s=1, frames=30, fps=30, lufs=-16, tp=-2, frames_ok=True, audio_ok=True, tp_ok=True,
                   comp_frames=30, width=960, height=540, scale=0.5)
        output = qc.version_record(self.ws, 'roughcut', rec, [], extra=[row])
        self.assertFalse(json.loads(Path(output).read_text())['pass'])

    def test_missing_model_remains_unchecked(self):
        row = self.row([None], available=False)
        self.assertEqual(row['status'], 'unchecked')
        self.assertIn('unavailable', row['note'])

    def test_unknown_take_remains_unchecked(self):
        self.assertEqual(self.row([None])['status'], 'unchecked')

    def test_rejected_take_does_not_fail_a_good_pick(self):
        self.assertEqual(self.row([False, True], picked=2)['status'], 'pass')

    def test_known_failure_survives_partial_availability(self):
        self.assertEqual(self.row([False], available=False)['status'], 'fail')


if __name__ == '__main__':
    unittest.main()
