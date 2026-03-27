/* Ambient declarations for Supabase Edge Function (Deno) JSR modules.
   Remove after setting up a full Deno development environment. */

declare module "jsr:@hono/hono" {
  export class Hono {
    constructor();
    basePath(path: string): Hono;
    use(path: string, ...middleware: any[]): void;
    get(path: string, handler: (c: any) => any): void;
    put(path: string, handler: (c: any) => any): void;
    post(path: string, handler: (c: any) => any): void;
  }
}

declare module "jsr:@hono/hono/cors" {
  export function cors(options?: Record<string, any>): any;
}

declare module "jsr:@hono/hono/logger" {
  export function logger(): any;
}

declare module "jsr:@supabase/supabase-js@2" {
  export function createClient(url: string, key: string): any;
}

declare const Deno: {
  env: {
    get(key: string): string | undefined;
  };
};
