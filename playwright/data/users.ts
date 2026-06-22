export const USERS = {
  standard: {
    username: 'standard_user',
    password: 'secret_sauce',
    expectedAccess: 'inventory',
  },

  lockedOut: {
    username: 'locked_out_user',
    password: 'secret_sauce',
    expectedAccess: 'denied',
  },

  problem: {
    username: 'problem_user',
    password: 'secret_sauce',
    expectedAccess: 'inventory_with_issues',
  },
};