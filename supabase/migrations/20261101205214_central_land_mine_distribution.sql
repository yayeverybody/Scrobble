-- Seed the active middle first; existing games keep their private saved positions.
create or replace function scrobble_private.random_mines() returns jsonb
language plpgsql volatile set search_path='' as $$
declare chosen jsonb; cell record; attempt integer; phase integer; target integer;
begin
 for attempt in 1..1000 loop
  chosen:='[]'::jsonb;
  for phase in 1..2 loop
   target:=case when phase=1 then 2 else 10 end;
   for cell in select r,c from generate_series(0,14) r cross join generate_series(0,14) c
    where phase=2 or (r between 4 and 10 and c between 4 and 10) order by random() loop
    if not exists(select 1 from jsonb_array_elements(chosen) p where
       ((p->>0)::int-cell.r)^2+((p->>1)::int-cell.c)^2<9) then
     chosen:=chosen||jsonb_build_array(jsonb_build_array(cell.r,cell.c));
     if jsonb_array_length(chosen)=target then exit; end if;
    end if;
   end loop;
  end loop;
  if jsonb_array_length(chosen)=10 then return chosen; end if;
 end loop;
 raise exception 'Could not place ten separated land mines with two in the center';
end $$;
revoke all on function scrobble_private.random_mines() from public,anon,authenticated;
