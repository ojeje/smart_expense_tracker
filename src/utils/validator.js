/**
 * Backend input validator strictly enforcing the SRS Validation Matrix.
 * @param {any} payload 
 * @returns {{isValid: boolean, errorMessage: string | null}}
 */
export function validateExpensePayload(payload) {
  const { customer_name, amount, category, custom_category } = payload || {};

  // Rule 1: Customer Name non-empty after trimming
  if (!customer_name || typeof customer_name !== 'string' || customer_name.trim() === '') {
    return { isValid: false, errorMessage: 'Please enter a valid customer name.' };
  }

  // Rule 2: Amount must be numeric and > 0 (must be > 0 after 2-decimal normalization)
  const parsedAmount = Number(amount);
  if (amount === undefined || amount === null || amount === '' || isNaN(parsedAmount)) {
    return { isValid: false, errorMessage: 'Please enter an amount greater than zero.' };
  }
  const roundedAmount = Math.round(parsedAmount * 100) / 100;
  if (roundedAmount <= 0) {
    return { isValid: false, errorMessage: 'Please enter an amount greater than zero.' };
  }

  // Rule 3: Category must not be empty or default prompt
  if (!category || typeof category !== 'string' || category.trim() === '' || category === 'default') {
    return { isValid: false, errorMessage: 'Please select a category.' };
  }

  // Rule 4: If category is "Custom", custom_category must be non-empty after trimming
  if (category === 'Custom') {
    if (!custom_category || typeof custom_category !== 'string' || custom_category.trim() === '') {
      return { isValid: false, errorMessage: 'Please enter a custom category name.' };
    }
  }

  return { isValid: true, errorMessage: null };
}

export default {
  validateExpensePayload
};

