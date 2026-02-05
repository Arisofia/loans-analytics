// create_test_user.js

// Usage: node create_test_user.js youremail@example.com 'StrongP@ssw0rd!'

import
 fetch 
from
 
'node-fetch'
;
const
 [,, email, password] = process.argv;
if
 (!email || !password) {
  
console
.error(
'Usage: node create_test_user.js email password'
);
  process.exit(
1
);
}
const
 SUPABASE_URL = process.env.SUPABASE_URL;
const
 SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
if
 (!SUPABASE_URL || !SERVICE_ROLE_KEY) {
  
console
.error(
'Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your env'
);
  process.exit(
1
);
}
(
async
 () => {
  
const
 res = 
await
 fetch(
`
${SUPABASE_URL}
/auth/v1/admin/users`
, {
    
method
: 
'POST'
,
    
headers
: {
      
Authorization
: 
`Bearer 
${SERVICE_ROLE_KEY}
`
,
      
'Content-Type'
: 
'application/json'
,
      
Prefer
: 
'return=representation'

    },
    
body
: 
JSON
.stringify({
      email,
      password,
      
email_confirm
: 
true

    })
  });
  
const
 data = 
await
 res.json();
  
if
 (!res.ok) {
    
console
.error(
'Error creating user:'
, res.status, data);
    process.exit(
2
);
  }
  
console
.log(
'User created:'
, 
JSON
.stringify(data, 
null
, 
2
));
})();
