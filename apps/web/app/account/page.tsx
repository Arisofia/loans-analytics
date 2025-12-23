import AccountForm from './account-form';
<<<<<<< HEAD
import { createClient } from '@/lib/supabase/server';

export default async function Account() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return <AccountForm user={user} />;
=======
import { createClient } from '../../src/lib/supabase/server';
import { redirect } from 'next/navigation';

export default async function Account() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect('/login');
  }

  return (
    <AccountForm user={user} />
  );
>>>>>>> origin/main
}
