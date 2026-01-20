import { MetaGraphClient } from './index';

describe('MetaGraphClient', () => {
  it('should construct with access token', () => {
    const client = new MetaGraphClient('test-token');
    expect(client).toBeDefined();
  });
});
