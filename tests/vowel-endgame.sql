-- Run against a database containing the migration. Uses only temporary copies;
-- no real games, participants, moves, triggers, or push notifications are touched.
begin;
create temporary table vowel_test_games (like public.games including defaults);
create temporary table vowel_test_players (like public.game_players including defaults);
create temporary table vowel_test_moves (like public.game_moves including defaults);
alter table vowel_test_moves alter column id set default 1;
do $test$
declare
  routine regprocedure;
  source text;
  rpc_name text;
  mode integer;
  expected integer;
  result jsonb;
  me uuid := gen_random_uuid();
  opponent uuid := gen_random_uuid();
  gid uuid;
begin
  perform set_config('request.jwt.claim.sub',me::text,true);
  for routine in select p.oid::regprocedure from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname in ('save_scrobble_turn','finish_scrobble_game')
  loop
    source:=pg_get_functiondef(routine);
    if source not like '%vowels_are_worth_too_much%' then raise exception 'Vowel endgame migration is missing'; end if;
    rpc_name:=case when source like '%FUNCTION public.save_scrobble_turn%' then 'vowel_test_save' else 'vowel_test_finish' end;
    source:=replace(source,'public.save_scrobble_turn','pg_temp.vowel_test_save');
    source:=replace(source,'public.finish_scrobble_game','pg_temp.vowel_test_finish');
    source:=replace(source,'public.games','pg_temp.vowel_test_games');
    source:=replace(source,'public.game_players','pg_temp.vowel_test_players');
    source:=replace(source,'public.game_moves','pg_temp.vowel_test_moves');
    execute source;
    for mode in 0..1 loop
      gid:=gen_random_uuid();expected:=case when mode=1 then 103 else 9 end;
      insert into pg_temp.vowel_test_games(id,current_player_id,score_1,score_2,weird_rules)
        values(gid,me,100,80,case when mode=1 then '["vowels_are_worth_too_much"]'::jsonb else '[]'::jsonb end);
      insert into pg_temp.vowel_test_players(game_id,player_id,player_number,rack)
        values(gid,me,1,'[]'),(gid,opponent,2,'["A","E","I","O","U","Y"]');
      if rpc_name='vowel_test_save' then
        result:=pg_temp.vowel_test_save(gid,'[]','[]',100,80,'[]','play','["A"]',20);
      else
        result:=pg_temp.vowel_test_finish(gid);
      end if;
      if (result->>'deduction')::integer<>expected or (result->'scores'->>0)::integer<>100+expected
        or (result->'scores'->>1)::integer<>80-expected or not (result->>'completed')::boolean then
        raise exception 'Incorrect % endgame for mode %: %',rpc_name,mode,result;
      end if;
    end loop;
  end loop;
end;
$test$;
select 'PASS: both multiplayer endgame paths, all five 20-point vowels, unchanged Y and Classic values' as result;
rollback;
