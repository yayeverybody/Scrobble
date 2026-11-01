-- Hidden multiplayer coordinates never enter client-readable tables or RPC responses.
create schema if not exists scrobble_private;
revoke all on schema scrobble_private from public,anon,authenticated;
create table scrobble_private.land_mines (
 game_id uuid primary key references public.games(id) on delete cascade,
 positions jsonb not null
);
alter table scrobble_private.land_mines enable row level security;
revoke all on scrobble_private.land_mines from public,anon,authenticated;
alter table public.game_moves add column land_mines jsonb not null default '[]'::jsonb;

create function scrobble_private.random_mines() returns jsonb
language plpgsql volatile set search_path='' as $$
declare chosen jsonb; cell record; attempt integer;
begin
 for attempt in 1..100 loop
  chosen:='[]'::jsonb;
  for cell in select r,c from generate_series(0,14) r cross join generate_series(0,14) c order by random() loop
   if not exists(select 1 from jsonb_array_elements(chosen) p where greatest(abs((p->>0)::int-cell.r),abs((p->>1)::int-cell.c))<5) then
    chosen:=chosen||jsonb_build_array(jsonb_build_array(cell.r,cell.c));
    if jsonb_array_length(chosen)=5 then return chosen; end if;
   end if;
  end loop;
 end loop;
 raise exception 'Could not place five separated mines';
end $$;
revoke all on function scrobble_private.random_mines() from public,anon,authenticated;

create function scrobble_private.initialize_mines() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if coalesce(new.weird_rules,'[]'::jsonb) ? 'hidden_land_mines' then
  if tg_op='UPDATE' and old.weird_rules is distinct from new.weird_rules
     and exists(select 1 from public.game_moves where game_id=new.id) then
   raise exception 'Cannot change mine rules after a game starts';
  end if;
  insert into scrobble_private.land_mines(game_id,positions)
   values(new.id,scrobble_private.random_mines()) on conflict(game_id) do nothing;
 end if;
 return new;
end $$;
revoke all on function scrobble_private.initialize_mines() from public,anon,authenticated;
create trigger initialize_hidden_land_mines after insert or update of weird_rules on public.games
 for each row execute function scrobble_private.initialize_mines();

create function scrobble_private.resolve_mines(game uuid,old_board jsonb,new_board jsonb) returns jsonb
language plpgsql set search_path='' as $$
declare hits jsonb:='[]'::jsonb; p jsonb; r integer; c integer;
begin
 -- Restore detonated markers even when an older client omitted them.
 for r in 0..14 loop for c in 0..14 loop
  if coalesce((old_board->r->c->>'landMine')::boolean,false) then
   new_board:=jsonb_set(new_board,array[r::text,c::text,'landMine'],'true'::jsonb);
  end if;
 end loop; end loop;
 for p in select jsonb_array_elements(positions) from scrobble_private.land_mines where game_id=game loop
  r:=(p->>0)::int;c:=(p->>1)::int;
  if (old_board->r->c is null or old_board->r->c='null'::jsonb)
     and new_board->r->c is not null and new_board->r->c<>'null'::jsonb then
   hits:=hits||jsonb_build_array(p);
   new_board:=jsonb_set(new_board,array[r::text,c::text,'landMine'],'true'::jsonb);
  end if;
 end loop;
 return jsonb_build_object('board',new_board,'hits',hits);
end $$;
revoke all on function scrobble_private.resolve_mines(uuid,jsonb,jsonb) from public,anon,authenticated;

CREATE OR REPLACE FUNCTION public.save_scrobble_turn(p_game_id uuid, p_board jsonb, p_bag jsonb, p_score_1 integer, p_score_2 integer, p_rack jsonb, p_move_type text, p_words jsonb, p_points integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  uid uuid := auth.uid();
  g public.games%rowtype;
  gp public.game_players%rowtype;
  opponent public.game_players%rowtype;
  next_player uuid;
  deduction integer := 0;
  final_score_1 integer := p_score_1;
  final_score_2 integer := p_score_2;
  winner uuid;
  finished boolean := false;
  mine_result jsonb;
  mine_hits jsonb := '[]'::jsonb;
begin
  if uid is null then raise exception 'Not signed in'; end if;
  select * into g from public.games where id=p_game_id for update;
  if g.id is null then raise exception 'Game not found'; end if;
  if g.status <> 'active' then raise exception 'Game is not active'; end if;
  if g.current_player_id <> uid then raise exception 'It is not your turn'; end if;

  select * into gp from public.game_players
  where game_id=p_game_id and player_id=uid;
  if gp.game_id is null then raise exception 'You are not in this game'; end if;
  select * into opponent from public.game_players
  where game_id=p_game_id and player_id<>uid limit 1;
  if opponent.game_id is null then raise exception 'Your opponent has not joined yet'; end if;
  next_player := opponent.player_id;

  if p_move_type='play' and coalesce(g.weird_rules,'[]'::jsonb) ? 'hidden_land_mines' then
    mine_result:=scrobble_private.resolve_mines(p_game_id,g.board,p_board);
    p_board:=mine_result->'board';mine_hits:=mine_result->'hits';
    if jsonb_array_length(mine_hits)>0 then
      p_points:=-abs(p_points);
      final_score_1:=g.score_1;final_score_2:=g.score_2;
      if gp.player_number=1 then final_score_1:=g.score_1+p_points;
      else final_score_2:=g.score_2+p_points; end if;
    end if;
  end if;

  update public.game_players set rack=p_rack
  where game_id=p_game_id and player_id=uid;

  finished := p_move_type='play'
    and jsonb_array_length(coalesce(p_bag,'[]'::jsonb))=0
    and jsonb_array_length(coalesce(p_rack,'[]'::jsonb))=0;

  if finished then
    select coalesce(sum(case value
      when 'A' then case when coalesce(g.weird_rules,'[]'::jsonb) ? 'vowels_are_worth_too_much' then 20 else 1 end when 'B' then 4 when 'C' then 4 when 'D' then 2
      when 'E' then case when coalesce(g.weird_rules,'[]'::jsonb) ? 'vowels_are_worth_too_much' then 20 else 1 end when 'F' then 4 when 'G' then 3 when 'H' then 3
      when 'I' then case when coalesce(g.weird_rules,'[]'::jsonb) ? 'vowels_are_worth_too_much' then 20 else 1 end when 'J' then 10 when 'K' then 5 when 'L' then 2
      when 'M' then 4 when 'N' then 2 when 'O' then case when coalesce(g.weird_rules,'[]'::jsonb) ? 'vowels_are_worth_too_much' then 20 else 1 end when 'P' then 4
      when 'Q' then 10 when 'R' then 1 when 'S' then 1 when 'T' then 1
      when 'U' then case when coalesce(g.weird_rules,'[]'::jsonb) ? 'vowels_are_worth_too_much' then 20 else 2 end when 'V' then 5 when 'W' then 4 when 'X' then 8
      when 'Y' then 3 when 'Z' then 10 else 0 end),0)::integer
    into deduction from jsonb_array_elements_text(coalesce(opponent.rack,'[]'::jsonb));
    if gp.player_number=1 then
      final_score_1:=final_score_1+deduction;final_score_2:=final_score_2-deduction;
    else
      final_score_2:=final_score_2+deduction;final_score_1:=final_score_1-deduction;
    end if;
    select player_id into winner from public.game_players
    where game_id=p_game_id
      and player_number=case when final_score_1>final_score_2 then 1
                             when final_score_2>final_score_1 then 2 else 0 end;
  end if;

  update public.games set board=p_board,bag=p_bag,score_1=final_score_1,score_2=final_score_2,
    current_player_id=case when finished then uid else next_player end,
    status=case when finished then 'completed' else status end,
    winner_id=case when finished then winner else winner_id end,
    challenge=case when finished then null else challenge end,updated_at=now()
  where id=p_game_id;

  insert into public.game_moves(game_id,player_id,move_type,words,points,board_after,land_mines)
  values(p_game_id,uid,p_move_type,coalesce(p_words,'[]'::jsonb),coalesce(p_points,0),p_board,mine_hits);

  return jsonb_build_object('ok',true,'points',p_points,'landMines',mine_hits,'completed',finished,
    'next_player_id',case when finished then null else next_player end,
    'finisher_slot',case when finished then gp.player_number else null end,
    'deduction',deduction,'scores',jsonb_build_array(final_score_1,final_score_2),
    'winner_id',winner);
end;
$function$;

CREATE OR REPLACE FUNCTION public.get_scrobble_game(p_game_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  uid uuid := auth.uid();
  g public.games%rowtype;
  gp public.game_players%rowtype;
  opp uuid;
  p1 uuid;
  p2 uuid;
  slot smallint;
  prof1 jsonb;
  prof2 jsonb;
  lm public.game_moves%rowtype;
  lm_player_number smallint;
  last_move_summary jsonb;
begin
  if uid is null then
    raise exception 'Not signed in';
  end if;

  select *
  into gp
  from public.game_players
  where game_id=p_game_id
    and player_id=uid;

  if gp.game_id is null then
    raise exception 'You are not in this game';
  end if;

  select * into g
  from public.games
  where id=p_game_id;

  select player_id into p1
  from public.game_players
  where game_id=p_game_id and player_number=1;

  select player_id into p2
  from public.game_players
  where game_id=p_game_id and player_number=2;

  select player_id into opp
  from public.game_players
  where game_id=p_game_id and player_id<>uid
  limit 1;

  slot := case
    when g.current_player_id=p1 then 0
    else 1
  end;

  select jsonb_build_object(
    'id',p1,
    'display_name',p.display_name,
    'avatar_url',p.avatar_url
  )
  into prof1
  from public.profiles p
  where p.id=p1;

  if prof1 is null then
    prof1:=jsonb_build_object(
      'id',p1,
      'display_name',null,
      'avatar_url',null
    );
  end if;

  if p2 is not null then
    select jsonb_build_object(
      'id',p2,
      'display_name',p.display_name,
      'avatar_url',p.avatar_url
    )
    into prof2
    from public.profiles p
    where p.id=p2;

    if prof2 is null then
      prof2:=jsonb_build_object(
        'id',p2,
        'display_name',null,
        'avatar_url',null
      );
    end if;
  end if;

  select *
  into lm
  from public.game_moves
  where game_id=p_game_id
  order by created_at desc,id desc
  limit 1;

  if lm.id is not null then
    select player_number
    into lm_player_number
    from public.game_players
    where game_id=p_game_id
      and player_id=lm.player_id;

    last_move_summary:=jsonb_build_object(
      'playedBy',greatest(coalesce(lm_player_number,1)-1,0),
      'move_type',lm.move_type,
      'words',coalesce(lm.words,'[]'::jsonb),
      'points',coalesce(lm.points,0),
      'landMines',lm.land_mines
    );
  end if;

  return jsonb_build_object(
    'id',g.id,
    'board',g.board,
    'bag',g.bag,
    'scores',jsonb_build_array(g.score_1,g.score_2),
    'current_player_id',g.current_player_id,
    'current_slot',slot,
    'player_number',gp.player_number,
    'rack',gp.rack,
    'opponent_id',opp,
    'status',g.status,
    'invite_code',g.invite_code,
    'updated_at',g.updated_at,
    'challenge',g.challenge,
    'player1_profile',prof1,
    'player2_profile',prof2,
    'lastMoveSummary',last_move_summary,
    'weird_rules',coalesce(g.weird_rules,'[]'::jsonb)
  );
end;
$function$;

CREATE OR REPLACE FUNCTION public.resolve_scrobble_challenge(p_game_id uuid, p_accept boolean)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  uid uuid := auth.uid();
  g public.games%rowtype;
  ch jsonb;
  challenger uuid;
  challenger_num smallint;
  mine_result jsonb;
  mine_hits jsonb := '[]'::jsonb;
begin
  if uid is null then raise exception 'Not signed in'; end if;

  select * into g from public.games where id = p_game_id for update;
  if g.id is null then raise exception 'Game not found'; end if;
  if g.current_player_id <> uid then
    raise exception 'Only the reviewing opponent can decide this word';
  end if;
  if g.challenge is null then
    raise exception 'There is no word awaiting review';
  end if;

  ch := g.challenge;
  challenger := (ch->>'challenger_id')::uuid;
  challenger_num := (ch->>'challenger_player_number')::smallint;

  if p_accept then
    if coalesce(g.weird_rules,'[]'::jsonb) ? 'hidden_land_mines' then
      mine_result:=scrobble_private.resolve_mines(p_game_id,g.board,ch->'candidate_board');
      mine_hits:=mine_result->'hits';
      ch:=jsonb_set(ch,'{candidate_board}',mine_result->'board');
      if jsonb_array_length(mine_hits)>0 then
        ch:=jsonb_set(ch,'{points}',to_jsonb(-abs((ch->>'points')::integer)));
        ch:=jsonb_set(ch,'{score_1}',to_jsonb(g.score_1+case when challenger_num=1 then (ch->>'points')::integer else 0 end));
        ch:=jsonb_set(ch,'{score_2}',to_jsonb(g.score_2+case when challenger_num=2 then (ch->>'points')::integer else 0 end));
      end if;
    end if;
    update public.games
    set board = ch->'candidate_board',
        bag = ch->'candidate_bag',
        score_1 = coalesce((ch->>'score_1')::integer, score_1),
        score_2 = coalesce((ch->>'score_2')::integer, score_2),
        challenge = null,
        updated_at = now()
    where id = p_game_id;

    update public.game_players
    set rack = ch->'candidate_rack'
    where game_id = p_game_id
      and player_id = challenger;

    insert into public.game_moves(
      game_id,
      player_id,
      move_type,
      words,
      points,
      board_after,
      land_mines
    )
    values(
      p_game_id,
      challenger,
      'play',
      coalesce(ch->'words','[]'::jsonb),
      coalesce((ch->>'points')::integer,0),
      ch->'candidate_board',
      mine_hits
    );
  else
    update public.games
    set challenge = null,
        updated_at = now()
    where id = p_game_id;
  end if;

  -- Reviewer keeps the turn either way.
  -- If denied, the invalid play costs the challenger the turn.
  return jsonb_build_object(
    'ok', true,
    'accepted', p_accept,
    'current_player_id', uid
  );
end;
$function$;
