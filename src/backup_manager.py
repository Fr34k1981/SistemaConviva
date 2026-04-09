"""
Sistema de Backup Automático e Gerenciamento de Dados
"""
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st


class BackupManager:
    """Gerencia backups automáticos dos dados"""
    
    def __init__(self, backup_dir: str = "data/backups"):
        """
        Inicializa o gerenciador de backups
        
        Args:
            backup_dir: Diretório onde os backups serão salvos
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path("data")
    
    def criar_backup(self, nome_customizado: str = None) -> bool:
        """
        Cria um backup completo dos dados
        
        Args:
            nome_customizado: Nome customizado para o backup
        
        Returns:
            True se backup criado com sucesso
        """
        try:
            if nome_customizado:
                timestamp = nome_customizado
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            backup_file = self.backup_dir / f"backup_{timestamp}.zip"
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar arquivos CSV
                for csv_file in self.data_dir.glob("*.csv"):
                    zipf.write(csv_file, arcname=csv_file.name)
                
                # Adicionar arquivos de turmas
                turmas_dir = self.data_dir / "turmas"
                if turmas_dir.exists():
                    for turma_file in turmas_dir.glob("*.csv"):
                        zipf.write(turma_file, arcname=f"turmas/{turma_file.name}")
            
            return True
        
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
            return False
    
    def listar_backups(self) -> list:
        """
        Lista todos os backups disponíveis
        
        Returns:
            Lista de dicionários com informações dos backups
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("backup_*.zip"), reverse=True):
            stat = backup_file.stat()
            tamanho_mb = stat.st_size / (1024 * 1024)
            timestamp_str = backup_file.stem.replace("backup_", "")
            
            # Converter timestamp para datetime legível
            try:
                data = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                data_formatada = data.strftime("%d/%m/%Y %H:%M:%S")
            except:
                data_formatada = timestamp_str
            
            backups.append({
                "arquivo": backup_file.name,
                "caminho": backup_file,
                "tamanho_mb": round(tamanho_mb, 2),
                "data": data_formatada,
                "data_obj": stat.st_mtime
            })
        
        return backups
    
    def restaurar_backup(self, caminho_backup: Path) -> bool:
        """
        Restaura um backup
        
        Args:
            caminho_backup: Caminho do arquivo de backup
        
        Returns:
            True se restaurado com sucesso
        """
        try:
            # Criar backup atual antes de restaurar
            self.criar_backup("pre_restore_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            
            # Extrair backup
            with zipfile.ZipFile(caminho_backup, 'r') as zipf:
                zipf.extractall(self.data_dir)
            
            return True
        
        except Exception as e:
            print(f"Erro ao restaurar backup: {e}")
            return False
    
    def deletar_backup(self, caminho_backup: Path) -> bool:
        """
        Deleta um backup
        
        Args:
            caminho_backup: Caminho do arquivo de backup
        
        Returns:
            True se deletado com sucesso
        """
        try:
            caminho_backup.unlink()
            return True
        except Exception as e:
            print(f"Erro ao deletar backup: {e}")
            return False
    
    def limpar_backups_antigos(self, dias_retencao: int = 30) -> int:
        """
        Remove backups mais antigos que o período especificado
        
        Args:
            dias_retencao: Número de dias de retenção (padrão: 30)
        
        Returns:
            Número de backups deletados
        """
        data_limite = datetime.now() - timedelta(days=dias_retencao)
        timestamp_limite = data_limite.timestamp()
        deletados = 0
        
        for backup_file in self.backup_dir.glob("backup_*.zip"):
            stat = backup_file.stat()
            if stat.st_mtime < timestamp_limite:
                try:
                    backup_file.unlink()
                    deletados += 1
                except Exception as e:
                    print(f"Erro ao deletar {backup_file}: {e}")
        
        return deletados
    
    def obter_info_backup(self, caminho_backup: Path) -> dict:
        """
        Obtém informações sobre um backup
        
        Args:
            caminho_backup: Caminho do arquivo de backup
        
        Returns:
            Dicionário com informações do backup
        """
        try:
            info = {
                "arquivo": caminho_backup.name,
                "tamanho": caminho_backup.stat().st_size / (1024 * 1024),
                "arquivos": [],
                "data_criacao": datetime.fromtimestamp(
                    caminho_backup.stat().st_mtime
                ).strftime("%d/%m/%Y %H:%M:%S")
            }
            
            with zipfile.ZipFile(caminho_backup, 'r') as zipf:
                for arquivo in zipf.namelist():
                    info["arquivos"].append(arquivo)
            
            return info
        
        except Exception as e:
            print(f"Erro ao obter info do backup: {e}")
            return {}
    
    def exportar_dados_texto(self) -> str:
        """
        Exporta dados em formato texto legível para backup manual
        
        Returns:
            String com dados formatados
        """
        try:
            dados_texto = f"BACKUP MANUAL - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            dados_texto += "=" * 80 + "\n\n"
            
            # Alunos
            alunos_file = self.data_dir / "alunos_cadastrados.csv"
            if alunos_file.exists():
                df = pd.read_csv(alunos_file)
                dados_texto += f"ALUNOS ({len(df)} registros)\n"
                dados_texto += df.to_string() + "\n\n"
            
            # Ocorrências
            ocorrencias_file = self.data_dir / "ocorrencias.csv"
            if ocorrencias_file.exists():
                df = pd.read_csv(ocorrencias_file)
                dados_texto += f"OCORRÊNCIAS ({len(df)} registros)\n"
                dados_texto += df.to_string() + "\n\n"
            
            return dados_texto
        
        except Exception as e:
            print(f"Erro ao exportar dados: {e}")
            return ""


def render_backup_page():
    """Renderiza a página de gerenciamento de backups"""
    st.title("💾 Gerenciamento de Backups")
    
    from src.components import render_header, render_info_box
    
    render_header(
        titulo="💾 Gerenciamento de Backups",
        subtitulo="Backup e restauração de dados",
        descricao="Gerencie backups automáticos e restaure dados quando necessário"
    )
    
    backup_manager = BackupManager()
    
    # Seção de Backup Manual
    st.markdown("### ➕ Criar Backup Manual")
    col1, col2 = st.columns(2)
    
    with col1:
        nome_backup = st.text_input(
            "Nome customizado (opcional)",
            placeholder="ex: backup_antes_dados_importantes"
        )
    
    with col2:
        if st.button("🔄 Criar Backup Agora", use_container_width=True):
            with st.spinner("Criando backup..."):
                if backup_manager.criar_backup(nome_backup):
                    st.success("✅ Backup criado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao criar backup")
    
    render_info_box(
        "Backups automáticos são criados diariamente. Você também pode criar backups manuais aqui.",
        tipo="info"
    )
    
    st.markdown("---")
    
    # Seção de Backups Disponíveis
    st.markdown("### 📋 Backups Disponíveis")
    
    backups = backup_manager.listar_backups()
    
    if backups:
        # Resumo
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Backups", len(backups))
        with col2:
            tamanho_total = sum(b["tamanho_mb"] for b in backups)
            st.metric("Tamanho Total", f"{tamanho_total:.2f} MB")
        with col3:
            st.metric("Backup Mais Recente", backups[0]["data"])
        
        st.markdown("---")
        
        # Lista de Backups
        for idx, backup in enumerate(backups):
            with st.expander(f"📦 {backup['arquivo']} ({backup['tamanho_mb']} MB) - {backup['data']}", expanded=(idx==0)):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("🔄 Restaurar", key=f"restore_{idx}"):
                        with st.spinner("Restaurando backup..."):
                            if backup_manager.restaurar_backup(backup["caminho"]):
                                st.success("✅ Backup restaurado com sucesso!")
                                st.info("⚠️ Recarregue a página para ver os dados restaurados")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao restaurar backup")
                
                with col2:
                    if st.button("📥 Download", key=f"download_{idx}"):
                        with open(backup["caminho"], "rb") as f:
                            st.download_button(
                                label="Download",
                                data=f.read(),
                                file_name=backup["arquivo"],
                                mime="application/zip",
                                key=f"download_btn_{idx}"
                            )
                
                with col3:
                    info = backup_manager.obter_info_backup(backup["caminho"])
                    if st.button("📊 Detalhes", key=f"info_{idx}"):
                        st.json(info)
                
                with col4:
                    if st.button("🗑️ Deletar", key=f"delete_{idx}"):
                        if backup_manager.deletar_backup(backup["caminho"]):
                            st.success("✅ Backup deletado")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao deletar backup")
    else:
        st.info("📭 Nenhum backup disponível. Crie o primeiro backup agora!")
    
    st.markdown("---")
    
    # Seção de Limpeza Automática
    st.markdown("### 🧹 Limpeza Automática")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        dias = st.slider(
            "Dias de retenção (backups mais antigos serão removidos)",
            min_value=7,
            max_value=90,
            value=30,
            step=1
        )
    
    with col2:
        if st.button("Limpar Agora", use_container_width=True):
            deletados = backup_manager.limpar_backups_antigos(dias)
            if deletados > 0:
                st.success(f"✅ {deletados} backup(s) antigo(s) removido(s)")
                st.rerun()
            else:
                st.info("ℹ️ Nenhum backup antigo para remover")
    
    render_info_box(
        f"Backups com mais de {dias} dias serão removidos automaticamente",
        tipo="warning"
    )
    
    st.markdown("---")
    
    # Seção de Exportação
    st.markdown("### 📄 Exportar Dados em Texto")
    
    if st.button("📥 Exportar Dados Legíveis (TXT)"):
        dados_texto = backup_manager.exportar_dados_texto()
        
        st.download_button(
            label="📥 Download TXT",
            data=dados_texto.encode('utf-8'),
            file_name=f"dados_exportados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        with st.expander("👁️ Visualizar dados exportados"):
            st.text(dados_texto)
