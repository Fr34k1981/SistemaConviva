"""Backup seguro e restauracao controlada dos dados locais do Sistema Conviva."""

from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st


class BackupManager:
    """Gerencia backups locais com manifesto, retencao e restauracao segura."""

    def __init__(self, backup_dir: str | Path = "data/backups", data_dir: str | Path = "data"):
        self.project_root = Path(__file__).resolve().parents[1]
        self.data_dir = self._resolve_project_path(data_dir)
        self.backup_dir = self._resolve_project_path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.backup_dir / ".backup_state.json"

    def _resolve_project_path(self, caminho: str | Path) -> Path:
        caminho = Path(caminho)
        if caminho.is_absolute():
            return caminho
        return self.project_root / caminho

    @staticmethod
    def _nome_seguro(valor: str | None) -> str:
        valor = str(valor or "").strip()
        if not valor:
            return datetime.now().strftime("%Y%m%d_%H%M%S")
        valor = re.sub(r"[^a-zA-Z0-9_.-]+", "_", valor).strip("._")
        return valor[:80] or datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def _sha256_bytes(dados: bytes) -> str:
        return hashlib.sha256(dados).hexdigest()

    @staticmethod
    def _sha256_file(caminho: Path) -> str:
        h = hashlib.sha256()
        with caminho.open("rb") as f:
            for bloco in iter(lambda: f.read(1024 * 1024), b""):
                h.update(bloco)
        return h.hexdigest()

    def _deve_ignorar(self, caminho: Path) -> bool:
        try:
            partes = set(caminho.relative_to(self.project_root).parts)
        except ValueError:
            partes = set(caminho.parts)
        ignorados = {
            "__pycache__",
            ".conviva_cache",
            "cache",
            "backups",
            ".pytest_cache",
        }
        if partes.intersection(ignorados):
            return True
        if caminho.suffix.lower() in {".pyc", ".tmp", ".log"}:
            return True
        return False

    def _iter_arquivos_dados(self):
        extensoes = {".csv", ".json", ".xlsx", ".xls", ".txt", ".md", ".db", ".sqlite", ".sqlite3"}
        for arquivo in self.data_dir.rglob("*"):
            if not arquivo.is_file() or self._deve_ignorar(arquivo):
                continue
            if arquivo.suffix.lower() in extensoes:
                yield arquivo, f"data/{arquivo.relative_to(self.data_dir).as_posix()}"

    def _iter_arquivos_projeto(self):
        candidatos = [
            self.project_root / "app.py",
            self.project_root / "requirements.txt",
            self.project_root / "BACKUP_GUIDE.md",
        ]
        sql_dir = self.project_root / "sql"
        if sql_dir.exists():
            candidatos.extend(sql_dir.glob("*.sql"))
        for arquivo in candidatos:
            if arquivo.exists() and arquivo.is_file() and not self._deve_ignorar(arquivo):
                yield arquivo, f"projeto/{arquivo.relative_to(self.project_root).as_posix()}"

    def criar_backup(self, nome_customizado: str | None = None) -> bool:
        """Cria backup ZIP com manifesto SHA-256."""
        try:
            timestamp = self._nome_seguro(nome_customizado)
            backup_file = self.backup_dir / f"backup_{timestamp}.zip"
            tmp_file = backup_file.with_suffix(".zip.tmp")
            manifesto = {
                "criado_em": datetime.now().isoformat(timespec="seconds"),
                "versao": 2,
                "arquivos": [],
            }

            with zipfile.ZipFile(tmp_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                for arquivo, arcname in list(self._iter_arquivos_dados()) + list(self._iter_arquivos_projeto()):
                    zipf.write(arquivo, arcname=arcname)
                    manifesto["arquivos"].append({
                        "path": arcname,
                        "size": arquivo.stat().st_size,
                        "sha256": self._sha256_file(arquivo),
                    })
                zipf.writestr("manifest.json", json.dumps(manifesto, ensure_ascii=False, indent=2))

            os.replace(tmp_file, backup_file)
            return True
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
            try:
                if "tmp_file" in locals() and tmp_file.exists():
                    tmp_file.unlink()
            except Exception:
                pass
            return False

    def criar_backup_automatico_se_necessario(self, intervalo_horas: int = 24) -> dict:
        """Cria backup automatico somente quando o ultimo estiver antigo."""
        intervalo = timedelta(hours=max(1, int(intervalo_horas or 24)))
        agora = datetime.now()
        backups = [b for b in self.listar_backups() if not str(b["arquivo"]).startswith("backup_pre_restore_")]
        if backups:
            mais_recente = max(backups, key=lambda b: b["data_obj"])
            idade = agora - datetime.fromtimestamp(float(mais_recente["data_obj"]))
            if idade < intervalo:
                return {"criado": False, "motivo": "backup_recente", "arquivo": mais_recente["arquivo"]}

        nome = "auto_" + agora.strftime("%Y%m%d_%H%M%S")
        criado = self.criar_backup(nome)
        if criado:
            try:
                self.state_file.write_text(
                    json.dumps({"ultimo_backup": agora.isoformat(), "arquivo": f"backup_{nome}.zip"}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass
        return {"criado": criado, "motivo": "criado" if criado else "falha", "arquivo": f"backup_{nome}.zip"}

    def listar_backups(self) -> list[dict]:
        backups = []
        for backup_file in sorted(self.backup_dir.glob("backup_*.zip"), reverse=True):
            stat = backup_file.stat()
            tamanho_mb = stat.st_size / (1024 * 1024)
            timestamp_str = backup_file.stem.replace("backup_", "")
            try:
                data = datetime.strptime(timestamp_str.replace("auto_", ""), "%Y%m%d_%H%M%S")
                data_formatada = data.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                data_formatada = timestamp_str
            backups.append({
                "arquivo": backup_file.name,
                "caminho": backup_file,
                "tamanho_mb": round(tamanho_mb, 2),
                "data": data_formatada,
                "data_obj": stat.st_mtime,
                "manifesto": self._tem_manifesto(backup_file),
            })
        return backups

    @staticmethod
    def _tem_manifesto(caminho_backup: Path) -> bool:
        try:
            with zipfile.ZipFile(caminho_backup, "r") as zipf:
                return "manifest.json" in zipf.namelist()
        except Exception:
            return False

    def verificar_integridade_backup(self, caminho_backup: Path) -> tuple[bool, str]:
        try:
            with zipfile.ZipFile(caminho_backup, "r") as zipf:
                if "manifest.json" not in zipf.namelist():
                    return True, "Backup antigo sem manifesto; arquivo ZIP abre corretamente."
                manifesto = json.loads(zipf.read("manifest.json").decode("utf-8"))
                for item in manifesto.get("arquivos", []):
                    path = item.get("path", "")
                    if path not in zipf.namelist():
                        return False, f"Arquivo ausente no backup: {path}"
                    sha = self._sha256_bytes(zipf.read(path))
                    if sha != item.get("sha256"):
                        return False, f"Integridade falhou em: {path}"
            return True, "Integridade confirmada."
        except Exception as e:
            return False, f"Backup invalido: {e}"

    def _destino_seguro(self, destino_base: Path, membro: str) -> Path | None:
        partes = Path(membro).parts
        if not partes or any(p in {"..", ""} for p in partes):
            return None
        destino = (destino_base / Path(*partes)).resolve()
        try:
            destino.relative_to(destino_base.resolve())
        except ValueError:
            return None
        return destino

    def restaurar_backup(self, caminho_backup: Path) -> bool:
        """Restaura somente arquivos de dados, com protecao contra Zip Slip."""
        try:
            ok, msg = self.verificar_integridade_backup(Path(caminho_backup))
            if not ok:
                print(msg)
                return False

            self.criar_backup("pre_restore_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            with zipfile.ZipFile(caminho_backup, "r") as zipf:
                for info in zipf.infolist():
                    if info.is_dir():
                        continue
                    nome = info.filename.replace("\\", "/")
                    if nome == "manifest.json" or nome.startswith("projeto/"):
                        continue
                    if nome.startswith("data/"):
                        rel = nome[len("data/"):]
                    else:
                        # Compatibilidade com backups antigos que gravavam direto na raiz do ZIP.
                        rel = nome
                    destino = self._destino_seguro(self.data_dir, rel)
                    if destino is None:
                        continue
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    destino.write_bytes(zipf.read(info))
            return True
        except Exception as e:
            print(f"Erro ao restaurar backup: {e}")
            return False

    def deletar_backup(self, caminho_backup: Path) -> bool:
        try:
            caminho = Path(caminho_backup).resolve()
            caminho.relative_to(self.backup_dir.resolve())
            caminho.unlink()
            return True
        except Exception as e:
            print(f"Erro ao deletar backup: {e}")
            return False

    def limpar_backups_antigos(self, dias_retencao: int = 30, min_backups: int = 3) -> int:
        data_limite = datetime.now() - timedelta(days=max(1, int(dias_retencao or 30)))
        backups = sorted(self.backup_dir.glob("backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
        deletados = 0
        for idx, backup_file in enumerate(backups):
            if idx < min_backups:
                continue
            if backup_file.stat().st_mtime >= data_limite.timestamp():
                continue
            try:
                backup_file.unlink()
                deletados += 1
            except Exception as e:
                print(f"Erro ao deletar {backup_file}: {e}")
        return deletados

    def obter_info_backup(self, caminho_backup: Path) -> dict:
        try:
            info = {
                "arquivo": Path(caminho_backup).name,
                "tamanho": round(Path(caminho_backup).stat().st_size / (1024 * 1024), 2),
                "arquivos": [],
                "data_criacao": datetime.fromtimestamp(Path(caminho_backup).stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                "integridade": self.verificar_integridade_backup(Path(caminho_backup))[1],
            }
            with zipfile.ZipFile(caminho_backup, "r") as zipf:
                info["arquivos"] = [n for n in zipf.namelist() if n != "manifest.json"]
            return info
        except Exception as e:
            print(f"Erro ao obter info do backup: {e}")
            return {}

    def exportar_dados_texto(self) -> str:
        try:
            partes = [f"BACKUP MANUAL - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", "=" * 80, ""]
            for arquivo in sorted(self.data_dir.glob("*.csv")):
                try:
                    df = pd.read_csv(arquivo)
                    partes.append(f"{arquivo.name} ({len(df)} registros)")
                    partes.append(df.to_string(index=False))
                    partes.append("")
                except Exception as e:
                    partes.append(f"{arquivo.name}: falha ao ler ({e})")
            return "\n".join(partes)
        except Exception as e:
            print(f"Erro ao exportar dados: {e}")
            return ""


def render_backup_page():
    """Renderiza a pagina de gerenciamento de backups."""
    st.title("Gerenciamento de Backups")
    st.caption("Backups locais com manifesto de integridade e restauracao protegida.")

    backup_manager = BackupManager()

    st.markdown("### Criar backup")
    col_nome, col_btn = st.columns([2, 1])
    with col_nome:
        nome_backup = st.text_input("Nome customizado (opcional)", placeholder="antes_da_importacao")
    with col_btn:
        st.write("")
        if st.button("Criar backup agora", use_container_width=True):
            with st.spinner("Criando backup..."):
                if backup_manager.criar_backup(nome_backup or None):
                    st.success("Backup criado com sucesso.")
                    st.rerun()
                else:
                    st.error("Erro ao criar backup.")

    st.markdown("### Backups disponiveis")
    backups = backup_manager.listar_backups()
    if not backups:
        st.info("Nenhum backup disponivel ainda.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(backups))
        col2.metric("Tamanho total", f"{sum(b['tamanho_mb'] for b in backups):.2f} MB")
        col3.metric("Mais recente", backups[0]["data"])

        for idx, backup in enumerate(backups):
            selo = "manifesto" if backup.get("manifesto") else "backup antigo"
            with st.expander(f"{backup['arquivo']} - {backup['tamanho_mb']} MB - {backup['data']} ({selo})", expanded=(idx == 0)):
                ok, msg = backup_manager.verificar_integridade_backup(backup["caminho"])
                st.success(msg) if ok else st.error(msg)

                with open(backup["caminho"], "rb") as f:
                    st.download_button(
                        "Baixar ZIP",
                        data=f.read(),
                        file_name=backup["arquivo"],
                        mime="application/zip",
                        key=f"download_backup_{idx}",
                    )

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("Detalhes", key=f"info_backup_{idx}", use_container_width=True):
                        st.json(backup_manager.obter_info_backup(backup["caminho"]))
                with col_b:
                    if st.button("Restaurar dados", key=f"restore_backup_{idx}", use_container_width=True):
                        with st.spinner("Restaurando dados..."):
                            if backup_manager.restaurar_backup(backup["caminho"]):
                                st.success("Dados restaurados. Recarregue a pagina para ver o resultado.")
                            else:
                                st.error("Erro ao restaurar backup.")
                with col_c:
                    if st.button("Deletar", key=f"delete_backup_{idx}", use_container_width=True):
                        if backup_manager.deletar_backup(backup["caminho"]):
                            st.success("Backup deletado.")
                            st.rerun()
                        else:
                            st.error("Erro ao deletar backup.")

    st.markdown("### Limpeza")
    col_dias, col_limpar = st.columns([2, 1])
    with col_dias:
        dias = st.slider("Dias de retencao", min_value=7, max_value=180, value=30, step=1)
    with col_limpar:
        st.write("")
        if st.button("Limpar antigos", use_container_width=True):
            deletados = backup_manager.limpar_backups_antigos(dias_retencao=dias)
            st.info(f"{deletados} backup(s) antigo(s) removido(s).")

    st.markdown("### Exportacao legivel")
    dados_texto = backup_manager.exportar_dados_texto()
    st.download_button(
        "Baixar TXT",
        data=dados_texto.encode("utf-8"),
        file_name=f"dados_exportados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
    )
