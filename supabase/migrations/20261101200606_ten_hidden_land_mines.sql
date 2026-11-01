-- New games receive ten mines. Existing concealed layouts remain untouched.
create or replace function scrobble_private.random_mines() returns jsonb
language plpgsql volatile set search_path='' as $$
declare chosen jsonb; cell record; attempt integer;
begin
 for attempt in 1..1000 loop
  chosen:='[]'::jsonb;
  for cell in select r,c from generate_series(0,14) r cross join generate_series(0,14) c order by random() loop
   if not exists(select 1 from jsonb_array_elements(chosen) p where
      ((p->>0)::int-cell.r)^2+((p->>1)::int-cell.c)^2<25) then
    chosen:=chosen||jsonb_build_array(jsonb_build_array(cell.r,cell.c));
    if jsonb_array_length(chosen)=10 then return chosen; end if;
   end if;
  end loop;
 end loop;
 raise exception 'Could not place ten separated mines';
end $$;
revoke all on function scrobble_private.random_mines() from public,anon,authenticated;
