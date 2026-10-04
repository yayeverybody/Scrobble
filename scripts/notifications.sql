create schema if not exists scrobble_private;
revoke all on schema scrobble_private from public, anon;
grant usage on schema scrobble_private to authenticated;

create table public.scrobble_native_push_tokens (
  token text primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  updated_at timestamptz not null default now()
);
alter table public.scrobble_native_push_tokens enable row level security;
create index on public.scrobble_native_push_tokens(user_id);
grant select on public.scrobble_native_push_tokens to authenticated;
grant all on public.scrobble_native_push_tokens to service_role;
create policy native_tokens_read_own on public.scrobble_native_push_tokens for select to authenticated using ((select auth.uid())=user_id and coalesce((select auth.jwt()->>'is_anonymous'),'false')='false');

create table public.scrobble_notification_events (
  id uuid primary key default gen_random_uuid(),
  game_id uuid not null references public.games(id) on delete cascade,
  sender_id uuid references auth.users(id) on delete set null,
  recipient_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (kind in ('turn','nudge')),
  status text not null default 'queued' check (status in ('queued','delivered','failed','skipped')),
  delivered_count integer not null default 0,
  created_at timestamptz not null default now()
);
alter table public.scrobble_notification_events enable row level security;
create index on public.scrobble_notification_events(game_id,sender_id,created_at desc);
grant select on public.scrobble_notification_events to authenticated;
grant all on public.scrobble_notification_events to service_role;
create policy notification_events_read_own on public.scrobble_notification_events for select to authenticated using (((select auth.uid())=sender_id or (select auth.uid())=recipient_id) and coalesce((select auth.jwt()->>'is_anonymous'),'false')='false');

create function scrobble_private.save_native_token(p_token text) returns void
language plpgsql security definer set search_path='' as $$
declare uid uuid:=auth.uid();
begin
  if uid is null or not exists(select 1 from auth.users where id=uid and is_anonymous=false) then raise exception 'Not signed in'; end if;
  if p_token is null or length(p_token)<64 or length(p_token)>512 or p_token !~ '^[a-fA-F0-9]+$' then raise exception 'Invalid device token'; end if;
  insert into public.scrobble_native_push_tokens(token,user_id) values(lower(p_token),uid)
  on conflict(token) do update set user_id=excluded.user_id,updated_at=now();
end;$$;
create function public.save_scrobble_native_push_token(p_token text) returns void
language sql security invoker set search_path='' as $$ select scrobble_private.save_native_token(p_token); $$;

create function scrobble_private.delete_native_token(p_token text) returns void
language plpgsql security definer set search_path='' as $$
begin
  if auth.uid() is null then raise exception 'Not signed in'; end if;
  delete from public.scrobble_native_push_tokens where token=lower(p_token) and user_id=auth.uid();
end;$$;
create function public.delete_scrobble_native_push_token(p_token text) returns void
language sql security invoker set search_path='' as $$ select scrobble_private.delete_native_token(p_token); $$;

create function scrobble_private.queue_notification(p_game uuid,p_sender uuid,p_recipient uuid,p_kind text)
returns uuid language plpgsql security definer set search_path='' as $$
declare event_id uuid; edge_url text; edge_secret text; sender_name text; game_version timestamptz;
begin
  select decrypted_secret into edge_url from vault.decrypted_secrets where name='scrobble_push_url' limit 1;
  select decrypted_secret into edge_secret from vault.decrypted_secrets where name='scrobble_push_secret' limit 1;
  if coalesce(edge_url,'')='' or coalesce(edge_secret,'')='' then raise exception 'Notifications are not configured'; end if;
  select coalesce(display_name,'Your opponent') into sender_name from public.profiles where id=p_sender;
  select updated_at into game_version from public.games where id=p_game;
  insert into public.scrobble_notification_events(game_id,sender_id,recipient_id,kind)
  values(p_game,p_sender,p_recipient,p_kind) returning id into event_id;
  perform net.http_post(url:=edge_url,headers:=jsonb_build_object('Content-Type','application/json','x-scrobble-secret',edge_secret),
    body:=jsonb_build_object('user_id',p_recipient,'game_id',p_game,'opponent_name',coalesce(sender_name,'Your opponent'),'kind',p_kind,'event_id',event_id,'game_version',game_version));
  return event_id;
end;$$;

create function scrobble_private.nudge_game(p_game_id uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare uid uuid:=auth.uid(); g public.games%rowtype; last_sent timestamptz; event_id uuid;
begin
  if uid is null or not exists(select 1 from auth.users where id=uid and is_anonymous=false) then raise exception 'Not signed in'; end if;
  if not exists(select 1 from public.game_players where game_id=p_game_id and player_id=uid) then raise exception 'Game not found'; end if;
  select * into g from public.games where id=p_game_id for update;
  if g.status<>'active' or g.current_player_id is null or g.current_player_id=uid
     or not exists(select 1 from public.game_players where game_id=g.id and player_id=g.current_player_id and player_id<>uid)
  then return jsonb_build_object('ok',false,'reason','not_waiting'); end if;
  select max(created_at) into last_sent from public.scrobble_notification_events where game_id=g.id and sender_id=uid and kind='nudge' and status in ('queued','delivered');
  if last_sent>now()-interval '12 hours' then return jsonb_build_object('ok',false,'reason','cooldown','available_at',last_sent+interval '12 hours'); end if;
  if not exists(select 1 from public.scrobble_native_push_tokens where user_id=g.current_player_id)
     and not exists(select 1 from public.scrobble_push_subscriptions where user_id=g.current_player_id)
  then return jsonb_build_object('ok',false,'reason','notifications_off'); end if;
  event_id:=scrobble_private.queue_notification(g.id,uid,g.current_player_id,'nudge');
  return jsonb_build_object('ok',true,'event_id',event_id);
end;$$;
create function public.nudge_scrobble_game(p_game_id uuid) returns jsonb
language sql security invoker set search_path='' as $$ select scrobble_private.nudge_game(p_game_id); $$;

create function scrobble_private.turn_notification_trigger() returns trigger
language plpgsql security definer set search_path='' as $$
declare actor uuid:=auth.uid();
begin
  if new.status<>'active' or new.current_player_id is null or old.current_player_id is not distinct from new.current_player_id or actor=new.current_player_id then return new; end if;
  if not exists(select 1 from public.game_players where game_id=new.id and player_id=new.current_player_id) then return new; end if;
  if actor is null then select player_id into actor from public.game_players where game_id=new.id and player_id<>new.current_player_id limit 1; end if;
  begin perform scrobble_private.queue_notification(new.id,actor,new.current_player_id,'turn');
  exception when others then raise warning 'Scrobble notification could not be queued'; end;
  return new;
end;$$;
drop trigger scrobble_turn_push_after_update on public.games;
create trigger scrobble_turn_push_after_update after update of current_player_id on public.games for each row execute function scrobble_private.turn_notification_trigger();

revoke all on all functions in schema scrobble_private from public,anon,authenticated;
grant execute on function scrobble_private.save_native_token(text),scrobble_private.delete_native_token(text),scrobble_private.nudge_game(uuid) to authenticated;
revoke all on function public.save_scrobble_native_push_token(text),public.delete_scrobble_native_push_token(text),public.nudge_scrobble_game(uuid) from public,anon;
grant execute on function public.save_scrobble_native_push_token(text),public.delete_scrobble_native_push_token(text),public.nudge_scrobble_game(uuid) to authenticated;
