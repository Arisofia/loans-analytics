export const createClient = () => ({
  auth: {
    getUser: async () => ({ data: { user: null }, error: null }),
    signInWithPassword: async (..._args: any[]) => ({ data: {}, error: null }),
    signOut: async () => ({ error: null }),
    signUp: async (..._args: any[]) => ({ data: {}, error: null }),
  },
  from: (table: string) => ({
    select: (_fields?: string) => ({
      eq: (..._args: any[]) => ({
        single: () => ({
          data: {
            full_name: 'Mock Name',
            username: 'mockuser',
            website: 'https://mock.site',
            avatar_url: 'https://mock.site/avatar.png',
          },
          error: null,
          status: 200,
        }),
      }),
      single: () => ({
        data: {
          full_name: 'Mock Name',
          username: 'mockuser',
          website: 'https://mock.site',
          avatar_url: 'https://mock.site/avatar.png',
        },
        error: null,
        status: 200,
      }),
    }),
    insert: () => ({ data: [], error: null }),
    update: () => ({ data: [], error: null }),
    upsert: (..._args: any[]) => Promise.resolve({ data: {}, error: null, status: 200 }),
  }),
  storage: {
    from: (_bucket: string) => ({
      download: async (_path: string) => ({
        data: new Blob(['mock image'], { type: 'image/png' }),
        error: null,
      }),
      upload: async (_path: string, _file: Blob) => ({ data: {}, error: null }),
    }),
  },
})
