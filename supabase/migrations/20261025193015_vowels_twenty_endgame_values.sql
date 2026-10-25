-- Preserve both existing endgame RPCs, permissions, and auth/turn checks.
-- Only the five vowel deduction values change, and only for the new rule.
do $migration$
declare
  routine regprocedure;
  source text;
  letter text;
  normal_value integer;
  old_value text;
  new_value text;
begin
  for routine in
    select p.oid::regprocedure from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname in ('save_scrobble_turn','finish_scrobble_game')
  loop
    source := pg_get_functiondef(routine);
    if source like '%vowels_are_worth_too_much%' then continue; end if;
    foreach letter in array array['A','E','I','O','U'] loop
      normal_value := case when letter='U' then 2 else 1 end;
      old_value := format('when %L then %s',letter,normal_value);
      new_value := format('when %L then case when coalesce(g.weird_rules,''[]''::jsonb) ? ''vowels_are_worth_too_much'' then 20 else %s end',letter,normal_value);
      if (length(source)-length(replace(source,old_value,'')))/length(old_value) <> 1 then
        raise exception 'Expected exactly one tile value for % in %',letter,routine;
      end if;
      source := replace(source,old_value,new_value);
    end loop;
    execute source;
  end loop;
end;
$migration$;
