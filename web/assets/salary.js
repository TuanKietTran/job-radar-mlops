'use strict';
var RATES_DATE = '2026-11-14';
var RATES_NOTE = 'Muc theo brief w-a-4 / worker 3: giam tru ban than 11 trieu, phu thuoc 4,4 trieu; thue 7 bac; BHXH 8%, BHYT 1,5%, BHTN 1%.';
var BASE_SALARY = 2340000;
var BHXH_BHYT_CAP = 46800000;
var MIN_WAGE_REGION_1 = 4960000;
var BHTN_CAP = 99200000;
var PERSONAL_DEDUCTION = 11000000;
var DEPENDENT_DEDUCTION = 4400000;
var BRACKETS = [[5000000, 0.05], [10000000, 0.10], [18000000, 0.15], [32000000, 0.20], [52000000, 0.25], [80000000, 0.30], [Infinity, 0.35]];
function insurance(gross) {
  var baseBhxh = Math.min(gross, BHXH_BHYT_CAP);
  var baseBhtn = Math.min(gross, BHTN_CAP);
  var bhxh = Math.round(baseBhxh * 0.08);
  var bhyt = Math.round(baseBhxh * 0.015);
  var bhtn = Math.round(baseBhtn * 0.01);
  var employerBhxh = Math.round(baseBhxh * 0.175);
  var employerBhyt = Math.round(baseBhxh * 0.03);
  var employerBhtn = Math.round(baseBhtn * 0.01);
  return { baseBhxhBhyt: baseBhxh, baseBhtn: baseBhtn, bhxh: bhxh, bhyt: bhyt, bhtn: bhtn, total: bhxh + bhyt + bhtn, employer: { bhxh: employerBhxh, bhyt: employerBhyt, bhtn: employerBhtn, total: employerBhxh + employerBhyt + employerBhtn } };
}
function personalIncomeTax(taxable) {
  if (taxable <= 0) { return 0; }
  var tax = 0;
  var prev = 0;
  var i;
  for (i = 0; i < BRACKETS.length; i += 1) {
    var upper = BRACKETS[i][0];
    var rate = BRACKETS[i][1];
    if (taxable <= prev) { break; }
    var part = Math.min(taxable, upper) - prev;
    if (part > 0) { tax += part * rate; }
    prev = upper;
  }
  return Math.round(tax);
}
function grossToNet(gross, dependents) {
  dependents = dependents || 0;
  var ins = insurance(gross);
  var taxable = Math.max(0, gross - ins.total - PERSONAL_DEDUCTION - dependents * DEPENDENT_DEDUCTION);
  var tax = personalIncomeTax(taxable);
  return { gross: gross, dependents: dependents, insurance: ins, taxableIncome: taxable, tax: tax, net: gross - ins.total - tax };
}
function netToGross(net, dependents) {
  dependents = dependents || 0;
  var low = net;
  var high = net * 2 + 20000000;
  var mid;
  var i;
  for (i = 0; i < 80; i += 1) {
    mid = Math.floor((low + high) / 2);
    if (grossToNet(mid, dependents).net < net) { low = mid; } else { high = mid; }
  }
  var gross = Math.round(high / 1000) * 1000;
  return grossToNet(gross, dependents);
}
function unemploymentBenefit(monthsContributed, avgSalary) {
  var months = 0;
  if (monthsContributed >= 12) { months = Math.min(12, 3 + Math.max(0, Math.floor((monthsContributed - 36) / 12))); }
  var monthly = Math.min(Math.round(avgSalary * 0.6), MIN_WAGE_REGION_1 * 5);
  return { monthsContributed: monthsContributed, months: months, monthly: monthly, total: monthly * months };
}
function formatVnd(n) {
  if (n === null || n === undefined) { return 'Thoa thuan'; }
  return Math.round(n).toLocaleString('vi-VN') + ' ₫';
}
function formatTrieu(n) {
  if (n === null || n === undefined) { return 'Thoa thuan'; }
  var t = Math.round(n / 100000) / 10;
  return t.toLocaleString('vi-VN') + ' trieu';
}
function formatRange(min, max) {
  if (min === null && max === null) { return 'Thoa thuan'; }
  if (min === null) { return 'Den ' + formatTrieu(max); }
  if (max === null) { return 'Tu ' + formatTrieu(min); }
  if (min === max) { return formatTrieu(min); }
  return formatTrieu(min) + ' - ' + formatTrieu(max);
}
var JobRadarSalary = { ratesDate: RATES_DATE, ratesNote: RATES_NOTE, baseSalary: BASE_SALARY, bhxhBhytCap: BHXH_BHYT_CAP, minWageRegion1: MIN_WAGE_REGION_1, bhtnCap: BHTN_CAP, personalDeduction: PERSONAL_DEDUCTION, dependentDeduction: DEPENDENT_DEDUCTION, insurance: insurance, personalIncomeTax: personalIncomeTax, grossToNet: grossToNet, netToGross: netToGross, unemploymentBenefit: unemploymentBenefit, formatVnd: formatVnd, formatTrieu: formatTrieu, formatRange: formatRange };
if (typeof window !== 'undefined') { window.JobRadarSalary = JobRadarSalary; }
if (typeof module !== 'undefined' && module.exports) { module.exports = JobRadarSalary; }
