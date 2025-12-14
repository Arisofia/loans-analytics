import { validateInput } from '../../src/utils/validation';

describe('validateInput', () => {
  it('should return true for valid input', () => {
    const input = { name: 'Valid Name', age: 25 };
    expect(validateInput(input)).toBe(true);
  });

  it('should throw an error for invalid input', () => {
    const input = { name: '', age: -1 };
    expect(() => validateInput(input)).toThrow('Invalid input');
  });
});