*** Begin Patch
*** Update File: apps/web/app/account/page.tsx
@@
 import { createClient } from '@/lib/supabase/server';
 
 export default async function Account() {
-  const supabase = await createClient();
+  const supabase = createClient();
   const {
     data: { user },
   } = await supabase.auth.getUser();
   return <AccountForm user={user} />;
 }
*** End Patch
