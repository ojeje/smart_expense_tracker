// public/js/validator.js

/**
 * Validates the expense form inputs according to the SRS Validation Matrix
 * @param {{customer_name: string, amount: string, category: string, custom_category: string}} formData 
 * @returns {{isValid: boolean, errorMessage: string | null}}
 */
export function validateExpenseForm(formData) {
  const { customer_name, amount, category, custom_category } = formData || {};

  // Rule 1: Customer Name must not be empty or whitespace only
  if (!customer_name || customer_name.trim() === '') {
    return {
      isValid: false,
      errorMessage: 'Please enter a valid customer name.'
    };
  }

  // Rule 2: Amount must be provided, numeric, and > 0 (must be > 0 after 2-decimal normalization)
  const parsedAmount = parseFloat(amount);
  if (amount === '' || amount === null || amount === undefined || isNaN(parsedAmount)) {
    return {
      isValid: false,
      errorMessage: 'Please enter an amount greater than zero.'
    };
  }
  const roundedAmount = Math.round(parsedAmount * 100) / 100;
  if (roundedAmount <= 0) {
    return {
      isValid: false,
      errorMessage: 'Please enter an amount greater than zero.'
    };
  }

  // Rule 3: Category must be selected (not empty or default prompt)
  if (!category || category.trim() === '' || category === 'default') {
    return {
      isValid: false,
      errorMessage: 'Please select a category.'
    };
  }

  // Rule 4: If Category is "Custom", Custom Category input must not be empty or whitespace only
  if (category === 'Custom') {
    if (!custom_category || custom_category.trim() === '') {
      return {
        isValid: false,
        errorMessage: 'Please enter a custom category name.'
      };
    }
  }

  return {
    isValid: true,
    errorMessage: null
  };
}

export default {
  validateExpenseForm
};

