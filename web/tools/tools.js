// Shared helpers for the salary tools pages.
// Vanilla JavaScript, no dependencies. The pages load this file as an
// ES module, and the validation tests import it in Node.
// Rates are 2026 assumptions dated 2026-11-14, see
// tests/tools/SALARY_API_CONTRACT.md.

export const API_BASE_DEFAULT = 'http://127.0.0.1:8001';
export const GROSS_MIN = 0;
export const GROSS_MAX = 500000000;
export const DEPENDENTS_MIN = 0;
export const DEPENDENTS_MAX = 10;
export const MONTHS_MIN = 0;
export const MONTHS_MAX = 600;

export function apiBase() {
  if (typeof window !== 'undefined' && window.location && window.location.search) {
    try {
      const api = new URLSearchParams(window.location.search).get('api');
      if (api) {
        return api.endsWith('/') ? api.slice(0, -1) : api;
      }
    } catch (error) {
      return API_BASE_DEFAULT;
    }
  }
  return API_BASE_DEFAULT;
}

export function parseIntegerText(text) {
  if (typeof text !== 'string') {
    return { ok: false };
  }
  const cleaned = text.trim().replace(/[\s,]/g, '');
  if (cleaned === '' || !/^\d+$/.test(cleaned)) {
    return { ok: false };
  }
  const value = Number(cleaned);
  if (!Number.isSafeInteger(value)) {
    return { ok: false };
  }
  return { ok: true, value: value };
}

function validateInteger(text, min, max, label) {
  const parsed = parseIntegerText(text);
  if (!parsed.ok) {
    return label + ' must be a whole number.';
  }
  if (parsed.value < min || parsed.value > max) {
    return label + ' must be between ' + min.toLocaleString('en-US') + ' and ' + max.toLocaleString('en-US') + '.';
  }
  return null;
}

export function validateGross(text) {
  return validateInteger(text, GROSS_MIN, GROSS_MAX, 'Gross salary');
}

export function validateNet(text) {
  return validateInteger(text, GROSS_MIN, GROSS_MAX, 'Net salary');
}

export function validateDependents(text) {
  return validateInteger(text, DEPENDENTS_MIN, DEPENDENTS_MAX, 'Dependents');
}

export function validateMonthsContributed(text) {
  return validateInteger(text, MONTHS_MIN, MONTHS_MAX, 'Months contributed');
}

export function validateAverageSalary(text) {
  return validateInteger(text, GROSS_MIN, GROSS_MAX, 'Average monthly salary');
}

export function formatVnd(value) {
  return Number(value).toLocaleString('en-US') + ' VND';
}

export async function callApi(path, body) {
  let response;
  try {
    response = await fetch(apiBase() + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  } catch (error) {
    throw new Error('Salary API is unreachable at ' + apiBase() + '. Start the stub server and try again.');
  }
  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }
  if (!response.ok) {
    const message = data && data.error && data.error.message
      ? data.error.message
      : 'Salary API returned status ' + response.status + '.';
    throw new Error(message);
  }
  return data;
}

export function setFieldError(input, errorElement, message) {
  if (message) {
    errorElement.textContent = message;
    errorElement.hidden = false;
    input.setAttribute('aria-invalid', 'true');
    return false;
  }
  errorElement.textContent = '';
  errorElement.hidden = true;
  input.removeAttribute('aria-invalid');
  return true;
}

export function showNotice(noticeElement, message) {
  noticeElement.textContent = message;
  noticeElement.hidden = false;
}

export function hideNotice(noticeElement) {
  noticeElement.textContent = '';
  noticeElement.hidden = true;
}
