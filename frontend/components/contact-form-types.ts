export type ContactFields = {
  name: string;
  company: string;
  email: string;
  phone: string;
  city: string;
  application: string;
  timeline: string;
  budget: string;
  message: string;
  website: string;
  fax: string;
};

export const emptyContactFields: ContactFields = {
  name: '',
  company: '',
  email: '',
  phone: '',
  city: '',
  application: '',
  timeline: '',
  budget: '',
  message: '',
  website: '',
  fax: '',
};