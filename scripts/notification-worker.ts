import webpush from 'npm:web-push@3.6.7';
import { createClient } from 'npm:@supabase/supabase-js@2.57.4';
import { importPKCS8, SignJWT } from 'npm:jose@6.1.0';

const apnsSetting=(name:string)=>Deno.env.get(name)?.trim()||'';
const normalizeAPNSKey=(value:string)=>value.trim().replace(/\\n/g,'\n');
const apnsReady=()=>['APNS_PRIVATE_KEY','APNS_KEY_ID','APNS_TEAM_ID'].every(k=>!!apnsSetting(k));
const admin=()=>createClient(Deno.env.get('SUPABASE_URL')!,Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);
let cachedJWT:string|null=null, signedAt=0;
async function providerToken(){
  if(cachedJWT&&Date.now()-signedAt<50*60*1000)return cachedJWT;
  const key=await importPKCS8(normalizeAPNSKey(apnsSetting('APNS_PRIVATE_KEY')),'ES256');
  cachedJWT=await new SignJWT({}).setProtectedHeader({alg:'ES256',kid:apnsSetting('APNS_KEY_ID')}).setIssuer(apnsSetting('APNS_TEAM_ID')).setIssuedAt().sign(key);
  signedAt=Date.now();return cachedJWT;
}
const json=(body:unknown,status=200)=>Response.json(body,{status});
Deno.serve(async req=>{
  if(req.method==='GET'&&new URL(req.url).pathname.endsWith('/health'))return json({native_push_ready:apnsReady(),web_push_ready:!!Deno.env.get('VAPID_PRIVATE_KEY')});
  if(req.method!=='POST')return json({error:'Method not allowed'},405);
  const secret=Deno.env.get('SCROBBLE_PUSH_SECRET');
  if(!secret||req.headers.get('x-scrobble-secret')!==secret)return json({error:'Unauthorized'},401);
  const db=admin();let eventId:string|undefined;
  try{
    const input=await req.json();eventId=input.event_id;
    const {user_id,game_id,kind='turn',opponent_name='Your opponent',game_version}=input;
    if(!['turn','nudge'].includes(kind)||typeof user_id!=='string'||typeof game_id!=='string')return json({error:'Invalid request'},400);
    if(eventId){
      const {data:event,error}=await db.from('scrobble_notification_events').select('id,recipient_id,game_id,kind,status').eq('id',eventId).single();
      if(error||!event||event.recipient_id!==user_id||event.game_id!==game_id||event.kind!==kind)return json({error:'Invalid event'},400);
      if(event.status!=='queued')return json({ok:true,duplicate:true});
    }
    const {data:game,error:gameError}=await db.from('games').select('status,current_player_id,updated_at').eq('id',game_id).single();
    const {data:player}=await db.from('game_players').select('player_id').eq('game_id',game_id).eq('player_id',user_id).maybeSingle();
    if(gameError||!player||game?.status!=='active'||game.current_player_id!==user_id||(game_version&&Date.parse(game_version)!==Date.parse(game.updated_at))){
      if(eventId)await db.from('scrobble_notification_events').update({status:'skipped'}).eq('id',eventId);
      return json({ok:true,skipped:true});
    }
    const title=kind==='nudge'?'A friendly Scrobble nudge':'Your turn in Scrobble!';
    const name=String(opponent_name).slice(0,80);
    const body=kind==='nudge'?`${name} is waiting for your move. Come play!`:`${name} played. It’s your move.`;
    const url=`/?game=${encodeURIComponent(game_id)}`;
    let delivered=0,failed=0;
    const failures:string[]=[];
    const {data:subs,error:subError}=await db.from('scrobble_push_subscriptions').select('id,endpoint,p256dh,auth').eq('user_id',user_id);
    if(subError)throw subError;
    if(subs?.length){
      webpush.setVapidDetails(Deno.env.get('VAPID_SUBJECT')||'mailto:hello@yayeverybody.com',Deno.env.get('VAPID_PUBLIC_KEY')!,Deno.env.get('VAPID_PRIVATE_KEY')!);
      for(const s of subs){
        try{
          const endpoint=new URL(s.endpoint);
          if(endpoint.protocol!=='https:'||!['fcm.googleapis.com','web.push.apple.com','updates.push.services.mozilla.com'].includes(endpoint.hostname))throw Error('Unsupported push endpoint');
          await webpush.sendNotification({endpoint:s.endpoint,keys:{p256dh:s.p256dh,auth:s.auth}},JSON.stringify({title,body,url,tag:`scrobble-${game_id}`}));delivered++;
        }catch(e){failed++;if([404,410].includes(e?.statusCode))await db.from('scrobble_push_subscriptions').delete().eq('id',s.id);}
      }
    }
    const {data:tokens,error:tokenError}=await db.from('scrobble_native_push_tokens').select('token').eq('user_id',user_id);
    if(tokenError)throw tokenError;
    if(tokens?.length&&apnsReady()){
      const jwt=await providerToken();
      const client=Deno.createHttpClient({http2:true,http1:false});
      try{
        for(const t of tokens){
          try{
            const response=await fetch(`https://api.push.apple.com/3/device/${t.token}`,{method:'POST',client,headers:{authorization:`bearer ${jwt}`,'apns-topic':'com.yayeverybody.scrobble','apns-push-type':'alert','apns-priority':'10','apns-collapse-id':`scrobble-${game_id}`,'content-type':'application/json'},body:JSON.stringify({aps:{alert:{title,body},sound:'default'},game_id,url})});
            if(response.ok){delivered++;await response.body?.cancel();}
            else{failed++;const result=await response.json();failures.push(`apns:${response.status}:${result.reason||'Unknown'}`);if(response.status===410||result.reason==='Unregistered')await db.from('scrobble_native_push_tokens').delete().eq('token',t.token);}
          }catch(e){failed++;failures.push(`apns_transport:${e instanceof Error?e.message:'Unknown'}`);}
        }
      }finally{client.close();}
    }else if(tokens?.length){failed+=tokens.length;failures.push('apns:credentials_missing');}
    if(failures.length)console.error(JSON.stringify({event_id:eventId,failures}));
    if(eventId)await db.from('scrobble_notification_events').update({status:delivered?'delivered':'failed',delivered_count:delivered}).eq('id',eventId);
    return json({ok:delivered>0,count:delivered,failed,failures,native_push_ready:apnsReady()});
  }catch(_){
    if(eventId)await db.from('scrobble_notification_events').update({status:'failed'}).eq('id',eventId);
    return json({error:'Notification delivery failed'},500);
  }
});
