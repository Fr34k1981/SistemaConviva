from db.repositories.alunos_repository import dataframe_from_rows


def test_dataframe_from_rows_empty():
    assert dataframe_from_rows([]).empty
