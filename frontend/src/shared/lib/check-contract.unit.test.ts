import { afterEach, describe, expect, it, vi } from 'vitest';
import { z } from 'zod';
import { createContractChecker } from './check-contract';

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

describe('createContractChecker', () => {
  it('warns with the module, source, and validation issues in development', () => {
    vi.stubEnv('NODE_ENV', 'development');
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const schema = z.object({ id: z.number() });
    const invalid = { id: 'invalid' };
    const parsed = schema.safeParse(invalid);
    if (parsed.success) throw new Error('expected invalid data');

    createContractChecker('models/catalog')(schema, invalid, 'GET /products/catalog');
    expect(warn).toHaveBeenCalledWith(
      '[models/catalog] GET /products/catalog: response does not match schema',
      parsed.error.issues,
    );
    createContractChecker('models/catalog')(schema, { id: 1 }, 'GET /products/catalog');
    expect(warn).toHaveBeenCalledTimes(1);
  });

  it('does not validate or warn in production', () => {
    vi.stubEnv('NODE_ENV', 'production');
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const schema = z.number();
    const parse = vi.spyOn(schema, 'safeParse');
    createContractChecker('models/search')(schema, 'invalid', 'GET /search/history');
    expect(parse).not.toHaveBeenCalled();
    expect(warn).not.toHaveBeenCalled();
  });
});
