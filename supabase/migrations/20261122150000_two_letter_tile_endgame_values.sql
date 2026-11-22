-- Keep the existing multiplayer RPCs and count each two-letter tile as 15.
do $migration$
declare
  routine regprocedure;
  source text;
  marker constant text := 'when ''Z'' then 10 else 0 end';
begin
  for routine in
    select unnest(array[
      'public.save_scrobble_turn(uuid,jsonb,jsonb,integer,integer,jsonb,text,jsonb,integer)'::regprocedure,
      'public.finish_scrobble_game(uuid)'::regprocedure
    ])
  loop
    source := pg_get_functiondef(routine);
    if strpos(source, 'when ''SH'' then 15') > 0 then continue; end if;
    if (length(source)-length(replace(source,marker,'')))/length(marker) <> 1 then
      raise exception 'Expected one rack value expression in %',routine;
    end if;
    execute replace(source,marker,
      'when ''Z'' then 10 when ''SH'' then 15 when ''CH'' then 15 when ''TH'' then 15 else 0 end');
  end loop;
end;
$migration$;
