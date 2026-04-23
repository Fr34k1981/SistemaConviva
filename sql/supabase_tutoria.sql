create extension if not exists pgcrypto;

create table if not exists public.tutoria (
    id uuid primary key default gen_random_uuid(),
    professora text not null,
    nome_aluno text not null,
    serie text default '',
    origem text default 'manual',
    tipo text default 'Professor(a)',
    espaco text default '',
    horario text default '',
    dia text default '',
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists tutoria_unq_professora_nome_serie
    on public.tutoria (professora, nome_aluno, serie);

create index if not exists tutoria_idx_professora
    on public.tutoria (professora);

create or replace function public.set_updated_at_tutoria()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = timezone('utc', now());
    return new;
end;
$$;

drop trigger if exists trg_set_updated_at_tutoria on public.tutoria;

create trigger trg_set_updated_at_tutoria
before update on public.tutoria
for each row
execute function public.set_updated_at_tutoria();

alter table public.tutoria enable row level security;

drop policy if exists "tutoria_select_authenticated" on public.tutoria;
create policy "tutoria_select_authenticated"
on public.tutoria
for select
to anon, authenticated
using (true);

drop policy if exists "tutoria_insert_authenticated" on public.tutoria;
create policy "tutoria_insert_authenticated"
on public.tutoria
for insert
to anon, authenticated
with check (true);

drop policy if exists "tutoria_update_authenticated" on public.tutoria;
create policy "tutoria_update_authenticated"
on public.tutoria
for update
to anon, authenticated
using (true)
with check (true);

drop policy if exists "tutoria_delete_authenticated" on public.tutoria;
create policy "tutoria_delete_authenticated"
on public.tutoria
for delete
to anon, authenticated
using (true);
