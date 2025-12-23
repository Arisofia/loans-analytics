'use client';
import { useCallback, useEffect, useState } from 'react';
<<<<<<< HEAD
import { createClient } from '@/lib/supabase/client';
=======
import { createClient } from '../../src/lib/supabase/client';
>>>>>>> origin/main
import { type User } from '@supabase/supabase-js';
import Avatar from './avatar';

export default function AccountForm({ user }: { user: User | null }) {
  const supabase = createClient();
  const [loading, setLoading] = useState(true);
  const [fullname, setFullname] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [website, setWebsite] = useState<string | null>(null);
  const [avatar_url, setAvatarUrl] = useState<string | null>(null);

  const getProfile = useCallback(async () => {
    try {
      setLoading(true);
      const { data, error, status } = await supabase
        .from('profiles')
        .select(`full_name, username, website, avatar_url`)
        .eq('id', user?.id)
        .single();
      if (error && status !== 406) {
        throw error;
      }
      if (data) {
        setFullname(data.full_name);
        setUsername(data.username);
        setWebsite(data.website);
        setAvatarUrl(data.avatar_url);
      }
<<<<<<< HEAD
    } catch (error) {
      alert('Error loading user data!');
=======
    } catch (_error) {
      alert('Error loading user data!')
>>>>>>> origin/main
    } finally {
      setLoading(false);
    }
  }, [user, supabase]);

  useEffect(() => {
<<<<<<< HEAD
    getProfile();
=======
    void getProfile();
>>>>>>> origin/main
  }, [user, getProfile]);

  async function updateProfile({
    username,
    website,
    avatar_url,
<<<<<<< HEAD
=======
    fullname,
>>>>>>> origin/main
  }: {
    username: string | null;
    fullname: string | null;
    website: string | null;
    avatar_url: string | null;
  }) {
    try {
      setLoading(true);
      const { error } = await supabase.from('profiles').upsert({
        id: user?.id as string,
        full_name: fullname,
        username,
        website,
        avatar_url,
        updated_at: new Date().toISOString(),
<<<<<<< HEAD
      });
      if (error) throw error;
      alert('Profile updated!');
    } catch (error) {
      alert('Error updating the data!');
=======
      })
      if (error) throw error
      alert('Profile updated!')
    } catch (_error) {
      alert('Error updating the data!')
>>>>>>> origin/main
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="form-widget">
      <Avatar
        uid={user?.id ?? null}
        url={avatar_url}
        size={150}
        onUpload={(url) => {
          setAvatarUrl(url);
<<<<<<< HEAD
          updateProfile({ fullname, username, website, avatar_url: url });
=======
          void updateProfile({ fullname, username, website, avatar_url: url });
>>>>>>> origin/main
        }}
      />
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="text" value={user?.email} disabled />
      </div>
      <div>
        <label htmlFor="fullName">Full Name</label>
        <input
          id="fullName"
          type="text"
          value={fullname || ''}
          onChange={(e) => setFullname(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          value={username || ''}
          onChange={(e) => setUsername(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="website">Website</label>
        <input
          id="website"
          type="url"
          value={website || ''}
          onChange={(e) => setWebsite(e.target.value)}
        />
      </div>
      <div>
        <button
          className="button primary block"
<<<<<<< HEAD
          onClick={() => updateProfile({ fullname, username, website, avatar_url })}
=======
          onClick={() => void updateProfile({ fullname, username, website, avatar_url })}
>>>>>>> origin/main
          disabled={loading}
        >
          {loading ? 'Loading ...' : 'Update'}
        </button>
      </div>
      <div>
        <form action="/auth/signout" method="post">
          <button className="button block" type="submit">
            Sign out
          </button>
        </form>
      </div>
    </div>
  );
}
