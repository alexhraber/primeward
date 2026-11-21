import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from applications.__main__ import main

class ApplicationCliTests(unittest.TestCase):
    def test_list(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(main(["list"]), 0)
        self.assertEqual(len(stream.getvalue().splitlines()), 8)

    def test_json_file_and_optional_plot(self):
        with tempfile.TemporaryDirectory() as directory:
            output, plot = Path(directory)/"form.json", Path(directory)/"form.png"
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["form-factor", "--count", "8", "--output", str(output),
                             "--plot", str(plot), "--summary"])
            self.assertEqual(code, 0)
            report = json.loads(output.read_text())
            self.assertTrue(report["passed"])
            self.assertEqual(report["prime_source"]["method"], "residual")
            self.assertGreater(plot.stat().st_size, 1000)

    def test_bad_count(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(["form-factor", "--count", "0"])
        self.assertEqual(error.exception.code, 2)

if __name__ == "__main__":
    unittest.main()
