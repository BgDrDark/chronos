import { z } from 'zod';

export const invoiceItemSchema = z.object({
  name: z.string().min(1, 'Задължително поле'),
  quantity: z.number().positive('Трябва да е положително'),
  unitPrice: z.number().nonnegative(),
  total: z.number().nonnegative(),
  discountPercent: z.number().min(0).max(100).default(0),
  ingredientId: z.number().optional().nullable(),
});

export const invoiceSchema = z.object({
  type: z.enum(['incoming', 'outgoing']),
  documentType: z.string().min(1, 'Задължително'),
  griff: z.string().default('ОРИГИНАЛ'),
  description: z.string().optional(),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Невалидна дата'),
  supplierId: z.number().nullable().optional(),
  clientName: z.string().optional(),
  clientEik: z.string().optional(),
  clientAddress: z.string().optional(),
  discountPercent: z.number().min(0).max(100).default(0),
  vatRate: z.number().min(0).max(100).default(20),
  paymentMethod: z.string().optional(),
  deliveryMethod: z.string().optional(),
  dueDate: z.string().optional(),
  paymentDate: z.string().optional(),
  status: z.enum(['draft', 'sent', 'paid', 'overdue', 'cancelled']).default('draft'),
  notes: z.string().optional(),
  items: z.array(invoiceItemSchema).min(1, 'Поне един артикул'),
});

export const proformaInvoiceSchema = z.object({
  type: z.literal('proforma'),
  documentType: z.string().min(1, 'Задължително'),
  griff: z.string().default('ОРИГИНАЛ'),
  description: z.string().optional(),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Невалидна дата'),
  clientName: z.string().min(1, 'Клиентът е задължителен'),
  clientEik: z.string().optional(),
  clientAddress: z.string().optional(),
  vatRate: z.number().min(0).max(100).default(20),
  status: z.enum(['draft', 'sent', 'paid', 'overdue', 'cancelled']).default('draft'),
  notes: z.string().optional(),
  items: z.array(invoiceItemSchema).min(1, 'Поне един артикул'),
});

export type InvoiceFormData = z.infer<typeof invoiceSchema>;
export type ProformaFormData = z.infer<typeof proformaInvoiceSchema>;
export type InvoiceItemFormData = z.infer<typeof invoiceItemSchema>;