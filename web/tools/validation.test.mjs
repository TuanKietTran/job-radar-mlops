import test from 'node:test';
import assert from 'node:assert/strict';
import {
  validateGross,
  validateNet,
  validateDependents,
  validateMonthsContributed,
  validateAverageSalary,
  formatVnd,
  parseIntegerText,
  GROSS_MAX,
  DEPENDENTS_MAX,
  MONTHS_MAX,
} from './tools.js';

test('gross accepts whole numbers in range', () => {
  assert.equal(validateGross('0'), null);
  assert.equal(validateGross('30000000'), null);
  assert.equal(validateGross('500000000'), null);
  assert.equal(validateGross('30,000,000'), null);
  assert.equal(validateGross(' 30000000 '), null);
});

test('gross rejects text, decimals, negatives, and over max', () => {
  assert.notEqual(validateGross(''), null);
  assert.notEqual(validateGross('abc'), null);
  assert.notEqual(validateGross('12.5'), null);
  assert.notEqual(validateGross('-5'), null);
  assert.notEqual(validateGross('500000001'), null);
});

test('net accepts whole numbers in range', () => {
  assert.equal(validateNet('0'), null);
  assert.equal(validateNet('25000000'), null);
  assert.equal(validateNet('500000000'), null);
  assert.notEqual(validateNet('600000000'), null);
  assert.notEqual(validateNet('net'), null);
});

test('dependents accepts 0 to 10', () => {
  assert.equal(validateDependents('0'), null);
  assert.equal(validateDependents('10'), null);
  assert.notEqual(validateDependents('11'), null);
  assert.notEqual(validateDependents('-1'), null);
  assert.notEqual(validateDependents('1.5'), null);
  assert.notEqual(validateDependents(''), null);
});

test('months contributed accepts 0 to 600', () => {
  assert.equal(validateMonthsContributed('0'), null);
  assert.equal(validateMonthsContributed('24'), null);
  assert.equal(validateMonthsContributed('600'), null);
  assert.notEqual(validateMonthsContributed('601'), null);
  assert.notEqual(validateMonthsContributed('two'), null);
});

test('average salary accepts whole numbers in range', () => {
  assert.equal(validateAverageSalary('20000000'), null);
  assert.equal(validateAverageSalary('0'), null);
  assert.notEqual(validateAverageSalary('500000001'), null);
  assert.notEqual(validateAverageSalary('20.5m'), null);
});

test('parseIntegerText strips commas and spaces', () => {
  assert.equal(parseIntegerText('30,000,000').value, 30000000);
  assert.equal(parseIntegerText('30 000 000').value, 30000000);
  assert.equal(parseIntegerText('0').value, 0);
  assert.equal(parseIntegerText('abc').ok, false);
  assert.equal(parseIntegerText('12.5').ok, false);
  assert.equal(parseIntegerText('').ok, false);
});

test('formatVnd groups digits and adds the suffix', () => {
  assert.equal(formatVnd(25882500), '25,882,500 VND');
  assert.equal(formatVnd(0), '0 VND');
  assert.equal(formatVnd(300000), '300,000 VND');
});

test('error messages name the field', () => {
  assert.match(validateGross('abc'), /Gross salary/);
  assert.match(validateDependents('11'), /Dependents/);
  assert.match(validateMonthsContributed('601'), /Months contributed/);
  assert.match(validateAverageSalary('abc'), /Average monthly salary/);
});

test('shared limits match the brief', () => {
  assert.equal(GROSS_MAX, 500000000);
  assert.equal(DEPENDENTS_MAX, 10);
  assert.equal(MONTHS_MAX, 600);
});
