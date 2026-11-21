import type { z } from 'zod';

export function createContractChecker(module: string) {
  return (schema: z.ZodType, data: unknown, source: string): void => {
    if (process.env.NODE_ENV === 'production') {
      return;
    }
    const result = schema.safeParse(data);
    if (!result.success) {
      console.warn(`[${module}] ${source}: response does not match schema`, result.error.issues);
    }
  };
}
