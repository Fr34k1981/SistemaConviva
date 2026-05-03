-- Sistema Conviva 179 - Estabilizacao Prova Paulista, Mapao, Tutoria e Conselho
-- Script idempotente. Revisar em staging antes de aplicar em producao.

create extension if not exists pgcrypto;

create table if not exists public.prova_paulista_resultados (
    id uuid primary key default gen_random_uuid(),
    ano_letivo text not null,
    bimestre text not null,
    turma text not null,
    ciclo text default '',
    turno text default '',
    ra text not null,
    estudante text not null,
    participacao numeric,
    acertos_percentual numeric,
    componentes jsonb default '{}'::jsonb,
    arquivo_origem text default '',
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists prova_paulista_resultados_unq
    on public.prova_paulista_resultados (ano_letivo, bimestre, turma, ra);

create index if not exists prova_paulista_resultados_turma_idx
    on public.prova_paulista_resultados (ano_letivo, bimestre, turma);

create table if not exists public.mapao_resultados (
    id uuid primary key default gen_random_uuid(),
    ano_letivo text not null,
    bimestre text not null,
    turma text not null,
    ciclo text default '',
    turno text default '',
    estudante text not null,
    situacao text default '',
    total_aulas numeric,
    frequencia_percentual numeric,
    faltas numeric,
    faltas_anuais numeric,
    componentes jsonb default '{}'::jsonb,
    notas_abaixo_cinco jsonb default '[]'::jsonb,
    arquivo_origem text default '',
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists mapao_resultados_unq
    on public.mapao_resultados (ano_letivo, bimestre, turma, estudante);

create index if not exists mapao_resultados_turma_idx
    on public.mapao_resultados (ano_letivo, bimestre, turma);

create table if not exists public.tutoria_responsaveis (
    id uuid primary key default gen_random_uuid(),
    responsavel text not null,
    perfil text default 'Professor(a)',
    espaco text default '',
    horario text default '',
    dia text default '',
    turno text default '',
    ativo boolean not null default true,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists tutoria_responsaveis_unq
    on public.tutoria_responsaveis (responsavel);

create table if not exists public.conselho_atas (
    id uuid primary key default gen_random_uuid(),
    ano_letivo text not null,
    bimestre text not null,
    turma text not null,
    ciclo text default '',
    turno text default '',
    data_conselho date,
    dados_ata jsonb default '{}'::jsonb,
    tabela_estudantes jsonb default '[]'::jsonb,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists conselho_atas_unq
    on public.conselho_atas (ano_letivo, bimestre, turma);

create or replace function public.set_updated_at_conviva179()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = timezone('utc', now());
    return new;
end;
$$;

drop trigger if exists trg_prova_paulista_updated_at on public.prova_paulista_resultados;
create trigger trg_prova_paulista_updated_at
before update on public.prova_paulista_resultados
for each row execute function public.set_updated_at_conviva179();

drop trigger if exists trg_mapao_updated_at on public.mapao_resultados;
create trigger trg_mapao_updated_at
before update on public.mapao_resultados
for each row execute function public.set_updated_at_conviva179();

drop trigger if exists trg_tutoria_responsaveis_updated_at on public.tutoria_responsaveis;
create trigger trg_tutoria_responsaveis_updated_at
before update on public.tutoria_responsaveis
for each row execute function public.set_updated_at_conviva179();

drop trigger if exists trg_conselho_atas_updated_at on public.conselho_atas;
create trigger trg_conselho_atas_updated_at
before update on public.conselho_atas
for each row execute function public.set_updated_at_conviva179();

alter table public.prova_paulista_resultados enable row level security;
alter table public.mapao_resultados enable row level security;
alter table public.tutoria_responsaveis enable row level security;
alter table public.conselho_atas enable row level security;

do $$
declare
    tabela text;
begin
    foreach tabela in array array[
        'prova_paulista_resultados',
        'mapao_resultados',
        'tutoria_responsaveis',
        'conselho_atas'
    ]
    loop
        execute format('drop policy if exists %I on public.%I', tabela || '_select', tabela);
        execute format('create policy %I on public.%I for select to anon, authenticated using (true)', tabela || '_select', tabela);
        execute format('drop policy if exists %I on public.%I', tabela || '_insert', tabela);
        execute format('create policy %I on public.%I for insert to anon, authenticated with check (true)', tabela || '_insert', tabela);
        execute format('drop policy if exists %I on public.%I', tabela || '_update', tabela);
        execute format('create policy %I on public.%I for update to anon, authenticated using (true) with check (true)', tabela || '_update', tabela);
        execute format('drop policy if exists %I on public.%I', tabela || '_delete', tabela);
        execute format('create policy %I on public.%I for delete to anon, authenticated using (true)', tabela || '_delete', tabela);
    end loop;
end $$;
