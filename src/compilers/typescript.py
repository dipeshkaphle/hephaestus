import re
import os
from src.compilers.base import BaseCompiler


class TypeScriptCompiler(BaseCompiler):

    ERROR_REGEX = re.compile(
        r'([A-Za-z0-9_.\-\/]+\.ts)\([0-9,]+\):\s+error\s+(TS\d+):\s+(.+)')

    CRASH_REGEX = re.compile(r'(.+)(\n(\s+at .+))+')

    def __init__(self, input_name, filter_patterns=None):
        super().__init__(input_name, filter_patterns)

    @classmethod
    def get_compiler_version(cls):
        return ['tsc', '-v']

    def get_compiler_cmd(self):
        return ['tsc --target es2020 --strict --pretty false', os.path.join(
            self.input_name, '**', '*.ts')]

    def get_filename(self, match):
        """
        Normalize relative path from TypeScript compiler to absolute path.
        TypeScript outputs paths relative to CWD, but oracle uses absolute paths.
        """
        filename = match[0]

        # Remove leading './' if present
        if filename.startswith('./'):
            filename = filename[2:]

        # Get parent directory of input_name
        # input_name is like /tmp/tmpz0oqnim2/src
        # We need to join with parent to get /tmp/tmpz0oqnim2/src/...
        parent_dir = os.path.dirname(self.input_name)

        # Join with parent directory to create absolute path
        abs_path = os.path.normpath(os.path.join(parent_dir, filename))

        return abs_path

    def get_error_msg(self, match):
        return f"{match[1]}{match[2]}"
