from __future__ import annotations

import json

import console_auth
from ceo_style import CSS
from shared_login import LOGIN_BODY


def page_bytes() -> bytes:
    config = json.dumps(console_auth.supabase_browser_config(), separators=(",", ":")).replace("<", "\\u003c")
    script = r'''const form=document.getElementById('login-form');
const message=document.getElementById('login-message');
const error=document.getElementById('login-error');
const config=__CONFIG__;
if(new URLSearchParams(location.search).get('msg')==='expired')message.textContent='Your session ended. Sign in again.';
form.addEventListener('submit',async event=>{
 event.preventDefault();error.textContent='';
 try{
  if(!config.url||!config.anon_key)throw Error('Authentication is not configured.');
  const fields=new FormData(form);
  const auth=await fetch(config.url.replace(/\/$/,'')+'/auth/v1/token?grant_type=password',{
   method:'POST',
   headers:{apikey:config.anon_key,'Content-Type':'application/json'},
   body:JSON.stringify({email:fields.get('email'),password:fields.get('password')})
  });
  const authData=await auth.json().catch(()=>({}));
  if(!auth.ok||!authData.access_token)throw Error('Sign-in failed.');
  const session=await fetch('/api/session',{headers:{Authorization:'Bearer '+authData.access_token},cache:'no-store'});
  const sessionData=await session.json().catch(()=>({}));
  if(!session.ok)throw Error(sessionData.error||'Console access could not be determined.');
  sessionStorage.setItem('cmo_token',authData.access_token);
  sessionStorage.setItem('cmo_email',sessionData.email);
  sessionStorage.setItem('cmo_role',sessionData.role);
  location.assign(sessionData.console);
 }catch(problem){error.textContent=problem.message;}
});'''.replace("__CONFIG__", config)
    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>iTarang sign in</title><style>{CSS}</style></head><body>{LOGIN_BODY}'
        f'<script>{script}</script></body></html>'
    )
    return document.encode("utf-8")
