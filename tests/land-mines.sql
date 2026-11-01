-- All fixture writes are rolled back inside this subtransaction, including queued notifications.
do $test$
declare
 game uuid:=gen_random_uuid();u1 uuid;u2 uuid;board jsonb;candidate jsonb;p jsonb;p2 jsonb;positions jsonb;
 result jsonb;snapshot jsonb;r integer;c integer;n integer;rr integer;cc integer;ch jsonb;
begin
 for n in 1..100 loop
  positions:=scrobble_private.random_mines();
  assert jsonb_array_length(positions)=10,'Exactly ten mines';
  assert not exists(select 1 from jsonb_array_elements(positions) a cross join jsonb_array_elements(positions) b where a<>b and ((a->>0)::int-(b->>0)::int)^2+((a->>1)::int-(b->>1)::int)^2<25),'Spacing includes diagonals';
 end loop;
 select player_id into u1 from public.game_players limit 1;
 select player_id into u2 from public.game_players where player_id<>u1 limit 1;
 assert u1 is not null and u2 is not null,'Two existing players available for rollback-only fixtures';
 select jsonb_agg(row) into board from (select jsonb_agg(null::text) as row from generate_series(1,15) a cross join generate_series(1,15) b group by a) x;
 insert into public.games(id,status,current_player_id,board,bag,score_1,score_2,weird_rules)
 values(game,'active',u1,board,'["E"]',100,0,'["hidden_land_mines"]');
 insert into public.game_players(game_id,player_id,player_number,rack) values(game,u1,1,'["A"]'),(game,u2,2,'["B"]');
 select m.positions into positions from scrobble_private.land_mines m where game_id=game;
 assert jsonb_array_length(positions)=10,'Initialized once for game';
 perform set_config('request.jwt.claim.sub',u1::text,true);
 perform public.set_scrobble_weird_rules(game,'["hidden_land_mines"]');
 assert positions=(select m.positions from scrobble_private.land_mines m where game_id=game),'Rules retry cannot reroll mines';
 p:=positions->0;r:=(p->>0)::int;c:=(p->>1)::int;
 candidate:=jsonb_set(board,array[r::text,c::text],'{"letter":"A","owner":0}');
 result:=public.save_scrobble_turn(game,candidate,'["E"]',130,0,'["A"]','play','["A"]',30);
 assert result->'scores'='[70,0]'::jsonb,'30 is subtracted, never awarded';
 assert result->>'points'='-30','Signed points returned';
 assert jsonb_array_length(result->'landMines')=1,'Only detonated coordinate returned';
 snapshot:=public.get_scrobble_game(game);board:=snapshot->'board';
 assert board->r->c->>'letter'='A','Letters remain';
 assert board->r->c->>'landMine'='true','Permanent red marker';
 assert snapshot->'lastMoveSummary'->>'points'='-30','Opponent receives negative score';
 assert jsonb_array_length(snapshot->'lastMoveSummary'->'landMines')=1,'Opponent receives explosion';
 assert not(snapshot ? 'land_mines') and not(snapshot ? 'positions'),'Untriggered positions are never returned';
 -- A later play across the same occupied mine does not detonate it again.
 select a,b into rr,cc from generate_series(0,14) a cross join generate_series(0,14) b
 where not exists(select 1 from jsonb_array_elements(positions) m where (m->>0)::int=a and (m->>1)::int=b) limit 1;
 candidate:=jsonb_set(board,array[rr::text,cc::text],'{"letter":"T","owner":0}');
 update public.games set current_player_id=u1 where id=game;
 result:=public.save_scrobble_turn(game,candidate,'["E"]',90,0,'["A"]','play','["AT"]',20);
 assert result->'scores'='[90,0]'::jsonb,'Spent mine does not retrigger';
 assert result->'landMines'='[]'::jsonb,'No duplicate explosion';
 board:=candidate;p2:=positions->1;r:=(p2->>0)::int;c:=(p2->>1)::int;
 candidate:=jsonb_set(board,array[r::text,c::text],'{"letter":"B","owner":0}');
 ch:=jsonb_build_object('challenger_id',u1,'challenger_player_number',1,'candidate_board',candidate,'candidate_bag','["E"]'::jsonb,'candidate_rack','["A"]'::jsonb,'score_1',100,'score_2',0,'points',10,'words','["AB"]'::jsonb);
 update public.games set challenge=ch,current_player_id=u2 where id=game;
 perform set_config('request.jwt.claim.sub',u2::text,true);
 perform public.resolve_scrobble_challenge(game,false);
 assert (select g.board->r->c from public.games g where g.id=game)='null'::jsonb,'Denied word cannot trigger mine';
 update public.games set challenge=ch where id=game;
 perform public.resolve_scrobble_challenge(game,true);
 assert (select score_1 from public.games where id=game)=80,'Approved word triggers deduction';
 assert (select g.board->r->c->>'landMine' from public.games g where g.id=game)='true','Approved word reveals mine';
 -- Multiple mines on a move produce one deduction; negative totals are allowed.
 select g.board into board from public.games g where g.id=game;
 for p in select value from jsonb_array_elements(positions) with ordinality where ordinality in (3,4) loop
  r:=(p->>0)::int;c:=(p->>1)::int;board:=jsonb_set(board,array[r::text,c::text],'{"letter":"C","owner":0}');
 end loop;
 update public.games set current_player_id=u1 where id=game;
 perform set_config('request.jwt.claim.sub',u1::text,true);
 result:=public.save_scrobble_turn(game,board,'["E"]',180,0,'["A"]','play','["CC"]',100);
 assert result->'scores'='[-20,0]'::jsonb,'Multiple hits deduct once and can go negative';
 assert jsonb_array_length(result->'landMines')=2,'Both triggered spaces revealed';
 -- Finishing on a mine still applies the usual remaining-rack adjustment.
 select g.board into board from public.games g where g.id=game;
 p:=positions->4;r:=(p->>0)::int;c:=(p->>1)::int;
 board:=jsonb_set(board,array[r::text,c::text],'{"letter":"D","owner":0}');
 update public.games set current_player_id=u1 where id=game;
 result:=public.save_scrobble_turn(game,board,'[]',10,0,'[]','play','["CD"]',30);
 assert result->>'completed'='true','Mine on final move completes game';
 assert result->'scores'='[-46,-4]'::jsonb,'Mine penalty precedes endgame rack transfer';
 select jsonb_agg(row) into board from (select jsonb_agg(null::text) as row from generate_series(1,15) a cross join generate_series(1,15) b group by a) x;
 result:=public.create_scrobble_rematch(game,board,'["E"]','["A"]','["B"]');
 assert (select jsonb_array_length(m.positions) from scrobble_private.land_mines m where m.game_id=(result->>'id')::uuid)=10,'Rematch gets ten fresh hidden mines';
 assert not has_schema_privilege('authenticated','scrobble_private','usage'),'Private coordinates inaccessible';
 raise sqlstate 'P9999' using message='All Hidden Land Mines SQL tests passed; rolling back fixtures';
exception when sqlstate 'P9999' then
 raise notice 'PASS: 100 random boards, stable initialization, server deductions, private coordinates, notices, denied/accepted challenges, spent mines and multiple hits. Fixture changes rolled back.';
end $test$;
