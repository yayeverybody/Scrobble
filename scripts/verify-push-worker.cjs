const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {stripTypeScriptTypes}=require('node:module');
const source=stripTypeScriptTypes(fs.readFileSync('scripts/notification-worker.ts','utf8').replace(/^import .*;\n/gm,''));
async function run(reason){
  let handler,importedKey,header,issuer;
  const deletes=[],updates=[];
  const db={from(table){const q={select(){return q},eq(){return q},
    update(value){updates.push(value);return q},delete(){deletes.push(table);return q},
    single:async()=>({data:{status:'active',current_player_id:'recipient'}}),
    maybeSingle:async()=>({data:{player_id:'recipient'}}),
    then(resolve){return Promise.resolve({data:table==='scrobble_native_push_tokens'?[{token:'a'.repeat(64)}]:[]}).then(resolve)}};return q}};
  const env={APNS_PRIVATE_KEY:'  KEY\\nLINE  ',APNS_KEY_ID:'  KEYID  ',APNS_TEAM_ID:'  TEAMID  ',SCROBBLE_PUSH_SECRET:'secret'};
  class JWT{setProtectedHeader(value){header=value;return this}setIssuer(value){issuer=value;return this}setIssuedAt(){return this}async sign(){return 'jwt'}}
  const ctx={Response,URL,Date,console:{error(){}},createClient:()=>db,SignJWT:JWT,
    importPKCS8:async key=>{importedKey=key;return {}},
    Deno:{env:{get:key=>env[key]},serve:fn=>handler=fn,createHttpClient:()=>({close(){}})},
    fetch:async()=>reason?Response.json({reason},{status:reason==='Unregistered'?410:403}):Response.json({})};
  vm.createContext(ctx);vm.runInContext(source,ctx);
  const result=await handler(new Request('https://example.test/',{method:'POST',headers:{'x-scrobble-secret':'secret'},body:JSON.stringify({user_id:'recipient',game_id:'game'})}));
  assert.equal(importedKey,'KEY\nLINE');assert.equal(header.kid,'KEYID');assert.equal(issuer,'TEAMID');
  return {body:await result.json(),deletes,updates,handler};
}
(async()=>{
  const bad=await run('InvalidProviderToken');assert.equal(bad.body.ok,false);assert.deepEqual(bad.body.failures,['apns:403:InvalidProviderToken']);assert.equal(bad.deletes.length,0);
  const device=await run('BadDeviceToken');assert.equal(device.deletes.length,0);
  const expired=await run('Unregistered');assert.deepEqual(expired.deletes,['scrobble_native_push_tokens']);
  const success=await run();assert.equal(success.body.ok,true);assert.equal(success.body.count,1);
  const denied=await success.handler(new Request('https://example.test/',{method:'POST'}));assert.equal(denied.status,401);
  console.log('PASS: APNs credential normalization, exact rejection reason, token preservation, expired-token cleanup, successful submission, and worker authentication.');
})().catch(error=>{console.error(error);process.exitCode=1});
