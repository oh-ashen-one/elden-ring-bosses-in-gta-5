# SPDX-License-Identifier: Apache-2.0
"""Check native-call arity against pinned external API facts, not our wrapper.

Missing trailing arguments otherwise read stale ScriptHook call-context slots.
No game, network request or retail content is required by this regression test.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = json.loads((ROOT / 'native-contracts.json').read_text())['natives']


def calls(source):
    # Preserve literals while removing comments, so quoted commas/parentheses
    # and comments mentioning hook.invoke cannot distort the argument count.
    source = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/',
                    lambda m: m[0] if m[0][0] in '\"\'' else ' ', source)
    for match in re.finditer(r'hook\.invoke(?:<[^>]+>)?\(', source):
        start = match.end(); depth = 1; quote = None; escape = False; parts = []
        for i in range(start, len(source)):
            c = source[i]
            if quote:
                if escape: escape = False
                elif c == '\\': escape = True
                elif c == quote: quote = None
                continue
            if c in '\"\'': quote = c; continue
            if c in '({[': depth += 1
            elif c in ')}]':
                depth -= 1
                if depth == 0:
                    parts.append(source[start:i].strip()); break
            elif c == ',' and depth == 1:
                parts.append(source[start:i].strip()); start = i + 1
        native = re.fullmatch(r'(0x[0-9A-Fa-f]+)(?:ULL|UL|LL|U)?', parts[0])
        if not native: raise ValueError('Native calls must have an audited constant hash')
        yield f'0x{int(native[1],16):016X}', parts[1:]


def validate(source):
    checked = 0
    for hash_, arguments in calls(source):
        if hash_ not in CONTRACTS: raise ValueError('Unaudited native: ' + hash_)
        contract = CONTRACTS[hash_]
        if len(arguments) != contract['arguments']:
            raise ValueError(f"{contract['name']} requires {contract['arguments']} arguments, got {len(arguments)}")
        checked += 1
    return checked


class NativeContracts(unittest.TestCase):
    def test_both_plugins_match_external_contracts(self):
        for name in ['encounter_plugin.cpp', 'plugin.cpp', 'encounter_review.hpp', 'spectacle_runtime.hpp']:
            with self.subTest(source=name):
                self.assertGreater(validate((ROOT / 'src' / name).read_text()), 30)

    def test_original_missing_spawn_argument_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'CREATE_OBJECT_NO_OFFSET requires 8 arguments, got 7'):
            validate('hook.invoke<int>(0x9A294B2138ABB884ULL,h,x,y,z,false,true,false);')

    def test_complete_reference_signature_is_accepted(self):
        self.assertEqual(validate('hook.invoke<int>(0x9A294B2138ABB884ULL,h,x,y,z,false,true,false,0);'), 1)

    def test_parser_handles_nested_calls_literals_and_comments(self):
        source = '// hook.invoke(0xBAD);\nhook.invoke(0x25FBB336DF1804CBULL, pick("(a,b)", 2));'
        self.assertEqual(validate(source), 1)


if __name__ == '__main__': unittest.main()
