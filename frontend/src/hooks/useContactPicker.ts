import { useState, useCallback } from 'react';

interface Contact {
  name: string;
  email?: string;
  phone?: string;
  photo?: Blob;
}

interface ContactPickerProperty {
  name?: string[];
  email?: string[];
  tel?: string[];
  photo?: Blob[];
}

interface ContactsManager {
  select: (properties: string[], options: { multiple?: boolean }) => Promise<ContactPickerProperty[]>;
}

export function useContactPicker() {
  const [isSupported] = useState('contacts' in navigator);

  const pickContacts = useCallback(async (
    options: { multiple?: boolean; includeFields?: string[] } = {}
  ): Promise<Contact[]> => {
    if (!isSupported) {
      throw new Error('Contact Picker API is not supported in this browser');
    }

    const { multiple = false, includeFields = ['name', 'email', 'tel'] } = options;

    try {
      const contacts = await ((navigator as unknown) as { contacts: ContactsManager }).contacts.select(
        includeFields,
        { multiple }
      );

      return contacts.map((contact) => ({
        name: contact.name?.[0] || '',
        email: contact.email?.[0] || undefined,
        phone: contact.tel?.[0] || undefined,
        photo: contact.photo?.[0] || undefined,
      }));
    } catch (e) {
      if ((e as Error).name === 'AbortError') {
        throw new Error('Изборът на контакт беше отменен');
      }
      throw e;
    }
  }, [isSupported]);

  return { pickContacts, isSupported };
}
