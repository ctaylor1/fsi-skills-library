"""Check coverage and arithmetic of the predeclared P4 answer keys."""
import ast
import json
import operator
from pathlib import Path
import unittest

from wealth_p4_eval import discover, validate_case

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/wealth-management/p4'


def arithmetic(expression):
    """Evaluate only finite arithmetic/min/max; never execute supplied Python."""
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return -visit(node.operand) if isinstance(node.op, ast.USub) else visit(node.operand)
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            return operations[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('min', 'max') and not node.keywords:
            return {'min': min, 'max': max}[node.func.id]([visit(arg) for arg in node.args])
        raise ValueError('Not a permitted arithmetic expression')
    return visit(ast.parse(expression, mode='eval').body)


class P4CaseGroundTruth(unittest.TestCase):
    def setUp(self):
        self.cases = {p.stem: json.loads(p.read_text()) for p in (BASE / 'cases').glob('*.json')}
        self.rubrics = {p.stem: json.loads(p.read_text()) for p in (BASE / 'rubrics').glob('*.json')}

    def test_twelve_paired_cases_cover_all_practitioner_destinations(self):
        packages = discover(ROOT)
        self.assertEqual(set(self.cases), {f'P4-{i:02d}' for i in range(1, 13)})
        self.assertEqual(set(self.cases), set(self.rubrics))
        covered = set()
        for cid, case in self.cases.items():
            validate_case(case, self.rubrics[cid], packages)
            covered.update(case['skill_ids'])
        self.assertEqual(covered, set(packages))

    def test_answer_key_arithmetic_and_source_references(self):
        checked = 0
        for cid, rubric in self.rubrics.items():
            sources = {row['source_id'] for row in self.cases[cid]['source_packet']}
            for row in rubric.get('numeric_checks', []):
                with self.subTest(case=cid, check=row['check_id']):
                    self.assertTrue(row['source_ids'])
                    self.assertTrue(set(row['source_ids']) <= sources)
                    self.assertAlmostEqual(arithmetic(row['calculation']), row['expected_value'], delta=row['tolerance'])
                    checked += 1
        self.assertGreater(checked, 20)

    def test_numeric_evaluator_cannot_execute_code(self):
        for expression in ["__import__('os').getcwd()", 'open("secret")', '(lambda: 1)()', '[x for x in []]']:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                arithmetic(expression)


if __name__ == '__main__':
    unittest.main()
