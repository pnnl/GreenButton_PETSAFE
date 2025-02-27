import { Roles, User } from '../types';

export const userContainer: User[] = [
  {
    username: 'testCustomer',
    password: 'testCustomer123',
    role: Roles.CUSTOMER,
    legalName: 'Test Customer',
    accountNumber: '',
    email: '',
    phone: '',
    address: {
      address: '',
      addressNumber: '',
      city: '',
      state: {
        code: '',
        name: '',
      },
      zip: '',
    },
  },
  {
    username: 'testUtility',
    password: 'testUtility123',
    role: Roles.UTILITY,
    legalName: 'Test Utility',
    accountNumber: '',
    email: '',
    phone: '',
    address: {
      address: '',
      addressNumber: '',
      city: '',
      state: {
        code: '',
        name: '',
      },
      zip: '',
    },
  },
  {
    username: 'testThirdParty',
    password: 'testThirdParty123',
    role: Roles.THIRD_PARTY,
    legalName: 'Test Third Party',
    accountNumber: '',
    email: '',
    phone: '',
    address: {
      address: '',
      addressNumber: '',
      city: '',
      state: {
        code: '',
        name: '',
      },
      zip: '',
    },
  },
];
